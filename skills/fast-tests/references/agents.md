# Tests and AI coding agents

When code is cheap to generate, the rate at which you can *verify* it sets the pace. For an agent, the test suite
is three things at once: the feedback signal in its loop, the oracle that says "done", and an attack surface it may
learn to game. Make it fast, make it unambiguous, and protect it.

## What the evidence says

- Test re-execution appears in 49.7–83.0% of agent tasks, driven by not knowing the repo's test runner and by
  truncated or ambiguous output; developer-written skills cut agent cost 7.9–41.7% (Hu et al. 2026).
- Frontier models cheat on ~50% of tasks whose tests contradict the spec (edit tests, special-case, override
  equality); an explicit "the tests are wrong" option cut one model's cheating from 54% to 9% (ImpossibleBench 2025).
- 80.2% of test changes in agent PRs have weak or no assertions (Banik et al. 2026); tests agents write mid-task
  don't raise resolution rates but cost 9–20% more tokens (Chen et al. 2026). The value is in the existing,
  trusted suite.
- Affected-only runs miss regressions: 7.8% of SWE-bench patches that passed the modified test files failed the
  full suite (Wang et al. 2026).
- Trimming logs to the relevant lines kept diagnosis accuracy with 4.5× fewer tokens (LogSage 2025).
- Context files help when short and command-first; long ones add cost without improving success (Gloaguen et al.
  2026; Lulla et al. 2026).

## Repo setup for agents

1. **One documented gate command** that CI also runs (`npm run check`, `make test`, `just test`), plus how to run
   one file and one test. Put it at the top of AGENTS.md / CLAUDE.md.
2. **Fast**: the full gate ideally ≤ 1–2 minutes (remove waits, parallelize). Every agent iteration pays it.
3. **Deterministic**: no sleeps, no real network, flakes quarantined in a machine-readable list.
4. **Compact output**: a quiet reporter by default (dots/summary + failures only). Full logs go to a file.
5. **Isolated**: tests pick their own temp dirs and ports, so several agents (worktrees) can run suites at once.
6. **Protected oracle**: CI flags diffs that delete, skip, or weaken tests; for autonomous runs consider read-only
   test directories or a hidden holdout suite.
7. **Automatic gate**: a pre-push hook or required CI check runs the full suite, so "done" can't skip it.

### AGENTS.md snippet

```markdown
## Tests
- Gate (run before saying a task is done): `npm run check` — typecheck + all tests, ~25 s, 10 workers
- One file: `npx vitest run path/to/file.test.ts`   One test: add `-t "name"`
- While editing: `npx vitest related --run <changed files>`
- Output is quiet by default; full log: `npm run check > /tmp/test.log 2>&1; grep -n "FAIL\|✗" /tmp/test.log`
- Loop: full gate before editing → a test that fails without the change → change → affected tests → full gate again.
- Rules: never delete/skip/weaken a test to make it pass — if a test looks wrong, say so. No sleeps; use fake
  timers or wait for a condition. No fixed ports/paths (port 0, temp dirs). Every change ships with a test.
- Known flaky tests: `test/quarantine.txt`
```

### TESTING.md template

```markdown
# Testing

The whole suite runs before every push (`<gate command>`, ~N s, W workers). Keep it that fast:
a slow test is almost always a wait, not work.

## Running
| Command | What | When |
|---|---|---|
| `<gate>` | typecheck + every test | before every push (hook) |
| `<affected>` | only tests the change can reach | quick loops while editing |
| `<one file>` | one file | debugging |
Workers: `TEST_WORKERS` (default W; 1 = serial for debugging).

## Writing a test
- Independent: own temp dir, port 0, own DB/schema; passes alone and in any order.
- No waiting on the clock: configurable intervals, fake timers, condition waits; simulate failures with a
  non-retried error (e.g. HTTP 500), not a thrown network error.
- Background timers must not keep a process alive (`unref`, daemon threads, teardown).
- Assert behavior people see; add a regression test for every bug fixed.

## When the suite gets slow
Profile wall vs CPU per file (`profile_tests.py`). Low CPU + high wall = waiting: remove the wait first,
then split the long pole, then add workers.
```

## Agent loop, step by step

1. Read AGENTS.md/CLAUDE.md/CI config for the gate command and one-file command. If missing, find them in package
   scripts, Makefile, CI workflow; don't guess a runner.
2. **Run the full gate before editing anything** and keep the summary. Red before you start is reported, not
   silently fixed or blamed on your change later.
3. **Write or extend a test that fails without your change** — a reproduction for a bug, the expected behavior
   from the spec for a feature. Watch it fail for the right reason.
4. Edit → run the affected tests → read only the failures → edit.
5. Budget-check the test files you added or changed (`profile_tests.py --max-seconds … --fail-on-waiting --repeat 5`).
6. **Run the full gate again** and show both summaries (passed/failed/skipped, time). Done means: green, at least
   as many passing tests as in step 2, no new skips.
7. If something unrelated fails: re-run that single test once. Flips → report as flaky with evidence; consistent
   failure → investigate or report, never paper over it.
8. Leave the suite at least as fast as you found it: no new sleeps, fixed ports, or real network calls.

## Reviewing agent-written tests

- Does each test assert the *expected* behavior (from the spec/issue), not just "no exception"?
- Would it fail if the fix were reverted? (Revert the source change and run it, or use a targeted mutant.)
- Are error paths covered, not only the happy path?
- Is it deterministic (stress it 20× in random order) and fast (no waits)?
