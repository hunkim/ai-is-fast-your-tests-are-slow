# What the research says: making tests fast in the AI coding era

A synthesis of ~270 papers, industry reports and tool docs (compiled September 2026). Each claim below cites its
source; the five annotated bibliographies in [`research/`](research) hold the full citations, links, numbers, and
how much of each source was actually read (full text vs abstract).

| Notes | Topic | Sources |
|---|---|---|
| [01-test-selection](research/01-test-selection.md) | Running only the tests a change can affect | 44 |
| [02-faster-suites](research/02-faster-suites.md) | Ordering, parallelism, isolation, caching, per-test cost | 67 |
| [03-flaky-isolation](research/03-flaky-isolation.md) | Flaky tests, order dependence, quarantine | 47 |
| [04-ai-era](research/04-ai-era.md) | Verification as the bottleneck for AI coding agents | 75 |
| [05-feedback-ci](research/05-feedback-ci.md) | Why latency matters, CI economics, adjacent techniques | 51 |

---

## The short version

1. **The return on AI coding is bounded by how cheaply, quickly and trustworthily you can verify a change.**
   Generation got cheap; review, CI and tests did not. Faros telemetry across 10,000+ developers: +98% PRs merged,
   +154% PR size, **+91% review time**, no company-level gain [Faros 2025]. Google's LLM migration team: the
   bottleneck "was the speed at which engineers could review the changes" [Google 2025]. DORA 2024: AI adoption
   correlated with −7.2% delivery stability [DORA 2024].
2. **A slow suite is mostly waiting, not working.** Async waits are the #1 cause of flaky tests (45% of fixes)
   [Luo 2014]; fixed CI overhead was 68% of Shopify's CI time before any test ran [Shopify]; in our case study
   ~85–90% of a 12-minute suite was idle ([CASE-STUDY](CASE-STUDY.md)). Measure wall vs CPU time per file first.
3. **Every second counts; there is no cliff.** Google: builds a few seconds faster → 11% faster active time and
   14% faster wall time on small/medium changes [Jaspan & Green 2023]. Humans keep focus up to ~10 s [Nielsen];
   only 10% of interrupted programming sessions resume within a minute [Parnin & Rugaber 2011].
4. **Parallelism is the largest safe speed-up, capped by isolation and the long pole.** Java OSS averages 3.53×,
   bounded by long test classes; only 19.1% of projects with long suites parallelize at all [Candido 2017].
   Wall time ≥ max(longest file, total / workers) [Graham 1969; Amdahl 1967].
5. **Running fewer tests works less well than people expect.** Tests selected ≠ time saved (Ekstazi selected 30.6%
   of tests but builds still took 76% of the time in CI) [Shi 2019]; hub modules make "safe" selection pick
   almost everything (module-level selection chose *all* modules in 65% of commits) [Shi 2019]. Every production
   deployment keeps a full-run safety net [01 §synthesis].
6. **Simple beats sophisticated.** "Recently failed, then fastest first" beat all 59 prioritization techniques on
   6.5-hour suites [Cheng 2024]; simple history heuristics match ML selection [Elsner 2021]; only 6 of 29 ML
   selection studies (21%) are reproducible [Pan 2022].
7. **Flakiness destroys the signal.** 84% of pass→fail transitions at Google involve a flaky test
   [Memon 2017]; ~16% of Google's tests show some flakiness [Micco 2017]. 75–78% of flaky tests are flaky from the
   day they are written [Luo 2014; Lam 2020], so check new tests at PR time.
8. **Tests are both the agent's steering wheel and its attack surface.** Frontier models cheat on ~50% of tasks
   whose tests contradict the spec (edit tests, special-case, override equality) [ImpossibleBench 2025]; giving the
   agent a sanctioned "the tests are wrong" exit cut one model's cheating from 54% to 9% [ImpossibleBench].
9. **Agent-written tests are often weak; the value is a trusted, fast, existing suite.** 80.2% of test changes in
   agent PRs have weak or no assertions [Banik 2026]; tests agents write mid-task don't raise SWE-bench
   resolution but cost 9–20% more tokens [Chen 2026]; weak tests and leaked solutions inflated one agent's benchmark
   score from 3.97% to 12.47% [SWE-Bench+ 2024].
10. **Agents waste runs on unclear test setups — and written-down know-how fixes it.** Test re-execution occurs in
    49.7–83.0% of agent tasks, driven by unknown test runners and truncated/ambiguous output; developer-written
    skills cut agent cost 7.9–41.7% [Hu 2026]. Grep+tail log reduction keeps diagnosis accuracy with 4.5× fewer
    tokens [LogSage 2025].

**The practical ordering that falls out of the evidence:** measure → remove waits → parallelize (with isolation) →
split the long pole → cache → order for first failure → select tests only for the inner loop → keep a full run as
the gate → quarantine flakes → protect the oracle from agents.

---

## 1. Why latency matters

### Human thresholds

| Band | Evidence | Effect |
|---|---|---|
| ≤ 1 s | 0.1 s feels instant, 1 s keeps flow uninterrupted [Nielsen]; median IDE test run ≈ 0.5 s [Beller 2019] | Tests become part of editing; TDD-style micro-cycles |
| ≤ 10 s | 10 s is the limit of focused attention [Nielsen]; >75% of IDE test runs finish within 5 s [Beller 2019] | Developers still wait deliberately |
| 1–10 min | Developers switch tasks every ~6 min anyway [Meyer 2014]; Google presubmit ≈ 11 min, "often run in the background" [SWE@Google ch. 23] | A context switch is likely; resuming is costly [Parnin & Rugaber 2011; Mark 2008] |
| ≥ 10 min | 10 min is the most common "maximum acceptable" CI time; 78–96% of teams worked to cut it [Hilton 2017]; Shopify targets p95 < 10 min [Shopify] | Batched PRs, bigger diffs, harder bisecting |

The "10-minute build" is a practitioner norm, not a measured cognitive threshold; the measured human thresholds
are in seconds [05 caveats].

**No cliff, and predictability matters.** In Google's blind experiment, speed-ups of a few seconds produced
measurable gains, and developers plan around the wait they *expect* — so variance hurts almost as much as the mean
[Jaspan & Green 2023; read via secondary summary].

### For agents, latency multiplies

An agent's loop is edit → run → read → edit. Test latency is paid on every iteration and by every parallel agent;
CI minutes are billed per agent session [GitHub coding agent docs]. Unknown test runners and ambiguous output
cause test re-execution in 49.7–83.0% of agent tasks [Hu 2026]. A 12-minute check allows ~5 verified iterations an hour;
a 24-second one allows 150.

### The cost

- People: builds a few seconds faster → 11–14% faster change completion [Jaspan & Green 2023].
- Signal: at Google only **1.23%** of affected test executions found a breakage [Memon 2017] — most runs carry no
  new information, so *when* a failure shows up matters more than total time.
- Money and carbon: ~$504/year per average paid GitHub Actions repo, 91% of it build and test [Bouzenia & Pradel
  2024]; ~457 tCO₂e/year for GitHub Actions open-source usage [Saavedra 2025].

---

## 2. Where the time actually goes

Four numbers explain almost any suite [02 Part D]:

1. **Wall time W vs summed per-file time ΣT** — parallel efficiency = ΣT / (W × workers).
2. **Long pole L** — W ≥ max(L, ΣT / P). If L > ΣT / P, more workers do nothing [Graham 1969].
3. **Serial fraction S** — setup before the first test and after the last (install, compile, migrate, boot).
   Speed-up ≤ W / S [Amdahl 1967]. At Shopify, 68% of CI time was setup; fixing it took p95 from 45 to 18 min
   [Shopify]. Caching the environment made 74% of accelerated builds ≥ 2× faster [Gallaba 2022].
4. **Idle waits** — wall ≫ CPU for a file means it is sleeping, backing off, timing out, or held open by a timer.

Idle waits are the most under-measured of the four. The literature documents their prevalence indirectly:

- **Async waits cause 45% of fixed flaky tests; a third of those use fixed delays** [Luo 2014]. Replacing fixed
  sleeps with condition waits was the fix in 54% (Luo) and 86% (Mozilla) of async cases [Luo 2014; Eck 2019].
- **Google bans sleeps in small tests** and caps test size by construction [SWE@Google ch. 11].
- Re-running failed commands is the factor most associated with long CI builds [Ghaleb 2019].
- Our case study found four idle patterns that no paper names as such but that are common in JS/TS and Python
  suites: background app timers holding finished test processes open, mock failures triggering real retry
  backoff, sleeping through a production interval, and non-`unref`'d debounce timers ([CASE-STUDY](CASE-STUDY.md)).

**Takeaway:** profile wall vs CPU per test file before choosing any technique. The
[profiler in this repo](skills/fast-tests/scripts/profile_tests.py) does exactly this.

---

## 3. Run everything, faster

### Parallelism

- Java OSS: average **3.53×** speed-up from parallel execution, limited by long-running classes; only 19.1% of
  projects with long suites use it [Candido 2017]. Bazel: 12.8× at 16-way for long builds [Zheng 2024].
  cargo-nextest: 1.4–3.4×, limited by long poles [nextest docs].
- Schedule longest-first (LPT) to pack workers; it is within 4/3 of optimal [Graham 1969].
- **Built-in shard flags split by count or hash, not duration** (Jest, Node, Vitest, Playwright `--shard`). Use
  duration-aware splitters (CircleCI `--split-by=timings`, Knapsack Pro, Buildkite, `pytest-split`,
  `parallel_tests --group-by runtime`) or work stealing (`pytest-xdist --dist worksteal`) [02 Part F].
- Cap workers at cores: 46.5% of flaky tests are resource-affected and fail more under contention [Silva 2023].

### Isolation: the hidden tax and the safety net

- Per-test process isolation averaged **618% overhead** (up to 4,153%); VMVM's lightweight reset cut suite time
  62% on average while still running every test [Bell & Kaiser 2014].
- Vitest's docs: isolation "greatly increases test times" [Vitest docs]; Rails won't parallelize < 50 tests
  because of setup overhead [Rails docs].
- But shared-process execution exposes order dependence: 50.5% of detected Java flaky tests [Lam 2019, iDFlakies],
  59% in Python [Gruber 2021].
- **Consensus:** isolate per process (per file) first; drop isolation only after proving independence (random
  order, repeat runs) [02 §C.4].

### Caching

- A hermetic test's result is a pure function of its inputs' hashes [Mokhov 2018, *Build Systems à la Carte*];
  Bazel, Go, Nx and Turborepo reuse results this way. Incremental builds with a CI cache gave a median 4.22× (4.71× with Bazel's own cache) on long builds [Zheng 2024].
- File-level dynamic dependency tracking (Ekstazi) saves 32% end-to-end on average, 54% on long suites
  [Gligoric 2015].
- CI caching is under-adopted (30% of projects) and caches go stale (27%) [Ghaleb 2026].

---

## 4. Run fewer tests (regression test selection)

**What works end to end**

- **Coarse beats fine.** File/class-level dependencies (Ekstazi, STARTS) beat method/statement level end to end;
  finer analysis selects fewer tests but costs more than it saves (FaultTracer was slower than running
  everything) [Gligoric 2015; Legunsen 2016].
- **Selection ratio ≠ time saved.** Fixed overhead caps the gain; RTS pays off mainly for suites longer than about
  a minute [Gligoric 2015; Shi 2019].
- **Static selection breaks on dynamic features** (reflection, dynamic imports, dynamic typing). Making static RTS
  reflection-safe pushed cost to 76–91% of a full run [Shi 2019b]. Production systems for dynamic languages trace
  at runtime: Stripe (file access; mean ~5% of tests, median < 0.5%) [Stripe 2026], Shopify (99.94% recall)
  [Shopify], RTSLinux (74% skipped) [Celik 2017].
- **Non-code dependencies cause most misses** — config, fixtures, templates, env vars. Tools fall back to "run
  everything" on unknown file types [01 §synthesis].

**Hubs**

In a codebase with hub modules, dependency-based selection selects nearly everything: module-level selection chose
every module in 65% of commits [Shi 2019]; at Facebook ~25% of all tests ran per mobile change and 99.9% of them
passed [Machalica 2019]; eager `__init__.py` imports widen Python file-level deps [Wang 2026, NameRTS]. Our case
study: 110 of 120 files selected for a three-commit diff.

**At scale, industry trades safety for speed, measured by caught faulty *changes***

- Meta: 3× fewer test executions, half the machines, > 99.9% of faulty changes caught [Machalica 2019].
- Microsoft: 15–30% compute saved at ~99% buggy-PR recall [Mehta 2021].
- Google: distance cut-offs saved 42–55% with no misses in simulation [Memon 2017].
- Mozilla: 70% fewer test tasks than previous heuristics [Mozilla 2020].

**Everyone keeps a full run.** Azure TIA periodic full runs, OpenClover `fullRunEvery=10`, Develocity post-merge
`REMAINING_TESTS`, Shopify full suite on main, Dropbox batching + automatic bisection [01 §synthesis]. RTS tools
have bugs of their own (RTSCheck found 27 in Clover, Ekstazi, STARTS) [Zhu 2019].

**Humans (and agents) guessing is the real alternative.** Developers' manual selections differed from the tool in
100% of sessions and were too narrow 27% of the time [Gligoric 2014]. An agent choosing tests by intuition is the
same problem at machine speed. In SWE-bench, 7.8% of "correct" patches fail the full developer suite because only the modified test files were run [Wang 2026b].

**Selection vs batching.** Selection missed up to 55% of failures while batching commits missed none
[Fallahzadeh 2024]; batching with bisection kept feedback time with 72–91% fewer machines [Fallahzadeh 2023].

---

## 5. Order tests so failures show up first

- Most runs pass (Google: 1.23% found a breakage [Memon 2017]; BMW: 98% of pre-submit runs pass [Schwendner
  2025]), so optimize **time to first failure** (APFDc/NTTF), not APFD, which ignores test cost [02 §A1].
- "Recently failed + fastest first" beat all 59 techniques on long suites [Cheng 2024]; quickest-first is a top
  baseline on real failures [Peng 2020]; history features are the most valuable [Yaraghi 2022].
- Google's cheap history windows (failed recently, not run lately, new) caught 70–80% of failing suites at 3× the
  efficiency of random [Elbaum 2014].
- Jest already runs previously-failed first, then longest [Jest docs]. `pytest --ff --nf`, `rspec --only-failures`.
- Tension: longest-first packs workers; fastest-first surfaces failures on one worker. With many workers: pack by
  LPT, put recently failed at the front.

---

## 6. Flaky tests and isolation

**Root causes (consistent across studies)**

| Cause | Prevalence |
|---|---|
| Async wait / timing | 45% of fixes [Luo 2014]; 22% [Eck 2019]; leading cause at Microsoft [Lam 2020] |
| Concurrency | 20% [Luo]; 26% [Eck] |
| Order dependence / shared state | 12% [Luo]; 50.5% Java [Lam 2019]; **59% Python** [Gruber 2021]; 61% of it via static/global state [Zhang 2014] |
| Resources / infrastructure | 46.5% resource-affected [Silva 2023]; 86% of Microsoft's flaky tests flaky only in CI [Lam 2019b] |
| Time, randomness, unordered collections, float | small each; randomness is #1 in *generated* tests [Gruber 2024] |

**Scale:** Google ~16% of 4.2M tests show some flakiness, 2–16% of compute spent on reruns [Micco 2017];
Microsoft 14–52% of builds per project affected [Lam 2020]; Slack test-job failures 57% → 3.85% after automatic
detection and suppression [Slack 2022]; GitHub flaky builds 9% → < 0.5% of commits [GitHub 2020].

**Detection is expensive:** 170 reruns for 95% confidence [Gruber 2021]; 10,000 reruns still miss some
[Alshammari 2021]. Detect at PR time: new/modified-test checks catch 85% [Lam 2020b].

**Order dependence breaks speed-ups:** selection, prioritization and parallelization broke 82% of suites that
contain order-dependent tests [Lam 2020c].

**Flakes hide bugs:** 24% of fixes touched the code under test, and 94% of those fixed a real bug [Luo 2014];
about 1 in 6 newly flaky Google tests were real bugs [Micco 2017]. Quarantine, don't delete.

**LLMs:** repair known-cause flakiness moderately well (FlakyDoctor 57–59% [Chen 2024]; FlakyGuard 47.6%
[Li 2025]) but cannot classify flakiness from test code alone (near random) [Berndt 2025] — they need runtime
evidence.

---

## 7. The AI era

### Is testing the bottleneck?

**Mostly yes — read "testing" broadly as verification: tests, CI, review, rollout.**

For:
- Controlled trials show 21–56% speed-ups on well-specified tasks [Peng 2023; Paradis 2024], but experienced
  maintainers in their own mature repos were **19% slower**, accepting < 44% of generations and spending ~9% of
  time reviewing AI output [METR 2025].
- Review time, PR size and instability grow with AI adoption [Faros 2025; DORA 2024; DORA 2025].
- Google deliberately throttled LLM-generated migration changes to avoid overwhelming reviewers [Google 2025].
- Amdahl's law: speed-up ≤ 1/H where H is the fraction that needs human judgment [Mathews 2026].
- Verification selects among cheap generations: AlphaCode discarded ~99% of samples by tests [Li 2022]; CodeT,
  LEVER, Agentless and R2E-Gym all gain from test-based selection [04 §B].

Against / nuance:
- Jellyfish (2M+ PRs) shows *faster* reviews as AI use rises [Jellyfish 2025]; METR's 2026 update now estimates
  ~18% speed-up with a wide interval and a broken design [METR 2026].
- AI review cut cycle time 30.8% at Atlassian [Atlassian 2026] but added 42% closure time in another industrial
  study [Cihan 2025].
- Much of the bottleneck evidence is correlational vendor telemetry.

**Net:** where verification is cheap and automated (strong suites, small batches, fast CI), AI speeds delivery up;
where it is human or slow, AI shifts cost onto reviewers and stability.

### Tests as the oracle — and its weaknesses

- Filtering out weak-test and leaked-solution tasks cut one agent's SWE-bench score from 12.47% to 3.97%
  [SWE-Bench+ 2024]; running only modified test files inflates success by 6.2 points [Wang 2026b]; test hardening changes leaderboards
  [UTBoost 2025].
- OpenAI reportedly stopped reporting SWE-bench Verified in February 2026 after finding flawed tests in 59.4% of
  audited tasks [OpenAI 2026; read via secondary source].
- **Reward hacking on tests** is documented by METR, OpenAI and Anthropic: special-casing, editing tests,
  `sys.exit(0)`, patching `conftest.py` [METR 2025b; Baker 2025; Anthropic 2025], and learned hacks generalize to
  broader misbehavior [MacDiarmid 2025].

### Agent-written tests

- 80.2% of agent test changes have weak or no oracles [Banik 2026]; error paths go untested 67–86% of the time
  [Dipongkor 2026]; LLM oracles tend to encode *actual* rather than *expected* behavior [Konstantinou 2024].
- Meta's TestGen-LLM landed tests only after filtering: builds, passes reliably, increases coverage [Alshahwan
  2024]; mutation-guided generation (ACH) targets specific faults [Meta 2025].
- Diff-based mutation testing checks whether tests *assert* anything; filtering low-value mutants raised
  usefulness from 20% to 80% at Google [Petrović 2021].

### What works for agents (evidence-backed practices)

1. One documented, deterministic test command, plus how to run one file/test, in AGENTS.md/CLAUDE.md; keep
   context files short and command-first [Hu 2026; Lulla 2026; Gloaguen 2026].
2. Two tiers: affected tests in the inner loop, the **full suite before merge** [Claude Code best practices;
   Wang 2026b].
3. Compact, unambiguous output: a summary line, failing tests with trimmed traces, full log to a file
   [Hu 2026; LogSage 2025; Anthropic tools guide].
4. Fast and deterministic: parallel, no sleeps, flakes quarantined (every flake is an agent rerun).
5. Protect the oracle: tests read-only during implementation or hidden holdouts; flag diffs that edit/skip/delete
   tests; give an explicit "tests conflict with spec" exit [ImpossibleBench 2025].
6. Tests from the spec before the code; reproduce bugs with a failing test first [Mathews & Nagappan 2024].
7. Judge tests by oracle strength (assertions, diff coverage, mutants), not presence.
8. Isolate parallel agents: worktree per agent, per-agent ports/DBs/temp dirs.
9. Separate doer and checker; ask for evidence (command + output).
10. Small batches, throttled to review capacity [DORA 2025; Google 2025].

---

## 8. Targets

| Loop | Target | Basis |
|---|---|---|
| Save → affected tests | ≤ 1 s typical, ≤ 10 s worst | Nielsen; Beller 2019 |
| Full local suite / agent gate | ≤ 1–2 min | Below the ~6-min task-switch interval [Meyer 2014]; *inference* |
| Blocking pre-merge CI | p95 ≤ 10 min, median ≤ 5 min | Hilton 2017; Shopify |
| Post-merge broad suites | ≤ 1–2 h, auto-bisected | SWE@Google ch. 23; Fallahzadeh 2023 |
| Flaky test runs | < 1% (stretch 0.15%) | SWE@Google ch. 11 |
| Tests with fixed sleeps in unit tests | 0 | Luo 2014; SWE@Google |

---

## 9. Open problems

- **Cheap expected-behavior oracles** for agent-written code (spec-derived, property-based, differential, mutation-
  guided). LLM oracles still mirror the implementation.
- **A standard "verification strength" score** for a PR; coverage is gameable.
- **Reward hacking in production repos**, beyond "did the diff touch tests?".
- **LLM-assisted test selection for agent inner loops**: little mature peer-reviewed work; execution-free result
  prediction is not yet reliable [Hora 2024].
- **Idle-wait detection** as a first-class metric: no study we found quantifies how much of real suites' wall time
  is idle (sleeps, backoff, held-open processes), even though flakiness studies show waits are the top root cause.
- **Economics of many parallel agents**: the cost-optimal mix of inner-loop, pre-merge and post-merge testing.

---

## Key references

Full list with notes: [`research/`](research). Links below were fetched during the research.

**Selection and industry scale**
- [Gligoric 2015] Gligoric, Eloussi, Marinov. Practical RTS with Dynamic File Dependencies (Ekstazi). ISSTA. https://users.ece.utexas.edu/~gligoric/papers/GligoricETAL15Ekstazi.pdf
- [Legunsen 2016] Legunsen et al. An Extensive Study of Static RTS in Modern Software Evolution. FSE. https://mir.cs.illinois.edu/~marinov/publications/LegunsenETAL16StaticRTS.pdf
- [Shi 2019] Shi, Zhao, Marinov. Understanding and Improving RTS in Continuous Integration. ISSRE. https://mir.cs.illinois.edu/marinov/publications/ShiETAL19RTSinCI.pdf
- [Shi 2019b] Shi et al. Reflection-Aware Static RTS. OOPSLA. https://mir.cs.illinois.edu/marinov/publications/ShiETAL19ReflectionAwareRTS.pdf
- [Celik 2017] Celik et al. RTS Across JVM Boundaries (RTSLinux). FSE. https://users.ece.utexas.edu/~gligoric/papers/CelikETAL17RTSLinux.pdf
- [Zhu 2019] Zhu et al. A Framework for Checking RTS Tools (RTSCheck). ICSE. https://users.ece.utexas.edu/~gligoric/papers/ZhuETAL19RTSCheck.pdf
- [Gligoric 2014] Gligoric et al. Manual and Automated Test Selection. ISSTA. https://users.ece.utexas.edu/~gligoric/papers/GligoricETAL14ManualRTS.pdf
- [Memon 2017] Memon et al. Taming Google-Scale Continuous Testing. ICSE-SEIP. https://research.google.com/pubs/archive/45861.pdf
- [Machalica 2019] Machalica et al. Predictive Test Selection. ICSE-SEIP. https://arxiv.org/abs/1810.05286
- [Mehta 2021] Mehta et al. Data-Driven Test Selection at Scale. FSE Industry. https://2021.esec-fse.org/details/fse-2021-industry/2/Data-Driven-Test-Selection-at-Scale
- [Elsner 2021] Elsner et al. Empirically Evaluating Readily Available Information for Regression Test Optimization. ISSTA. https://conf.researchr.org/details/issta-2021/issta-2021-technical-papers/15/Empirically-Evaluating-Readily-Available-Information-for-Regression-Test-Optimization
- [Pan 2022] Pan et al. Test Case Selection and Prioritization Using ML: A Systematic Literature Review. EMSE. https://arxiv.org/abs/2106.13891
- [Mozilla 2020] Testing Firefox More Efficiently with Machine Learning. https://hacks.mozilla.org/2020/07/testing-firefox-more-efficiently-with-machine-learning/
- [Stripe 2026] Selective Test Execution at Stripe. https://stripe.dev/blog/selective-test-execution-at-stripe-fast-ci-for-a-50m-line-ruby-monorepo
- [Shopify] Spark Joy by Running Fewer Tests; Test Budget; Faster Shopify CI. https://shopify.engineering/spark-joy-by-running-fewer-tests · https://shopify.engineering/faster-shopify-ci
- [Wang 2026] Wang, Pradel, Liu. Names Are All You Need: RTS for Python (NameRTS). https://arxiv.org/abs/2605.25356
- [Fallahzadeh 2024] Fallahzadeh, Rigby, Adams. Contrasting Test Selection, Prioritization, and Batch Testing at Scale. EMSE. https://mcislab.github.io/publications/2025/emse_scale.pdf
- [Fallahzadeh 2023] Accelerating CI with Parallel Batch Testing. ESEC/FSE. https://arxiv.org/pdf/2308.13129

**Faster suites**
- [Candido 2017] Candido, Melo, d'Amorim. Test Suite Parallelization in Open-Source Projects. ASE. https://damorim.github.io/publications/candido-etal-ase17.pdf
- [Bell & Kaiser 2014] Unit Test Virtualization with VMVM. ICSE. https://jonbell.net/publications/vmvm
- [Graham 1969] Bounds on Multiprocessing Timing Anomalies. SIAM J. Appl. Math. https://people.irisa.fr/Sophie.Pinchinat/AA/Graham1969SIAM.pdf
- [Amdahl 1967] Validity of the Single Processor Approach. AFIPS. https://dl.acm.org/doi/10.1145/1465482.1465560
- [Mokhov 2018] Mokhov, Mitchell, Peyton Jones. Build Systems à la Carte. ICFP. https://www.microsoft.com/en-us/research/wp-content/uploads/2018/03/build-systems.pdf
- [Zheng 2024] Zheng, Adams, Hassan. Does Using Bazel Help Speed Up CI Builds? EMSE. https://arxiv.org/pdf/2405.00796
- [Gallaba 2022] Accelerating CI by Caching Environments and Inferring Dependencies. TSE. https://rebels.cs.uwaterloo.ca/papers/tse2020_gallaba.pdf
- [Ghaleb 2026] The Promise and Reality of CI Caching. https://arxiv.org/abs/2601.19146
- [Cheng 2024] Cheng et al. Revisiting Test-Case Prioritization on Long-Running Test Suites. ISSTA. https://mir.cs.illinois.edu/marinov/publications/ChengETAL24LongRTP.pdf
- [Peng 2020] Peng, Shi, Zhang. Empirically Revisiting and Enhancing IR-Based TCP. ISSTA. https://sites.utexas.edu/august/wp-content/uploads/sites/5034/2020/08/ISSTA2020-tcp.pdf
- [Yaraghi 2022] Scalable and Accurate Test Case Prioritization in CI. TSE. https://arxiv.org/abs/2109.13168
- [Elbaum 2014] Elbaum, Rothermel, Penix. Techniques for Improving Regression Testing in CI. FSE. https://cs.uwaterloo.ca/~m2nagapp/courses/CS846/1171/papers/elbaum_fse14.pdf
- [Schwendner 2025] Practical Pipeline-Aware Regression Test Optimization (BMW). https://arxiv.org/pdf/2501.11550
- [SWE@Google] Winters, Manshreck, Wright. Software Engineering at Google, ch. 11–14, 23. https://abseil.io/resources/swe-book/html/ch11.html

**Flakiness**
- [Luo 2014] Luo, Hariri, Eloussi, Marinov. An Empirical Analysis of Flaky Tests. FSE. https://mir.cs.illinois.edu/marinov/publications/LuoETAL14FlakyTestsAnalysis.pdf
- [Eck 2019] Eck et al. Understanding Flaky Tests: The Developer's Perspective. ESEC/FSE. https://arxiv.org/pdf/1907.01466
- [Parry 2021] Parry et al. A Survey of Flaky Tests. TOSEM. https://eprints.whiterose.ac.uk/id/eprint/230095/1/parry2021.pdf
- [Gruber 2021] Gruber et al. An Empirical Study of Flaky Tests in Python. ICST. https://arxiv.org/pdf/2101.09077
- [Lam 2019] Lam et al. iDFlakies. ICST. https://taoxie.cs.illinois.edu/publications/icst19-idflakies.pdf
- [Lam 2019b] Lam et al. Root Causing Flaky Tests in a Large-Scale Industrial Setting. ISSTA. https://mir.cs.illinois.edu/winglam/publications/2019/LamETAL19RootFinder.pdf
- [Lam 2020] Lam et al. A Study on the Lifecycle of Flaky Tests. ICSE. https://mir.cs.illinois.edu/winglam/publications/2020/LamETAL20FaTB.pdf
- [Lam 2020b] Lam et al. A Large-Scale Longitudinal Study of Flaky Tests. OOPSLA. https://mir.cs.illinois.edu/winglam/publications/2020/LamETAL20OOPSLA.pdf
- [Lam 2020c] Lam et al. Dependent-Test-Aware Regression Testing Techniques. ISSTA. https://taoxie.cs.illinois.edu/publications/issta20-dependtest.pdf
- [Zhang 2014] Zhang et al. Empirically Revisiting the Test Independence Assumption. ISSTA. https://dada.cs.washington.edu/research/tr/2014/01/UW-CSE-14-01-01.PDF
- [Silva 2023] Silva et al. The Effects of Computational Resources on Flaky Tests. https://arxiv.org/abs/2310.12132
- [Alshammari 2021] FlakeFlagger. ICSE. https://www.jonbell.net/preprint/icse21-flakeflagger.pdf
- [Micco 2017] The State of Continuous Integration Testing @Google (ICST keynote). http://aster.or.jp/conference/icst2017/program/jmicco-keynote.pdf
- [Slack 2022] Handling Flaky Tests at Scale. https://slack.engineering/handling-flaky-tests-at-scale-auto-detection-suppression/
- [GitHub 2020] Reducing Flaky Builds by 18x. https://github.blog/engineering/engineering-principles/reducing-flaky-builds-by-18x/
- [Chen 2024] Chen, Jabbarvand. Neurosymbolic Repair of Test Flakiness (FlakyDoctor). ISSTA. https://arxiv.org/abs/2404.09398
- [Berndt 2025] Can We Classify Flaky Tests Using Only Test Code? https://arxiv.org/abs/2602.05465

**Feedback loops and CI**
- [Jaspan & Green 2023] Developer Productivity for Humans, Part 4: Build Latency, Predictability. IEEE Software. https://research.google/pubs/developer-productivity-for-humans-part-4-build-latency-predictability-and-developer-productivity/
- [Nielsen] Response Times: The 3 Important Limits. https://www.nngroup.com/articles/response-times-3-important-limits/
- [Parnin & Rugaber 2011] Resumption Strategies for Interrupted Programming Tasks. SQJ. https://chrisparnin.me/pdf/parnin-sqj11.pdf
- [Meyer 2014] Software Developers' Perceptions of Productivity. FSE. https://thomas-zimmermann.com/publications/files/meyer-fse-2014.pdf
- [Beller 2019] Developer Testing in the IDE. TSE. https://gousios.org/pub/developer-testing-in-IDE.pdf
- [Hilton 2017] Trade-offs in Continuous Integration. FSE. https://mir.cs.illinois.edu/marinov/publications/HiltonETAL17TradeOffsInCI.pdf
- [Ghaleb 2019] An Empirical Study of the Long Duration of CI Builds. EMSE. https://danielcalencar.github.io/journal%20papers/2019/05/01/emse-19-taher.html
- [Petrović 2021] Practical Mutation Testing at Scale: A View from Google. TSE. https://arxiv.org/pdf/2102.11378
- [Bouzenia & Pradel 2024] Resource Usage and Optimization Opportunities in GitHub Actions. ICSE. https://software-lab.org/publications/icse2024_workflows.pdf
- [Saavedra 2025] Environmental Impact of CI/CD Pipelines. https://arxiv.org/pdf/2510.26413

**AI era**
- [METR 2025] Measuring the Impact of Early-2025 AI on Experienced OSS Developer Productivity. https://arxiv.org/abs/2507.09089
- [METR 2026] Uplift update. https://metr.org/blog/2026-02-24-uplift-update/
- [Peng 2023] The Impact of AI on Developer Productivity: Evidence from GitHub Copilot. https://arxiv.org/abs/2302.06590
- [Paradis 2024] How Much Does AI Impact Development Speed? An Enterprise-Based RCT. https://arxiv.org/abs/2410.12944
- [DORA 2024] Accelerate State of DevOps 2024. https://dora.dev/research/2024/dora-report/
- [DORA 2025] State of AI-assisted Software Development. https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report
- [Faros 2025] The AI Productivity Paradox. https://www.faros.ai/blog/ai-software-engineering
- [Jellyfish 2025] AI impact data. https://jellyfish.co/blog/ai-impact-data-june-2025/
- [Google 2025] How is Google Using AI for Internal Code Migrations? https://arxiv.org/html/2501.06972v1
- [Mathews 2026] Amdahl's Law for AI Agents. https://electric.ax/blog/2026/02/19/amdahls-law-for-ai-agents
- [SWE-Bench+ 2024] Aleithan et al. https://arxiv.org/abs/2410.06992
- [UTBoost 2025] https://arxiv.org/abs/2506.09289
- [Wang 2026b] Are "Solved Issues" in SWE-bench Really Solved Correctly? ICSE 2026. https://arxiv.org/abs/2503.15223
- [OpenAI 2026] Introducing SWE-bench Verified (and its retirement). https://openai.com/index/introducing-swe-bench-verified/
- [Li 2022] Competition-Level Code Generation with AlphaCode. Science. https://arxiv.org/abs/2203.07814
- [ImpossibleBench 2025] Zhong, Raghunathan, Carlini. https://arxiv.org/html/2510.20270v1
- [METR 2025b] Recent Frontier Models Are Reward Hacking. https://metr.org/blog/2025-06-05-recent-reward-hacking/
- [Baker 2025] Monitoring Reasoning Models for Misbehavior. https://arxiv.org/abs/2503.11926
- [Anthropic 2025] Claude 3.7 Sonnet System Card. https://www.anthropic.com/claude-3-7-sonnet-system-card
- [MacDiarmid 2025] Natural Emergent Misalignment from Reward Hacking in Production RL. https://arxiv.org/abs/2511.18397
- [Alshahwan 2024] Automated Unit Test Improvement using LLMs at Meta (TestGen-LLM). FSE Industry. https://arxiv.org/abs/2402.09171
- [Meta 2025] Mutation-Guided LLM-based Test Generation at Meta (ACH). https://arxiv.org/abs/2501.12862
- [Konstantinou 2024] Do LLMs Generate Test Oracles that Capture the Actual or the Expected Program Behaviour? https://arxiv.org/abs/2410.21136
- [Mathews & Nagappan 2024] Test-Driven Development for Code Generation. ASE. https://arxiv.org/abs/2402.13521
- [Banik 2026] All Smoke, No Alarm: Oracle Signals in Agent-Authored Test Code. https://arxiv.org/pdf/2606.18168
- [Dipongkor 2026] Test Coverage Analysis of Agentic Pull Requests. https://arxiv.org/html/2607.18057v1
- [Chen 2026] Rethinking the Value of Agent-Generated Tests. https://arxiv.org/html/2602.07900v2
- [Hu 2026] Analyzing and Mitigating Cost-Inefficient Behaviors in Coding Agents. https://arxiv.org/html/2609.30725
- [LogSage 2025] LogSage (ByteDance). https://arxiv.org/abs/2506.03691
- [Gloaguen 2026] Evaluating AGENTS.md. https://arxiv.org/abs/2602.11988
- [Lulla 2026] On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents. https://arxiv.org/abs/2601.20404
- [Cihan 2025] Automated Code Review in Practice. ICSE-SEIP. https://arxiv.org/abs/2412.18531
- [Atlassian 2026] RovoDev Code Reviewer. ICSE-SEIP. https://arxiv.org/html/2601.01129v2
- [Hora 2024] Predicting Test Results without Execution. FSE IVR. https://2024.esec-fse.org/details/fse-2024-ideas--visions-and-reflections/19/Predicting-Test-Results-without-Execution
- [Claude Code best practices] https://code.claude.com/docs/en/best-practices
- [Anthropic tools guide] Writing effective tools for AI agents. https://www.anthropic.com/engineering/writing-tools-for-agents
- [GitHub coding agent docs] https://docs.github.com/copilot/concepts/agents/coding-agent/about-coding-agent
