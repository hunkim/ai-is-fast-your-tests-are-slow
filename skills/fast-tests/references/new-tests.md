# Adding tests without adding a bottleneck

Speeding up a suite once is easy to undo: a few new tests with a `sleep`, a real HTTP call, or a leaked timer, and
the suite is slow and flaky again. The cheapest moment to keep it fast is when a test is written — 75–78% of flaky
tests are flaky from the start (Luo et al. 2014; Lam et al. 2020), and checking new and modified tests at PR time
catches most of them.

## Design checklist

| Question | Good | Bottleneck |
|---|---|---|
| What level? | Unit test of the function/component; integration only for wiring | E2E for logic a unit test could check |
| Does it depend on time? | Fake timers / injected clock / configurable interval | `sleep`, waiting out a real interval |
| Does it test a failure? | Non-retried error, or zero retry delays injected | Thrown network error the client retries with backoff |
| What does it touch? | Temp dir, port 0, own schema, in-memory fakes | Fixed paths, fixed ports, shared DB, real services |
| What does it leave behind? | Nothing: servers closed, timers cleared, threads joined | Background timers/sockets that hold the process |
| What does it assert? | Expected behavior from the spec; fails if the fix is reverted | "No exception", snapshot of current output |
| Where does it live? | The feature's test file, kept small | Appended to the biggest, slowest file |

Examples of the good column, per language: [waits.md](waits.md).

## Budget check for changed tests

```bash
BASE=${BASE:-origin/main}
FILES=$(git diff --name-only --diff-filter=AM "$BASE"...HEAD | grep -E '(^|/)(test|tests|spec|__tests__)/|[._](test|spec)\.' || true)
[ -z "$FILES" ] && exit 0
python3 scripts/scan_test_smells.py $FILES
python3 scripts/profile_tests.py --cmd "npx vitest run {file}" --max-seconds 2 --fail-on-waiting --repeat 5 $FILES
```

- `--max-seconds` — per-file budget. Suggested: unit ≤ 1–2 s, integration ≤ 10 s, E2E set separately. A good upper
  bound is the suite's current long pole (from a full `profile_tests.py` run): a new file should never become it.
- `--fail-on-waiting` — a file that mostly waits (low CPU, high wall) fails, even under budget; that wait will grow.
- `--repeat 5` — runs each file 5 times; different outcomes are reported as FLAKY. For stronger checks, add random
  order (`--randomize`, `-shuffle=on`, `pytest-randomly`) inside `--cmd`, and run once with more workers than cores.

Exit code 1 on any violation, so it works as a CI step or a pre-push hook. For Go, the unit is a package: pass
`$(dirname $FILES | sort -u)` with `--cmd "go test ./{file}"`.

## Enforce it in CI

GitHub Actions example (adapt the runner command):

```yaml
name: new-tests-budget
on: pull_request
jobs:
  budget:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-node@v4
        with: { node-version: 22 }
      - run: npm ci
      - name: Budget for new and changed test files
        run: |
          FILES=$(git diff --name-only --diff-filter=AM origin/${{ github.base_ref }}...HEAD \
            | grep -E '(^|/)(test|tests|spec|__tests__)/|[._](test|spec)\.' || true)
          [ -z "$FILES" ] && exit 0
          python3 skills/fast-tests/scripts/scan_test_smells.py $FILES
          python3 skills/fast-tests/scripts/profile_tests.py --cmd "npx vitest run {file}" \
            --max-seconds 2 --fail-on-waiting --repeat 5 $FILES
```

Keep the full suite as a separate required check; this job only guards what the PR adds.

## A guard for structural fixes

When you fix a structural cause (a timer that held processes open, a retry that tests triggered), add a test that
fails if it comes back — e.g. a fixture that leaves 30 s timers behind must exit within 10 s; run it in a child
process with a timeout. A future change that reintroduces the problem then fails in seconds instead of silently
adding minutes.

## For agents

When you add a test:
1. Write it from the spec/bug first; run it and see it fail for the right reason.
2. Fix the code; run it and the affected tests.
3. Run the budget check on the files you added or changed. Fix any WAITING/OVER/FLAKY result in the test.
4. Run the full suite once before saying done; report the budget check and the full-suite summary.
