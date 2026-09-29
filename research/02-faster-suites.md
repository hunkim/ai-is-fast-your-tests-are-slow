# 02 — Making test suites finish faster without skipping them

*Part of "In the AI coding era, the bottleneck is testing". Research compiled 2026-09-29.*

**Scope.** How to cut the wall-clock time from "change made" to "I know whether it broke anything" while still running the tests. Five families of techniques: (1) **ordering** (test case prioritization, so failures show up sooner), (2) **redundancy removal** (suite minimization/reduction, with its fault-detection cost), (3) **parallelism** (workers, sharding, duration-balanced scheduling, and what isolation costs), (4) **not recomputing what hasn't changed** (hermetic builds, content-addressed caching of test results), and (5) **making each test cheaper** (fake clocks instead of sleeps, cheaper isolation, process reuse). Test *selection* (skipping tests judged irrelevant) is covered only where it shows the trade-off, or where it is *safe*, meaning it amounts to fine-grained result caching.

**Why it matters more now.** A coding agent runs the suite many times per task, not a few times per day. Every idle second in the suite adds up across those runs, and a suite slow enough that people, or agents, start skipping it has stopped protecting anything. Google's testing book says this directly (see [W36]).

**How this was sourced.** Each entry below was located and opened. "Read: full text" means I downloaded the PDF and pulled numbers from its body. "Abstract only" means I could reach only the abstract or a publisher/author summary. Numbers are quoted as reported. Where I am unsure of something (a venue, how far a result generalizes), the entry says so.

---

## Part A — Research literature

### A1. Test case prioritization (TCP): ordering so failures come first

**[W1] Rothermel, Untch, Chu, Harrold. "Prioritizing Test Cases for Regression Testing." IEEE TSE 27(10):929–948, 2001.**
URL: https://ieeexplore.ieee.org/document/10872897/ (IEEE retrospective "On 'Prioritizing Test Cases for Regression Testing'") · UNL repository copy https://digitalcommons.unl.edu/cgi/viewcontent.cgi?article=1017&context=csearticles (returned HTTP 403 to my fetcher)
- Summary: The foundational TCP paper. It frames prioritization as ordering a suite to maximize an objective, usually the *rate of fault detection*. It introduces **APFD** (Average Percentage of Faults Detected, the area under the "% faults found vs. % suite run" curve). Its coverage-based techniques (total and additional statement/branch coverage) became the baselines for two decades of later work.
- Quantitative: Secondary sources I could read describe the evaluation: nine techniques on the seven Siemens programs plus *space*, compared against random, untreated and optimal orders, with coverage-based orders improving the rate of fault detection. I could not get the primary PDF, so no numbers are given here.
- Takeaway: APFD ignores test *cost*. A 10-minute test and a 10 ms test count the same. For wall-clock feedback, use cost-aware APFDc or time-to-first-failure (see W5, W8).
- Read: **abstract/secondary only.**

**[W2] Elbaum, Rothermel, Penix. "Techniques for Improving Regression Testing in Continuous Integration Development Environments." FSE 2014, pp. 235–245.**
URL: https://cs.uwaterloo.ca/~m2nagapp/courses/CS846/1171/papers/elbaum_fse14.pdf · https://research.google/pubs/pub49405/
- Summary: This is the Google study. It uses lightweight, coverage-free, history-window heuristics. Pre-submit: select test suites that failed within a failure window W_f, have not run within an execution window W_e, or are new. Post-submit: give those suites higher priority within a prioritization window W_p. It released the **Google Shared Dataset of Test Suite Results (GSDTSR)**.
- Quantitative: GSDTSR has more than **3.5 million test-suite executions over 30 days**. The failure rate is about **0.5%**. The share of failing suites caught rises quickly with W_f, levels off around W_f = 12 h, and reaches **70–80% at W_f = 96 h**. At that point the percentage of failing suites selected is at least 3× the percentage of suites (or execution time) selected. Random selection of the same size did "approximately six times worse". Selecting 33% of suites pushes less than 0.17% extra load to post-submit. For prioritization, W_p = 1 h gave the lowest median delay (11 h); very small windows (0.1 h) had a better median (53 h better than no prioritization) but very high variance.
- Takeaway: **Recent-failure history plus "hasn't run lately" plus "new" is a cheap, strong signal.** You need no coverage data. Tune the window on your own history.
- Read: **full text.**

**[W3] Spieker, Gotlieb, Marijan, Mossige. "Reinforcement Learning for Automatic Test Case Prioritization and Selection in Continuous Integration" (RETECS). ISSTA 2017.**
URL: https://arxiv.org/abs/1811.04122
- Summary: An online reinforcement-learning agent (tableau or small neural network) ranks tests using only **duration, last execution, and failure history**, rewarded per CI cycle. It needs no prior training and adapts as tests are added and removed.
- Quantitative: Evaluated on two ABB Robotics datasets (Paint Control, IOF/ROL) and GSDTSR, each with more than 300 CI cycles and about a year of CI data. The authors report that the cycles needed to beat baselines correspond to "less than 2-months of data, if there is only one CI cycle per day". Performance drops when many new tests appear at once (Paint Control cycles 200–250).
- Takeaway: Proof of concept that history-only learning works. Later studies (W4, W8) find simpler heuristics or supervised rankers match or beat it.
- Read: **full text.**

**[W4] Bertolino, Guerriero, Miranda, Pietrantuono, Russo. "Learning-to-Rank vs Ranking-to-Learn: Strategies for Regression Testing in Continuous Integration." ICSE 2020.**
URL: https://cin.ufpe.br/~bafm/publications/bertolino_etal_icse20.pdf
- Summary: Compares 10 machine-learning prioritizers in CI on Apache Commons subjects: supervised learning-to-rank (RF, MART, LambdaMART, RankBoost, RankNet, KNN, CA) against reinforcement-learning "ranking-to-learn" (RL, RL-RF, RL-MLP). The metric is RPA/NRPA.
- Quantitative: **MART and LambdaMART had the best RPA** with medium ranking and training times. The worst group (RL-MLP, CA, RL) still averaged RPA above 0.8. Pairwise LTR was the best strategy. "Online learning (by RL) does not necessarily ensure better performance than static methods". RL is more robust to test-suite volatility.
- Takeaway: If you use machine learning at all, gradient-boosted trees on history features are the safe default. Measure the cost of training.
- Read: **full text.**

**[W5] Peng, Shi, Zhang. "Empirically Revisiting and Enhancing IR-Based Test-Case Prioritization." ISSTA 2020, pp. 324–336.**
URL: https://sites.utexas.edu/august/wp-content/uploads/sites/5034/2020/08/ISSTA2020-tcp.pdf
- Summary: Evaluates information-retrieval TCP (BM25 similarity between the diff and the test source) on **real** CI failures instead of mutants. It compares against QTF (Quickest Test First), history, and coverage techniques, and builds hybrids.
- Quantitative: Dataset of **2,042 Travis builds, 2,980 jobs, 6,618 real test failures, 123 Java projects**. On cost-unaware APFD, IR beats coverage-based TCP. But **on cost-aware APFDc, the trivial QTF "outperforms the other TCP techniques, including the coverage-based ones"**, and APFD overestimates IR by 12.9% while underestimating QTF by 50%. The best hybrid (IR + prior execution time + failure frequency) beats OptIR by 10.7% and QTF by 6.9% on APFDc. Flaky tests substantially distort TCP evaluation.
- Takeaway: **When wall-clock time is what you care about, "run the fastest tests first" is a very strong baseline.** Add recent failures and diff similarity on top of it.
- Read: **full text.**

**[W6] Yaraghi, Bagherzadeh, Kahani, Briand. "Scalable and Accurate Test Case Prioritization in Continuous Integration Contexts." IEEE TSE 49(4):1615–1639, 2023.**
URL: https://arxiv.org/abs/2109.13168 · dataset https://github.com/Ahmadreza-SY/TCP-CI
- Summary: Defines a CI data model and **150 features in nine groups**, and collects them for 25 open-source projects whose regression tests take at least 5 minutes and that have enough failed builds (21.5k builds, 3.6k failed per the dataset description). It studies what each feature group costs to collect and how much it helps.
- Quantitative: Feature collection costs **0.1–11.7 minutes per build**, mostly for static coverage features. **Test execution-history features have the greatest impact** on effectiveness. Models should be retrained **no less frequently than every 11 builds**.
- Takeaway: Expensive features (coverage, static analysis) can cost more time than prioritization saves. Start with history features.
- Read: **full text** (introduction and findings).

**[W7] Zhao, Hao, Zhang. "Revisiting Machine Learning based Test Case Prioritization for Continuous Integration." ICSME 2023.**
URL: https://arxiv.org/pdf/2311.13413
- Summary: Compares 11 machine-learning TCP techniques under one setup on 11 subjects.
- Quantitative: Performance across CI cycles varies mainly with *the amount of training data*, not with code evolution. **Pretraining MART on data from other projects and then fine-tuning on the target project gave the optimal order on 80% of subjects, against 50% for the original MART.**
- Takeaway: A cold start is the main weakness of learned prioritizers. Bootstrap from other repositories or start with heuristics.
- Read: **abstract + intro.**

**[W8] Cheng, Wang, Jabbarvand, Marinov. "Revisiting Test-Case Prioritization on Long-Running Test Suites" (LRTS). ISSTA 2024.**
URL: https://mir.cs.illinois.edu/marinov/publications/ChengETAL24LongRTP.pdf · https://github.com/lrtsuser/LRTS
- Summary: Builds the first dataset of *long-running* suites from Jenkins CI in 10 large open-source projects and evaluates 59 TCP techniques (time-based, history, IR, learning-to-rank, reinforcement learning, hybrids).
- Quantitative: **21,255 CI builds, 57,437 test-suite runs, 2020–2023, average run 6.5 hours.** It confirms 9 prior findings and refutes 2. "**Prioritizing faster tests that recently failed performs the best, outperforming the sophisticated techniques.**" Time-based techniques are the most effective basic family and the least affected by flaky or frequently failing tests.
- Takeaway: **This is the strongest single piece of evidence for the playbook's ordering rule: failed-recently first, then fastest first.**
- Read: **full text** (abstract, contributions, findings).

**[W9] Schwendner, Jungwirth, Gruber, Knoche, Merget, Fraser (BMW). "Practical Pipeline-Aware Regression Test Optimization for Continuous Integration." ICST 2025 Industry Track.**
URL: https://arxiv.org/pdf/2501.11550
- Summary: Deep Q-learning prioritization and selection in a large multi-language monorepo, using language-agnostic features (no per-test coverage). It uses different objectives for pre-submit (find failures) and post-submit (find pass-to-fail transitions).
- Quantitative: **98% of pre-submit test executions pass.** On pre-submit, the approach scored NAPFD 0.75 ± 0.25 and placed the first failure at about **17% of suite time (NFR) and 19% (NTTF)**, against COLEMAN at 0.72 / 0.19. Post-submit, it selected 87% of developer-relevant tests while cutting execution time in half, and over 99% within five cycles.
- Takeaway: In industry, **time-to-first-failure** is the metric people use. Most CI runs are green, so ordering matters most on the few red ones.
- Read: **full text** (abstract and results).

**[W10] Luo, Moran, Poshyvanyk. "A Large-Scale Empirical Comparison of Static and Dynamic Test Case Prioritization Techniques." FSE 2016.**
URL: https://arxiv.org/pdf/1801.05917
- Summary: Compares four static TCP techniques (call-graph, string, topic-model, and others) with four dynamic, coverage-based ones on 30 Java programs (431 KLoC) at test-class and test-method granularity.
- Quantitative: The static call-graph technique is best among the static ones at class level and the most efficient; topic-model is best at method level. The top 10% of tests chosen by static and dynamic techniques agree on only about 25–30% of detected faults.
- Takeaway: Different signals find different faults. Hybrids are reasonable, but granularity (class vs method) changes which technique wins.
- Read: **abstract + intro.**

**[W11] Luo, Moran, Poshyvanyk, Di Penta. "Assessing Test Case Prioritization on Real Faults and Mutants." ICSME 2018.**
URL: https://arxiv.org/pdf/1807.08823
- Summary: Compares 8 TCP techniques on 35k+ mutants against 357 real Defects4J faults.
- Quantitative: A technique's ranking on mutants "may not strongly correlate" with its ranking on real faults, and this depends on the program.
- Takeaway: Treat mutant-only TCP results with caution. Prefer evidence from real CI failures (W5, W8, W9).
- Read: **abstract.**

**[W12] Li, Zhou, Li, Hao, Zhang. "AGA: An Accelerated Greedy Additional Algorithm for Test Case Prioritization." IEEE TSE 2021.**
URL: https://arxiv.org/pdf/2205.10239
- Summary: The classic "additional coverage" greedy algorithm is effective but O(m²n). AGA reduces this to O(kmn) with extra data structures and a bounded iteration count.
- Quantitative: **5.95× average speedup over GA on 55 open-source subjects with the same average APFD; 44.27× on 22 Baidu subjects.**
- Takeaway: If you do use coverage-based prioritization, the prioritizer itself can become a bottleneck. Its cost counts against its benefit.
- Read: **abstract.**

### A2. Suite minimization / reduction: removing redundancy, and what it costs

**[W13] Yoo, Harman. "Regression Testing Minimization, Selection and Prioritization: A Survey." STVR 22(2):67–120, 2012.**
URL: http://www0.cs.ucl.ac.uk/staff/m.harman/stvr-shin-survey.pdf · https://onlinelibrary.wiley.com/doi/abs/10.1002/stvr.430
- Summary: The standard survey. It defines **minimization** (permanently drop redundant tests), **selection** (run tests relevant to a change) and **prioritization** (reorder). It catalogues the techniques (greedy set cover, integer linear programming, search-based, multi-objective) and open problems.
- Quantitative: A survey, so no single headline number.
- Takeaway: The vocabulary for the rest of this document. Only prioritization runs every test. Minimization and selection both accept some risk of missing a fault.
- Read: **full text (skimmed; preprint version).**

**[W14] Shi, Gyori, Gligoric, Zaytsev, Marinov. "Balancing Trade-Offs in Test-Suite Reduction." FSE 2014, pp. 246–256.**
URL: https://mir.cs.illinois.edu/awshi2/publications/FSE2014.pdf
- Summary: Measures reduction against killed mutants, "inadequate" reduction (keeping less than 100% of the requirements), and evolution-aware metrics across later versions.
- Quantitative: **18 projects, 261,235 tests, 3,590 commits.** Statement-coverage reduction shrinks suites by **62.9% on average (median) but loses up to 20.5% of killed mutants.** Reduction based on killed mutants loses no killed mutants but produces suites 11.9 percentage points larger. Keeping 95% of requirements instead of 100% increases the median size reduction by 17.14 pp. The authors compare with prior studies that found roughly 40–50% fault-detection loss. Reduced suites stay fairly robust as the software evolves.
- Takeaway: **Coverage-equivalent does not mean fault-detection-equivalent.** If you minimize, minimize by mutants, and keep running the full suite somewhere (nightly or post-submit).
- Read: **full text.**

**[W15] Gligoric, Eloussi, Marinov. "Practical Regression Test Selection with Dynamic File Dependencies" (Ekstazi). ISSTA 2015.**
URL: https://users.ece.utexas.edu/~gligoric/papers/GligoricETAL15Ekstazi.pdf
- Summary: *Safe* selection: record which files each test class touches at run time, and re-run a test only if one of those files changed. In effect this is test-result caching keyed on dynamic dependencies. It skips no test whose inputs changed.
- Quantitative: **615 revisions of 32 projects (about 5M LOC): end-to-end testing time reduced 32% on average and 54% for longer-running suites.** It is faster end-to-end than finer-grained techniques even though it selects more tests. Adopted by Apache Camel, Commons Math and CXF.
- Takeaway: **Coarse-grained dependency tracking wins**, because the analysis overhead is small. This is the same idea as Bazel/Nx/Go test caching (A4).
- Read: **abstract + intro.**

### A3. Parallelization, isolation and the long pole

**[W16] Candido, Melo, d'Amorim. "Test Suite Parallelization in Open-Source Projects: A Study on Its Usage and Impact." ASE 2017, pp. 838–848.**
URL: https://damorim.github.io/publications/candido-etal-ase17.pdf
- Summary: Studies 468 popular Java/Maven projects. It measures how often parallelism is used, the speedups, and flakiness under different JUnit/Maven configurations: sequential; parallel methods; parallel classes; both; forked JVMs.
- Quantitative: **24% of projects have costly suites, yet only 19.1% of those use parallelization.** The main reason given is fear of concurrency problems. **Average speedup 3.53×** (max 28.8×, Jcabi). Forked-JVM parallelism "scales with the number of cores but the speedups are **bounded by long-running test classes**". Forked JVMs show "very low rates of test flakiness", while in-JVM thread parallelism gives bigger speedups "at the expense of sometimes impressive rates of flakiness".
- Takeaway: **Process-level parallelism first (safe), thread-level second (fast but you must fix shared state).** Split the long test classes, because they set the floor.
- Read: **full text** (abstract, findings).

**[W17] Bell, Kaiser. "Unit Test Virtualization with VMVM." ICSE 2014 (ACM SIGSOFT Distinguished Paper).**
URL: https://mice.cs.columbia.edu/getTechreport.php?techreportID=1549&format=pdf · code https://github.com/Programming-Systems-Lab/vmvm
- Summary: Many Java projects isolate each test by starting a new JVM, which is expensive. VMVM instead resets only the static state a test could have polluted, inside one JVM.
- Quantitative: Across the projects studied, per-test initialization added **up to 4,153% of total testing time (average 618%)**. **81% of projects with more than 1,000 tests start a new process per test.** VMVM cut suite time by **up to 97% (average 62%)** on 20 applications. That is **4× more reduction than a well-known minimization technique, with no loss in fault-finding** because every test still runs.
- Takeaway: **Isolation overhead is often larger than the test bodies.** Reducing it is the "run everything, but faster" alternative to minimization.
- Read: **full text** (abstract, motivation).

**[W18] Zhang, Jalali, Wuttke, Muşlu, Lam, Ernst, Notkin. "Empirically Revisiting the Test Independence Assumption." ISSTA 2014.**
URL: https://dada.cs.washington.edu/research/tr/2014/01/UW-CSE-14-01-01.PDF
- Summary: Studies 96 real dependent tests from 5 issue trackers. It proves that detecting dependent tests (a useful special case) is NP-complete, and builds DTDetector.
- Quantitative: DTDetector found **27 previously unknown dependent tests** across 4 programs. Dependent tests **changed the output of all 5 prioritization techniques tested**. In one case, a bug in Apache CLI was masked by dependent tests for 3 years.
- Takeaway: Reordering, sharding and parallelism all assume test independence. **Randomize the order in CI** (`go test -shuffle`, `pytest-randomly`, `rspec --order rand`) to find dependencies *before* you parallelize.
- Read: **full text** (abstract, intro).

**[W19] Lam, Oei, Shi, Marinov, Xie. "iDFlakies: A Framework for Detecting and Partially Classifying Flaky Tests." ICST 2019, pp. 312–322.**
URL: https://dblp.org/rec/conf/icst/LamOSM019.html · https://par.nsf.gov/biblio/10101224-idflakies-framework-detecting-partially-classifying-flaky-tests
- Summary: Reruns tests in modified orders to detect flaky tests and separate order-dependent ones from the rest.
- Quantitative: A dataset of **422 flaky tests, 50.5% order-dependent**.
- Takeaway: About half of flakiness in Java open source is order dependence, which is exactly what parallelism and sharding expose.
- Read: **abstract only.**

**[W20] Silva, Gruber, Gokhale, Arteca, Turcotte, d'Amorim, Lam, Winter, Bell. "The Effects of Computational Resources on Flaky Tests." arXiv 2310.12132, 2023 (submitted to IEEE; I did not confirm the final venue).**
URL: https://arxiv.org/pdf/2310.12132
- Summary: Runs 52 Java/JS/Python projects under 27 CPU/memory configurations to find resource-affected flaky tests (RAFTs).
- Quantitative: **46.5% of the flaky tests were RAFTs.**
- Takeaway: **Over-subscribing a machine with too many workers turns timing-sensitive tests flaky.** Cap workers at cores (or cores minus 1), give each shard fixed resources, and rerun with fewer resources to *find* RAFTs.
- Read: **abstract + intro.**

**[W21] Luo, Hariri, Eloussi, Marinov. "An Empirical Analysis of Flaky Tests." FSE 2014, pp. 643–653.**
URL: http://mir.cs.illinois.edu/marinov/publications/LuoETAL14FlakyTestsAnalysis.pdf
- Summary: Root-cause study of 161 commits that fixed flaky tests.
- Quantitative: **Async Wait 45% (74/161), Concurrency 20% (32/161), Test Order Dependency 12% (19/161).** 34% of async-wait flaky tests use "a simple method call with time delays to enforce orderings" (the canonical example is `Thread.sleep(2000)`), and 54% were fixed with `waitFor`-style waiting.
- Takeaway: **Sleep-based waiting is both the most common cause of flakiness and a direct source of wasted time.** Replacing it with event-based or condition-based waits fixes both.
- Read: **full text** (findings, Async Wait section).

**[W22] Gruber, Lukasczyk, Kroiß, Fraser. "An Empirical Study of Flaky Tests in Python." ICST 2021.**
URL: https://arxiv.org/pdf/2101.09077
- Summary: Runs tests repeatedly across 22,352 PyPI projects (876,186 tests).
- Quantitative: 7,571 flaky tests, of which **59% are order-dependent** and 28% come from test-infrastructure problems. **170 reruns** would be needed for 95% confidence that a passing test is not flaky.
- Takeaway: In Python, shared module and global state dominates flakiness. Moving to `pytest-xdist` or `--dist loadscope` will surface it.
- Read: **abstract.**

**[W23] Graham. "Bounds on Multiprocessing Timing Anomalies." SIAM J. Appl. Math. 17(2):416–429, 1969.**
URL: https://people.irisa.fr/Sophie.Pinchinat/AA/Graham1969SIAM.pdf
- Summary: The theory behind duration-balanced sharding. List scheduling in arbitrary order is within 2 − 1/n of optimal makespan. **Longest-processing-time-first (LPT) is within 4/3 − 1/(3n).** The paper also describes the "anomalies": adding processors can *increase* the finishing time under naive list scheduling.
- Quantitative: The bounds above.
- Takeaway: **Sort test files by historical duration, largest first, then greedily assign each to the least-loaded worker.** That is what Jest's default sequencer does (D1) and what the timing-based CI splitters approximate. It cannot beat the single longest file. That file is the long pole, so split it.
- Read: **full text** (bound statement).

**[W24] Amdahl. "Validity of the Single Processor Approach to Achieving Large Scale Computing Capabilities." AFIPS SJCC 1967, pp. 483–485.**
URL: https://dl.acm.org/doi/10.1145/1465482.1465560
- Summary: The origin of Amdahl's law. The serial fraction of a workload bounds its speedup. For a test run, the serial parts are process and VM startup, transpile/compile, global setup (such as a database migration), report merging, and the longest single test file.
- Quantitative: With serial fraction s, speedup ≤ 1/s. (The formula is the standard textbook form; the paper itself argues in prose.)
- Takeaway: Measure the serial part first (Part D). Adding workers after it dominates gives nothing.
- Read: **abstract only.**

**[W25] Fallahzadeh, Bavand, Rigby. "Accelerating Continuous Integration with Parallel Batch Testing." ESEC/FSE 2023.**
URL: https://arxiv.org/pdf/2308.13129
- Summary: Studies how machine count and batching of commits affect feedback time, using Ericsson data and 276 million Chrome test outcomes.
- Quantitative: Parallelism has a **non-linear** effect on feedback time, because each delay compounds down the queue. ConstantBatching (size 4) keeps the actual average feedback time with **up to 72% fewer machines**. BatchAll does so with up to 91% fewer, and TestCaseBatching with up to 81% fewer.
- Takeaway: Queueing matters as well as per-run time. Past a threshold, extra machines stop helping, so find that threshold from your own history.
- Read: **abstract.**

**[W26] Fallahzadeh, Rigby, Adams. "Contrasting Test Selection, Prioritization, and Batch Testing at Scale." Empirical Software Engineering, 2024.**
URL: https://mcislab.github.io/publications/2025/emse_scale.pdf
- Summary: Compares selection, prioritization and batching on Chrome, a Google project and JMRI.
- Quantitative: **Selection cut median feedback time by up to 96% but missed up to 55% of failures. Batching cut feedback time by up to 99% while missing none.** Selection saved up to 66% of execution time, batching up to 98%. The prioritization algorithms studied "significantly underperform".
- Takeaway: **If "never miss a failure" is a hard requirement, prefer batching, parallelism and caching over selection.**
- Read: **abstract.**

### A4. Caching, hermeticity and build-system theory

**[W27] Mokhov, Mitchell, Peyton Jones. "Build Systems à la Carte." Proc. ACM PL 2 (ICFP), Article 79, 2018.**
URL: https://www.microsoft.com/en-us/research/wp-content/uploads/2018/03/build-systems.pdf
- Summary: Breaks every build system into a **scheduler** and a **rebuilder**, and places Make, Shake, Bazel, Excel and others in that design space. Definition 2.1 of *minimality*: execute each task at most once per build, and only if it transitively depends on inputs that changed. It explains *early cutoff* (stop when a rebuilt output is unchanged) and *cloud builds*. Bazel keeps a content-addressable cache plus a history of commands annotated with file hashes, so it can "predict the hash of the result from the hashes of its dependencies" and download instead of executing.
- Quantitative: Theory paper; none.
- Takeaway: **A test is a build task whose output is pass/fail.** If it is hermetic, its result can be keyed on the hash of its inputs and reused. That is test caching in Bazel, Go, Nx and Turborepo.
- Read: **full text** (sections 2.1–2.4).

**[W28] Zheng, Adams, Hassan. "Does Using Bazel Help Speed Up Continuous Integration Builds?" Empirical Software Engineering, 2024.**
URL: https://arxiv.org/pdf/2405.00796 · https://link.springer.com/article/10.1007/s10664-024-10497-x
- Summary: 383 Bazel projects on GitHub. The authors ran 102,232 experiments on 70 buildable projects × their last 100 commits.
- Quantitative: For projects with long builds, median parallel speedups were **2.00×, 3.84×, 7.36× and 12.80× at parallelism 2, 4, 8 and 16**. Incremental builds with a CI cache gave a median **4.22×** (tool-independent cache) or **4.71×** (Bazel-specific cache). **31.23% of Bazel projects with CI don't run Bazel in CI.** Benefits are limited for projects with short builds.
- Takeaway: Parallelism plus a remote or incremental cache compound. Both are worth it for long suites and marginal for short ones.
- Read: **full text** (abstract, results).

**[W29] Ghaleb, da Costa, Zou. "The Promise and Reality of Continuous Integration Caching: An Empirical Study of Travis CI Builds." arXiv 2601.19146, 2026.**
URL: https://arxiv.org/pdf/2601.19146
- Summary: Studies 513,384 builds from 1,279 projects.
- Quantitative: **Only 30% of projects adopt CI caching.** About half of the PRs the authors sent to enable caching were accepted. One third of projects see substantial reductions in build time, but **cache uploads happen in 97% of builds and 27% of projects hold stale cached artifacts.**
- Takeaway: Dependency and artifact caching is under-used and needs maintenance. Key caches on lockfile hashes, and check hit rates.
- Read: **abstract.**

**[W30] Gallaba, Ewart, Junqueira, McIntosh. "Accelerating Continuous Integration by Caching Environments and Inferring Dependencies" (Kotinos). IEEE TSE 48(6):2040–2052, 2022.**
URL: https://rebels.cs.uwaterloo.ca/journalpaper/2020/12/27/accelerating-continuous-integration-by-caching-environments-and-inferring-dependencies.html
- Summary: Language-agnostic CI acceleration. It caches build environments and infers dependencies without migrating the build system.
- Quantitative: On 14,364 builds across 10 projects, **87.9% of builds activated at least one acceleration, and 74% of accelerated builds ran at least 2× faster**, with less than 1% median CPU overhead.
- Takeaway: Environment setup (containers, dependency installs) is often a large, easily cached serial fraction.
- Read: **abstract only.**

**[W31] Esfahani et al. "CloudBuild: Microsoft's Distributed and Caching Build Service." ICSE-SEIP 2016.**
URL: https://www.microsoft.com/en-us/research/publication/cloudbuild-microsofts-distributed-and-caching-build-service/
- Summary: Microsoft's content-based caching plus distributed build and test service. It tolerates non-deterministic tools and incomplete dependency declarations.
- Quantitative: **Speedups of 1.3× to 10×**; 99% availability.
- Read: **abstract only.**

### A5. Industrial scale: most tests pass, so spend less on the ones that always pass

**[W32] Memon, Gao, Nguyen, Dhanda, Nickell, Siemborski, Micco. "Taming Google-Scale Continuous Testing." ICSE-SEIP 2017, pp. 233–242.**
URL: https://huang.isis.vanderbilt.edu/cs8395/paper/google-testing-icse-seip-17.pdf
- Summary: Studies Google's TAP system (a codebase of about 2 billion LOC), which cuts "milestones" roughly every 45 minutes at peak.
- Quantitative: Per day, **more than 13K projects, 800K builds and 150 million test runs**. Milestones reached **4.2 million tests**, and delays reached **up to 9 hours**. **Of 5.5 million affected tests over a month, only 63K ever failed. Only 1.23% of test executions found a breakage. 91.3% of targets passed at least once and never failed.**
- Takeaway: Nearly all test executions carry no new information. That is why ordering (W2, W8) and caching unchanged results (W27) pay off so well.
- Read: **full text** (intro, data).

**[W33] Machalica, Samylkin, Porth, Chandra. "Predictive Test Selection." ICSE-SEIP 2019 (Facebook).**
URL: https://arxiv.org/abs/1810.05286
- Summary: Machine-learning selection for each change, trained on historical outcomes.
- Quantitative: **Halved the infrastructure cost of testing changes while catching over 95% of individual test failures and over 99.9% of faulty changes.**
- Takeaway: This is the bar for "unsafe" selection. It still misses some test failures, so run the full suite later (post-submit or nightly).
- Read: **abstract + intro.**

### A6. Per-test cost: sleeps, smells, isolation

**[W34] Garousi, Küçük. "Smells in Software Test Code: A Survey of Knowledge in Industry and Academia." JSS 138:52–81, 2018.**
URL: https://pureadmin.qub.ac.uk/ws/portalfiles/portal/178889150/MLR_Smells_in_test_code_Dec_9.pdf
- Summary: A multivocal literature review covering **166 sources (120, or 72.2%, grey literature)** that catalogues test smells, including a "Test execution / behavior → Performance" family (*Slow Test*, *Long Running Test*).
- Quantitative: 81 of the 166 sources proposed smells; 24 contributed tools.
- Takeaway: Practitioners recognize slow tests as a smell, but tool support for finding them is weak. Measure durations yourself (Part D).
- Read: **full text (skimmed; smell tables).**

**[W35] Peruma, Almalki, Newman, Mkaouer, Ouni, Palomba. "tsDetect: An Open Source Test Smells Detection Tool." ESEC/FSE 2020 (Tool Demos).**
URL: https://testsmells.org/assets/publications/FSE2020_TechnicalPaper.pdf
- Summary: Detects 19 test smells in Java, including **Sleepy Test**, defined as "A test method that invokes the Thread.sleep() method".
- Quantitative: 96% precision and 97% recall on a 65-file benchmark (per the abstract).
- Takeaway: `sleep` in a test is statically detectable. Add a lint rule that forbids it (for example, grep in CI for `sleep(`, `setTimeout(` with literal delays, and `time.sleep` in test directories).
- Read: **full text** (rule table).

**[W36] Winters, Manshreck, Wright (eds.). *Software Engineering at Google*, O'Reilly 2020. Ch. 11 "Testing Overview" and Ch. 14 "Larger Testing".**
URL: https://abseil.io/resources/swe-book/html/ch11.html · https://abseil.io/resources/swe-book/html/ch14.html
- Summary: Google classifies tests by size. **Small tests**: one process, and they "aren't allowed to sleep, perform I/O operations, or make any other blocking calls", with test doubles used instead. **Medium tests**: one machine, network only to localhost. **Large tests**: multiple machines. "All tests should strive to be hermetic." Suggested mix: about 80% unit, 15% integration, 5% end-to-end.
- Quantitative (quoting the guidance): sleeps and `setTimeout` introduce "unnecessary speed limits"; a wait-and-check helper inside a widely used utility can add "minutes of idle time to every run". It recommends polling at close to microsecond frequency with a timeout. Engineers facing slow suites went "as far as to skip the tests entirely when submitting changes".
- Takeaway: **Enforce size constraints mechanically.** Small tests should run with no sleeps, no network and no disk (use in-memory filesystems or fakes).
- Read: **full text** (relevant sections).

**[W37] Rasheed, Tahir, Dietrich, Hashemi, Zhang. "Test Flakiness' Causes, Detection, Impact and Responses: A Multivocal Review." arXiv 2212.00908, 2022.**
URL: https://arxiv.org/pdf/2212.00908
- Summary: Combines academic and grey-literature evidence on flakiness. Relevant here because the common "fix" of retrying failed tests costs time, and the common causes (async waits, concurrency, order) are the same things that make suites slow or hard to parallelize.
- Read: **abstract.**

---

## Part B — Official tool documentation (verified behavior)

These are primary sources for the commands in Part E. Each was fetched on 2026-09-29.

| # | Source | What I verified |
|---|---|---|
| D1 | Jest default `TestSequencer` source, https://raw.githubusercontent.com/jestjs/jest/main/packages/jest-test-sequencer/src/index.ts | `sort()` orders: **previously failed first, then tests without timing data, then longest duration first, falling back to file size**. The comment explains: "running long tests first is an effort to minimize worker idle time at the end of a long test run." That is LPT (W23) plus failed-first (W8). `shard()` assigns files by **sha1 of the relative path**, not by duration. |
| D2 | Jest CLI, https://jestjs.io/docs/cli | `--maxWorkers` defaults to cores − 1 in single-run mode and half the cores in watch mode, and accepts a percentage such as `50%`. `--shard=i/n`. `--runInBand`. Disabling the cache "makes Jest at least two times slower". `--detectOpenHandles` implies `--runInBand`. |
| D3 | Jest config `workerIdleMemoryLimit`, https://raw.githubusercontent.com/jestjs/jest/main/docs/Configuration.md | Workers are recycled after exceeding a memory limit (a workaround for leak issue #11956). |
| D4 | Jest Timer Mocks, https://raw.githubusercontent.com/jestjs/jest/main/docs/TimerMocks.md | `jest.useFakeTimers()`, `jest.runAllTimers()`, `jest.runOnlyPendingTimers()`, `jest.advanceTimersByTime(ms)`. |
| D5 | Node.js CLI, https://nodejs.org/api/cli.md | `--test-concurrency` (added v21.0.0/v20.10.0/v18.19.0) defaults to `os.availableParallelism() - 1` and is ignored when isolation is `none`. `--test-isolation=process\|none` (added v22.8.0, renamed from `--experimental-test-isolation` in v23.6.0). `--test-shard=<index>/<total>` (v20.5.0/v18.19.0) "will divide all tests files into `total` equal parts", which balances by **file count**, not duration. |
| D6 | Node.js test runner, https://nodejs.org/api/test.html | `mock.timers.enable({apis:[...]})`, `.tick(ms)`, `.runAll()`. |
| D7 | Vitest "Improving Performance", https://raw.githubusercontent.com/vitest-dev/vitest/main/docs/guide/improving-performance.md | The Duration line breaks down into environment/import/transform/setup/tests. Per-file isolation "greatly increases test times". `--no-isolate`, `--no-file-parallelism`, `pool: threads\|forks\|vmThreads`. jsdom costs "roughly 200–500ms per import", happy-dom 90–200 ms. `--shard=i/n --reporter=blob` then `--merge-reports`. Shards are by *test files*, not test cases. `NODE_COMPILE_CACHE`. *(These are the main-branch docs; `vitest doctor` and `experimental.diagnostics` may be newer than your installed version.)* |
| D8 | pytest-xdist distribution, https://pytest-xdist.readthedocs.io/en/stable/distribution.html | `-n auto` (physical cores), `-n logical`; `--dist load\|loadscope\|loadfile\|loadgroup\|worksteal\|no`. |
| D9 | pytest-split README, https://raw.githubusercontent.com/jerry-git/pytest-split/master/README.md | `pytest --store-durations`, then `pytest --splits N --group k`. `--splitting-algorithm least_duration` gives "more balanced groups" than the default `duration_based_chunks`. |
| D10 | pytest cache and usage docs, https://raw.githubusercontent.com/pytest-dev/pytest/main/doc/en/how-to/cache.rst and https://docs.pytest.org/en/stable/how-to/usage.html | `--lf`, `--ff` (failed first), `--nf` (new first), `--sw` (stepwise); `--durations=10 --durations-min=1.0`. |
| D11 | Go `cmd/go`, https://pkg.go.dev/cmd/go | `-p n` (test binaries in parallel, default GOMAXPROCS); `-parallel n` (within one binary, for `t.Parallel` tests, default GOMAXPROCS); **test result caching** applies only when using "cacheable" flags, and `-count=1` is "the idiomatic way to disable test caching"; `-shuffle on`; `-failfast`. |
| D12 | Go `testing/synctest` + Go 1.25 release notes, https://pkg.go.dev/testing/synctest · https://go.dev/doc/go1.25 | Inside a bubble "the time package uses a fake clock", and time advances only when every goroutine is durably blocked. The package was experimental in 1.24 and **generally available in Go 1.25**. |
| D13 | Gradle performance guide, https://docs.gradle.org/current/userguide/performance.html | `org.gradle.parallel=true`, `--build-cache`, `--configuration-cache`; `maxParallelForks = availableProcessors()/2` (their example); `forkEvery` ("Forking a JVM is an expensive operation. Setting forkEvery too low can increase test time"). |
| D14 | Maven Surefire fork/parallel, https://maven.apache.org/surefire/maven-surefire-plugin/examples/fork-options-and-parallel-execution.html | `forkCount` accepts the `C` suffix (for example `2.5C` = 2.5 × cores); `reuseForks` (default true); `parallel=classes\|methods\|classesAndMethods\|all` with `threadCount`. In-JVM parallelism is "more vulnerable towards race conditions". |
| D15 | JUnit 5 parallel execution, https://docs.junit.org/current/writing-tests/parallel-execution.html | `junit.jupiter.execution.parallel.enabled=true`, `...mode.default=concurrent\|same_thread`, `...mode.classes.default=...`, `...config.strategy=dynamic` with `...config.dynamic.factor`. |
| D16 | Bazel command-line reference, https://bazel.build/reference/command-line-reference | `--cache_test_results` (auto: rerun only if the test or its dependencies changed, the test is external, `--runs_per_test` is set, or it failed previously), `--remote_cache=<URI>`, `--disk_cache`, `--test_sharding_strategy`, `--flaky_test_attempts`, `--runs_per_test`, `--local_test_jobs`, `--remote_download_minimal`. |
| D17 | Bazel Test Encyclopedia and Hermeticity, https://bazel.build/reference/test-encyclopedia · https://bazel.build/basics/hermeticity | "Tests should be hermetic". `shard_count`, `TEST_TOTAL_SHARDS`, `TEST_SHARD_INDEX`, `TEST_SHARD_STATUS_FILE`. Benefits of hermeticity: caching, parallel execution, reproducibility. |
| D18 | Nx caching and affected, https://nx.dev/docs/concepts/how-caching-works · https://nx.dev/docs/features/ci-features/affected | The hash covers project and dependency sources, relevant configuration, external dependency versions, OS/arch, and CLI arguments. A hit replays stdout/stderr plus declared `outputs`. Local cache is checked, then remote. `nx affected -t test --base=origin/main`. |
| D19 | Turborepo caching and run reference, https://turborepo.dev/docs/crafting-your-repository/caching · https://turborepo.dev/docs/reference/run | Global and package hashes (including `globalEnv`). "If you do not declare file outputs for a task, Turborepo will not cache them." `--summarize` and `--dry` for debugging misses. `turbo run test --affected`. |
| D20 | CircleCI test splitting, https://circleci.com/docs/guides/optimize/parallelism-faster-jobs/ | `parallelism: N`; `circleci tests run --split-by=timings` (cloud) or `circleci tests split --split-by=timings`; needs JUnit XML with `time` and `file` attributes; the first run has no timings and falls back to alphabetical order. |
| D21 | Knapsack Pro overview, https://docs.knapsackpro.com/overview/ | Queue Mode: each node repeatedly pulls the next batch from an API queue so "each CI node finishes at the same time". The rationale for dynamic over static splitting: varying test times, faster failing tests, heterogeneous nodes, staggered boots. Split-by-examples for slow files. |
| D22 | Buildkite Test Engine splitting, https://buildkite.com/docs/test-engine/test-splitting | The `bktec` client splits by historical timing and rebalances. **Mute** (still runs, result ignored) is preferred over **skip**. |
| D23 | Playwright sharding, https://playwright.dev/docs/test-sharding | `npx playwright test --shard=i/n`. With `fullyParallel: true` it balances at test level; otherwise at file level. |
| D24 | cargo-nextest benchmarks, partitioning and design, https://nexte.st/docs/benchmarks/ · https://nexte.st/docs/ci-features/partitioning/ · https://nexte.st/docs/design/how-it-works/ | Measured speedups over `cargo test`: 1.37× (penumbra) to 3.38× (crucible), for example tokio 24.27 s → 11.60 s (2.09×), on a 16-core Ryzen, excluding build time. The cause is **long-pole test binaries**: a 60 s test in a binary blocks `cargo test` from starting other binaries. `--partition slice:m/n` or `hash:m/n`. Process-per-test is slower to spawn on Windows and macOS. |
| D25 | Rails Testing Guide, https://raw.githubusercontent.com/rails/rails/main/guides/source/testing.md | `parallelize(workers: :number_of_processors)`, `with: :threads`, `work_stealing: true`, `PARALLEL_WORKERS=15`, `parallelize_setup`. There is a default threshold of 50 tests below which Rails does not parallelize, because of database setup and fixture overhead (`config.active_support.test_parallelization_threshold`). |
| D26 | parallel_tests README, https://raw.githubusercontent.com/grosser/parallel_tests/master/Readme.md | Groups by runtime log (`--group-by runtime`, `ParallelTests::RSpec::RuntimeLogger`), with one database per process. |
| D27 | Spring README, https://raw.githubusercontent.com/rails/spring/main/README.md | A Rails preloader that keeps the app running so you don't "boot it every time you run a test". MRI 3.1+ and Rails 7.1+. |
| D28 | RSpec option parser, https://raw.githubusercontent.com/rspec/rspec/main/rspec-core/lib/rspec/core/option_parser.rb | `--profile [COUNT]`, `--only-failures`, `--next-failure`, `--fail-fast[=N]`, `--bisect`. |
| D29 | tokio `time::pause`, https://docs.rs/tokio/latest/tokio/time/fn.pause.html | Paused time auto-advances when the runtime is idle; `#[tokio::test(start_paused = true)]`; requires the current_thread runtime. |
| D30 | Python `-X importtime`, https://docs.python.org/3/using/cmdline.html | Per-import cumulative and self time, useful for startup cost per test process. |

---

## Part C — Consensus synthesis

1. **Most runs are green, so what matters is how fast a red run shows up.** At Google, 1.23% of test executions found a breakage [W32]. At BMW, 98% of pre-submit executions pass [W9]. Optimize time-to-first-failure (NTTF/APFDc), not APFD [W5, W8, W9].

2. **Simple ordering beats sophisticated ordering.** On real failures with cost-aware metrics, *quickest-test-first* is a top baseline [W5]. *Failed-recently plus fastest-first* beat all 59 techniques on 6.5-hour suites [W8]. History features are the most valuable ones [W6]. Machine-learning rankers help mainly when well trained [W4, W7], and expensive features can cost more than they save [W6, W12]. **Jest already ships a failed-first plus longest-first sequencer [D1].** Note the tension: longest-first is right for **packing workers** (LPT, W23), and fastest-first is right for **first-failure latency** on a single worker. With many workers, pack by LPT and put recently failed tests at the front.

3. **Parallelism gives the biggest speedups, but isolation and the long pole cap it.** Average 3.53× in Java open source, bounded by long test classes [W16]. Bazel: 12.8× at 16-way parallelism for long builds [W28]. nextest: 1.4–3.4×, caused by long poles [D24]. The theory [W23, W24] says: pack by LPT, then split whatever is longest, then remove serial setup.

4. **Isolation is the hidden tax, and the safety/speed trade-off is real.** Per-test process isolation can cost more than the tests themselves (average 618% overhead in [W17]). Vitest's docs say isolation "greatly increases test times" [D7]. Rails will not parallelize fewer than 50 tests because of setup overhead [D25]. On the other side, shared-process parallelism exposes order-dependent tests, which are 50.5% of Java flaky tests [W19] and 59% in Python [W22], plus resource-affected ones (46.5%) [W20]. The consensus: **processes first; then drop isolation once you can prove independence** (random-order runs, `vitest doctor`, iDFlakies-style reruns).

5. **Caching unchanged work is the only way to go below "run everything once."** A hermetic test's result is a pure function of its input hashes [W27, D17]. Bazel, Go, Nx and Turborepo all reuse results this way [D11, D16, D18, D19]. Ekstazi shows that file-level dynamic dependencies give a 32–54% reduction safely [W15]. CI caching is under-adopted (30% of projects) and goes stale (27%) [W29].

6. **Sleeping is the most common single cause of both wasted time and flakiness.** Async-wait accounts for 45% of fixed flaky tests, a third of those use fixed delays, and most fixes switch to condition waits [W21]. Google forbids sleeps in small tests [W36]. Fake clocks are standard in every major ecosystem [D4, D6, D12, D29].

7. **Reduction and unsafe selection trade away fault detection.** Coverage-based reduction lost up to 20.5% of killed mutants [W14]. Selection missed up to 55% of failures, while batching missed none [W26]. Facebook's selector keeps more than 95% of failures [W33]. If "never miss" is the rule, prefer parallelism, caching and batching, and run the full suite at least post-merge.

8. **Measure before you optimize.** Every tool reports per-file durations. The things to look for are wall time vs. summed CPU time (parallel efficiency), the single longest file (the long pole), and serial startup (the Amdahl fraction) [W24, D7, D10].

---

## Part D — How to profile a test suite (the four numbers)

1. **Wall time W** of the whole command, and **ΣT**, the sum of per-file durations from the reporter. Parallel efficiency is ΣT / (W × workers). If it is well below 1, the time is going to idle workers or serial overhead, not to test bodies.
2. **Long pole L**, the longest single file or shard. With P workers, W ≥ max(L, ΣT/P). If L > ΣT/P, adding workers does nothing; split L instead.
3. **Serial fraction S**: time before the first test starts and after the last one ends (transpile, DB migrate, container boot, report merge). By Amdahl, speedup ≤ W/S.
4. **Idle waits**: grep tests for `sleep`, `setTimeout(…, N)`, `time.sleep`, `Thread.sleep`, and retry-with-delay helpers. Multiply each delay by how often it runs.

Tools: `pytest --durations=0`; `vitest` Duration breakdown [D7]; Jest per-file times plus `--logHeapUsage`; `go test -json` (per-test `Elapsed`); `cargo nextest` slow-test reporting; `rspec --profile 20`; Gradle Build Scan and `--profile`; Bazel `--profile` and `bazel analyze-profile` *(standard Bazel commands; not re-verified in this research)*; `python -X importtime` for import startup [D30].

---

## Part E — Prioritized playbook (do these in this order)

Each step keeps "run every test", or keeps it for the merge gate.

1. **Measure (Part D).** Record W, ΣT, L and S. Write per-file durations to a file you commit or cache, because later steps need them.
2. **Remove idle waits.** Replace fixed sleeps with fake clocks (`jest.useFakeTimers`, `mock.timers`, `synctest`, `tokio::time::pause`, `time-machine`/`freezegun`) or condition polling with a timeout. Lint against new sleeps in test directories. This is usually the best return on effort, and it also removes the largest flakiness category [W21, W36].
3. **Use all cores with process-level parallelism.** Jest and Vitest do this by default; add `node --test --test-concurrency`, `pytest -n auto`, `go test` (already parallel across packages), Gradle `maxParallelForks`, Surefire `forkCount=1C`, `cargo nextest`, and Rails `parallelize`. Cap workers at cores, not above [W20].
4. **Make tests order-independent, then prove it.** Randomize order in CI (`-shuffle on`, `pytest-randomly`, `rspec --order rand`). Give each worker its own database, schema, temp directory and port. This must be true before step 5 and before any cache is trustworthy [W18, W19, W22].
5. **Cut isolation overhead where independence is proven.** Share one worker process per file group (`vitest --no-isolate` per project, `node --test-isolation=none`, Surefire `reuseForks=true`), use lighter environments (node instead of jsdom), preload the application (Spring), and reuse one DB and schema per worker with transactional rollback [W17, D7, D25, D27].
6. **Order for first failure.** Previously failed first, then new tests, then (for packing) longest first. Jest does this already [D1]. Use `pytest --ff --nf`, `rspec --only-failures` locally, and Bazel's automatic rerun of previously failed tests. Fail fast locally (`-x`, `--bail`, `-failfast`), but not in the merge gate [W2, W5, W8].
7. **Split the long pole.** Break the longest file or class until L ≤ ΣT/P. Move slow end-to-end tests into their own shard or job so they start at t = 0 [W16, W23, D24].
8. **Shard across machines by *duration*, not file count.** Built-in `--shard` flags in Jest, Node, Vitest and Playwright (without `fullyParallel`) split by hash or file count [D1, D5, D7, D23]. Use timing-based splitters (CircleCI `--split-by=timings`, Buildkite `bktec`, Knapsack Pro Queue Mode, `pytest-split --splitting-algorithm least_duration`, `parallel_tests --group-by runtime`) or a queue with work stealing (`pytest-xdist --dist worksteal`, Rails `work_stealing: true`).
9. **Cache.** First dependencies and environments (lockfile-keyed) [W29, W30]. Then **test results keyed by input hashes**: Go's test cache, Bazel `--remote_cache` with `--cache_test_results=auto`, `nx affected` plus the Nx cache, `turbo run test --affected` with declared outputs. This requires hermetic tests (step 4) [W27, W28].
10. **Only then consider safe selection** (Ekstazi-style file-dependency RTS, `jest --changedSince`) for the *inner* loop. Keep the full, uncached suite as a scheduled or post-merge safety net. Treat ML or unsafe selection [W33] and minimization [W14] as last resorts, and never apply them at the merge gate if "never miss a failure" is a principle.

---

## Part F — Commands per ecosystem (verified against the docs in Part B)

### JavaScript / TypeScript
```bash
# Jest: workers, sharding, fake timers, memory recycling
npx jest --maxWorkers=50%            # or a number; default = cores-1 [D2]
npx jest --shard=2/4                 # shards by sha1(path), NOT duration [D1]
npx jest --changedSince=origin/main  # inner loop only [D2]
# jest.config: workerIdleMemoryLimit: '512MB' [D3]
# in tests: jest.useFakeTimers(); jest.advanceTimersByTime(1000); [D4]

# Node built-in runner (v22.8+ for isolation flag)
node --test --test-concurrency=8                 # default availableParallelism()-1 [D5]
node --test --test-isolation=none                # one process; only if tests are independent [D5]
node --test --test-shard=1/3                     # equal parts by FILE COUNT [D5]
# in tests: t.mock.timers.enable({ apis: ['setTimeout','Date'] }); t.mock.timers.tick(1000) [D6]

# Vitest
vitest run --no-isolate                          # or per-project isolate:false [D7]
vitest run --pool=threads
vitest run --reporter=blob --shard=1/3 && vitest run --merge-reports   # shards by file [D7]
NODE_COMPILE_CACHE=node_modules/.cache/node-compile-cache vitest run   [D7]

# Playwright
npx playwright test --shard=1/4                  # set fullyParallel: true for test-level balance [D23]

# Monorepo caching
npx nx affected -t test --base=origin/main      [D18]
npx turbo run test --affected --summarize       [D19]
```

### Python
```bash
pytest -n auto --dist worksteal        # physical cores; or -n logical (needs psutil) [D8]
pytest -n auto --dist loadscope        # keep module/class fixtures on one worker [D8]
pytest --durations=20 --durations-min=0.5    [D10]
pytest --ff --nf                       # failed first, then new first [D10]
pytest --store-durations               # then, per CI shard:
pytest --splits 4 --group 2 --splitting-algorithm least_duration   [D9]
python -X importtime -c "import yourpkg" 2> import.log                [D30]
# fake time: time-machine / freezegun (third-party); avoid time.sleep in tests
```

### JVM (Gradle / Maven / JUnit 5)
```kotlin
// build.gradle.kts [D13]
tasks.withType<Test>().configureEach {
    maxParallelForks = (Runtime.getRuntime().availableProcessors() / 2).coerceAtLeast(1)
    // forkEvery = 100   // only to contain leaks; forking is expensive
}
// gradle.properties: org.gradle.parallel=true, org.gradle.caching=true, org.gradle.configuration-cache=true
// CLI: ./gradlew test --build-cache --configuration-cache --parallel
```
```xml
<!-- Maven Surefire [D14] -->
<forkCount>1C</forkCount>          <!-- 1 JVM per core -->
<reuseForks>true</reuseForks>      <!-- default; avoids per-class JVM startup -->
```
```properties
# src/test/resources/junit-platform.properties [D15]
junit.jupiter.execution.parallel.enabled=true
junit.jupiter.execution.parallel.mode.default=concurrent
junit.jupiter.execution.parallel.mode.classes.default=concurrent
junit.jupiter.execution.parallel.config.strategy=dynamic
```

### Go
```bash
go test ./...                       # packages in parallel (-p = GOMAXPROCS); results cached [D11]
go test -parallel 8 ./...           # cap t.Parallel() tests within a binary [D11]
go test -count=1 ./...              # idiomatic cache bypass (merge gate / nightly) [D11]
go test -shuffle=on ./...           # surface order dependence [D11]
go test -json ./... | tee test.json # per-test Elapsed for profiling
# Fake clock for concurrent code (Go 1.25+): synctest.Test(t, func(t *testing.T){ ... }) [D12]
```
In test code, call `t.Parallel()` in independent tests.

### Rust
```bash
cargo nextest run --workspace                    # process-per-test; handles long poles [D24]
cargo nextest run --partition slice:1/4          # or hash:1/4, for CI sharding [D24]
# async fake time: #[tokio::test(start_paused = true)] / tokio::time::pause() [D29]
```

### Ruby / Rails
```ruby
# test/test_helper.rb [D25]
class ActiveSupport::TestCase
  parallelize(workers: :number_of_processors, work_stealing: true)   # or with: :threads
  parallelize_setup { |worker| ... }       # per-worker resources
end
# config/environments/test.rb: config.active_support.test_parallelization_threshold = 50 (default)
```
```bash
PARALLEL_WORKERS=8 bin/rails test                            [D25]
bundle exec rspec --profile 20                               [D28]
bundle exec rspec --only-failures   # / --next-failure       [D28]
bundle exec parallel_rspec -n 8 --group-by runtime           # after recording runtime log [D26]
# Spring preloader (Rails 7.1+): bin/spring binstub --all    [D27]
```

### Bazel (polyglot)
```bash
bazel test //... --remote_cache=grpcs://cache.example:443 --cache_test_results=auto   [D16]
bazel test //... --disk_cache=~/.cache/bazel-disk --remote_download_minimal           [D16]
bazel test //... --test_sharding_strategy=explicit   # with shard_count = N in BUILD [D16, D17]
bazel test //... --runs_per_test=20 --test_output=errors   # deflake hunting only [D16]
```

### CI splitters (duration-aware)
```yaml
# CircleCI [D20]
parallelism: 4
# run: <list tests> | circleci tests run --command "xargs <runner>" --split-by=timings
# requires store_test_results with JUnit XML (time + file attributes)
```
Knapsack Pro Queue Mode [D21] and Buildkite `bktec` [D22] also split by duration, and they rebalance dynamically.

---

## Gaps and uncertainty

- **Rothermel et al. 2001 [W1]** and **Elbaum et al. TSE 2002** ("Test Case Prioritization: A Family of Empirical Studies"): I could not get the primary PDFs (HTTP 403). No numbers are quoted from them.
- **Lam et al. on parallelism-induced flakiness specifically:** the closest works I located and cite are iDFlakies [W19] (order dependence) and Silva et al. [W20] (resource contention). I did not locate a dedicated "parallel-execution flakiness" paper by Lam in this research.
- **Jest isolation cost:** Jest has no no-isolate switch comparable to Vitest's. The only quantified isolation-overhead claims here are VMVM [W17], Vitest's docs [D7] and Rails' threshold rationale [D25].
- **Several commands** (Bazel `--profile`, `rspec --order rand`, `pytest-randomly`, freezegun/time-machine APIs) are standard, but I did not re-open their docs in this research. They are marked in the text where they appear.
- Vitest docs were read from the **main branch**. Check that features such as `vitest doctor` and `experimental.diagnostics` exist in your installed version.
