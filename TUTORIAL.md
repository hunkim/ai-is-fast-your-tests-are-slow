# Tutorial: make a slow test suite fast in 15 minutes

You'll take a small test suite from **12.0 s to 1.1 s** without deleting or skipping a single test, then apply the
same steps to your own project. You need Node.js 22+ and Python 3.8+. No packages to install.

```bash
git clone https://github.com/hunkim/ai-is-fast-your-tests-are-slow
cd ai-is-fast-your-tests-are-slow/examples/slow-suite
```

## The idea in one paragraph

When a test suite is slow, the instinct is to run fewer tests or buy bigger machines. But most slow suites are not
busy — they are **waiting**: sleeping, retrying, or stuck because something keeps the process alive after the tests
finish. A waiting test uses almost no CPU. So the first question is not "which tests can I skip?" but
**"which tests are using the CPU, and which are just waiting?"**

## Step 1 — Measure the baseline

```bash
npm test
```

```
# tests 10
# pass 10
real 12.0 s
```

Ten tests, twelve seconds. Most of them are one-liners.

## Step 2 — Find the waiting

Run each test file on its own and compare **wall time** (how long it took) with **CPU time** (how long it
actually computed):

```bash
python3 ../../skills/fast-tests/scripts/profile_tests.py --cmd "node --test {file}" "test/*.test.mjs"
```

```
unit                            wall s    cpu s   cpu%  note
test/lingering-timer.test.mjs      5.1      0.1     2%  WAITING
test/retry.test.mjs                3.6      0.1     2%  WAITING
test/sleepy.test.mjs               2.2      0.1     4%  WAITING
test/busy.test.mjs                 1.0      1.0    98%
test/fast1.test.mjs                0.1      0.1    80%
…
waiting: 3 units spend ~10.6 s (85% of serial time) not using the CPU
long pole: test/lingering-timer.test.mjs (5.1 s) — no worker count can finish faster than this
```

Three files use 2–4% CPU: they are waiting. `busy.test.mjs` is genuinely working (98% CPU) — that one is fine.

Also try the static scanner, which finds suspicious patterns without running anything:

```bash
python3 ../../skills/fast-tests/scripts/scan_test_smells.py .
```

It flags the `setTimeout(r, 2100)` sleep and the `--test-concurrency=1` setting in `package.json`.

## Step 3 — Remove the three waits

Each file shows one pattern that is extremely common in real projects. The fixed versions are in
`examples/fast-suite`.

### Wait 1: sleeping for an interval — `sleepy.test.mjs` (2.2 s)

The cache flushes every 2 seconds, so the test sleeps 2.1 seconds:

```js
const cache = new Cache({ flushMs: 2000 });
cache.set("a", 1);
await new Promise((r) => setTimeout(r, 2100)); // ✗ waits for real
assert.equal(cache.flushed, 1);
```

**Fix: control the clock.** Fake timers make time pass instantly:

```js
test("the cache flushes to disk", (t) => {
  t.mock.timers.enable({ apis: ["setInterval"] });
  const cache = new Cache({ flushMs: 2000 });
  cache.set("a", 1);
  t.mock.timers.tick(2000); // ✓ two seconds pass instantly
  assert.equal(cache.flushed, 1);
  cache.close();
});
```

(Jest: `jest.useFakeTimers()` + `jest.advanceTimersByTime()`. Vitest: `vi.useFakeTimers()`. Python: `time-machine`
or `freezegun`. Go 1.25+: `testing/synctest`. If the code runs in another process, make the interval configurable
instead and set it short in tests.)

### Wait 2: a timer that keeps the process alive — `lingering-timer.test.mjs` (5.1 s)

The test itself finishes in 1 ms. But the code under test schedules a metrics upload 5 seconds later and never
cancels it, so Node can't exit until the timer fires:

```js
count(name) {
  this.pending.push(name);
  this.timer ??= setTimeout(() => this.upload(), 5000); // ✗ holds the process open
}
```

**Fix: background timers shouldn't keep a process alive.** One line in the source:

```js
this.timer = setTimeout(() => this.upload(), 5000);
this.timer.unref?.(); // ✓ doesn't hold the process (no-op in browsers)
```

This is the most invisible wait of all: every test passes quickly, yet the file takes seconds. In our real-world
[case study](CASE-STUDY.md), 22 files each sat idle for 30 seconds after their last test because of timers like
this.

### Wait 3: a fake failure that triggers real retries — `retry.test.mjs` (3.6 s)

The client retries network errors with backoff (0.5 s, 1 s, 2 s). The test simulates "the server is down" by
throwing, so it sits through all three retries:

```js
const fetch = async () => { throw new Error("network down"); }; // ✗ retried 3 times
```

**Fix: simulate the failure you mean.** "The load failed" is an HTTP error, which the client doesn't retry:

```js
const fetch = async () => new Response("{}", { status: 500 }); // ✓ answered, not retried
```

(When you do want to test the retry logic itself, pass the delays in: `getJson(path, { fetch, delays: [0, 0, 0] })`.)

## Step 4 — Use all your cores

The suite ran files one at a time (`--test-concurrency=1`). Each test file here is independent (no shared files,
ports, or databases), so run several at once:

```json
"test": "node --test --test-concurrency=8 'test/*.test.mjs'"
```

## Step 5 — Measure again

```bash
cd ../fast-suite
npm test
python3 ../../skills/fast-tests/scripts/profile_tests.py --cmd "node --test {file}" "test/*.test.mjs"
```

```
# tests 10
# pass 10
real 1.1 s

waiting: 0 units spend ~0.0 s (0% of serial time) not using the CPU
long pole: test/busy.test.mjs (1.1 s)
```

**12.0 s → 1.1 s.** Same ten tests, all passing. Now the only thing left is real work (`busy.test.mjs`), which is
exactly what should be left.

Notice the order: if we had only added parallelism, the 5-second lingering file would still be the long pole —
no number of workers can finish faster than the slowest file.

## Step 6 — Do it on your project

1. **Baseline.** Time the exact command your CI runs.
2. **Profile.** Point the profiler at your runner — it works with anything that can run one file:
   ```bash
   profile_tests.py --cmd "npx jest {file}"             "src/**/*.test.ts"
   profile_tests.py --cmd "npx vitest run {file}"       "src/**/*.test.ts"
   profile_tests.py --cmd "python -m pytest -q {file}"  "tests/**/test_*.py"
   profile_tests.py --cmd "go test ./{file}"            pkg/a pkg/b pkg/c
   profile_tests.py --cmd "bundle exec rspec {file}"    "spec/**/*_spec.rb"
   ```
3. **Remove the waits** in every WAITING file. The catalogue of patterns and fixes per language is in
   [`skills/fast-tests/references/waits.md`](skills/fast-tests/references/waits.md).
4. **Parallelize** — after checking that each file uses its own temp dir, port and database
   ([isolation checklist](skills/fast-tests/references/parallel.md#isolation-checklist)). Run the suite three
   times to prove it's stable.
5. **Split the long pole** if one file bounds the total.
6. **Run the whole suite before every push.** Once it's fast, there's little reason to run less.

## Step 7 — Keep it fast when you add tests

A fast suite stays fast only if new tests follow the same rules. Before merging, check the test files you added or
changed against a budget — a time limit, no waiting, and repeated runs to catch flakiness:

```bash
python3 ../../skills/fast-tests/scripts/profile_tests.py --cmd "node --test {file}" \
  --max-seconds 2 --fail-on-waiting --repeat 5 test/sleepy.test.mjs
```

In `slow-suite` this fails (`OVER 2s`, `WAITING`); in `fast-suite` it passes. It exits with code 1 on any
violation, so it works as a CI job for pull requests
([example](skills/fast-tests/references/new-tests.md#enforce-it-in-ci)). The design checklist for new tests is in
[`references/new-tests.md`](skills/fast-tests/references/new-tests.md).

## Step 8 — Give it to your AI agent

The [`fast-tests` skill](skills/fast-tests/SKILL.md) packages this whole method so a coding agent can do it — and
so it runs tests efficiently in its own loop.

- **Claude Code:** copy the folder into your skills directory, and Claude will use it when tests come up:
  ```bash
  mkdir -p ~/.claude/skills && cp -R skills/fast-tests ~/.claude/skills/        # all projects
  mkdir -p .claude/skills && cp -R /path/to/skills/fast-tests .claude/skills/    # one project
  ```
  Then ask: *"Our tests are slow — use the fast-tests skill to speed them up."*
- **Other agents (Codex, Cursor, Gemini CLI, …):** add a line to `AGENTS.md`:
  *"When tests are slow or flaky, or before changing how tests run, follow `skills/fast-tests/SKILL.md`."*
  Also add your gate command and the rules from the
  [AGENTS.md snippet](skills/fast-tests/references/agents.md#agentsmd-snippet).

## Why this matters now

An AI agent can write a change in seconds. It then waits for the tests — every iteration, every agent, every PR.
A 12-minute suite allows about five verified iterations an hour; a 24-second suite allows 150. When code is cheap,
**verification speed is development speed**. The evidence is in [RESEARCH.md](RESEARCH.md).
