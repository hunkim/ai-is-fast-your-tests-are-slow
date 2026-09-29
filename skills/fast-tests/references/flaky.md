# Flaky tests: prevent, detect, quarantine

A flaky test passes and fails on the same code. At Google ~16% of tests show some flakiness and 84% of
pass→fail transitions involve a flaky test (Micco 2017; Memon et al. 2017). Flakes waste reruns, block
parallelism, and teach people — and agents — to ignore red.

## Root causes (most common first)

| Cause | Share | Fix |
|---|---|---|
| Async wait (fixed sleeps, missing awaits) | 45% of fixes (Luo 2014) | Condition waits, fake timers ([waits.md](waits.md)) |
| Concurrency (races) | 20–26% | Deterministic scheduling; await all work; avoid shared mutable state |
| Order dependence / shared state | 12% (Java commits) to 59% (Python suites) | Isolation checklist ([parallel.md](parallel.md)); reset globals |
| Resources / environment | 46.5% resource-affected; 86% of Microsoft's flaky tests only in CI | Size timeouts for loaded CI; don't oversubscribe cores; hermetic setup |
| Time, randomness, unordered collections, floats | Small each; randomness #1 in generated tests | Pin clock/timezone; seed RNG and print seed; sort before compare; approximate float compare |

75–78% of flaky tests are flaky from the day they are written (Luo 2014; Lam et al. 2020): the cheapest place to
catch them is the PR that adds them.

## Rules for new tests

1. Never sleep to wait; await or poll a condition.
2. Await everything; nothing outlives the test.
3. Control time (fake or injected clock) and randomness (seeded, printed).
4. No shared mutable global state; fresh fixtures per test.
5. Every external resource per test or per worker: temp dir, port 0, DB schema, unique names.
6. Passes alone, in any order, and twice in a row.
7. Hermetic unit tests: no real network.
8. Tolerant where the domain is (float `approx`, sort unordered collections); never assert on exact durations.
9. Declare any dependency you truly need (a group), instead of relying on order.
10. Stress new and modified tests before merge (below) — especially AI-generated ones.

## Detect

**Stress changed tests at PR time** (catches most flakes):
```bash
for i in $(seq 20); do npx jest --randomize path/to/new.test.ts || break; done
for i in $(seq 20); do npx vitest run --sequence.shuffle path/to/new.test.ts || break; done
go test -run 'TestNew' -count=50 -shuffle=on -race ./pkg/...
for i in $(seq 20); do pytest -p randomly --randomly-seed=$i tests/test_new.py || break; done
bazel test //pkg:new_test --runs_per_test=50
```
Also run them with more workers than cores once, to expose resource sensitivity.

**Random order in CI with the seed printed** (`jest --randomize --showSeed`, `go test -shuffle=on`,
`pytest-randomly`, `rspec --order rand`, `vitest --sequence.shuffle`), so any failure can be replayed and bisected
to the polluting test (iDFlakies/iFixFlakies for Java, iPFlakies for Python).

**Cheap triage signal:** if the failing test did not execute any changed code, it is probably flaky (DeFlaker).

Detecting flakiness by reruns alone is expensive: ~170 reruns for 95% confidence (Gruber et al. 2021).

## Retries: diagnosis, never silence

If you retry, record the result as **flaky**, not pass: Surefire `rerunFailingTestsCount` (reports
`flakyFailure`), Gradle test-retry with `failOnPassedAfterRetry`, Playwright `--retries` ("flaky" status),
Bazel `FLAKY`, `pytest-rerunfailures --reruns 2 --only-rerun <InfraError>`. Cap the budget.

## Quarantine

- Score each test over a window (e.g. last 50 runs). Above a threshold, take it off the blocking path
  automatically and open a ticket for its owner. Slack went from 57% to 3.85% failing test jobs this way;
  GitHub from 9% to < 0.5% flaky builds.
- Quarantine means **not blocking**, not deleted: keep running it off the critical path; bring it back after N
  consecutive passes. About a quarter of flaky-test fixes found real bugs (Luo 2014).
- Keep the quarantine list machine-readable (a file in the repo) so agents can read it.
- Critical tests are never quarantined; they get fixed first.

## For agents

- Read the quarantine list before interpreting failures.
- On a failure unrelated to your diff, re-run that one test once. If it flips, report it as flaky with the evidence
  (seed, order, output). Don't loop the whole suite.
- Never "fix" flakiness by adding sleeps or retries. LLMs repair flaky tests best with runtime evidence (seed,
  order, logs), not from code alone (Berndt et al. 2025).
