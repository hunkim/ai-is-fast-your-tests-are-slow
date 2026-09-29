# Running only affected tests (regression test selection)

Selection is the first idea most people have and, in practice, often the least effective. Use it for the **inner
loop**; keep the full suite as the gate.

## What the evidence says

- **Tests selected ≠ time saved.** Ekstazi selected 30.6% of tests in CI, yet builds still took 76% of the time,
  because of fixed overhead (Shi et al. 2019). Selection pays off mainly for suites over about a minute.
- **Hub modules select everything.** Module-level selection chose *every* module in 65% of commits (Shi et al.
  2019). A shared store, DB layer, barrel `index.ts`, `__init__.py`, lock file or root config reaches almost all
  tests. Expect this in application code.
- **Coarse beats fine end to end.** File/class-level dependencies (Ekstazi, STARTS) beat method-level analysis,
  which costs more than it saves (Gligoric et al. 2015; Legunsen et al. 2016).
- **Static analysis misses dynamic dependencies** (reflection, dynamic `import()`, dynamic typing) and non-code
  inputs (config, fixtures, templates, env vars). Production systems for dynamic languages trace at runtime
  (Stripe, Shopify, Azure TIA).
- **Every serious deployment keeps a full run** (post-merge, nightly, every Nth build), and RTS tools have bugs of
  their own (27 found in Clover, Ekstazi and STARTS — Zhu et al. 2019).
- **The alternative is guessing.** Developers' manual picks differed from tools in 100% of sessions and were too
  narrow 27% of the time (Gligoric et al. 2014). An agent picking tests by intuition is the same.
- At huge scale (Meta, Google, Microsoft), ML/heuristic selection on top of safe selection cut compute 2–3× while
  catching > 99% of faulty *changes* — with a full run behind it.

## Decision

| Situation | Do |
|---|---|
| Full suite ≤ ~2 min after removing waits and parallelizing | Run everything every time. Use selection only for watch mode |
| Monorepo with many packages | Package/target-level affected runs (Nx, Turborepo, Bazel, Pants) at PR time; full suite post-merge |
| Large JVM/.NET module | File/class-level dynamic selection (Ekstazi, Azure TIA) |
| JS/TS package | Module-graph selection (`jest --findRelatedTests`, `vitest related`) + force-rerun triggers for config |
| Python | Coverage-based (`pytest --testmon`) |
| Dynamic language at scale | Runtime file-access tracing (Stripe/Shopify style) |
| Safe set still too big at scale | ML/heuristic pruning on top (Develocity PTS, Launchable) + post-merge remaining tests |

Always also run: tests that failed recently, new or changed test files, and a small must-run smoke set. Treat lock
files, root/CI config, test infrastructure and unknown file types as "run everything" triggers.

Before trusting a selector, run it in **shadow mode** for a while (selected set, then the full suite) and measure
how many faulty changes the selected set would have missed.

## Tools

**JS/TS**
- `npx jest --findRelatedTests src/a.ts src/b.ts` · `npx jest --changedSince=origin/main` · `npx jest -o` (uncommitted)
- `npx vitest related --run src/a.ts` · `npx vitest --changed origin/main` (config `forceRerunTriggers`)
- `npx nx affected -t test --base=origin/main --head=HEAD`
- `npx turbo run test --affected` (base via `TURBO_SCM_BASE`)
- Custom: walk the import graph from each test file and check if it reaches a changed file; add tests that read
  changed files by path; treat tests that scan whole directories as affected by any change there.

**Python**
- `pytest --testmon` (coverage-based; stores `.testmondata`); `--testmon-noselect` to only reorder
- `pants --changed-since=origin/main --changed-dependents=transitive test`

**JVM**
- STARTS: `mvn starts:starts` · Ekstazi (Maven/JUnit plugin) · OpenClover `clover:optimize`
- Gradle Develocity Predictive Test Selection: `./gradlew test -Dpts.enabled=true`

**.NET** — Azure Pipelines VSTest "Run only impacted tests" (Test Impact Analysis)

**Go** — the test cache already skips unchanged packages (`go test ./...` prints `(cached)`); `-count=1` bypasses it
for the gate. Reverse deps: `go list -f '{{.ImportPath}} {{join .Deps " "}}' ./...`

**Bazel** — `bazel query 'kind(test, rdeps(//..., //pkg:changed_target))'`; bazel-diff for impacted targets;
`bazel test` caches unchanged results.

**Rust** — no stock selection; cargo-difftests (experimental, coverage-based).

## For agents

Use selection while iterating ("run the tests for the file I just changed"), then run the full gate before
declaring the task done. In the SWE-bench setting, 7.8% of patches that passed the modified test files failed the
full suite (Wang et al. 2026).
