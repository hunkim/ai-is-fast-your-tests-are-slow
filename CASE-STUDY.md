# Case study: 12 minutes → 24 seconds

A real production TypeScript monorepo (a Node server and a React web app, built largely by AI coding
agents): 120 test files, ~900 tests, `node:test` via `tsx`. The team's complaint was "tests are too slow; we're a
big project now, testing is the bottleneck." The request was to apply the research on change-based test selection.

## What we expected vs what we found

**Expected:** run fewer tests — pick only the ones a change can affect.

**Found:** the repo already had a static, file-level selector (`check:changed`, the same idea as Ekstazi/STARTS),
and it barely helped. A diff touching three recent commits selected **56/59** server files and **54/61** web files,
because hub modules (`store.ts`, `db.ts`) are imported, directly or transitively, by almost every test. This is the
known weak spot of dependency-based selection: in a codebase with hubs, most changes reach most tests.

The suite was also running **serially** (`--test-concurrency=1`) on a 16-core machine.

## Step 1 — measure before choosing a fix

| Suite | Tests | Serial wall time |
|---|---|---|
| server | 372 | 65 s |
| web | 522 | **667 s** |

Per-file profiling (wall time vs CPU time, one process per file) showed the web number was mostly idle:

```
unit                      wall s   cpu s   cpu%
test/nav.test.ts            30.3     0.5     1%   ← 22 tests, all done in 30 ms
test/store.test.ts          31.0     …       …
… 22 files at ~30 s, the rest < 1 s
```

A file whose tests finish in 30 ms but whose process lives 30 s is **waiting**, not working. Parallelism would
only have overlapped the waiting.

## Step 2 — remove the waits (the big win)

| Root cause | Where | Effect | Fix |
|---|---|---|---|
| App background timers (perf-metrics flush 30 s, polling 20 s, toast/mark-read debounces) kept each finished test process alive | 22 web files | ~30 s per file after the last test | In the web test setup, timers ≥ 1 s are `unref`'d; one ref'd handle keeps the process alive until the file's tests finish (`after()`), so tests that *wait* on a timer still work |
| Mock API route `throw`s → client treats it as a network error → GET retry backoff (0.5+1+2+3+4+5+5 s) | 2 web tests | ~20 s each | Answer `HTTP 500` (not retried). Throw only when testing the retry itself |
| Test `sleep(21_000)` to wait for a 20 s vault flush interval | 1 server test | 21 s | Interval configurable by env (`VAULT_FLUSH_MS=500`), test waits 1 s |
| A 5 s debounced cache-write timer not `unref`'d | 3 server files | 5 s each | `.unref()` (the codebase already did this for the vault flush) |

Result, still serial: web **667 s → 79 s**, server 65 s → ~35 s.

## Step 3 — parallelize (safe because tests were already isolated)

Every test file already used its own `mkdtemp` directory for DB/vault files and an OS-assigned port (`port 0`),
and `node:test` runs each file in its own process. So raising concurrency was a one-flag change:
`--test-concurrency=${TEST_WORKERS:-10}`. The selective runner was changed to run both apps at once.

| | Before | After |
|---|---|---|
| server | 65 s | 9 s |
| web | 667 s | ~15 s |
| full gate (`typecheck + all tests`) | ~12 min | **~24 s** |

Three consecutive full runs: 0 failures, 0 cancelled. Parallelism alone (before removing waits) gave 12 min → 2 min;
removing waits first is what made it 24 s, because the long pole (a 30 s idle file) disappeared.

## Step 4 — change the policy

With a 24 s full suite, selection stopped being worth its risk as a gate:

- The pre-push hook now runs **every** test (it previously only type-checked; the auto-deploy also only
  type-checks, so the hook is where tests gate code).
- `check:changed` stays for the inner loop while editing, never as the gate.

## Step 5 — lock it in

- A regression test runs a fixture file that leaves 30 s / 20 s timers behind and waits on a 1.2 s timer; it must
  exit in < 10 s. With the setup fix disabled it fails (process never exits → 10 s timeout); with it, 1.5 s.
- A written testing guideline (independence rules, "no waiting on the clock", how to profile).
- A lesson in the project's lessons file: *a slow test is a wait, not work*.

## Takeaways

1. **Profile wall vs CPU per file first.** 85–90% of this suite's time was idle.
2. **Selection underdelivers in hub-heavy code.** It was the first idea and the least effective one here.
3. **Parallelism needs isolation and is capped by the long pole.** Remove the long idle files first.
4. **When the full suite is fast, run all of it.** Selection is an inner-loop tool; the gate should be complete.
5. **Agents make this matter more.** Every agent iteration and every agent-authored PR pays the suite's latency;
   12 minutes per check means a handful of verified iterations per hour, 24 s means over a hundred.
