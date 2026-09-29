# 03: Flaky tests, test isolation, and order dependence

*How reliable fast feedback is. Part of "In the AI coding era, the bottleneck is testing".*

Research date: 2026-09-29. Every source below was located and fetched during this research. "Read: full text" means I extracted the PDF text and read the abstract, findings tables, and the sections I quote. It does **not** mean I read every page. "Abstract only" means I read the abstract or landing page and no more. Numbers are copied from the source. Where a number reached me second-hand (a paper citing another paper), I say so.

**Why this matters for fast feedback.** Making a suite fast usually means running it in parallel, selecting a subset of tests, running tests in a different order, or sharing fixtures. Each of these breaks the hidden assumption that tests are independent and deterministic. A flaky signal hurts people, and it hurts an AI coding agent even more. An agent takes a red test at face value. It will "fix" code that is not broken, retry until the suite happens to go green, or learn to ignore failures. The studies below give the base rates, the root causes, and the fixes that work.

---

## Part A: Foundational empirical studies

### A1. Luo, Hariri, Eloussi, Marinov. *An Empirical Analysis of Flaky Tests.* FSE 2014, pp. 643–653. doi:10.1145/2635868.2635920
- URL fetched: https://mir.cs.illinois.edu/marinov/publications/LuoETAL14FlakyTestsAnalysis.pdf
- Summary: The first large study of what causes flaky tests. The authors searched the commit logs of Apache projects for the keywords "intermit" and "flak". This found 486 commits that likely fix a flaky test (LDFFT commits). They inspected 201 of them and classified the root cause of 161. The resulting taxonomy has 10 categories, and they also looked at how each kind of flaky test can be made to show itself (manifested) and how developers fixed it.
- Quantitative:
  - Share of the 161 classified root causes (the first three account for 77%):
    - Async Wait 74 (45%)
    - Concurrency 32 (20%)
    - Test Order Dependency 19 (12%)
    - Resource Leak 11
    - Network 10
    - Time 5
    - IO 4
    - Randomness 4
    - Floating point 3
    - Unordered collections 1
  - 78% of flaky tests were flaky from the first time they were written.
  - 96% of flaky tests do not depend on the platform.
  - Async Wait: 34% enforce ordering with a simple time-delay call such as `sleep`. 85% do not wait for any external resource and involve only one ordering. 54% were fixed with `waitFor`, which usually removes the flakiness entirely instead of just making it rarer.
  - Concurrency: fixes were locks (31%), making the code deterministic (25%), or changing a condition (9%). 97% of failures involve concurrent access to in-memory objects only.
  - Test Order Dependency: 47% come from external resources such as files or ports, not in-memory state. 74% were fixed by cleaning shared state between tests.
  - 24% of fixes changed the code under test, and 94% of those fixed a real bug in it.
  - Cites a personal communication with John Micco: 73K of 1.6M (4.56%) daily test failures at Google were from flaky tests.
- Takeaway: About three quarters of flakiness comes from missing synchronization, from races, and from state shared between tests. Replace sleeps with condition waits. Clean all shared state, including files and ports. Do not delete flaky tests: about a quarter of the fixes exposed real product bugs.
- Read: full text.

### A2. Eck, Palomba, Castelluccio, Bacchelli. *Understanding Flaky Tests: The Developer's Perspective.* ESEC/FSE 2019. doi:10.1145/3338906.3338945
- URL fetched: https://arxiv.org/pdf/1907.01466
- Summary: 21 Mozilla developers classified 200 flaky tests they had fixed themselves (N = 234 labels, because a test could get more than one). The authors also surveyed 121 developers. Four causes that Luo et al. did not have were found, and these were among the most expensive to fix.
- Quantitative:
  - Frequencies:
    - Concurrency 61 (26%), fixing effort 4.0
    - Async Wait 52 (22%), with 86% fixed by adding a `waitFor`/`await`
    - Too-Restrictive Range (new) 40
    - Test Order Dependency 22
    - Test Case Timeout (new) 18
  - 79% of respondents consider flaky tests a moderate or serious problem.
  - 40% deal with flaky tests at least weekly.
  - Fixes included "split up all tests (run in parallel) into more groups to reduce risk of a timeout."
- Takeaway: Assertions that are too tight, such as exact timing or exact floating-point values, and timeouts sized to a fast machine are big flake sources in their own right. Reproducing the flaky behavior is the hardest part.
- Read: full text.

### A3. Parry, Kapfhammer, Hilton, McMinn. *A Survey of Flaky Tests.* ACM TOSEM 31(1):17, 2021/22. doi:10.1145/3476105
- URL fetched: https://eprints.whiterose.ac.uk/id/eprint/230095/1/parry2021.pdf (accepted version)
- Summary: A systematic review of 76 papers, organized by causes, costs and consequences, detection, and mitigation and repair. It is the best entry point to the field.
- Quantitative (all cited from primary studies):
  - 59% of developers deal with flaky tests monthly, weekly, or daily.
  - 13% of failing Travis CI builds across 61 projects were caused by flaky tests (Labuschagne et al.).
  - 47% of builds from a sample of more than 75M were restarted after failing and then passed.
  - Google: 41% of test targets that had both passed and failed at least once were flaky (Memon et al.).
  - Microsoft: flaky failures appeared in 26% of sampled builds. A 0.02% flaky-failure rate over 80M executions would have caused 5.7% of all failed builds.
  - Order-dependent flaky tests appeared in 11 of 15 projects under at least one parallelization strategy.
  - Rerun policy: Google reruns failures up to 10 times; Microsoft's Flakes system reruns once by default.
  - About 88% of flaky tests fail up to 5 times in a row before a pass reveals them (Lam et al. burst-length study, 4,000 reruns of 26 modules).
- Takeaway: Rerun budgets are a real trade-off. Parallelizing a suite reliably exposes order dependence.
- Read: full text (sections on costs and detection).

### A4. Gruber, Lukasczyk, Kroiß, Fraser. *An Empirical Study of Flaky Tests in Python.* ICST 2021, pp. 148–158.
- URL fetched: https://arxiv.org/pdf/2101.09077
- Summary: 22,352 PyPI projects and 876,186 tests were each rerun many times, in the same order and in random orders.
- Quantitative:
  - 7,571 flaky tests found: 0.86% of tests, in 1,006 projects (4.5% of projects).
  - Causes:
    - 59% order dependency
    - 28% test-infrastructure problems (a cause not documented before)
    - 13% mostly network and randomness APIs
  - To be 95% confident that a passing test is not flaky takes 170 reruns on average.
- Takeaway: In Python, where pytest shares one process and module-level state, order dependence dominates. Randomize order by default, for example with `pytest-randomly`. A few reruns cannot certify that a test is not flaky.
- Read: full text.

### A5. Lam, Oei, Shi, Marinov, Xie. *iDFlakies: A Framework for Detecting and Partially Classifying Flaky Tests.* ICST 2019, pp. 312–322.
- URL fetched: https://taoxie.cs.illinois.edu/publications/icst19-idflakies.pdf
- Summary: A Maven tool that reruns test suites in the original order and in shuffled orders. It classifies each flaky test as order-dependent (OD) or not (NOD). It was applied to 683 projects.
- Quantitative:
  - 422 flaky tests found: 50.5% OD and 49.5% NOD.
  - In some projects, the probability that a test-suite run has at least one flaky failure was as high as 50%.
- Takeaway: About half of the flaky tests in Java unit suites are order-dependent. These are *deterministic* given the order, so shuffling the order is a cheap way to find them.
- Read: full text (abstract and results).
- Note: an automated summary of this PDF gave "597 tests / 11 projects". That was wrong. The numbers above come from my own text extraction.

### A6. Zhang, Jalali, Wuttke, Muşlu, Lam, Ernst, Notkin. *Empirically Revisiting the Test Independence Assumption.* ISSTA 2014. doi:10.1145/2610384.2610404
- URL fetched: https://dada.cs.washington.edu/research/tr/2014/01/UW-CSE-14-01-01.PDF (tech report version)
- Summary: A study of 96 real dependent tests from 5 issue trackers. It proves that detecting dependent tests is NP-complete even in a useful special case. It presents DTDetector (randomized, exhaustive-bounded, and dependence-aware algorithms). Dependent tests changed the output of all 5 test-prioritization techniques tested.
- Quantitative:
  - At least 82% of the dependent tests can be manifested with 2 or fewer tests.
  - 61% come from shared static variables, 4% from the file system, 10% from databases (the rest unknown).
  - Developers fixed only 40% of them. 51% were "fixed" by adding a comment documenting the dependence.
  - A bug in Apache CLI was hidden by two dependent tests for 3 years.
  - DTDetector found 27 previously unknown dependent tests.
- Takeaway: Most order dependence involves just a pair of tests: one that pollutes state and one that suffers from it. Checking pairs, or running each test alone, catches most of it. Mutable static or global state is the main cause.
- Read: full text (study section).

### A7. Shi, Lam, Oei, Xie, Marinov. *iFixFlakies: A Framework for Automatically Fixing Order-Dependent Flaky Tests.* ESEC/FSE 2019.
- URL fetched: https://taoxie.cs.illinois.edu/publications/esecfse19-ifixflakies.pdf
- Summary: Defines the vocabulary for order dependence:
  - **victim**: passes alone, fails after a *polluter*
  - **brittle**: fails alone, passes after a *state-setter*
  - **cleaner**: a test that resets polluted state
  
  iFixFlakies searches the existing suite for "helper" tests and turns their code into patches.
- Quantitative: 110 truly OD tests split into 100 victims and 10 brittles. 58 had helpers, and iFixFlakies fixed all 58. PRs were opened for 56 of them, and 21 were accepted at the time of writing.
- Takeaway: The code needed to fix an order-dependent test often already exists elsewhere in the suite. The durable fix is to move that reset logic into shared `setUp`/`tearDown` code or fixtures.
- Read: full text (abstract and definitions).

### A8. Bell, Legunsen, Hilton, Eloussi, Yung, Marinov. *DeFlaker: Automatically Detecting Flaky Tests.* ICSE 2018.
- URL fetched: https://www.cs.cornell.edu/~legunsen/pubs/BellETAL18DeFlaker.pdf
- Summary: Detects flaky failures without rerunning. If a newly failing test did not execute any changed code, DeFlaker marks the failure as flaky. It tracks coverage of the diff only, which keeps overhead low.
- Quantitative:
  - Deployed live on 96 Java projects on Travis CI, where it found 87 previously unknown flaky tests in 10 of them.
  - On project histories: 1,874 flaky tests identified from 4,846 failures, with a 1.5% false-alarm rate.
  - Recall of 95.5%, versus 23% for Maven's rerun-based detector.
  - Cites Microsoft Windows/Dynamics estimates of about 5% flaky failures, and Pivotal's estimate that half of its build failures involve flaky tests.
- Takeaway: "Failed without touching the change" is a strong, cheap signal. It is useful for gating CI and for triage by an agent.
- Read: full text (abstract and introduction).

### A9. Alshammari, Morris, Hilton, Bell. *FlakeFlagger: Predicting Flakiness Without Rerunning Tests.* ICSE 2021.
- URL fetched: https://www.jonbell.net/preprint/icse21-flakeflagger.pdf
- Summary: Each of 24 projects' test suites was rerun 10,000 times. Even then, some previously known flaky tests never flaked. FlakeFlagger predicts flakiness from behavioral features of each test, such as coverage, execution time, and use of I/O.
- Quantitative: Matched the prior classifier's true positives with far fewer false positives. Better F1 on 16 of 23 projects and tied on 4.
- Takeaway: Detection by rerunning never finishes. Use a prediction to pick which tests get the expensive detection runs.
- Read: full text (abstract).

### A10. Pinto, Miranda, Dissanayake, d'Amorim, Treude, Bertolino. *What is the Vocabulary of Flaky Tests?* MSR 2020. doi:10.1145/3379597.3387482
- URL fetched: https://damorim.github.io/publications/pintoETALmsr2020.pdf
- Summary: 64k tests were each run 100 times (6.4M executions). Classifiers were then trained on the identifiers in the test code.
- Quantitative: F-measure 0.95 with Random Forest or SVM. The tokens most associated with flakiness were `job`, `action`, `services`, and `table`.
- Takeaway: Tests that touch jobs, queues, services, or time budgets are likely suspects. Later work found poor generalization across projects (see C6).
- Read: full text (abstract).

### A11. Lam, Godefroid, Nath, Santhiar, Thummalapenta. *Root Causing Flaky Tests in a Large-Scale Industrial Setting.* ISSTA 2019, pp. 101–111. doi:10.1145/3293882.3330570
- URL fetched: https://mir.cs.illinois.edu/winglam/publications/2019/LamETAL19RootFinder.pdf
- Summary: A study of flakiness at Microsoft (CloudBuild), plus RootFinder. RootFinder instruments the code and diffs the logs of passing and failing runs to find the cause.
- Quantitative:
  - 4.6% of individual tests were flaky over one month in 5 projects.
  - Builds with at least one flaky failure, per project: 14%, 52%, 30%, 17%, 24%.
  - When flaky tests were rerun 100 times locally, 86% were flaky only in the CI pipeline.
  - 58 Microsoft developers rated flaky tests the #2 of 10 reasons deployments slow down.
  - Quotes Micco: 1.5% of Google test runs are flaky; almost 16% of 4.2M tests; roughly 2–16% of the testing budget goes to rerunning flaky tests.
- Takeaway: A small number of distinct flaky tests can still fail a large share of builds. Most flakes do not reproduce on a laptop, so collect evidence in CI (logs, seeds, timing).
- Read: full text (introduction and study).

### A12. Lam, Muşlu, Sajnani, Thummalapenta. *A Study on the Lifecycle of Flaky Tests.* ICSE 2020, pp. 1471–1482. doi:10.1145/3377811.3381749
- URL fetched: https://mir.cs.illinois.edu/winglam/publications/2020/LamETAL20FaTB.pdf
- Summary: Follows flaky tests in 6 large proprietary Microsoft projects: how often they recur, their runtimes, and time-to-fix. Async Wait is the leading cause. Proposes FaTB, which tunes wait and timeout values to balance flakiness against runtime.
- Quantitative:
  - FaTB cut test runtimes by up to 78% without a measurable change in how often the tests flaked.
  - Flaky-failure reproducibility was only 17–43% per project.
  - Builds affected ranged from 0.4% to 35.7% across projects.
  - *No* Test Order Dependency flakes were found. The authors attribute this to CloudBuild always running tests in the same order.
  - Several developer "fixes" did not actually reduce the failure rate.
- Takeaway: A fixed order *hides* order dependence rather than removing it. The dependence comes back the moment you parallelize, shard, or select tests. After a "fix", verify it with repeated runs.
- Read: full text.

### A13. Lam, Winter, Wei, Xie, Marinov, Bell. *A Large-Scale Longitudinal Study of Flaky Tests.* OOPSLA 2020, PACMPL 4:202. doi:10.1145/3428270
- URL fetched: https://mir.cs.illinois.edu/winglam/publications/2020/LamETAL20OOPSLA.pdf
- Summary: Two detectors were applied over the history of 55 Java projects to find out *when* tests become flaky.
- Quantitative: 245 flaky tests. 75% (184) were flaky when added. Running detectors on new *or modified* tests catches 85%. The other 15% become flaky because of other changes.
- Takeaway: Gate new and modified tests with N repeated runs at PR time. That is where most flakiness comes in. Periodically sweep the whole suite for the rest.
- Read: full text (abstract).

### A14. Lam, Winter, Astorga, Stodden, Marinov. *Understanding Reproducibility and Characteristics of Flaky Tests Through Test Reruns in Java Projects.* ISSRE 2020, pp. 403–413.
- URL fetched: https://mir.cs.illinois.edu/winglam/publications/2020/LamETAL20ISSRE.pdf
- Summary: 26 modules were rerun 4,000 times with Surefire configured as the developers had it. 107 flaky tests were found. Many tests previously labeled non-order-dependent actually fail at very different rates under different orders.
- Quantitative: see A3 for the burst-length result (about 88% of flaky tests fail up to 5 times in a row before passing).
- Takeaway: The OD/NOD split is fuzzy. Order also changes the failure *rate* of timing-dependent tests.
- Read: full text (abstract).

### A15. Wei, Yi, Xie, Marinov, Lam. *Probabilistic and Systematic Coverage of Consecutive Test-Method Pairs for Detecting Order-Dependent Flaky Tests.* TACAS 2021.
- URL fetched: https://pmc.ncbi.nlm.nih.gov/articles/PMC7979169/
- Summary: The first probability analysis of how well random orders detect OD tests. It builds on the fact that most OD tests depend on only one other test. It gives an improved way to sample random orders, and an algorithm that covers all consecutive test pairs with far fewer runs than trying every pair.
- Takeaway: A few random orders catch most OD tests, and covering all consecutive pairs gives a guarantee.
- Read: abstract only.

### A16. Wei, Yi, Li, Xie, Marinov, Lam. *Preempting Flaky Tests via Non-Idempotent-Outcome Tests.* ICSE 2022. doi:10.1145/3510003.3510170
- URL fetched: https://mir.cs.illinois.edu/marinov/publications/WeiETAL22NIO.pdf
- Summary: A non-idempotent-outcome (NIO) test passes on its first run and fails when run a second time in the same process, because it pollutes its own state.
- Quantitative: 223 NIO Java tests and 138 NIO Python tests found. PRs fixing 268 of them were opened: 192 accepted and 6 rejected.
- Takeaway: "Run every test twice in the same process" is a cheap check that catches state leaks. Those same leaks break watch mode, retries, and parallel workers that reuse processes.
- Read: full text (abstract).

### A17. Lam, Shi, Oei, Zhang, Ernst, Xie. *Dependent-Test-Aware Regression Testing Techniques.* ISSTA 2020, pp. 298–311. doi:10.1145/3395363.3397364
- URL fetched: https://taoxie.cs.illinois.edu/publications/issta20-dependtest.pdf
- Summary: Measured how OD tests affect test prioritization (4 algorithms), test selection (6), and parallelization (2) on 11 modules. The authors then made 12 algorithms respect declared test dependencies.
- Quantitative:
  - With unmodified algorithms, 82% of human-written suites and 100% of generated suites that contain OD tests had at least one flaky failure.
  - The dependence-aware versions had 80% fewer OD flaky failures and ran only 1% slower.
- Takeaway: Test selection and sharding for speed *will* surface hidden order dependence. Either remove the dependence or declare it explicitly.
- Read: full text (abstract).

### A18. Bell, Kaiser. *Unit Test Virtualization with VMVM.* ICSE 2014 (ACM SIGSOFT Distinguished Paper). doi:10.1145/2568225.2568248
- URL fetched: https://jonbell.net/publications/vmvm (serves the PDF)
- Summary: A study of about 1,200 Java projects found that most large ones run each test in its own process to isolate side effects. VMVM instead resets only the static state that can leak, inside one JVM, using bytecode instrumentation.
- Quantitative:
  - Setting up a new process per test added up to 4,153% (mean 618%) to total testing time.
  - VMVM cut test-suite time by up to 97% (mean 62%) on 20 applications with no loss of fault-finding ability.
  - That is 4 times the reduction from test-suite minimization.
- Takeaway: A process per test is safe but costly. The best option is isolation that resets exactly the leaking state. In JS, Python, and other languages the equivalent is "reset module-level state or globals between tests" rather than forking.
- Read: full text (abstract and introduction).

### A19. Gruber, Fraser. *A Survey on How Test Flakiness Affects Developers and What Support They Need to Address It.* ICST 2022.
- URL fetched: https://arxiv.org/pdf/2203.00483
- Summary: A survey of 335 professional developers and testers. They care less about the compute wasted on reruns than about the **loss of trust** in test results. They want IDE plugins and dashboards showing test outcomes over time.
- Quantitative (background, cited): 0.5% to 1% of tests are flaky in scientific studies. At Google, 16% of tests show some flakiness, 84% of pass→fail transitions involve a flaky test, and 41% of 115,160 test targets are flaky.
- Takeaway: The main cost is trust. A distrusted suite is ignored, and an ignored suite gives no feedback at all.
- Read: full text (abstract and background).

### A20. Parry, Kapfhammer, Hilton, McMinn. *Surveying the Developer Experience of Flaky Tests.* ICSE-SEIP 2022, pp. 253–262. doi:10.1145/3510457.3513037
- URL fetched: https://eprints.whiterose.ac.uk/id/eprint/230090/ and https://eprints.whiterose.ac.uk/id/eprint/230090/1/parry2022a.pdf
- Summary: 170 survey responses and 38 StackOverflow threads.
- Quantitative: 93.5% agreed with the proposed definition of a flaky test.
- Findings:
  1. Developers strongly agree that flaky tests hinder CI.
  2. Developers who see flakes more often may be more likely to **ignore real failures**.
  3. Developers rate setup and teardown problems as the most common cause.
  
  One participant said 90% of their flakes were date or timezone logic.
- Takeaway: Put effort into fixture hygiene first. Frequent flakes teach people, and agents, to ignore red builds.
- Read: full text (abstract and parts).

### A21. Barbosa, Ferreira, Pinto, d'Amorim, Miranda. *Test Flakiness Across Programming Languages.* IEEE TSE 49(4):2039–2052, 2023.
- URL fetched: https://portal.cin.ufpe.br/2023/10/02/test-flakiness-across-programming-languages/
- Summary: Flaky-test issues in C, Go, Java, JS, and Python, studied for concentration, similarity, and cost.
- Quantitative:
  - 5 of 13 root causes explain 78.07% of issues.
  - 10 of 23 fix strategies cover 85.20%.
  - Issues are resolved either early (under 10 days) or late (over 100 days).
  - Improper resource release is more common in C.
- Takeaway: A short checklist covers most flakiness in any language.
- Read: abstract only (university summary page).

### A22. (Hashemi, Tahir, Rasheed, per my recollection; author list not verified) *An Empirical Study of Flaky Tests in JavaScript.* arXiv 2207.01047, 2022 (venue not verified).
- URL fetched: https://arxiv.org/abs/2207.01047
- Summary: 452 flaky-test-fixing commits from popular JS projects. Concurrency is the dominant cause: async wait, races, deadlocks. OS-specific behavior and network stability follow.
- Quantitative: more than 80% of flaky tests were fixed. Others were skipped, quarantined, or removed.
- Takeaway: In JS (single-threaded but async), un-awaited promises and timers are the main hazard.
- Read: abstract only.

### A23. Romano, Song, Grandhi, Yang, Wang. *An Empirical Analysis of UI-based Flaky Tests.* ICSE 2021 (arXiv 2103.02669).
- URL fetched: https://arxiv.org/abs/2103.02669
- Summary: 235 flaky UI tests from 62 web and Android projects. Covers root causes, how the flakiness was manifested, and fixes. UI tests are too expensive for rerun-based detection.
- Read: abstract only.

### A24. Silva, Gruber, Gokhale, Arteca, Turcotte, d'Amorim, Lam, Winter, Bell. *The Effects of Computational Resources on Flaky Tests.* arXiv 2310.12132 (2023; later published, venue not verified).
- URL fetched: https://arxiv.org/abs/2310.12132
- Summary: 52 Java, JS, and Python projects run under 27 CPU and memory configurations.
- Quantitative: **46.5%** of flaky tests are Resource-Affected Flaky Tests (RAFT). Starving tests of resources is a cheap way to expose flakiness.
- Takeaway: Parallel workers compete for CPU. Tests with timing assumptions will flake more as parallelism rises. To shake these tests out on purpose, run them with `--maxWorkers` at 2× the core count or with CPU limits (cgroup quotas).
- Read: abstract only.

### A25. Gruber, Roslan, Parry, Scharnböck, McMinn, Fraser. *Do Automatic Test Generation Tools Generate Flaky Tests?* ICSE 2024.
- URL fetched: https://arxiv.org/abs/2310.05223
- Summary: Tests were generated with EvoSuite and Pynguin for 6,356 projects, and each was run 200 times.
- Quantitative: Generated tests are flaky at least as often as developer-written ones. EvoSuite's flakiness suppression reduces flaky tests by 71.7%. The main cause is randomness, not networking or concurrency.
- Takeaway: This is directly relevant to AI-generated tests. Machine-written tests need determinism controls (seeded RNG, mocked clock), and new tests need repeated runs before they are accepted.
- Read: abstract only.

### A26. Rasheed, Tahir, Dietrich, Hashemi, Zhang. *Test Flakiness' Causes, Detection, Impact and Responses: A Multivocal Review.* JSS 206, 2023. doi:10.1016/j.jss.2023.111837
- URL fetched: https://arxiv.org/abs/2212.00908
- Summary: 651 articles: 560 academic and 91 grey literature. Organized by causes, detection, impact, and responses.
- Read: abstract only.

### A27. Habchi, Haben, Papadakis, Cordy, Le Traon. *A Qualitative Study on the Sources, Impacts, and Mitigation Strategies of Flaky Tests.* ICST 2022 (arXiv 2112.04919).
- URL fetched: https://arxiv.org/abs/2112.04919
- Summary: Interviews with 14 practitioners. Flakiness comes from interactions between system components, test infrastructure, and external factors, not only from test code. Guidelines plus stable infrastructure are the key mitigations.
- Read: abstract only.

### A28. Parry et al. (author list not verified in fetch) *Systemic Flakiness: An Empirical Analysis of Co-Occurring Flaky Test Failures.* arXiv 2504.16777, 2025.
- URL fetched: https://arxiv.org/abs/2504.16777
- Summary: Uses the FlakeFlagger dataset: 10,000 runs of 24 Java projects with 810 flaky tests.
- Quantitative: **75%** of flaky tests belong to a cluster of tests that fail together, with a mean cluster size of 13.5. The main causes are intermittent networking and unstable external dependencies. Cites an industrial case where developers spent 1.28% of their time repairing flaky tests, at $2,250 per month.
- Takeaway: Group flaky failures by the tests they co-fail with and by stack trace. One fix, such as a hermetic network fake, can remove a dozen flakes at once.
- Read: abstract only.

### A29. Alshammari, Ammann, Hilton, Bell. *230,439 Test Failures Later: An Empirical Evaluation of Flaky Failure Classifiers.* arXiv 2401.15788, 2024.
- URL fetched: https://arxiv.org/abs/2401.15788
- Summary: 230,439 failure messages from 498 flaky tests in 22 Java projects. Tests whether matching a new failure message to earlier flaky or genuine failures can tell them apart. Specificity ranges from 100% in some projects to useless in others.
- Takeaway: Using the failure message as a fingerprint for triage works only for some projects. Measure it before trusting it.
- Read: abstract only.

---

## Part B: Industry reports

### B1. John Micco (Google). *Flaky Tests at Google and How We Mitigate Them.* Google Testing Blog, 2016-05-27.
- URL fetched: https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html
- Content: In what the fetcher rendered, the post body was missing and only the comments came through. The comments mention rerunning only tests marked flaky or when a user asks, and "Reservoir", which runs new tests in a loop for a week before they join CI.
- Numbers: The widely quoted figures come from Micco's keynote (B2). "~1.5% of runs flaky; ~16% of tests some flakiness" appears there and is quoted by A11 and A12. I could not confirm the exact wording of the post body.
- Read: partial (comments only).

### B2. John Micco. *The State of Continuous Integration Testing @Google.* ICST 2017 keynote slides.
- URL fetched: http://aster.or.jp/conference/icst2017/program/jmicco-keynote.pdf
- Quantitative:
  - "Almost 16% of our 4.2M tests have some level of flakiness."
  - "84% of transitions from Pass -> Fail are from 'flaky' tests."
  - Only 1.23% of tests ever found a breakage.
  - Continual rate of 1.5% of test executions reporting a flaky result.
  - 2–16% of compute resources spent re-running flaky tests.
  - Google reruns failure transitions 10 times to verify flakiness and keeps a database and UI of known flaky tests.
  - "Testing systems must be able to deal with a certain level of flakiness."
- Takeaway: Most red signals at scale are noise. Infrastructure has to separate flakes from real breakages automatically.
- Read: full text (slides).

### B3. Jeff Listfield (Google). *Where do our flaky tests come from?* Google Testing Blog, 2017-04-17.
- URL fetched: https://testing.googleblog.com/2017/04/where-do-our-flaky-tests-come-from.html
- Summary: Across about 4.2M tests, flakiness rises with test size (binary size and RAM). Tests on the Android emulator and with WebDriver are more flaky. However, size explains more than the choice of tool.
- Quantitative: About 1/6 of tests that were stable and *became* flaky after a code change turned out to be real production bugs.
- Takeaway: Keep tests small and hermetic. "A flake and a bug are different manifestations of the same problem."
- Read: full text (via fetch summary).

### B4. Memon, Gao, Nguyen, Dhanda, Nickell, Siemborski, Micco. *Taming Google-Scale Continuous Testing.* ICSE-SEIP 2017, pp. 233–242.
- URL fetched: https://huang.isis.vanderbilt.edu/cs8395/paper/google-testing-icse-seip-17.pdf
- Quantitative: Of 115,160 test targets that had previously both passed and failed, 46,694 (41%) were flaky. The heuristic "rerun tests that failed recently" was rejected because it would mostly rerun flaky tests.
- Takeaway: Flakiness pollutes history-based test selection and prioritization.
- Read: full text (relevant sections).

### B5. Ziftci, Cavalcanti (Google). *De-Flake Your Tests: Automatically Locating Root Causes of Flaky Tests in Code at Google.* ICSME 2020, pp. 736–745.
- URL fetched: https://research.google/pubs/de-flake-your-tests-automatically-locating-root-causes-of-flaky-tests-in-code-at-google/
- Summary: Locates root causes in code by comparing executions, across 428 Google projects.
- Quantitative: 82% accuracy in locating the root cause.
- Takeaway: Adoption depends on fitting into the developer's workflow and on fixes being fully automated.
- Read: abstract only.

### B6. Herzig, Nagappan (Microsoft). *Empirically Detecting False Test Alarms Using Association Rules.* ICSE-SEIP 2015, pp. 39–48.
- URL fetched: https://www.microsoft.com/en-us/research/wp-content/uploads/2015/05/Empirically-Detecting-False-Test-Alarms-Using-Association-Rules.pdf
- Quantitative: On Windows 8.1 and Dynamics AX system and integration tests, precision was 0.85–0.90 and the model caught 34–48% of all false alarms. DeFlaker (A8) cites Microsoft's estimate of about 5% flaky failures from this work.
- Read: full text (abstract).

### B7. Arpita Patel (Slack). *Handling Flaky Tests at Scale: Auto Detection & Suppression.* Slack Engineering, 2022-04-05.
- URL fetched: https://slack.engineering/handling-flaky-tests-at-scale-auto-detection-suppression/
- Summary: Project Cornflake covers mobile: 16k+ Android tests, 11k+ iOS tests, and 550+ PRs per week from 120+ developers.
- How it works: flakiness is computed over the last N runs (N=50 proposed). When a test crosses a threshold, the system automatically files a Jira ticket for the owner, opens a PR that disables the test (`@Ignore` on Android, a `disabled_` prefix on iOS), and posts a Slack alert.
- Lesson from V1: suppressing *results* instead of *execution* let broken tests leak onto main.
- Quantitative:
  - Test-job failures fell from 56.76% to 3.85%.
  - Main-branch pass rate rose from 19.82% to 96%.
  - 553 hours of triage saved, at 28 minutes per failure.
- Read: full text.

### B8. Jason Palmer (Spotify). *Test Flakiness – Methods for Identifying and Dealing with Flaky Tests.* Spotify Engineering, 2019-11-18.
- URL fetched: https://engineering.atspotify.com/2019/11/test-flakiness-methods-for-identifying-and-dealing-with-flaky-tests
- Summary: Three tools:
  - Odeneye visualizes failures: scattered dots mean flakiness, solid columns mean an infrastructure problem.
  - A table of each test's flakiness.
  - Flakybot runs a PR's tests repeatedly before merge.
- Quantitative: Making flakiness visible alone cut the flaky rate from 6% to 4% in two months.
- Practices: poll on a condition instead of hard-coded waits, fully reset state, minimize global state, and use few end-to-end tests.
- Read: full text.

### B9. Jordan Raine (GitHub). *Reducing Flaky Builds by 18x.* GitHub Blog, 2020-12-16 (updated 2021-12-20).
- URL fetched: https://github.blog/engineering/engineering-principles/reducing-flaky-builds-by-18x/
- Summary: Failed tests get three kinds of retry:
  1. Same process (same Ruby VM, database, and host), which catches randomness and races.
  2. In simulated **future time**, which catches assumptions about the date or time.
  3. On a **different host**, which catches order dependence and shared state.
  
  If an "impact score" crosses a threshold, an issue is auto-assigned to whoever last touched the test or code, with a git-blame link.
- Quantitative:
  - Flaky red builds fell from 1 in 11 commits (9%) to 1 in 200 (<0.5%).
  - 90% of flaky failures are now identified automatically, up from 25%.
  - Only 0.4% of flaky tests failed 100 or more times, and most failed fewer than 10 times.
- Takeaway: Design retries as experiments that diagnose the cause (same process, shifted time, different host), not blind reruns.
- Read: full text.

### B10. Nitish Malik (Atlassian). *Taming Test Flakiness: How We Built a Scalable Tool to Detect and Manage Flaky Tests (Flakinator).* Atlassian Engineering, 2025-12-08.
- URL fetched: https://www.atlassian.com/blog/atlassian-engineering/taming-test-flakiness-how-we-built-a-scalable-tool-to-detect-and-manage-flaky-tests
- Summary: Two detection methods:
  - Implicit retries within the same build.
  - A Bayesian flakiness score (0–1) over a moving window, using duration variability, environment consistency, result patterns, and retry frequency.
  
  Detected tests are quarantined, a Jira ticket with a deadline is filed, and the owning team gets a Slack notification. A test is reintroduced after staying healthy for a configured period.
- Quantitative:
  - Flaky tests caused 21% of master build failures in Jira Frontend and 15% in the Jira backend.
  - 350M+ test executions per day.
  - 22,000 builds recovered in one quarter.
  - 7,000 unique flaky tests identified.
  - An estimated 150,000+ developer hours per year lost to reruns (company estimate).
- Read: full text.

### B11. Tan, Balabanov, Lin (Uber). *Flaky Tests Overhaul at Uber.* Uber Blog, 2024-06-04.
- URL fetched: https://www.uber.com/en-US/blog/flaky-tests-overhaul/
- Summary: Testopedia is a per-test state machine: New → Stable ↔ Unstable → Disabled → Deleted, with enter/exit actions such as filing or closing Jira tickets. A single failure in the lookback window marks a test Unstable. It must pass N times in a row to return to Stable.
- Policies: critical tests always run. Engineers can opt flaky tests back in with diff annotations. Flaky and integration tests run in non-blocking mode.
- Quantitative: About 1,000 flaky tests out of 600K in the Go monorepo, and about 1K out of 350K in Java. 2,500+ diffs per day with 10,000+ tests each.
- Read: full text.

### B12. Utsav Shah (Dropbox). *Athena: Our Automated Build Health Management System.* Dropbox Tech, 2019-05-22.
- URL fetched: https://dropbox.tech/infrastructure/athena-our-automated-build-health-management-system
- Summary: About 35,000 builds per day. Failing tests are rerun up to 10 times, and inconsistent results mean the test is flaky. Environmental failures are rerun on the last known-green commit. Noisy tests are automatically quarantined from pre-submit until fixed. Commits are not auto-reverted; owners are notified instead.
- Quantitative: Quarantines doubled and the test cluster shrank by about 8%.
- Lessons: keep notifications high-signal. Automation settles arguments about the quality bar, much as code formatters do.
- Read: full text.

---

## Part C: LLM and ML-based flaky test detection and repair

### C1. Fatima, Ghaleb, Briand. *Flakify: A Black-Box, Language Model-Based Predictor for Flaky Tests.* IEEE TSE 49(4):1912–1927, 2023.
- URL fetched: https://arxiv.org/abs/2112.12331
- Summary: CodeBERT fine-tuned on test source code only, with no access to production code and no reruns.
- Quantitative: On the FlakeFlagger dataset, precision was 10 percentage points higher and recall 18 points higher than FlakeFlagger. It also generalized better to new projects.
- Read: abstract only.

### C2. Fatima, Hemmati, Briand. *FlakyFix: Using Large Language Models for Predicting Flaky Test Fix Categories and Test Code Repair.* IEEE TSE 50(12):3146–3171, 2024.
- URL fetched: https://arxiv.org/abs/2307.00012
- Summary: Predicts which of 13 fix categories applies, for flakiness rooted in the test code. The predicted category is added to GPT-3.5-Turbo's prompt as a hint.
- Quantitative: An estimated 51–83% of the repairs pass. The failing ones needed about 16% more of the test code changed.
- Read: abstract only.

### C3. Lin, Liu, Tahvildari. *FlaKat: A Machine Learning-Based Categorization Framework for Flaky Tests.* arXiv 2403.01003, 2024.
- URL fetched: https://arxiv.org/abs/2403.01003
- Summary: Classifies the root-cause category of flaky tests in IDoFT, using sampling to handle class imbalance. Proposes the Flakiness Detection Capacity metric.
- Read: abstract only.

### C4. Chen, Jabbarvand. *Neurosymbolic Repair of Test Flakiness (FlakyDoctor).* ISSTA 2024. doi:10.1145/3650212.3680369
- URL fetched: https://arxiv.org/abs/2404.09398
- Summary: Combines an LLM with program analysis.
- Quantitative:
  - 873 flaky tests (332 OD and 541 implementation-dependent) from 243 projects.
  - 57% of OD and 59% of ID tests repaired.
  - Beats iFixFlakies by 17% on OD tests and DexFix by 8% on ID tests.
  - The non-LLM components contribute 12–31%, so an LLM alone was not enough.
  - 79 previously unfixed tests repaired; 19 PRs merged.
- Read: abstract only.

### C5. Li, Behrang, Shi, Liu. *FlakyGuard: Automatically Fixing Flaky Tests at Industry Scale.* arXiv 2511.14002 (listed as "to appear in ASE 2025").
- URL fetched: https://arxiv.org/abs/2511.14002
- Summary: Treats code as a graph and explores it selectively to give the LLM just the right context.
- Quantitative: Repairs 47.6% of reproducible industrial flaky tests. Developers accepted 51.8% of the fixes. At least 22% better than prior approaches.
- Read: abstract only.

### C6. Berndt, Bekmyradov, Gemulla, Kessel, Bach, Baltes. *Can We Classify Flaky Tests Using Only Test Code? An LLM-Based Empirical Study.* SANER-RENE 2025 (arXiv 2602.05465).
- URL fetched: https://arxiv.org/abs/2602.05465
- Summary: A **negative result**. Three LLMs with three prompting styles on two benchmarks did only marginally better than random guessing. When the authors inspected 50 samples by hand, the test code often did not contain enough information to decide.
- Takeaway: Classifying flakiness from code alone does not generalize. Give LLMs runtime evidence: failure logs, rerun history, and co-failure clusters.
- Read: abstract only.

---

## Part D: Tool documentation (verified during this research)

| Ecosystem | Capability | Verified command / setting | Source URL |
|---|---|---|---|
| Jest | Shuffle tests in a file; reproduce with a seed | `jest --randomize --seed 1234` (`--showSeed`; requires jest-circus) | https://jestjs.io/docs/cli |
| Jest | Find leaked handles | `--detectOpenHandles`: implies `--runInBand` and has a significant performance cost, so use it for debugging only | https://jestjs.io/docs/cli |
| Jest | `--forceExit` smell | Docs call it an "escape-hatch": a hang means held resources or pending timers. Tear down after each test | https://jestjs.io/docs/cli |
| Jest | Fake timers | `jest.useFakeTimers()`, `advanceTimersByTime`, `runOnlyPendingTimers`, `setSystemTime`, `useRealTimers` | https://jestjs.io/docs/timer-mocks |
| Mocha | `--exit` smell | Forced exit stopped being the default in v4 because it hid tests that do not clean up. Docs suggest async_hooks, wtfnode, or `.only` to bisect | https://mochajs.org/running/cli/ |
| Mocha | Retries / CI | `--retries n` (off by default); `--forbid-only` defaults to true when `CI` is set (v12+) | https://mochajs.org/running/cli/ |
| Vitest | Isolation | `isolate` defaults to `true`. Turning it off can help performance "if your code doesn't rely on side effects" | https://vitest.dev/config/isolate |
| Vitest | Random order | `--sequence.shuffle`, `sequence.seed` (default `Date.now()`) | https://vitest.dev/config/sequence |
| Node test runner | Isolation / concurrency | `isolation: 'process'` (default, one child process per file); `--test-concurrency` | https://nodejs.org/api/test.html |
| Node test runner | Random order | `node --test --test-randomize`; replay with `--test-random-seed=<n>` (present in current docs; check your Node version) | https://nodejs.org/api/test.html |
| Node test runner | Mock timers | `mock.timers.enable({apis:['setTimeout']})`, `tick(ms)`, `setTime(ms)` | https://nodejs.org/api/test.html |
| pytest | Random order and seed reset | `pytest-randomly`: shuffles modules, then classes, then functions, and resets `random` (plus Faker, NumPy, and others) before each test. Flags: `-p no:randomly`, `--randomly-seed=<n>` or `last`, `--randomly-dont-reorganize`, `--randomly-dont-reset-seed` | https://github.com/pytest-dev/pytest-randomly |
| pytest | Reruns | `pytest --reruns 5 --reruns-delay 1`, `--only-rerun AssertionError`, `@pytest.mark.flaky(reruns=5)`. Not compatible with `--looponfail` or pytest-forked | https://github.com/pytest-dev/pytest-rerunfailures |
| pytest | Parallel | `pytest -n auto --dist loadfile` (also `loadscope`, `loadgroup`, `worksteal`) | https://pytest-xdist.readthedocs.io/en/stable/distribution.html |
| pytest | Guidance | The flaky-tests page lists system state, overly strict assertions, and threads as causes; `xfail(strict=False)` as manual quarantine; pytest-replay | https://docs.pytest.org/en/stable/explanation/flaky.html |
| RSpec | Random order | `--order rand` or `--seed 123` (same as `--order rand:123`); `config.order = :random` | https://rspec.info/features/3-13/rspec-core/command-line/order/ |
| Go | Shuffle / repeat / race | `go test -shuffle=on` (or `=N` to replay), `-count=N` (`-count=1` also disables the test cache), `-race` | https://pkg.go.dev/cmd/go/internal/test , https://pkg.go.dev/cmd/go#hdr-Testing_flags |
| Maven Surefire | Reruns and flake reporting | `mvn -Dsurefire.rerunFailingTestsCount=2 test` prints "Flakes: N" and records `<flakyFailure>` in the XML. `failOnFlakeCount` (3.0.0-M6+) fails the build if there are too many flakes | https://maven.apache.org/surefire/maven-surefire-plugin/examples/rerun-failing-tests.html |
| Gradle | Retries | test-retry plugin: `retry { maxRetries; maxFailures; failOnPassedAfterRetry }`. Build scans mark fail-then-pass as flaky | https://github.com/gradle/test-retry-gradle-plugin |
| Java | Nondeterministic-spec detector | NonDex: `mvn edu.illinois:nondex-maven-plugin:2.2.1:nondex`; Gradle `./gradlew nondexTest`. Shuffles results that the spec leaves unspecified, such as HashMap iteration order | https://github.com/TestingResearchIllinois/NonDex |
| Bazel | Flaky attempts / repeat runs | `flaky = True` means up to 3 attempts. `--flaky_test_attempts` (max 10; fail-then-pass reported as FLAKY). `--runs_per_test=N` (or `regex@N`). `--runs_per_test_detects_flakes` | https://bazel.build/reference/be/common-definitions , https://bazel.build/docs/user-manual |
| Playwright | Retries and flaky status | `npx playwright test --retries=3` labels each test passed / flaky / failed. The worker and browser are discarded after a failure | https://playwright.dev/docs/test-retries |

---

## (a) Consensus synthesis: top root causes and how common they are

These are the results that hold across studies, languages, and companies.

1. **Async Wait / timing is the top cause in Java and industry.**
   - Luo: 45% of classified fixes.
   - Eck (Mozilla): 22%, and Concurrency is 26%.
   - Microsoft's lifecycle study (Lam 2020): the leading cause across 6 proprietary projects.
   - JavaScript study: "concurrency-related (async wait, races)" is dominant.
   
   The usual bad pattern is a fixed `sleep`. Luo found that 34% of Async Wait tests enforce ordering with a time delay. Replacing it with a condition wait fixes most cases: 54% of Luo's fixes used `waitFor`, and 86% of Eck's Async Wait fixes added a `waitFor`/`await`.
2. **Concurrency (races and atomicity) is second**: 20% (Luo) to 26% (Eck). These tests almost always involve just two threads (Luo: "almost all"), with 97% on in-memory objects only.
3. **Order dependence / shared state varies a lot with the runner.**
   - Luo, Java commits: 12%.
   - iDFlakies, Java suites: 50.5% of detected flaky tests.
   - Gruber, Python: **59%**.
   - Microsoft CloudBuild: 0%, because tests always run in the same order. That hides the problem instead of fixing it.
   
   The root is mostly static or global state (61% in Zhang). Luo found that 47% involve external resources such as files, ports, or databases. At least 82% of cases involve only one other test, which makes pair checks effective.
4. **Infrastructure, resources, and environment.**
   - Test-infrastructure problems: 28% in Python (Gruber).
   - 46.5% of flaky tests are resource-affected (Silva et al.).
   - 86% of Microsoft's flaky tests were flaky only in CI (Lam 2019).
   - Flakiness grows with test size (Google 2017).
   - 75% of flaky tests fail in co-failure clusters, driven by network and external-dependency instability (systemic flakiness).
5. **Time, randomness, tight assertions, unordered collections, and floating point** each account for a small share on their own. Together they matter:
   - Eck's "too-restrictive range" (40 of 234 labels).
   - Randomness is the leading cause in *generated* tests (Gruber 2024).
   - A developer quote that 90% of their flakes were date/timezone logic (Parry 2022).
   - GitHub runs a dedicated "future time" retry.
   
**Prevalence at scale.**
- Google: 1.5% of executions and ~16% of 4.2M tests show some flakiness. 84% of pass→fail transitions are flaky. 2–16% of compute goes to reruns.
- Microsoft: 4.6% of tests are flaky, and 14–52% of builds per project are affected.
- Open source: about 0.5–1% of tests.
- Travis CI: 13% of failed builds.
- GitHub before its fix: 9% of commits.
- Slack before its fix: 57% of test-job failures.

**Lifecycle.** 75–78% of flaky tests are flaky from the moment they are written (Luo 78%, Lam OOPSLA 75%). Detecting at PR time for new and modified tests catches 85% (Lam OOPSLA).

**Detection is expensive.**
- 170 reruns are needed for 95% confidence (Gruber).
- 10,000 reruns still miss some flakes (FlakeFlagger).
- About 88% of flaky tests fail up to 5 times in a row before a pass reveals them (Lam, via Parry).

**Flakes hide bugs.**
- 24% of Luo's fixes touched the code under test, and 94% of those fixed a real bug.
- About 1 in 6 newly flaky tests at Google were real bugs.
- Deleting or ignoring flaky tests throws that signal away.

**Trust is the main cost** (Gruber & Fraser; Parry 2022). Frequent flakes lead developers to ignore real failures. Inference, not directly measured: an AI agent has no memory of "this test is always flaky", so it is misled even more easily. Keep flake status machine-readable, for example in a quarantine list and in the JUnit `flakyFailure` element.

**LLMs.**
- LLMs *repair* known-cause flakiness moderately well: FlakyDoctor 57–59%, FlakyGuard 47.6% with 51.8% of fixes accepted, FlakyFix 51–83% of repairs expected to pass.
- LLMs do *not* reliably *classify* flakiness from test code alone: near random (Berndt 2025).
- The symbolic or runtime components matter (FlakyDoctor: 12–31% of performance).

## (b) Rules for writing tests that are safe to run in parallel and never flaky

These are derived from the evidence above. The source for each rule is in brackets.

1. **Never `sleep` to wait for something.** Wait on a condition: `waitFor`, `await` the promise, poll with a predicate and a deadline. Keep the timeout generous, because it is an upper bound and not the expected time. [Luo F.4/F.8; Eck; Spotify; FaTB]
2. **Await everything.** Do not leave floating promises, callbacks you never wait for, or background work outliving the test. Treat a hang at the end of the run as a bug: never add `--forceExit` or `--exit`. Use `--detectOpenHandles` or wtfnode to find the leak. [Jest docs; Mocha docs; JS study]
3. **Control time.** Inject a clock or use fake timers (`jest.useFakeTimers`, `mock.timers`, `setSystemTime`). Never assert on the real wall-clock date, the timezone, or midnight or DST boundaries without pinning them. Run the suite once with a shifted clock. [GitHub future-time retry; Parry 2022 "90% date/timezone"; Luo "Time"]
4. **Control randomness.** Seed every RNG from one logged seed and reset it before each test, as `pytest-randomly` does. Print the seed so any failure can be replayed. [Gruber 2024: randomness is the #1 cause in generated tests; pytest-randomly]
5. **No shared mutable global or static state between tests.** Build fresh fixtures in `beforeEach`/`setUp`. If a module singleton must exist, reset it in `afterEach`/`tearDown`. Singletons, caches, and registries are the typical polluters. [Zhang 61% static; Luo F.10 74% fixed by cleaning state; iFixFlakies]
6. **Every external resource is per-test or per-worker.**
   - A unique temporary directory for each test.
   - Port 0 (the OS picks a free port) instead of a fixed port.
   - A unique database schema or name, or a transaction rolled back after each test.
   - Unique queue and topic names.
   
   Include the worker ID in names, for example `JEST_WORKER_ID` or the xdist `worker_id`. [Luo F.7: 47% of order dependence is external resources; Eck "separate output directory" fix]
7. **Tests must pass alone, in any order, and twice in a row.** Enforce this with random order in CI (`--randomize`, `-shuffle=on`, `pytest-randomly`, `--order rand`), and periodically run each test twice in the same process (NIO check). [iDFlakies; Wei 2022; Lam 2020 ISSTA]
8. **Hermetic by default.** No real network calls in unit tests. Fake or stub external services. Keep true end-to-end tests few and non-blocking, or quarantined. [Systemic flakiness: network is the main cluster cause; Google 2017: size correlates with flakiness; Spotify "5 instead of 500"]
9. **Keep tests small.** Flakiness grows with binary size, memory, and the use of emulators or browsers. Push checks down to the lowest level that can catch the bug. [Google 2017; pytest docs "rewrite at lower levels"]
10. **Assertions should be tolerant where the domain is.** Use `approx` for floats. Sort before comparing collections whose order is not guaranteed, such as HashMap or Set iteration or directory listings (NonDex finds these). Never assert on exact durations. [Eck "too-restrictive range"; Luo "unordered collections", "floating point"; NonDex]
11. **Don't depend on how fast the machine is.** Base timeouts on a slow CI worker under load, not a laptop. Tests should pass with double the usual number of workers. [Silva RAFT 46.5%; Eck "Test Case Timeout"]
12. **Isolation granularity.** Use the cheapest isolation that actually resets the state that leaks. A process per file is the Jest and Node default, and a process per test is very costly (+618% on average). Turn isolation off, for example Vitest `isolate: false`, only after random-order and repeat checks pass. [VMVM; Vitest docs]
13. **Declare any dependence you truly need**, for example with a named group (xdist `loadgroup`), instead of relying on implicit order. Test selection, sharding, and prioritization will otherwise break it. [Lam ISSTA 2020: 82% of suites with OD tests broke]
14. **Every new or modified test gets a stress run before merge**: N repetitions, in random orders, under CPU pressure. This matters most for AI-generated tests. [Lam OOPSLA 75–85%; Luo 78%; Gruber 2024]

## (c) Detection and quarantine playbook

**Step 1: Stress new and changed tests at PR time.** This catches the 75–85% of flakes that are there from the start.
- JS (Jest): `jest --randomize --seed $RANDOM <changed files>`, repeated N times in a shell loop. Jest has no built-in repeat-count flag for this, so loop.
- JS (Vitest): `vitest run --sequence.shuffle` in a loop.
- Node test runner: `node --test --test-randomize`, then replay with `--test-random-seed=<n>`.
- Go: `go test -run 'TestNew' -count=50 -shuffle=on -race ./pkg/...`
- Python: `pytest -p randomly --count` requires `pytest-repeat`, which I did **not** verify in docs. A verified alternative is a loop of `pytest --randomly-seed=$i path::test`.
- Java/Maven: iDFlakies (https://github.com/UT-SE-Research/iDFlakies) for order-dependent tests; `mvn edu.illinois:nondex-maven-plugin:2.2.1:nondex -Dtest=NewTest` for implementation-dependent tests.
- Bazel: `bazel test //pkg:new_test --runs_per_test=50 --runs_per_test_detects_flakes`
- Resource starvation: run the same loops with more workers than cores, or under a CPU quota. This exposes resource-affected (RAFT) tests.

**Step 2: Random order in every CI run, with the seed printed.** Replay a failure with its seed, then bisect to the polluter/victim pair.
- `jest --randomize --showSeed`
- `rspec --order rand`
- `go test -shuffle=on`
- `pytest-randomly` (on by default once installed)
- `vitest --sequence.shuffle`

Pairwise or bisect tools: iDFlakies and iFixFlakies (Java); iPFlakies (Python, https://yangc9.github.io/files/WangETAL22iPFlakies.pdf; located only, not read).

**Step 3: Retries as diagnosis, and never silent.**
- Record a flaky outcome separately from a pass:
  - Surefire `rerunFailingTestsCount` writes `<flakyFailure>` in the XML and "Flakes: N" in the summary. Add `failOnFlakeCount`.
  - Gradle test-retry with `failOnPassedAfterRetry` on protected branches.
  - Playwright `--retries` gives a "flaky" status.
  - Bazel reports `FLAKY`.
  - pytest-rerunfailures `--reruns 2 --only-rerun <InfraError>`.
- Copy GitHub's three-way retry:
  1. Same process, for races and randomness.
  2. Shifted clock, for time assumptions.
  3. Different host or fresh process, for order and shared state.
- Cap the budget. Google reruns up to 10 times, Microsoft once, Dropbox up to 10. The costs are 2–16% of compute (Google) and developer attention.

**Step 4: Rerun-free triage signals.**
- DeFlaker-style: did the failing test cover the diff? If not, it is probably a flake.
- Match the failure message against known flaky signatures (useful only in some projects; A29).
- Co-failure clustering (systemic flakiness), to find one shared cause.

**Step 5: Quarantine automatically and hand the test to an owner.**
- Score each test over a window: Slack uses the last 50 runs, Atlassian a Bayesian score, Uber marks a test Unstable on one failure in the lookback window.
- Above the threshold, **disable execution on main**, not just the result (Slack's V1 lesson). Automatically file a ticket for the owner (Slack, Atlassian, Uber) or git-blame assignee (GitHub).
- Quarantine mechanisms:
  - Jest/Vitest: `test.skip` plus a ticket link.
  - pytest: `@pytest.mark.xfail(strict=False, reason=TICKET)`, the documented manual quarantine.
  - JUnit: `@Disabled` or `@Ignore`.
  - Go: `t.Skip`.
  - Bazel: `flaky = True` (up to 3 attempts), or a tag excluded from blocking runs.
  - RSpec: `skip`.
- Keep running quarantined tests off the critical path (Dropbox, Uber, Atlassian). Bring a test back only after N consecutive passes (Uber) or a healthy period (Atlassian).
- Never delete by default. About a quarter of fixes find real bugs (Luo), and about 1 in 6 newly flaky Google tests were real bugs.
- Critical tests are never quarantined (Uber).

**Step 6: Make it visible.** Show a per-test flake-rate table or timeline: Spotify's Odeneye, and the dashboards developers asked for in Gruber & Fraser's survey. Visibility alone moved Spotify from 6% to 4%.

**Step 7: For AI agents** (inference from the evidence above, not a measured result).
- Show the agent a machine-readable quarantine list and flake history.
- Run each failing test again in the same process before the agent acts on it.
- Tell the agent that a failure which did not cover the diff is probably a flake.
- When an LLM repairs flakiness, give it runtime evidence: seed, order, logs, co-failures (C4–C6).
- Before accepting an agent-written test, stress it (Step 1).

---

### Items located but not read, or with uncertain details
- The Google 2016 blog body did not render in the fetch. The numbers are taken from Micco's ICST 2017 keynote and from papers quoting him.
- Candido, Melo, d'Amorim, *Test suite parallelization in open-source projects*, ASE 2017. Located via search only. The "OD flaky in 11 of 15 projects under parallelization" figure is quoted from Parry's survey, reference [73]. I believe it refers to this or a related study, but did not verify.
- Labuschagne, Inozemtseva, Holmes, FSE 2017. Located; the 13% figure is quoted second-hand from DeFlaker, iFixFlakies, and Parry.
- The JS study's authors and the systemic-flakiness paper's authors were not captured in the fetch; see notes on A22 and A28.
- `pytest-repeat`'s `--count` flag was not verified.
- Wing Lam's ISSRE 2020 burst-length numbers come via Parry's survey.
