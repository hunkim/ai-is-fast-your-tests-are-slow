# Regression Test Selection (RTS) and Test Impact Analysis

*Part of "In the AI coding era, the bottleneck is testing". Research compiled 2026-09-29.*

**Question:** When code changes, which tests can that change actually affect, and how much time do you save by running only those?

**How to read this file**

- Every work below was found and opened during this research. "Read: full text" means I downloaded the PDF and read the abstract, introduction, results and conclusions. It does not mean I read every page. "Read: abstract only" means I checked the abstract or the publisher/official page and nothing more.
- All numbers are copied from the source. Anything I could not check directly is marked **(unverified)**.
- Terms used throughout:
  - **Safe:** the technique never skips a test whose result could change.
  - **Precise:** the technique does not select tests that cannot be affected.
  - **RetestAll:** run the full suite.
  - **A / E / C phases** (Gligoric et al.): **A**nalysis (decide what to run), **E**xecution (run the selected tests), **C**ollection (record dependencies for next time).
  - **End-to-end time:** A + E + C. This is the time a developer actually waits.

---

## Part 1 — Foundations and surveys

### 1. Rothermel & Harrold — *A Safe, Efficient Regression Test Selection Technique* (DejaVu)
- **Citation:** G. Rothermel, M. J. Harrold. ACM TOSEM 6(2):173–210, April 1997. DOI 10.1145/248233.248262.
- **URL:** https://www.cs.purdue.edu/homes/xyzhang/fall07/Papers/p173-rothermel.pdf
- **Summary:** The paper builds control-flow graphs (CFGs) for the old and new program and walks them together. It selects every test whose old execution trace reaches a changed edge; these are the "modification-traversing" tests. The authors prove the technique is safe under *controlled regression testing*, meaning everything except the code (environment, inputs and so on) stays fixed. They argue it is at least as precise as other safe techniques. They implemented it as the DejaVu tools.
- **Numbers:**
  - Intraprocedural DejaVu1 on the Siemens programs: for 21 of 41 procedures it always selected 100% of the tests. It cut the test set by more than 50% in only 5 cases.
  - Interprocedural DejaVu2: selected tests were on average 55.6% of RetestAll, a 44.4% saving. The range was 43.3% to 93.6%.
  - On the larger `player` subsystem (Empire game), it selected on average 4.8% of the tests, a reduction of more than 95%. Overall regression-testing time fell by 82–93%, about 4.5–5.5 hours per version.
- **Takeaway:** This paper defines "safe". The safety proof depends on the controlled-regression-testing assumption, and real CI violates that assumption through flakiness, environment and config changes. How much you save depends heavily on the subject: small programs save little, large modular systems save a lot.
- **Read:** full text.

### 2. Rothermel & Harrold — *Analyzing Regression Test Selection Techniques*
- **Citation:** G. Rothermel, M. J. Harrold. IEEE TSE 22(8), 1996. DOI 10.1109/32.536955.
- **URL:** https://doi.org/10.1109/32.536955. Metadata confirmed via Semantic Scholar; the full text was not accessible.
- **Summary:** This paper introduced the framework for comparing RTS techniques on four criteria: **inclusiveness** (how safe), **precision**, **efficiency** and **generality**. The Engström and Yoo–Harman surveys below both confirm it is the standard evaluation lens.
- **Takeaway:** Judge any RTS tool on all four criteria, not only on how many tests it selects.
- **Read:** abstract/metadata only. The four-criteria description is confirmed by Engström et al. (#4).

### 3. Yoo & Harman — *Regression Testing Minimisation, Selection and Prioritisation: A Survey*
- **Citation:** S. Yoo, M. Harman. Software Testing, Verification & Reliability 22(2):67–120, 2012. DOI 10.1002/stvr.430.
- **URL:** https://www.cse.chalmers.se/~feldt/advice/yoo_2010_regression_testing_survey.pdf (preprint). Official page: https://onlinelibrary.wiley.com/doi/abs/10.1002/stvr.430
- **Summary:** Surveys 159 papers on minimisation, selection and prioritisation. It lists the selection approaches: integer programming, data-flow, symbolic execution, dynamic slicing, CFG graph-walk, textual diff, SDG slicing, path analysis, modification detection, firewall, and others. Two ideas anchor the RTS field: Leung and White's test classification (obsolete, retestable, reusable) and Rothermel's definition of safe RTS. The survey argues RTS is the only one of the three areas with a well-defined notion of safety, because minimisation and prioritisation must rely on surrogate metrics. It also covers cost models. Rosenblum et al.'s predictor estimated that 87.3% of KornShell's tests would be selected; TestTube actually selected 88.1%. Under Leung and White's cost model, TestTube was *not cost-effective* because coverage analysis per test cost more than running the test.
- **Takeaway:** Analysis overhead can wipe out the savings. The field has known this since the 1990s.
- **Read:** full text (preprint version).

### 4. Engström, Runeson, Skoglund — *A Systematic Review on Regression Test Selection Techniques*
- **Citation:** E. Engström, P. Runeson, M. Skoglund. Information and Software Technology 52(1):14–30, 2010.
- **URL:** https://fileadmin.cs.lth.se/cs/Personal/Emelie_Engstrom/Papers/IST_syst_review_regr_test.pdf
- **Summary:** Reviews 27 papers reporting 36 empirical studies (21 experiments, 15 case studies) of 28 RTS techniques. Evidence for differences between techniques is "not very strong, and sometimes contradictory", so there is "no basis for selecting one superior technique". Many time-reduction results come from small programs such as the Siemens suite, with savings measured in milliseconds. Only 42% of studies measured total time (selection plus execution), and only 30% measured both fault detection and cost.
- **Takeaway:** Much of the classic RTS evidence cannot be carried over to industrial scale. Measure on your own codebase.
- **Read:** full text.

### 5. Greca, Miranda, Bertolino — *State of Practical Applicability of Regression Testing Research: A Live Systematic Literature Review*
- **Citation:** R. Greca, B. Miranda, A. Bertolino. ACM Computing Surveys 55(13s), 2023. DOI 10.1145/3579851.
- **URL:** https://dl.acm.org/doi/10.1145/3579851
- **Summary:** Reviews 79 studies from 2016–2022 that claim industrial relevance, plus surveys of their authors and 23 practitioners. Conclusion: although these approaches are "widely motivated by industrial relevance", few were evaluated on industrial or large open-source systems, and "even fewer approaches have been adopted in practice".
- **Takeaway:** The research-to-practice gap is still the main obstacle.
- **Read:** abstract only.

### 6. Pan, Bagherzadeh, Ghaleb, Briand — *Test Case Selection and Prioritization Using Machine Learning: A Systematic Literature Review*
- **Citation:** R. Pan, M. Bagherzadeh, T. A. Ghaleb, L. Briand. Empirical Software Engineering 27(2), 2022. arXiv:2106.13891.
- **URL:** https://arxiv.org/abs/2106.13891
- **Summary:** Reviews 29 ML-based selection/prioritisation studies (2006–2020). Features are mostly cheap signals: execution history, coverage, complexity and text. Metrics vary so much, and failure rates in the datasets are so low, that techniques cannot be compared with each other. Only 6 of the 29 studies (21%) are reproducible.
- **Takeaway:** Treat published ML test-selection numbers with caution. Always report the failure rate of the dataset.
- **Read:** full text.

---

## Part 2 — Analysis-based RTS: dynamic, static and hybrid

### 7. Gligoric, Eloussi, Marinov — *Practical Regression Test Selection with Dynamic File Dependencies* (Ekstazi)
- **Citation:** M. Gligoric, L. Eloussi, D. Marinov. ISSTA 2015, pp. 211–222. DOI 10.1145/2771783.2771784. ACM SIGSOFT Distinguished Paper.
- **URL:** https://users.ece.utexas.edu/~gligoric/papers/GligoricETAL15Ekstazi.pdf
- **Summary:** Ekstazi records which *files* each test class uses at runtime: `.class` files, jars and resources. On the next run it skips any test whose files all have the same checksum. It does not need the version-control system, because it compares file checksums rather than diffs. "Smart checksums" ignore changes such as debug information. The paper argues RTS should be judged on end-to-end time (A + E + C), not on how many tests are selected.
- **Numbers:**
  - 615 revisions of 32 Java projects, about 5M LOC.
  - End-to-end time fell by 32% on average, and by 54% for longer-running suites.
  - When dependency collection runs separately offline, the cut was 47% on average and 66% for long suites.
  - Selection ratio ranged from 5% to 38% of tests. End-to-end time ranged from 9% to 138% of RetestAll; the 138% case was a slowdown on a short suite.
  - Example: on Cucumber, Ekstazi selected 12% of tests but still took 99% of RetestAll time.
  - Ekstazi selects more tests than the fine-grained FaultTracer, yet has lower end-to-end time. FaultTracer was on average *slower than RetestAll*.
  - Class-level selection gave more savings than method-level selection.
  - Adopted by Apache Camel, Commons Math and CXF.
- **Takeaway:** Coarse (file/class) dependencies usually beat fine (method/statement) ones end to end, because analysis and collection costs dominate. RTS pays off mainly for suites that take longer than about a minute.
- **Read:** full text.

### 8. Legunsen, Hariri, Shi, Lu, Zhang, Marinov — *An Extensive Study of Static Regression Test Selection in Modern Software Evolution*
- **Citation:** O. Legunsen et al. FSE 2016, pp. 583–594. DOI 10.1145/2950290.2950361.
- **URL:** https://mir.cs.illinois.edu/~marinov/publications/LegunsenETAL16StaticRTS.pdf
- **Summary:** Compares static class-level RTS (ClassSRTS, based on the class firewall and a type dependency graph) and static method-level RTS (MethSRTS, based on a call graph) with Ekstazi. The study covers 985 revisions of 22 projects.
- **Numbers:**
  - Tests selected: Ekstazi 20.6%, ClassSRTS 29.4%, MethSRTS 43.8%.
  - End-to-end time for ClassSRTS and Ekstazi: 62.5–68.2% of RetestAll.
  - Safety violations occurred in 0.2% of revisions for ClassSRTS and 10.6% for MethSRTS. Precision violations occurred in 33.0% and 55.7% respectively.
  - Reflection was the cause of unsafety.
  - Call-graph analysis can blow up when libraries are included: 370.8% of RetestAll time without libraries versus 81,304.2% with them.
- **Takeaway:** Static class-level RTS performs about as well as dynamic RTS but is occasionally unsafe because of reflection. Method-level static RTS is worse on every axis.
- **Read:** full text.

### 9. Legunsen, Shi, Marinov — *STARTS: STAtic Regression Test Selection* (tool paper)
- **Citation:** ASE 2017 Tool Demos, pp. 949–954.
- **URL:** https://github.com/TestingResearchIllinois/starts
- **Summary:** A Maven plugin for class-level static RTS that uses only compile-time information. Goals: `starts:diff`, `starts:impacted`, `starts:select`, `starts:starts`, `starts:clean`. Coordinates: `edu.illinois:starts-maven-plugin`, latest release 1.4. The README says it supports Java 8–15.
- **Read:** README only.

### 10. Shi, Hadzi-Tanovic, Zhang, Marinov, Legunsen — *Reflection-Aware Static Regression Test Selection*
- **Citation:** Proc. ACM Program. Lang. 3 (OOPSLA), Article 187, 2019. DOI 10.1145/3360613.
- **URL:** https://mir.cs.illinois.edu/marinov/publications/ShiETAL19ReflectionAwareRTS.pdf
- **Summary:** Tests five ways to make STARTS safe in the presence of reflection, on 1,173 versions of 24 projects. The authors describe the results as *negative*.
- **Numbers:**
  - Purely static reflection-aware variants were safe but cost at best 85.8% of RetestAll, versus 69.1% for the reflection-unaware version.
  - One hybrid variant cost 91.2%.
  - The best hybrid cost 75.8% but could still be unsafe when tests depend on execution order.
- **Takeaway:** Making static RTS sound for dynamic language features costs most of the savings. This supports using dynamic (traced) dependencies for dynamic languages.
- **Read:** full text (abstract and introduction).

### 11. Zhang — *Hybrid Regression Test Selection* (HyRTS)
- **Citation:** L. Zhang. ICSE 2018. DOI 10.1145/3180155.3180198.
- **URL:** https://lingming.cs.illinois.edu/publications/icse2018.pdf
- **Summary:** Mixes granularities: method-level changes where that is cheap, file-level changes otherwise. Evaluated on 2,707 revisions of 32 projects (124M LoC).
- **Numbers:**
  - Tests selected: HyRTS 18.35% versus file-level RTS (Ekstazi-style) 27.18%.
  - Offline test time: 42.87% versus 54.35% of original, i.e. 21.1% faster.
  - Online end-to-end (AEC) time: 53.66% versus 58.67%.
- **Takeaway:** Hybrid granularity gains real but modest improvements over file-level RTS once overhead is counted.
- **Read:** full text (abstract and results).

### 12. Zhang, Liu, Chen, Wang — *Hybrid Regression Test Selection by Integrating File and Method Dependences* (JcgEks)
- **Citation:** ASE 2024. DOI 10.1145/3691620.3695525.
- **URL:** https://doi.org/10.1145/3691620.3695525
- **Summary:** Adds static method call graphs to Ekstazi and handles callbacks from external libraries safely. Evaluated on 1,000 revisions of 20 projects.
- **Numbers:** Compared with Ekstazi, end-to-end time fell 29% and selected test classes fell 30.9% "while ensuring safety". The authors report that the competing FineEkstazi tool missed test classes.
- **Read:** abstract only.

### 13. Liu, Zhang, Nie, Gligoric, Legunsen — *More Precise Regression Test Selection via Reasoning about Semantics-Modifying Changes* (FineRTS)
- **Citation:** ISSTA 2023. DOI 10.1145/3597926.3598086.
- **URL:** https://users.ece.utexas.edu/~gligoric/papers/LiuETAL23FineRTS.pdf
- **Summary:** Notes that analysis-based RTS has hit a "performance wall". The authors classify 29 kinds of changes that do not need re-running certain tests and teach Ekstazi and STARTS to recognise them. Evaluated on 1,150 versions of 23 projects.
- **Numbers:** 41.7% and 31.8% fewer tests selected, and 33.7% and 28.7% less time, than Ekstazi and STARTS respectively, "with no loss in safety".
- **Read:** abstract only.

### 14. Ren, Shah, Tip, Ryder, Chesley — *Chianti: A Tool for Change Impact Analysis of Java Programs*
- **Citation:** OOPSLA 2004, pp. 432–448.
- **URL:** https://prolangs.cs.vt.edu/refs/docs/oopsla04.pdf
- **Summary:** Breaks the difference between two versions into atomic changes and maps them to affected tests using call graphs. It also reports which changes affect each test, which helps debugging.
- **Numbers:** On a year (2002) of Daikon CVS history, on average 52% of unit tests were affected. Each affected test was affected by only 3.95% of the atomic changes.
- **Takeaway:** Early evidence that "affected" can easily mean half the suite in a tightly coupled codebase. Impact analysis is also valuable for explaining failures.
- **Read:** full text (abstract).

### 15. Orso, Shi, Harrold — *Scaling Regression Testing to Large Software Systems*
- **Citation:** FSE 2004, pp. 241–252. DOI 10.1145/1029894.1029928.
- **URL:** https://dl.acm.org/doi/10.1145/1029894.1029928
- **Summary:** A two-phase technique for Java. A cheap high-level partitioning step comes first, followed by precise edge-level analysis only on the partitions it flags. This keeps safe RTS affordable on subjects of 70 to more than 500 KLOC.
- **Numbers:** None verified.
- **Takeaway:** This two-phase idea (coarse filter, then fine analysis) reappears in HyRTS and in combined analysis-plus-ML approaches.
- **Read:** abstract/metadata only (via search results).

### 16. Celik, Vasic, Milicevic, Gligoric — *Regression Test Selection Across JVM Boundaries* (RTSLinux)
- **Citation:** ESEC/FSE 2017, pp. 809–820. DOI 10.1145/3106237.3106297.
- **URL:** https://users.ece.utexas.edu/~gligoric/papers/CelikETAL17RTSLinux.pdf
- **Summary:** A Linux kernel module that records *every file* a test touches at the OS level. This covers spawned processes, native code and other languages, which in-JVM tools like Ekstazi miss.
- **Numbers:** On 21 Java projects that escape the JVM (2.05M LOC), it skipped 74.17% of tests and saved 52.83% of test execution time on average.
- **Takeaway:** System-call-level file tracing is the language-agnostic way to get safe dependencies. Stripe's production system (#33) uses the same idea.
- **Read:** full text (abstract).

### 17. Vasic, Parvez, Milicevic, Gligoric — *File-Level vs. Module-Level Regression Test Selection for .NET* (Ekstazi#)
- **Citation:** ESEC/FSE 2017 Industry. DOI 10.1145/3106237.3117763.
- **URL:** https://users.ece.utexas.edu/~gligoric/papers/VasicETAL17EkstaziSharp.pdf
- **Summary:** Ports Ekstazi to .NET and compares it with a Microsoft incremental build system that skips at module level.
- **Numbers:** Regression testing time fell 43.70% on 11 open-source projects. On a large Microsoft project it fell 65.26% *on top of* the savings from module-level incremental builds.
- **Takeaway:** File-level RTS inside modules adds a lot beyond build-system (module/target-level) skipping.
- **Read:** full text (abstract).

### 18. Fu, Celik, Vasic, Gligoric (et al.) — *Resurgence of Regression Test Selection for C++* (RTS++)
- **Citation:** ICST 2019 (venue from the author PDF header; authors per the PDF).
- **URL:** https://users.ece.utexas.edu/~gligoric/papers/FuETAL19RTS++.pdf
- **Summary:** Static function-call-graph RTS over LLVM IR for projects using Google Test. It integrates with Make, CMake and AutoMake. Evaluated on 11 projects (3.8M LOC).
- **Numbers:** Executed tests fell 88% and end-to-end time fell 61% on average.
- **Read:** full text (abstract).

### 19. Zhu, Legunsen, Shi, Gligoric — *A Framework for Checking Regression Test Selection Tools* (RTSCheck)
- **Citation:** ICSE 2019, pp. 430–441. DOI 10.1109/ICSE.2019.00056.
- **URL:** https://users.ece.utexas.edu/~gligoric/papers/ZhuETAL19RTSCheck.pdf
- **Summary:** Feeds evolving programs into RTS tools and checks the results against rules. It uses generated programs, bug-database programs and real project histories.
- **Numbers:** Found **27 bugs** in three Java RTS tools: Clover, Ekstazi and STARTS.
- **Takeaway:** RTS tools themselves are a source of missed failures. Plan for a periodic full run to catch them.
- **Read:** full text (abstract).

### 20. Gligoric, Negara, Legunsen, Marinov — *An Empirical Evaluation and Comparison of Manual and Automated Test Selection*
- **Citation:** ASE 2014, pp. 361–372.
- **URL:** https://users.ece.utexas.edu/~gligoric/papers/GligoricETAL14ManualRTS.pdf
- **Summary:** Studied 14 developers over 3 months and 450 test sessions. Almost all developers chose which tests to run by hand, in ad-hoc ways.
- **Numbers:** Manual and automated selection differed in *every one* of the 450 sessions. Manual selection chose more tests 73% of the time (wasted time) and fewer tests 27% of the time (possible missed bugs).
- **Takeaway:** The realistic alternative to tool-based RTS is manual guessing, not RetestAll. This matters even more when an AI agent is the one choosing which tests to run.
- **Read:** full text (abstract).

### 21. Gu, Mesbah — *Fine-Grained Assertion-Based Test Selection* (Selertion)
- **Citation:** arXiv:2403.16001 (v2, April 2025).
- **URL:** https://arxiv.org/abs/2403.16001
- **Summary:** Uses individual test *assertions*, found by statement-level slicing, as the unit of selection.
- **Numbers:** On 11 subjects, overall test time fell 63% on average, 7–38% faster than other techniques. Longer-running suites benefit more.
- **Read:** full text (abstract).

### 22. Wang, Wang, Nie — *Efficient Incremental Code Coverage Analysis for Regression Test Suites* (iJaCoCo)
- **Citation:** arXiv:2410.21798, 2024.
- **URL:** https://arxiv.org/abs/2410.21798
- **Summary:** Plain RTS produces *incorrect coverage reports*, because skipped tests contribute no coverage. iJaCoCo, built on Ekstazi and JaCoCo, updates only the coverage data that a change affects.
- **Numbers:** Coverage analysis was 1.86× faster on average and up to 8.20× faster, over 1,122 versions of 22 repositories.
- **Takeaway:** If CI enforces coverage gates, naive RTS breaks them. You need incremental coverage or a periodic full run.
- **Read:** full text (abstract).

### 23. Wang, Pradel, Liu — *Names Are All You Need: Effective and Safe Regression Test Selection for Python* (NameRTS)
- **Citation:** arXiv:2605.25356, May 2026.
- **URL:** https://arxiv.org/abs/2605.25356
- **Summary:** Python is hard for RTS in two ways.
  - Call graphs are unreliable. Cited evidence: PyCG failed on 11 of 50 projects and found only 49% of the call edges seen at runtime.
  - *Eager importing* runs every parent `__init__.py`, which makes file-level and coverage-level dependencies overly broad.
  NameRTS instead builds a bipartite graph of code elements and identifier names and treats selection as a reachability question. Evaluated on 500 commits across 10 projects.
- **Numbers:** Skipped 69.90% of test files and cut end-to-end time by 45.59%. It was safe on 99.6% of commits, versus 76.6% for BabelRTS.
- **Takeaway:** For Python and JS, the import graph is the hub problem. Package `__init__`/barrel files make everything depend on everything.
- **Read:** full text (abstract, introduction and evaluation setup).

### 24. Maurina, Cazzola, Ghosh — *BabelRTS: Polyglot Regression Test Selection*
- **Citation:** IEEE TSE 51(5), 2025. Artifact: Zenodo 10.5281/zenodo.10805500.
- **URL:** https://ieeexplore.ieee.org/document/10944548/
- **Summary:** Static, file-level RTS that supports 12 languages and 5 language combinations. Running separate single-language RTS tools on a multi-language system is unsafe because dependencies between languages are missed. In polyglot mode, BabelRTS selected more tests (i.e. was safer) on 60% of commits.
- **Read:** abstract only (via search summary). NameRTS (#23) independently measured it as safe on only 76.6% of Python commits.

### 25. Hundsdorfer, Würsching, Pretschner — *RustyRTS: Regression Test Selection for Rust*
- **Citation:** ICST 2025, pp. 338–348.
- **URL:** https://ieeexplore.ieee.org/document/10988992/
- **Summary:** Described as the first RTS for Rust. It offers module-level selection and function-level selection, the latter using either static or dynamic analysis.
- **Numbers:** Evaluated on mutation-induced changes in 9 projects. The variants selected 99.99%, 97.87% and 99.97% of the tests that failed.
- **Read:** abstract only (via search summary). I found no public repository or CLI instructions.

---

## Part 3 — RTS in CI and at build/module level

### 26. Shi, Zhao, Marinov — *Understanding and Improving Regression Test Selection in Continuous Integration*
- **Citation:** A. Shi, P. Zhao, D. Marinov. ISSRE 2019.
- **URL:** https://mir.cs.illinois.edu/marinov/publications/ShiETAL19RTSinCI.pdf
- **Summary:** Replays 935 Travis builds of 22 projects using three approaches:
  - module-level RTS, as used in industry (GIB, gitflow-incremental-builder);
  - class-level Ekstazi;
  - a hybrid of the two (GIBstazi).
- **Numbers:**
  - Out of the box, GIB selected **all** modules in 65% of commits and more than 70% of modules overall. This is the hub problem at module granularity.
  - Total CI build time as a share of RetestAll: GIB 79.7%, Ekstazi 76.0%, GIBstazi 77.4%. That is much worse than the 60–70% seen locally, and much worse than the 30.6% of tests Ekstazi actually selected, because of fixed CI overhead.
  - Almost all the failures RTS "missed" were *flaky* test failures.
- **Takeaway:** In cloud CI, fixed overhead (checkout, dependency install, build) caps what RTS can save. RTS also filters flaky noise that has nothing to do with the change.
- **Read:** full text.

### 27. Elsner, Hauer, Pretschner, Reimer — *Empirically Evaluating Readily Available Information for Regression Test Optimization in Continuous Integration*
- **Citation:** ISSTA 2021, pp. 491–504.
- **URL:** https://conf.researchr.org/details/issta-2021/issta-2021-technical-papers/15/Empirically-Evaluating-Readily-Available-Information-for-Regression-Test-Optimization
- **Summary:** Unsafe RTS using only CI and VCS metadata. Covers 23 projects, 37k CI logs and 76k commits.
- **Numbers:** While still triggering 90% of failures, it saved on average 84% of test execution time. Test-history features beat change-based features, and "simple and well-known heuristics often outperform complex machine-learned models".
- **Read:** abstract only.

### 28. Elsner, Wuersching, Schnappinger, Pretschner, Graber, Dammer, Reimer — *Build System Aware Multi-language Regression Test Selection in Continuous Integration*
- **Citation:** ICSE-SEIP 2022 (IVU Traffic Technologies).
- **URL:** https://conf.researchr.org/details/icse-2022/icse-2022-seip---software-engineering-in-practice/14/Build-System-Aware-Multi-language-Regression-Test-Selection-in-Continuous-Integration
- **Summary:** Industrial codebase of more than 13M LOC in Java and C/C++ with thousands of non-code artifacts. Selection is aware of the build system and works across languages.
- **Numbers:** Across 397 PRs and about 2,700 commits, it safely excluded up to 75% of tests on average, with no real failures slipping into target branches. Testing time fell 72% and end-to-end CI time fell up to 63%.
- **Read:** abstract only. The TUM PDF host blocked automated fetches.

### 28b. OpenClover — Test Optimization (tool documentation)
- **URL:** https://openclover.org/doc/manual/latest/general--what-is-test-optimization.html and https://openclover.org/doc/manual/latest/maven--using-test-optimization.html
- **Summary:** Uses per-test coverage to run only the tests that cover modified code, and orders them so likely failures run first. By default it forces a full run every 10 builds (`fullRunEvery`). Tests must be fully independent of each other. Command: `mvn clover:setup clover:optimize test clover:snapshot`.
- **Numbers:** The documentation cites an Atlassian case study: about 70% less cumulative build time over 142 changesets, with fewer than 10% of tests run per optimised build **(vendor claim)**.
- **Read:** official documentation.

---

## Part 4 — Industry at scale

### 29. Memon, Gao, Nguyen, Dhanda, Nickell, Siemborski, Micco — *Taming Google-Scale Continuous Testing* (TAP)
- **Citation:** ICSE-SEIP 2017, pp. 233–242. DOI 10.1109/ICSE-SEIP.2017.16.
- **URL:** https://huang.isis.vanderbilt.edu/cs8395/paper/google-testing-icse-seip-17.pdf (also https://research.google.com/pubs/pub45861.html)
- **Summary:** TAP already selects tests by reverse build dependencies on changed files. It then batches commits into "milestones" (roughly every 45 minutes at peak). This paper asks how to skip even more of the *affected* tests.
- **Numbers:**
  - Scale: a 2-billion-LOC monorepo. Each day, more than 13K projects, 800K builds and 150M test runs, with about one commit per second.
  - Milestones reached up to 4.2M tests, and delays of up to 9 hours were observed.
  - Of 5.5M affected test targets over one month, only 63K ever failed. 91.3% passed at least once and never failed. Only 1.23% of executions found a breakage or fix.
  - Running only affected tests within dependency distance ≤ 10 (or ≤ 6) of the change executed 61% (50%) of targets and saved 42% (55%) of resources. In simulation, this *missed no breakage or fix*.
- **Takeaway:** Even "safe" build-graph selection over-selects hugely at monorepo scale. Most affected tests almost never fail. Distance in the dependency graph and failure history are strong signals for skipping further.
- **Read:** full text.

### 30. Leong, Singh, Papadakis, Le Traon, Micco — *Assessing Transition-based Test Selection Algorithms at Google*
- **Citation:** ICSE-SEIP 2019. DOI 10.1109/ICSE-SEIP.2019.00019.
- **URL:** https://mpapad.github.io/publications/pdfs/ICSE-SEIP2019.pdf
- **Summary:** Builds a simulation framework using real TAP data. The key metric is *transitions* (pass→fail or fail→pass), not raw failures. At Google there are more than 20× as many failures as transitions in a month.
- **Numbers:**
  - 84% of transitions are caused by flaky tests, and 16% of tests show some flakiness.
  - The best heuristics used how often a test was recently triggered and how many distinct authors triggered it. They beat random selection on more than 30% of transition commits in some cases.
  - Directory-overlap selection performed about as well as random. The gap to optimal was up to 90%.
- **Takeaway:** History-based selection is weaker than hoped once flakiness is filtered out. Evaluate selection against *transitions* with flaky tests removed.
- **Read:** full text (abstract and introduction).

### 31. Machalica, Samylkin, Porth, Chandra — *Predictive Test Selection* (Facebook/Meta)
- **Citation:** ICSE-SEIP 2019, pp. 91–100. DOI 10.1109/ICSE-SEIP.2019.00018. arXiv:1810.05286.
- **URL:** https://arxiv.org/abs/1810.05286. Blog: https://engineering.fb.com/2018/11/21/developer-tools/predictive-test-selection/
- **Summary:** Build-dependency selection at Facebook was too broad. About 99.9% of the tests it selected passed, and a change to a low-level library triggered tests across every dependent project. The blog says about 25% of all tests ran per mobile change. Facebook trained a gradient-boosted decision tree on (change, test) features: change size, file and extension history, and test failure rates over the last 7, 14, 28 and 56 days. Flakiness was handled by retrying to separate real failures from flaky ones.
- **Numbers:**
  - Catches more than 95% of individual test failures and more than 99.9% of faulty changes, with a selection rate below 0.33 of the tests that build-dependency selection would run.
  - In production, total test executions fell 3× and infrastructure cost (machines) fell 2× relative to build-dependency selection.
- **Takeaway:** This is the reference design for *unsafe* ML selection layered on top of safe dependency selection. It works because landing-time testing only needs to catch *faulty changes*, not every failing test.
- **Read:** full text.

### 31b. Aichmann (supervised by Cito) — *Predictive Test Selection: A Replication Study*
- **Citation:** Diploma thesis, TU Wien, 2025.
- **URL:** https://repositum.tuwien.at/bitstream/20.500.12708/215633/1/Aichmann%20Stefan%20-%202025%20-%20Predictive%20Test%20Selection%20A%20Replication%20Study.pdf
- **Summary:** Replicates Meta's predictive test selection (PTS) on open-source data. The original paper describes its features only at a high level, so assumptions were needed. The thesis reports the key findings were replicated.
- **Read:** abstract only. I did not extract its numbers.

### 32. Mehta, Farmahinifarahani, Bhagwan, Guptha, Jafari, Kumar, Saini, Santhiar — *Data-Driven Test Selection at Scale* (Microsoft)
- **Citation:** ESEC/FSE 2021 Industry. DOI 10.1145/3468264.3473916.
- **URL:** https://2021.esec-fse.org/details/fse-2021-industry/2/Data-Driven-Test-Selection-at-Scale
- **Summary:** A "generic, language-agnostic and lightweight statistical model" that needs no complex feature extraction and scales to hundreds of repositories. It also proposes metrics that capture both reduced resource cost and reduced PR turnaround time.
- **Numbers:** Across 22 large Microsoft repositories, it saved 15–30% of compute time while still reporting about 99% of buggy PRs.
- **Takeaway:** Realistic ML savings on heterogeneous enterprise repositories are much smaller than the monorepo headline figures.
- **Read:** abstract only.

### 33. Microsoft — *Test Impact Analysis (TIA)*, Azure Pipelines documentation
- **URL:** https://learn.microsoft.com/en-us/azure/devops/pipelines/test/test-impact-analysis?view=azure-devops
- **Summary:** Instrumented dynamic file-level mapping from tests to source files for managed .NET code, enabled via **Run only impacted tests** in VSTest v2.
- **Safety net:** It always includes impacted, previously failing and newly added tests. It falls back to running all tests for file types it does not understand (for example HTML or CSS changes). It recommends a periodic full run and offers the `DisableTestImpactAnalysis=true` build variable to force one.
- **Tuning:** `TIA_IncludePathFilters` sets which paths it applies to and which files to ignore. `TIA.UserMapFile` supplies a custom XML dependency map (for JS, C++ or multi-machine setups).
- **Not supported:** .NET Core, UWP, multi-machine topologies, data-driven tests.
- **Validation advice:** Run the impacted subset (T1) followed by all tests (T2) and compare results.
- **Takeaway:** Microsoft's documented pattern is conservative fallback, periodic full runs, and shadow-mode validation.
- **Read:** official documentation.

### 34. Mozilla — *Testing Firefox More Efficiently with Machine Learning* (bugbug / `mach try auto`)
- **Citation:** Mozilla Hacks, July 2020. Also cross-posted on Andrew Halberstadt's blog (ahal.ca), so he is an author; the full author list was not verified.
- **URL:** https://hacks.mozilla.org/2020/07/testing-firefox-more-efficiently-with-machine-learning/
- **Summary:** An XGBoost model over (test, patch) pairs. Features include how often a test failed when the same files were touched, directory distance between source and test, and co-modification history. It is retrained every two weeks. Mozilla built a large set of heuristics to handle missing data (tests do not run on every push) and to separate regressions from intermittent failures; backouts are used as labels.
- **Numbers:**
  - About 85k test files across about 90 configurations, and about 300 pushes per workday. Running everything everywhere would be about 2.3B test-file executions per day.
  - 70% fewer test tasks on the integration branch than the previous heuristics, and about 99% fewer than an unoptimised system.
- **Combining with full runs:** Periodic full runs plus backfilling and sheriff backouts on the integration branch.
- **Read:** official blog (via fetch summary). Numbers **should be re-checked against the post** before quoting.

### 35. Stripe — *Selective Test Execution at Stripe: Fast CI for a 50M-line Ruby monorepo*
- **Citation:** A. Anchuri, stripe.dev blog, 2026-04-09.
- **URL:** https://stripe.dev/blog/selective-test-execution-at-stripe-fast-ci-for-a-50m-line-ruby-monorepo
- **Summary:** Records runtime *file access* per test using an `LD_PRELOAD` interceptor library. Because it sees every file a test opens, it captures non-Ruby dependencies such as config, fixtures and templates. It always re-runs previously failing tests and always runs tests that glob directories, since those accesses are not captured by open syscalls.
- **Numbers:** About 100k test files (about 1.2M test units) and about 50k builds per week. On average about 5% of the suite runs, with a median below 0.5%. Compute is less than 10% of run-everything. A sequential full run would take about 4 months.
- **Takeaway:** This is Ekstazi/RTSLinux-style dynamic file tracing working at very large scale in a dynamic language.
- **Read:** official blog.

### 36. Shopify — *Spark Joy by Running Fewer Tests*
- **Citation:** J. Xie, Shopify Engineering, 2020-06-11.
- **URL:** https://shopify.engineering/spark-joy-by-running-fewer-tests
- **Summary:** Dynamic analysis, using method-call tracing (Rotoscope, TracePoint), builds a map from files to tests for the Rails monolith. Shopify rejected static analysis because the code is only partly typed with Sorbet, and rejected ML because it wanted determinism. Rails was patched to trace config and YAML such as I18n. Unmapped file types run everything.
- **Numbers:** More than 150k tests. About 60% of tests run on average, and 40% of builds run fewer than 20% of tests. Compute fell 25%. Recall was 99.94% (5 missed failures in 8,360 commits). Developers requested a full run on fewer than 2% of PRs.
- **Safety net:** The full suite runs asynchronously on main.
- **Read:** official blog.

### 36b. Shopify — *Test Budget: Time Constrained CI Feedback*
- **Citation:** A. Stergiou, 2022-03-07.
- **URL:** https://shopify.engineering/test-budget-time-constrained-ci-feedback
- **Summary:** Adds prioritisation and a time budget on top of the call-graph-based selection. Failures were found after running 70% of the selected suite. Ordering by failure rate found 80% of failures after 60% of selected tests. More than 170k tests.
- **Read:** official blog.

### 37. Dropbox — *Continuous Integration and Deployment with Bazel*
- **Citation:** B. Peterson, dropbox.tech, 2019-12-11.
- **URL:** https://dropbox.tech/infrastructure/continuous-integration-and-deployment-with-bazel
- **Summary:** `bazel query` computes the tests affected by each commit. The affected sets are *rolled up* over a tunable time window and run once on the last commit of the window. If a test runs on commit N and is not affected by N+1, its status carries forward. The Athena system bisects failures across the rollup window.
- **Numbers:** None given.
- **Takeaway:** Batching plus bisection is how you spend less than "affected tests × every commit".
- **Read:** official blog.

### 38. Chromium — commit queue "analyze" step
- **URL:** https://www.chromium.org/developers/testing/commit-queue/chromium_trybot-json/
- **Summary:** Try bots run an analyze step (build-graph based) to decide whether to compile and which test targets to run. Known weakness: undeclared dependencies such as test data files. The workaround is an exclusion list (`trybot_analyze_config.json`); a change to any listed file runs all tests.
- **Takeaway:** Build-graph RTS is only as safe as the dependencies the build declares.
- **Read:** official documentation (may be dated).

### 39. Gradle — *Develocity Predictive Test Selection*
- **URL:** https://docs.develocity.ai/2026.3/using-develocity/predictive-test-selection/ and https://docs.develocity.ai/2026.3/guides/predictive-test-selection/
- **Summary:** An ML model trained on Build Scan history of changes and test outcomes, combined with cross-project training. It always selects tests that were recently added, changed, failed or flaky.
- **Profiles:** `CONSERVATIVE`, `STANDARD` (default), `FAST`.
- **Modes:** `RELEVANT_TESTS` (pre-merge) and `REMAINING_TESTS`. The documentation recommends running the remaining tests in "post-merge, nightly or ready-for-release builds".
- **`mustRun`:** class patterns that always run.
- **Numbers:** None published on the pages I read.
- **Read:** official documentation.

### 40. Launchable (now part of CloudBees) — *Predictive Test Selection: subset optimisation targets*
- **URL:** https://help.launchableinc.com/features/predictive-test-selection/requesting-and-running-a-subset-of-tests/choosing-a-subset-optimization-target/
- **Summary:** `launchable subset --build $BUILD --confidence 90%`, `--time 10m`, or `--target 20%`. "Confidence" means the probability of catching a failing *session*, read from a confidence curve built on evaluation sessions. The documentation mentions an optional "remainder" list output. **(I did not verify the exact flag.)**
- **Read:** official documentation.

### 41. Zhang, Liu, Gligoric, Legunsen, Shi — *Comparing and Combining Analysis-Based and Learning-Based Regression Test Selection*
- **Citation:** AST 2022. DOI 10.1145/3524481.3527230.
- **URL:** https://sweetstreet.github.io/publication/predictiverts/
- **Summary:** Trains ML models on mutation-derived data and uses them to *filter* the tests chosen by Ekstazi or STARTS. Evaluated on 10 projects.
- **Numbers:** Selected 25.34% fewer tests than Ekstazi and 21.44% fewer than STARTS.
- **Takeaway:** A layered design (safe analysis first, then ML pruning) works for mid-size projects as well as monorepos.
- **Read:** abstract only.

**Total: 41 numbered entries plus 3 sub-entries (28b, 31b, 36b) = 44 sources.**

---

## (a) Synthesis — what the evidence agrees on

1. **Coarse dependencies usually win end to end.** Ekstazi (#7), STARTS (#8), HyRTS (#11) and RTSLinux (#16) all show that file- or class-level dependencies have lower *end-to-end* time than method- or statement-level ones. Finer analysis selects fewer tests, but its analysis and collection costs outweigh the gain (FaultTracer was slower than RetestAll). Hybrid approaches win a further 5–30% at best.
2. **Selection ratio is not time saved.** Ekstazi on Cucumber selected 12% of tests but took 99% of the time. In Travis CI, Ekstazi selected 30.6% of tests yet the build still took 76% of the time (#26). Fixed overhead (JVM start-up, checkout, dependency install, compile) caps the gain. RTS pays off for suites longer than about a minute and when setup is cached.
3. **Safe build-graph selection over-selects badly because of hub modules.**
   - GIB selected all modules in 65% of commits (#26).
   - At Facebook, about 25% of all tests ran per mobile change and 99.9% of selected tests passed (#31).
   - At Google, 5.5M affected targets in a month produced only 63K that ever failed (#29).
   - In Python, eager `__init__.py` imports widen every file-level dependency (#23).
   - Common hubs are low-level libraries, lock files (`package.json` and `pnpm-lock` changes mark everything affected in Nx, Pants and Vitest), barrel/`__init__` files, and shared config.
4. **Static RTS is fragile with dynamic features.** Reflection (Java), dynamic imports (JS), dynamic typing (Python/Ruby) and cross-language or process boundaries all break static analysis (#8, #10, #16, #23, #24). Making static RTS sound costs most of its benefit (#10). Industry systems for dynamic languages (Stripe, Shopify, Azure TIA) all trace dependencies at runtime.
5. **Non-code dependencies are the main source of unsafety in practice.** Config files, fixtures, test data, templates and environment variables cause the misses. Tools that trace at the syscall or file-access level (RTSLinux, Stripe) catch them. Build-graph tools miss undeclared ones (Chromium #38). Every production tool falls back to "run everything" on unknown file types (Azure TIA, Shopify, Vitest `forceRerunTriggers`).
6. **At scale, industry deliberately trades safety for speed with ML on top of safe selection.** Meta: 3× fewer executions and 2× lower cost, catching more than 99.9% of faulty changes (#31). Google: 42–55% resource savings by distance cutoff with no misses in simulation (#29). Mozilla: 70% fewer tasks than its previous heuristics (#34). Microsoft: 15–30% compute saved at about 99% buggy-PR recall (#32). Unsafe metadata-only RTS saves 84% of time at 90% failure recall (#27). **The unit of recall that matters is the faulty change, not the individual failing test.**
7. **Simple history heuristics are competitive with complex ML.** This holds for Elsner et al. (#27), Leong et al. (#30) and Shopify (#36b, failure-rate ordering). ML results are hard to compare and mostly not reproducible (#6).
8. **Flakiness dominates the signal.** 84% of Google transitions are flaky (#30), and almost all of RTS's "misses" in Travis were flaky failures (#26). RTS has a side benefit: it keeps developers from chasing failures that have nothing to do with their change.
9. **Every serious deployment keeps a full-run safety net.** Examples: Azure TIA periodic full runs, OpenClover `fullRunEvery=10`, Develocity `REMAINING_TESTS` post-merge, Shopify full suite on main, Mozilla periodic full runs plus backfill, Dropbox rollups plus Athena bisection. RTS tools have bugs of their own (RTSCheck found 27, #19), and naive RTS breaks coverage reports (#22).
10. **The real alternative to automated RTS is humans guessing.** Developers already select tests by hand, differently from tools in 100% of sessions, and too few tests 27% of the time (#20). An AI coding agent that picks tests "by intuition" is this same manual RTS problem at machine speed.

## (b) Practical decision guide

**When does RTS pay off?**
- The suite takes more than about 1–2 minutes, or CI queues are the bottleneck. Below that, analysis and collection overhead can make RTS *slower* (#7).
- Setup overhead is small compared with test time. If most CI time is `npm ci`, image pulls or compilation, fix caching first; RTS only shortens the test step (#26).
- Changes are usually local. If most commits touch a hub (monolithic config, a shared utils barrel file, a lock file), a dependency-based tool will select everything. Break up the hub or add ML/heuristic pruning.

**Which granularity?**

| Situation | Recommended granularity | Why |
|---|---|---|
| Monorepo with many packages | Package/target level (Nx, Turborepo, Bazel, Pants) first | Cheap and deterministic, and uses the build graph you already have |
| Inside a large package, JVM/.NET | File/class-level dynamic (Ekstazi, Azure TIA) | Best end-to-end time in the literature. It adds 44–65% savings beyond module-level skipping (#17) |
| Inside a package, JS/TS | Module-graph static (Jest `--changedSince`, Vitest `--changed`) plus force-rerun triggers | Cheap. Fails on dynamic `import()`, so add globs for config |
| Python | Coverage-based dynamic (pytest-testmon) | Static call graphs are unreliable, and eager imports blow up file-level selection (#23) |
| Ruby/other dynamic languages at scale | Runtime file-access tracing (Stripe/Shopify style) | Captures config and fixtures, and is safe in practice |
| Huge monorepo, safe set still too big | Add ML/heuristic pruning *on top of* the safe set (Meta, Develocity, Launchable) | Unsafe, so it needs a safety net |

Avoid method- or statement-level static RTS as your main mechanism unless tests are very expensive, for example long end-to-end runs where Selertion-style precision pays off.

**Safe or unsafe?**
- **Pre-merge / on each PR / for agents iterating:** Unsafe is acceptable, even preferred, *if* a later stage runs the rest. Aim for "catch the faulty change", not "catch every failing test".
- **Merge gate / main branch / release:** Safe selection at minimum. The full suite should run somewhere before release.
- **Always add:** previously failing tests, new or changed test files, flaky-quarantine awareness, and a list of must-run smoke or integrity tests.

**Combining selective runs with full runs (the pattern used everywhere):**
1. **Local or agent loop:** use watch mode or the related-tests mode (`jest --findRelatedTests`, `vitest related`, `pytest --testmon`).
2. **PR:** run the affected package/target set, and optionally prune it with ML or a time budget.
3. **Post-merge or on a schedule:** run the remaining tests or the full suite. Batch commits (Dropbox rollups, Google milestones) and bisect failures automatically.
4. **Periodically (e.g. every N builds or nightly):** run a full suite to rebuild dependency maps and catch RTS-tool bugs (OpenClover `fullRunEvery`, Azure TIA periodic full run).
5. **Shadow mode first:** run the selected set and then the full suite for a few weeks and compare, as Azure TIA recommends and as Develocity's simulator does. Measure recall of faulty changes and end-to-end time, not the selection ratio.
6. **Treat these files as "run everything" triggers:** lock files, root config, CI config, test infrastructure, and any file type the tool cannot map.

## (c) Tools per ecosystem (commands verified in the docs, Sept 2026)

### JS/TS
- **Jest** (https://jestjs.io/docs/cli)
  - `jest --findRelatedTests <files...>` — "useful for pre-commit hook integration".
  - `jest --changedSince=origin/main` — changes since a branch or commit.
  - `jest -o` / `--onlyChanged` — uncommitted changes. Requires git/hg and a *static dependency graph (no dynamic requires)*.
  - `jest --lastCommit`.
  - `--passWithNoTests` — for when nothing is selected.
- **Vitest** (https://vitest.dev/guide/cli)
  - `vitest --changed origin/main` (or `HEAD~1`) — tracks static imports only, not `import(filepath)`.
  - `vitest related --run src/a.ts src/b.ts`.
  - Config `forceRerunTriggers` defaults to `['**/package.json','**/vitest.config.*','**/vite.config.*']`. A match in the diff runs the whole suite.
- **Nx** (https://nx.dev/docs/features/ci-features/affected)
  - `nx affected -t test --base=origin/main --head=HEAD`, or set `NX_BASE` / `NX_HEAD`.
  - Uses the project graph. By default a lock-file change marks every project affected; `projectsAffectedByDependencyUpdates: "auto"` narrows this.
  - `nx graph --affected` visualises the affected set.
  - Set base to the last successful main commit.
- **Turborepo** (https://turborepo.dev/docs/reference/run)
  - `turbo run test --affected` — defaults to `--filter=...[main...HEAD]`. Override with `TURBO_SCM_BASE` / `TURBO_SCM_HEAD`.
  - `turbo run test --filter=...[HEAD^1]`.
  - Shallow clones can mark everything as changed; use `git fetch --filter=blob:none --depth=0`.
  - `futureFlags.affectedUsingTaskInputs` filters at task level using `inputs` globs.

### Python
- **pytest-testmon** (https://testmon.org/)
  - `pytest --testmon` — selects, and collects coverage-based dependencies into `.testmondata`.
  - `--testmon-noselect` — reorder only.
  - `--testmon-nocollect` — select without updating the data.
  - `--testmon-forceselect` — combine with `-k`/markers.
  - `--testmon-env` — separate data per environment.
  - Tracks Python code, environment variables, Python version and package versions. It does **not** track static or non-Python files or external services.
- **Pants** (https://www.pantsbuild.org/stable/docs/using-pants/advanced-target-selection)
  - `pants --changed-since=$(git merge-base HEAD origin/main) --changed-dependents=transitive test`.
  - Caveat: a lockfile or `python_requirements` change marks all users of *any* dependency as changed.
- **Research:** NameRTS (#23), Python only, no packaged tool verified.

### JVM
- **Ekstazi** (https://github.com/gliga/ekstazi): Maven/JUnit dynamic class-level RTS. The README lists tested Java 8/11/17/21 and extra JVM flags needed on newer JDKs (`-Djdk.attach.allowAttachSelf=true`; on 21, `-Djava.security.manager=allow`). I did not verify the exact pom snippet, because ekstazi.org/maven.html returned 404.
- **STARTS** (https://github.com/TestingResearchIllinois/starts): `mvn starts:starts` (select and run), `starts:select`, `starts:impacted`, `starts:diff`, `starts:clean`. Plugin `edu.illinois:starts-maven-plugin:1.4`, Java 8–15.
- **OpenClover:** `mvn clover:setup clover:optimize test clover:snapshot`. `fullRunEvery` defaults to 10.
- **Develocity PTS (Gradle):**
  ```kotlin
  tasks.test { useJUnitPlatform(); develocity.predictiveTestSelection { enabled.set(true) } }
  ```
  - Or run `./gradlew test -Dpts.enabled=true`.
  - `-Dpts.profile=FAST|STANDARD|CONSERVATIVE`.
  - `-Dpts.mode=REMAINING_TESTS`.
  - `mustRun { includeClasses.addAll("*.SanityTest") }`.
- **Develocity PTS (Maven):** Surefire `<properties><predictiveSelection><enabled>true</enabled>...` or `mvn -Dpts.enabled=true test`.
- **Launchable:** `launchable subset --build $B --confidence 90%` (or `--time 10m`, or `--target 20%`).

### .NET
- **Azure Pipelines TIA:** VSTest v2 task, **Run only impacted tests**.
  - `DisableTestImpactAnalysis=true` forces a full run.
  - `TIA_IncludePathFilters` scopes paths and ignored files (e.g. `!**\*.csproj`).
  - `TIA.UserMapFile` supplies a custom map.
  - Not supported on .NET Core.

### Go
- **Built-in test result cache** (`go help test`, go1.24):
  - `go test ./...` in package-list mode caches successful package results and prints `(cached)`.
  - A cache hit requires the same test binary and only "cacheable" flags (`-run`, `-short`, `-v`, `-timeout`, `-count` excluded, …).
  - Tests that open files in the module or read environment variables only hit the cache if those are unchanged.
  - `-count=1` disables the cache.
  - In effect this is package-level dynamic RTS that you get for free. Keep the Go build cache warm in CI to benefit.
- **Reverse dependencies for custom selection:** `go list -f '{{.ImportPath}} {{join .Deps " "}}' ./...` (the `Deps`, `TestImports` and `XTestImports` fields are documented in `go help list`), then invert the mapping. In Bazel repos, use Bazel (below).

### Rust
- **Stock cargo:** no test selection or test-result caching.
- **cargo-difftests** (https://github.com/dnbln/cargo-difftests): LLVM-coverage-based selection. Requires nightly and `cargo-binutils`.
  - `cargo difftests collect-profiling-data --compile-index --index-root=difftests-index-root`
  - `cargo difftests rerun-dirty-from-indexes --index-root=difftests-index-root`
  - Its documentation is marked "under construction", so treat it as experimental.
- **Research:** RustyRTS (#25). I found no public CLI.

### Monorepo / build systems
- **Bazel** (https://bazel.build/query/language)
  - `bazel query 'kind(test, rdeps(//..., //pkg:file.cc))'` — `rdeps(universe, x [, depth])`; the optional depth gives Google-style distance cutoffs.
  - Also `tests(x)`, and `allrdeps` under Sky Query.
- **bazel-diff** (https://github.com/Tinder/bazel-diff): hashes the target graph at two revisions and outputs impacted targets.
  - `bazel-diff generate-hashes -w $WS -b bazel start.json`
  - `bazel-diff get-impacted-targets -sh start.json -fh final.json -w $WS -b bazel -o impacted_targets.json`
  - Then `bazel test $(jq -r '.[]' impacted_targets.json)`.
- **Pants, Nx, Turborepo:** see above.
- **Chromium GN:** a `gn analyze` step in the commit queue, plus an exclusion list that forces full runs.

---

### Items I could not verify (flagged)
- Rothermel & Harrold 1996 and Orso et al. 2004: I did not get the full text. The four-criteria framework is confirmed by the Engström survey.
- Mozilla figures (85k files, 90 configurations, 70% / 99% reductions, two-week retraining) come from a fetch summary and should be checked against the post. The full author list is unverified.
- The Launchable flag for the remainder list, the Ekstazi Maven pom snippet, and a RustyRTS repository/CLI were not verified.
- BabelRTS and RustyRTS numbers come from search-engine abstract summaries, not the PDFs.
- I found no Uber or Spotify primary source specifically about test selection. The search results were about flaky tests and monorepo rollout, and a third-party claim about Spotify was not checked, so they are omitted.
