# Parallel execution: isolation, workers, sharding

Parallelism is the largest *safe* speed-up (Java OSS average 3.53×; only 19.1% of projects with long suites use
it — Candido et al. 2017). Two things cap it: **isolation** (tests that share state break or flake) and the
**long pole** (wall time ≥ max(longest file, total ÷ workers)).

## Isolation checklist

A test file must pass **alone, in any order, twice in a row, and next to any other file**. Check each:

1. **Filesystem** — a fresh temp dir per test or file (`mkdtemp`, `tmp_path`, `t.TempDir()`,
   `@TempDir`, `tempfile::tempdir()`); no fixed `/tmp/x`; never write into the repo.
2. **Ports** — bind port **0** and read the assigned port; never hard-code 3000/8080. If a helper asks the OS for a
   free port and then passes it to a child process, that is fine in practice (tiny race).
3. **Databases** — per worker: a separate DB file/schema/database name (include the worker id:
   `JEST_WORKER_ID`, `VITEST_POOL_ID`, pytest-xdist `worker_id`, `TEST_ENV_NUMBER` in parallel_tests), or a
   transaction rolled back after each test.
4. **Environment** — env vars set by a test are process-local only if each file runs in its own process
   (Node `node:test`, Jest, Vitest default pools); with threads or `--no-isolate`, reset them.
5. **Global/static state** — singletons, caches, registries, module-level state: reset in `beforeEach`/`setUp`.
   (Static state is the root of 61% of order-dependent tests — Zhang et al. 2014.)
6. **External names** — unique queue/topic/bucket/key names per test.
7. **Time and randomness** — fake or injected clock; seeded RNG with the seed printed.
8. **No order assumptions** — no test relies on data another test created. If a group truly must share, declare
   it (pytest-xdist `--dist loadgroup` + `@pytest.mark.xdist_group`, a single file).
9. **Resources** — timeouts sized for a loaded CI machine; 46.5% of flaky tests are resource-affected (Silva et al.
   2023), so don't run more workers than cores.

Isolation level: a process per file is the usual sweet spot. A process per *test* can cost more than the tests
(618% average overhead — Bell & Kaiser 2014). Turn isolation off (`vitest --no-isolate`,
`node --test-isolation=none` on Node 24+, `--experimental-test-isolation=none` on Node 22) only after random-order and repeat runs pass.

## Workers per runner

| Runner | Parallel across files | Notes |
|---|---|---|
| Node `node:test` | `node --test --test-concurrency=N` | Default is `availableParallelism() - 1` in recent Node; older setups often pin 1 |
| Jest | `--maxWorkers=N` or `50%` | Default cores − 1; `--runInBand` / `-i` forces serial |
| Vitest | `--maxWorkers=N`; `--pool=forks\|threads` | `fileParallelism: false` forces serial |
| Mocha | `--parallel --jobs N` | |
| Playwright | `--workers=N`; `fullyParallel: true` | Parallel tests within a file with `fullyParallel` |
| pytest | `pytest -n auto` (pytest-xdist) | `--dist worksteal` balances uneven files; `--dist loadscope` keeps module fixtures together |
| Go | packages in parallel by default (`-p`); `t.Parallel()` + `-parallel N` within a package | |
| Gradle | `maxParallelForks = N` in `tasks.test` | `forkEvery` only to contain leaks |
| Maven Surefire | `<forkCount>1C</forkCount>` + `<reuseForks>true</reuseForks>` | JUnit 5: `junit.jupiter.execution.parallel.enabled=true` |
| Rust | `cargo nextest run` (process per test) | `cargo test -- --test-threads=N` for libtest |
| Rails | `parallelize(workers: :number_of_processors, work_stealing: true)` | Threshold: < 50 tests stay serial by default |
| RSpec | `parallel_rspec -n N` (parallel_tests) | |

Make the count overridable (`TEST_WORKERS`, default ≈ CPU count; `1` for debugging), e.g. in `package.json`:
`"test": "node --test --test-concurrency=${TEST_WORKERS:-10} 'test/**/*.test.js'"`.

## Prove it

```bash
for i in 1 2 3; do <full test command> || break; done        # 3 green runs in a row
# random order, if supported:
npx jest --randomize --showSeed         # replay: --seed=<n>
npx vitest run --sequence.shuffle
node --test --test-randomize             # Node 24+; replay: --test-random-seed=<n>
pytest -p randomly                       # pytest-randomly; replay: -p randomly --randomly-seed=<n>
go test -shuffle=on ./...
bundle exec rspec --order rand           # replay: --seed <n>
```

A failure that appears only in parallel or random order is an isolation bug: find the shared resource and fix it.
Don't lower the worker count to hide it.

## The long pole

- Compute the bound: `profile_tests.py` prints projected wall time per worker count (LPT schedule) and the long
  pole. Longest-processing-time-first scheduling is within 4/3 of optimal (Graham 1969).
- If the long pole ≈ projected wall time, split that file (by feature/describe block) or move its slow part into
  its own file so it starts at t = 0.
- Run the slowest files first (Jest sorts by previous duration; for others, order the file list by recorded
  duration).

## Sharding across CI machines

Built-in `--shard` flags split by **count or hash, not duration** (Jest `--shard=i/n`, Vitest `--shard`, Node
`--test-shard`, Playwright `--shard` without `fullyParallel`). Uneven shards waste machines. Duration-aware options:

- CircleCI: `circleci tests run --command "xargs <runner>" --split-by=timings` (needs JUnit timing results)
- Knapsack Pro (queue mode), Buildkite Test Engine Client (`bktec`)
- pytest: `pytest --store-durations`, then `pytest --splits 4 --group 2 --splitting-algorithm least_duration`
  (pytest-split)
- Ruby: `parallel_tests --group-by runtime`
- Bazel: `shard_count` in BUILD + `--test_sharding_strategy=explicit`
- Rust: `cargo nextest run --partition slice:1/4`

Shard only after removing waits and using all cores on one machine; each shard repeats the serial setup.
