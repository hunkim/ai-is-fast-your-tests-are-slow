---
name: fast-tests
description: Make a test suite fast and trustworthy without skipping tests, and run tests efficiently as a coding agent. Use when tests or CI are slow ("tests take too long", "CI is the bottleneck", "speed up the test suite"), when considering test selection / affected-test runs / parallel workers / sharding, when tests are flaky or hang after finishing, when adding or changing tests (so new tests never become the bottleneck), or when setting up how agents should run tests in a repo. Measures first (wall vs CPU per file), removes idle waits, parallelizes safely, budgets every new test file, and keeps the full suite as the gate.
---

# Fast tests

In the AI coding era, generating a change takes seconds and verifying it is the bottleneck. Most of a slow suite's
time is not work but **waiting**: sleeps, retry backoff, timers that hold a finished process open, network
timeouts, serial execution on idle cores. Remove the waits, then parallelize, and the full suite usually becomes
fast enough to run on every change. Test selection comes last, and only for the inner loop.

Evidence for every rule here: [RESEARCH.md](https://github.com/hunkim/ai-is-fast-your-tests-are-slow/blob/main/RESEARCH.md)
(~270 sources). Condensed numbers: [references/evidence.md](references/evidence.md).

## Non-negotiables

- **Never trade correctness for speed.** Don't delete, skip, weaken or mark tests as expected-to-fail to make the
  suite faster. The number of passing tests after your change must be ≥ before, with no new skips.
- **Measure before and after.** Every claim of "faster" comes with numbers from the same command on the same
  machine.
- **The gate runs everything.** Selective runs are for the edit loop. Before a change is done (commit, push,
  PR, "task complete"), the full suite runs and passes.
- **No hiding.** Don't raise timeouts, add retries, add `--forceExit`/`--exit`, or disable isolation to make a
  symptom go away. Find the cause.

## The loop for any change

Every change to code follows the same six steps, whether a person or an agent makes it. Fast tests exist so this
loop is cheap enough to run every time.

1. **Full suite first, before editing anything.** Record the result. Green means a later red is yours; red means
   report it before you start, and don't count it against your change. (Never "fix" pre-existing failures silently.)
2. **Write or extend a test that fails without the change.** For a bug, reproduce it; for a feature, assert the
   expected behavior from the spec. Run it and watch it fail for the right reason. Follow the new-test rules below.
3. **Make the change.**
4. **Run the affected tests** (the new/changed test, its file, related files) until they pass.
5. **Budget-check the test files you added or changed** (time, no waiting, repeated runs — below).
6. **Full suite again**, then report both runs: the exact command, tests passed/failed/skipped, time. The change
   is done only when step 6 is green with at least as many passing tests as step 1 and no new skips.

If the full suite takes too long to run twice per change, that is the problem to fix first (next sections), not a
reason to skip steps 1 or 6.

## Workflow: adding or changing a test

A fast suite stays fast only if every new test follows the same rules. Most flaky tests are flaky from the day they
are written (75–78%), and one slow new file can become the whole suite's long pole. Apply this to every test you
write — as a person or an agent.

**Before writing** (design; details in [references/new-tests.md](references/new-tests.md)):

1. **Lowest level that can catch the bug.** Unit over integration over end-to-end; a new E2E test needs a reason.
2. **No waiting on the clock.** Fake timers or an injected clock for anything time-based; configurable intervals
   when the code runs in another process; wait for conditions, never `sleep(N)`.
3. **Simulate the failure you mean.** A non-retried error (e.g. HTTP 500), not a thrown network error that triggers
   backoff; or inject zero retry delays.
4. **Independent.** Own temp dir, port 0, own DB/schema, unique names; reset any global state; no reliance on other
   tests or order.
5. **Hermetic.** No real network or external services; local fakes on port 0.
6. **Nothing outlives the test.** Close servers/pools/sockets, clear timers, join threads.
7. **Asserts expected behavior** from the spec or bug report (write it first and watch it fail), not whatever the
   code currently does.
8. **Right file.** Add to the feature's file if it stays small; don't grow the suite's long pole.

**After writing** — check the new/changed test files against a budget, repeated to catch flakiness:

```bash
# new or modified test files on this branch
FILES=$(git diff --name-only --diff-filter=AM origin/main...HEAD | grep -E '(^|/)(test|tests|spec|__tests__)/|[._](test|spec)\.' )
python3 scripts/scan_test_smells.py $FILES
python3 scripts/profile_tests.py --cmd "<run one test file>" --max-seconds 2 --fail-on-waiting --repeat 5 $FILES
```

- Budget: unit-test files ≤ 1–2 s each; integration files ≤ 10 s; never above the suite's current long pole.
- Any WAITING, OVER budget or FLAKY result: fix the test (or the code's timers) before merging, don't raise the
  budget. Then run the full suite once.
- Make it automatic: the same two commands as a CI job or pre-push step on changed test files
  ([references/new-tests.md](references/new-tests.md#enforce-it-in-ci)).

## Workflow: speeding up a suite

Work through the steps in order. Each step usually makes the next one cheaper, and the first two are where most of
the time is.

### 1. Baseline

Find the exact command CI (or the deploy/pre-push hook) runs. Run it once and record: wall time, number of tests,
passed/failed/skipped, worker count, CPU count (`nproc` / `sysctl -n hw.ncpu`). If the suite has more than one part
(server/web, packages), time each part.

### 2. Profile per file: wall vs CPU

```bash
python3 scripts/profile_tests.py --cmd "<run one test file>" "<glob>" [--workers N] [--json out.json]
# e.g.  --cmd "npx jest {file}"   --cmd "node --test {file}"   --cmd "python -m pytest -q {file}"
#       --cmd "npx vitest run {file}"   --cmd "go test ./{file}" (units = package dirs)   --cmd "bundle exec rspec {file}"
```

Read four numbers ([references/evidence.md](references/evidence.md#where-the-time-goes)):

| Signal | Meaning | Go to |
|---|---|---|
| Files marked **WAITING** (low CPU %, high wall) | Sleeping, backing off, held open by a timer, timing out | Step 3 |
| Serial sum ≫ wall at N workers is not achieved | Not parallel, or parallel but idle | Step 4 |
| **Long pole** ≈ projected wall time | One file bounds the whole run | Step 5 |
| Time before first / after last test | Serial setup (install, compile, boot, migrate) | Step 6 |
| Files that fail when run alone | Order dependence / shared state | [references/flaky.md](references/flaky.md) |

Also run `python3 scripts/scan_test_smells.py <test dirs>` for static hints (sleeps, fixed ports and paths, real
network calls, retry annotations, serial-only settings, focused tests).

### 3. Remove idle waits (usually the biggest win)

For each WAITING file, find out *what* it waits on. Check if the tests themselves are slow or the process is.
Per-test durations are in any reporter (`--test-reporter=tap`, `pytest --durations=0`, Jest `--verbose`, `go test
-json`, `rspec --profile`):

- **Tests fast, file slow** → something outlives the tests: a timer, interval, socket, child process, thread, or
  unawaited promise. Find it (Jest `--detectOpenHandles`, `why-is-node-running`, `faulthandler`/thread dumps) and
  fix it at the source, or `unref` background timers.
- **One test slow** → a sleep, a retry with backoff, a timeout, or a real network call on its path.

Fix patterns, per language: [references/waits.md](references/waits.md). The common ones:

| Wait | Fix |
|---|---|
| `sleep(N)` to wait for something | Wait for the condition (poll with a deadline), or await the event |
| Waiting out a production interval (flush every 20 s) | Make the interval configurable; shorten it in tests, or use fake timers |
| Mock failure that the client retries with backoff | Simulate the failure you mean (an HTTP 500 is an answer; a thrown error is retried), or inject zero delays |
| Background timer holds a finished test process open | `unref()` it at the source (JS), make threads daemon (Python), or stop it in teardown |
| Real network / DNS timeout | Local fake on port 0, or a stub |
| Per-test service boot (DB, browser, container) | Boot once per worker; isolate by schema/transaction/temp dir |

Re-profile after each fix. Stop when no file is WAITING.

### 4. Parallelize, with proof of isolation

1. Check isolation ([references/parallel.md](references/parallel.md#isolation-checklist)): every file gets its own
   temp dir, DB/schema, port 0 (OS-assigned), unique queue names; no fixed paths; no shared mutable globals across
   files; no dependence on another file having run first.
2. Set workers to about the CPU count (the user may name a number; ~10 on a 16-core machine is a good default).
   Make it overridable (`TEST_WORKERS=1` for debugging). Flags per runner: [references/parallel.md](references/parallel.md#workers-per-runner).
3. Prove it: run the full suite **3 times** in a row, and once in **random order** if the runner supports it. Zero
   failures, zero cancelled. A failure only in parallel is an isolation bug; fix it and don't lower the workers.

### 5. Split the long pole

With P workers, wall ≥ max(longest file, total / P). If the longest file is close to the projected wall time, split
it by feature, or move its slow part to its own file. On CI with several machines, shard by **duration**, not file
count ([references/parallel.md](references/parallel.md#sharding)).

### 6. Cut serial overhead and cache

Cache dependencies/environments keyed by lockfile; start services once; reuse compiled output. If tests are
hermetic, cache test results by input hash (Bazel, Go test cache, Nx/Turborepo).

### 7. Order and select (inner loop only)

- Order: previously failed first, then new/changed tests (`pytest --ff --nf`, Jest does this by default).
- Selection (affected tests only) is for the edit loop: `jest --findRelatedTests`, `vitest related`,
  `pytest --testmon`, `nx affected`, `bazel query rdeps`. Expect it to under-deliver in code with hub modules;
  details and tools: [references/selection.md](references/selection.md).
- The full suite stays the gate. If the full suite is already under ~2 minutes, selection rarely pays for its risk.

### 8. Lock it in

- Add a regression test for each structural fix (e.g. a fixture file that leaves long timers behind must exit
  within N seconds).
- Write the rules down where people and agents look (a TESTING.md or a section in AGENTS.md/CLAUDE.md). Template:
  [references/agents.md](references/agents.md#testingmd-template).
- Make the gate automatic (pre-push hook or required CI check) if it isn't.
- Report a before/after table: per part and total, serial → final, tests passed, runs checked.

## Working as a coding agent in any repo

These rules make your own loop fast and your results trustworthy ([references/agents.md](references/agents.md)):

1. **Find the real test command** (CI config, package scripts, Makefile, AGENTS.md) and how to run one file or test.
   Don't guess; a wrong runner causes repeated reruns.
2. **Baseline:** run the full suite once before editing, and keep the result.
3. **Inner loop:** after each edit, run the affected tests (the file you changed, its test, related tests).
4. **Before saying done:** run the full suite (or the repo's gate command) again and show both summaries.
   Affected-only runs miss regressions.
5. **Keep output compact:** summary line plus failing tests; send full logs to a file and grep them. Don't paste
   thousands of lines into context.
6. **Never make tests pass by changing the tests** unless the task is to change the tests. Don't delete, skip,
   special-case, or loosen assertions. If a test seems wrong, say so and ask.
7. **Every change ships with a test that fails without it** — written first (see it fail, then make it pass). A bug
   gets a reproduction; a feature gets an assertion of the expected behavior from the spec, not of whatever the
   code currently does.
8. **Don't add waits.** No fixed sleeps in new tests; use fake timers or condition waits. No fixed ports or paths.
9. **Flaky failure?** Re-run that one test once to classify it; if it is unrelated to your diff and flips, report it
   as flaky with evidence. Don't retry the whole suite in a loop.
10. **Parallel agents:** use your own worktree and your own ports, DBs and temp dirs so concurrent runs don't collide.

## Done criteria for a speed-up task

- [ ] Before/after numbers from the same command, per part and total
- [ ] Same or more tests passing; no new skips/xfails; no weakened assertions
- [ ] Full suite green 3 times in a row at the new worker count (and once in random order if supported)
- [ ] No WAITING files left in the profile (or each remaining one explained)
- [ ] Regression test(s) for structural fixes; rules written down; gate runs the full suite
