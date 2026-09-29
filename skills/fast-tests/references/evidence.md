# Evidence, condensed

Numbers behind the skill's rules. Full citations and links:
[RESEARCH.md](https://github.com/hunkim/ai-is-fast-your-tests-are-slow/blob/main/RESEARCH.md).

## Why speed matters

- Builds a few seconds faster → 11% faster active time, 14% faster wall time on small/medium changes; no threshold
  "cliff"; predictability matters too (Jaspan & Green, Google, IEEE Software 2023).
- 1 s keeps flow; 10 s is the limit of attention (Nielsen). Median IDE test run ≈ 0.5 s, 75% under 5 s (Beller et
  al. 2019). Only 10% of interrupted programming sessions resume within a minute (Parnin & Rugaber 2011).
- 10 min is the most common "max acceptable" CI time (Hilton et al. 2017); Shopify targets p95 < 10 min.
- AI era: +98% PRs merged, +91% review time, no company-level gain (Faros, 10k+ developers, 2025); Google throttled
  LLM-generated changes to reviewer capacity (2025); experienced maintainers 19% slower with AI in mature repos
  (METR 2025).

## Where the time goes

- Four numbers: wall vs summed file time, long pole, serial setup fraction, idle waits.
- Wall ≥ max(longest file, total ÷ workers) (Graham 1969); speed-up ≤ 1 ÷ serial fraction (Amdahl 1967).
- Shopify: 68% of CI time was setup before any test; p95 45 → 18 min after fixing it.
- Async waits: 45% of flaky-test fixes; a third of those used fixed delays (Luo et al. 2014).
- Case study in this repo: ~85–90% of a 12-minute suite was idle; 12 min → 24 s.

## Parallelism and isolation

- Java OSS: 3.53× average speed-up; only 19.1% of projects with long suites parallelize (Candido et al. 2017).
- Per-test process isolation: 618% average overhead (Bell & Kaiser 2014).
- Order dependence: 50.5% of Java flaky tests (iDFlakies), 59% in Python (Gruber et al. 2021); 61% via static state
  (Zhang et al. 2014); speed-up techniques broke 82% of suites with order-dependent tests (Lam et al. 2020).
- 46.5% of flaky tests are resource-affected (Silva et al. 2023).
- Bazel: 12.8× median at 16-way parallelism; 4.22× (4.71× Bazel cache) median from CI caching on long builds (Zheng et al. 2024).

## Selection and ordering

- Ekstazi: −32% end-to-end on average, −54% on long suites; in CI selected 30.6% of tests but builds took 76% of
  the time (Gligoric 2015; Shi 2019).
- Module-level selection picked all modules in 65% of commits (Shi 2019).
- Google: 1.23% of affected test runs found a breakage (Memon 2017). Meta: 3× fewer runs, > 99.9% faulty changes
  caught (Machalica 2019).
- Manual selection differed from tools in 100% of sessions; too narrow 27% (Gligoric 2014).
- "Recently failed + fastest first" beat 59 prioritization techniques (Cheng et al. 2024).
- Selection missed up to 55% of failures; batching missed none (Fallahzadeh et al. 2024).

## Flakiness

- Google: ~16% of tests some flakiness; 84% of pass→fail transitions flaky; 2–16% compute on reruns (Micco 2017).
- 75–78% flaky from birth (Luo 2014; Lam 2020); PR-time checks catch 85%.
- 170 reruns for 95% confidence (Gruber 2021).
- Slack: 57% → 3.85% failing test jobs with auto-quarantine; GitHub: 9% → < 0.5% flaky builds.

## Agents

- Test re-execution in 49.7–83.0% of agent tasks; skills cut cost 7.9–41.7% (Hu et al. 2026).
- ~50% cheating when tests contradict the spec; 54% → 9% with an explicit exit (ImpossibleBench 2025).
- 80.2% of agent test changes have weak/no oracles (Banik 2026).
- 7.8% of SWE-bench "passing" patches fail the full suite (Wang et al. 2026).
- Log trimming: same diagnosis accuracy, 4.5× fewer tokens (LogSage 2025).
