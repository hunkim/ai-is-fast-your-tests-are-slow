# 05 — Why fast feedback matters, and what else research says about test efficiency

Scope: developer feedback loops and DevEx, how waiting and interruptions affect developers, empirical CI studies (cost, duration, breakage), CI at industrial scale (Google, Uber, Meta/Facebook, Shopify), test-level economics (pyramid, sizes, trophy), adjacent efficiency techniques (flaky tests, mutation testing, coverage, property-based testing, fuzzing, snapshot and contract tests, test doubles), and the cost and energy of CI.

Method: every work below was located and fetched in September 2026. For PDFs I downloaded the file and extracted text with `pdftotext`, then grepped for the figures quoted here. **"Read: full text"** means I extracted and searched the full paper. **"Read: abstract only"** or **"secondary"** means I could not get past a paywall or a bot check (ACM Queue/CACM and Springer blocked automated access), so the figures come from the abstract or from a named secondary summary. I never solved or bypassed a bot check. Figures are quoted as the source states them. Where a number that is often cited could not be traced to the source, I say so.

**Works cited: 51.**

---

## Part A. Feedback loops, DevEx, and the human cost of waiting

### A1. Noda, Storey, Forsgren, Greiler — "DevEx: What Actually Drives Productivity" (2023)
- **Citation:** A. Noda, M.-A. Storey, N. Forsgren, M. Greiler. "DevEx: What Actually Drives Productivity: The developer-centric approach to measuring and improving productivity." *ACM Queue* 21(2), 2023. DOI 10.1145/3595878. Reprinted in *CACM*.
- **URLs located:** https://queue.acm.org/detail.cfm?id=3595878 (blocked by a bot check), https://dl.acm.org/doi/abs/10.1145/3595878 (403). Content read from https://getdx.com/report/devex-productivity/ and https://develocity.io/a-summary-devex-what-actually-drives-productivity-by-noda-et-al-2023/
- **Summary:** Proposes three core dimensions of developer experience: **feedback loops** ("the speed and quality of responses to developers' actions"), **cognitive load**, and **flow state**. These three cut across 25 sociotechnical factors identified in earlier work by Greiler, Storey and Noda. Measurement should combine perceptual (survey) measures with workflow (system) measures, rolled up into KPIs such as perceived productivity and satisfaction. The feedback-loop examples include build and test time, code-review turnaround and deployment lead time.
- **Quantitative:** The paper is a framework, not a controlled study. The DX report page says eBay's "Velocity Initiative" "improved feedback loops and reduced deployment lead times by 6x". This is a vendor case example, not peer-reviewed.
- **Takeaway:** Treat test and CI latency as one of three top-level DevEx levers. Measure it two ways: wall-clock time from the system, and how satisfied developers say they are with it.
- **Read:** secondary summaries plus abstract. The full text was blocked by a bot check.

### A2. Forsgren, Storey, Maddila, Zimmermann, Houck, Butler — "The SPACE of Developer Productivity" (2021)
- **Citation:** *ACM Queue* 19(1):20–48, 2021. DOI 10.1145/3454124. Also in *CACM* 64(6).
- **URLs fetched:** https://www.microsoft.com/en-us/research/publication/the-space-of-developer-productivity-theres-more-to-it-than-you-think/ and https://getdx.com/research/space-of-developer-productivity/
- **Summary:** Productivity "cannot be measured by a single metric or dimension." The five dimensions are Satisfaction and well-being, Performance, Activity, Communication and collaboration, and Efficiency and flow. "Efficiency and flow" is where handoffs, interruptions and waiting on systems (builds, tests, reviews) sit.
- **Quantitative:** None. This is a framework paper.
- **Takeaway:** Don't turn "tests per minute" into the goal. Pair the speed metric with a satisfaction measure and a quality measure, such as escaped defects or the change failure rate.
- **Read:** abstract only (the Queue full text was blocked).

### A3. Jaspan & Green — "Developer Productivity for Humans, Part 4: Build Latency, Predictability, and Developer Productivity" (2023)
- **Citation:** C. Jaspan, C. Green. *IEEE Software* 40(4):25–29, 2023. DOI 10.1109/MS.2023.3275268. IEEE Xplore document 10176199.
- **URLs fetched:** https://research.google/pubs/developer-productivity-for-humans-part-4-build-latency-predictability-and-developer-productivity/ (abstract) and https://newsletter.getdx.com/p/build-times-and-developer-productivity (detailed summary by Abi Noda, 14 Jul 2023)
- **Summary:** A Google study of how developers react to how long builds take and how predictable that time is. There were three parts:
  1. Log analysis of when developers go off-task during a build and when they come back.
  2. A two-week experience-sampling study asking how long developers expected a build to take and what they did while waiting.
  3. A blind experiment in which 15% of developers got faster build machines.
- **Quantitative (via the secondary summary):**
  - **No "magic number."** Every reduction in latency raised the chance of staying on task and returning sooner. Longer builds need proportionally larger cuts before the effect shows.
  - **Expectations drive behaviour.** Developers decide whether to switch tasks based on how long they *think* the build will take (for example, lunch for about 60 minutes, a code review for a few minutes). They often guess wrong.
  - **Blind experiment.** The median developer in the treatment group saw builds only "a few seconds" faster. Within three months, the treatment group had significantly higher self-reported productivity, velocity and satisfaction with build latency. It also ran about one more build per week, submitted about 24 more lines of code per week, and finished small and medium changes **11% faster in active time and 14% faster in wall-clock time**. The behaviour change only appeared in month three and held through a two-month extension.
- **Takeaway:** (i) Even seconds matter at Google scale. (ii) If you can't make a step faster, make it **predictable**: show an ETA and keep durations consistent. (iii) Tell developers when the tooling gets faster, because behaviour adapts slowly.
- **Uncertain:** A search snippet said "once a build is longer than about 10 minutes, the developer has shifted to another task." I could not trace that sentence to the paper itself, so treat it as unverified.
- **Read:** abstract plus a detailed secondary summary. The IEEE full text is paywalled.

### A4. Nielsen — "Response Times: The 3 Important Limits" (1993, web version)
- **Citation:** J. Nielsen, *Usability Engineering*, ch. 5, 1993. Builds on R. B. Miller (1968) and Card, Robertson & Mackinlay (1991).
- **URL fetched:** https://www.nngroup.com/articles/response-times-3-important-limits/
- **Summary and quantitative:**
  - **0.1 s** is the limit for feeling that the system reacts instantly.
  - **1.0 s** is "about the limit for the user's flow of thought to stay uninterrupted."
  - **10 s** is "about the limit for keeping the user's attention focused on the dialogue." Beyond that, users switch tasks, so show progress.
- **Takeaway:** These are the classic human thresholds for interactive loops. They map directly onto "test on save" (under 1 s), "run this file's tests" (under 10 s) and "anything longer means a context switch."
- **Read:** full text (web article).

### A5. Meyer, Fritz, Murphy, Zimmermann — "Software Developers' Perceptions of Productivity" (FSE 2014)
- **Citation:** FSE 2014, pp. 19–29. DOI 10.1145/2635868.2635892.
- **URL fetched:** https://thomas-zimmermann.com/publications/files/meyer-fse-2014.pdf
- **Summary:** A survey of 379 professional developers plus observation of 11. Developers feel a day was productive when they "complete many or big tasks without significant interruptions or context switches."
- **Quantitative:**
  - 50.4% (182) of survey respondents judged a productive week by "no or few interruptions and distractions."
  - Observed developers switched tasks **13.3 (±8.5) times per hour**, spending on average **6.2 (±3.3) minutes per task**.
  - They switched activities **47 (±19.8) times per hour**, about every 1.6 minutes.
- **Takeaway:** Developers already switch context constantly. A long test wait adds a forced switch on top, and it lands right at the "is my change correct?" moment.
- **Read:** full text.

### A6. Parnin & Rugaber — "Resumption strategies for interrupted programming tasks" (SQJ 2011, ICPC 2009)
- **Citation:** C. Parnin, S. Rugaber. *Software Quality Journal* 19:5–34, 2011. DOI 10.1007/s11219-010-9104-9.
- **URL fetched:** https://chrisparnin.me/pdf/parnin-sqj11.pdf
- **Summary:** Analysed 10,000 recorded IDE sessions from 86 programmers and surveyed 414. Resuming work after an interruption is a "frequent and persistent problem." Programmers rebuild context by navigating, not by editing straight away.
- **Quantitative:**
  - Only **10% of sessions resume programming activity within 1 minute** after an interruption.
  - Only **7% of sessions involve no navigation** to other locations before the first edit.
  - Sessions were split at breaks of 15 minutes or more. 98% of 4.5 million events were less than 1 minute apart.
- **Caution:** The popular claim that "it takes 10–15 minutes to resume" is not stated in this paper's abstract. Cite the 10% and 7% figures instead.
- **Takeaway:** Once a wait pushes a developer out of the task, getting back costs more than the wait itself. Keep the inner loop below the switch threshold.
- **Read:** full text.

### A7. Mark, Gudith, Klocke — "The Cost of Interrupted Work: More Speed and Stress" (CHI 2008)
- **Citation:** CHI 2008, pp. 107–110. DOI 10.1145/1357054.1357072.
- **URL fetched:** https://ics.uci.edu/~gmark/chi08-mark.pdf
- **Summary:** A controlled experiment. Interrupted participants finished tasks *faster* with no loss of quality. They made up for the interruptions by working faster, "but this comes at a price: experiencing more stress, higher frustration, time pressure and effort" (NASA-TLX workload was significantly higher).
- **Caution:** The widely quoted "23 minutes to get back on task" comes from other work by Mark and colleagues, not from this paper.
- **Takeaway:** The cost of interruptions shows up as stress and effort, which throughput metrics miss. This supports measuring satisfaction alongside speed.
- **Read:** full text.

### A8. Stripe — "The Developer Coefficient" (2018)
- **Citation:** Stripe / Harris Poll, September 2018.
- **URL fetched:** https://stripe.com/files/reports/the-developer-coefficient.pdf
- **Summary:** A survey of thousands of C-level executives and developers across six countries, estimating how much developer time is lost to inefficiency.
- **Quantitative:**
  - The average developer spends "more than 17 hours a week" on maintenance issues (debugging, refactoring), including about 4 hours a week on "bad code." That is about $85B a year.
  - The report estimates a **31.6% developer efficiency loss**, about $300B a year in lost global GDP.
  - 96% of executives rate developer productivity a high or medium priority.
- **Takeaway:** Useful for business-level framing. These are survey estimates, not measurements.
- **Read:** full text.

### A9. Fucci, Erdogmus, Turhan, Oivo, Juristo — "A Dissection of the Test-Driven Development Process" (TSE 2017)
- **Citation:** *IEEE TSE* 43(7), 2017. arXiv:1611.05994.
- **URL fetched:** https://arxiv.org/pdf/1611.05994
- **Summary:** 82 data points from 39 professionals. Quality and productivity were associated with **granularity** (short cycles) and **uniformity** (steady rhythm), not with writing the test first. The authors conclude that TDD's benefits may come from "fine-grained, steady steps that improve focus and flow."
- **Takeaway:** The benefit comes from short, even edit-test cycles. You only get those if a test run takes seconds.
- **Read:** abstract plus introduction (full text available).

### A10. Beller, Gousios, Panichella, Proksch, Amann, Zaidman — "Developer Testing in the IDE: Patterns, Beliefs, and Behavior" (TSE 2019)
- **Citation:** *IEEE TSE* 45(3):261–284, 2019.
- **URL fetched:** https://gousios.org/pub/developer-testing-in-IDE.pdf
- **Summary:** A field study of 2,443 engineers over 2.5 years in four IDEs (the WatchDog and FeedBag++ tools).
- **Quantitative:**
  - Half the developers do not test in the IDE, and most sessions end without running a test.
  - **50% of test executions finish within about half a second, and over 75% within five seconds.** Per IDE, the medians and 75th percentiles vary; Visual Studio is much slower, with a median of 10.9 s and 163 s at the 75th percentile.
  - A quarter of test cases cause three quarters of failures. **12% of tests show flaky behaviour.**
  - Developers spend about a quarter of their time on tests but believe they spend half.
- **Takeaway:** Local test runs that developers actually use are sub-second to seconds long. Anything slower gets skipped locally and pushed to CI.
- **Read:** full text.

---

## Part B. Empirical CI studies (open source)

### B1. Hilton, Tunnell, Huang, Marinov, Dig — "Usage, Costs, and Benefits of Continuous Integration in Open-Source Projects" (ASE 2016)
- **Citation:** ASE 2016, pp. 426–437. DOI 10.1145/2970276.2970358.
- **URL fetched:** https://ir.library.oregonstate.edu/downloads/s1784r12q
- **Summary:** Three methods: 34,544 GitHub projects, 1,529,291 Travis builds, and a survey of 442 developers.
- **Quantitative:**
  - 40.27% of projects use CI, and 70% of the most popular do.
  - **The average build time is "just under 500 seconds."** Passing builds run faster than failing or errored ones.
  - Projects using CI release **0.54 versions per month vs 0.24** without CI.
  - The **median PR is merged 1.6 hours faster** with CI.
  - Reasons for not using CI: developers not familiar with it (47%), no automated tests (44%), and "CI takes too long to set up" (17.65%).
  - The authors note that longer builds mean "more wasted developer time."
- **Takeaway:** CI pays for itself mainly by making integration faster and releases more frequent. Build time is the main recurring cost.
- **Read:** full text.

### B2. Hilton, Nelson, Tunnell, Marinov, Dig — "Trade-offs in Continuous Integration: Assurance, Security, and Flexibility" (ESEC/FSE 2017)
- **Citation:** ESEC/FSE 2017, pp. 197–207. DOI 10.1145/3106237.3106270.
- **URL fetched:** https://mir.cs.illinois.edu/marinov/publications/HiltonETAL17TradeOffsInCI.pdf
- **Summary:** Interviews (16), a broad survey (523 respondents, 95% from industry) and a focused survey at Pivotal. It names three trade-offs: **Assurance (speed vs certainty)**, security vs access, and flexibility vs simplicity.
- **Quantitative:**
  - When asked the **maximum acceptable CI build time, the most common answer was 10 minutes**, matching the XP and Fowler guideline.
  - **96% (focused) and 78% (broad) of respondents had actively worked to reduce build times.**
  - Barriers: "troubleshooting a CI build failure" (50% and 64%) and "overly long build times" (38% and 50%).
  - Pivotal builds typically took "greater than 60 minutes", against "5–10 minutes" in the broad survey.
  - Benefits cited: CI catches bugs earlier (75% and 86%), and CI makes developers less worried about breaking the build (72% and 82%).
  - Quote: "CI isn't very useful if it takes too long to get the feedback." Build times "slowly grow over time."
- **Takeaway:** 10 minutes is the practitioner consensus ceiling for blocking CI. Build time creeps up, so it needs an owner and a budget.
- **Read:** full text.

### B3. Vasilescu, Yu, Wang, Devanbu, Filkov — "Quality and Productivity Outcomes Relating to Continuous Integration in GitHub" (ESEC/FSE 2015)
- **Citation:** ESEC/FSE 2015, pp. 805–816. DOI 10.1145/2786805.2786850.
- **URL fetched:** https://cmustrudel.github.io/papers/fse15ci.pdf
- **Summary:** Regression models over 246 GitHub projects. CI "improves the productivity of project teams, who can integrate more outside contributions, without an observable diminishment in code quality." Core developers also found more bugs after adopting CI.
- **Takeaway:** CI lets teams take in more contributions without losing quality. That is the benefit side of the speed-vs-certainty trade-off.
- **Read:** full text (abstract and key sections).

### B4. Beller, Gousios, Zaidman — "Oops, My Tests Broke the Build: An Explorative Analysis of Travis CI with GitHub" (MSR 2017)
- **Citation:** MSR 2017, pp. 356–367. DOI 10.1109/MSR.2017.62.
- **URL fetched:** https://research.tudelft.nl/en/publications/oops-my-tests-broke-the-build-an-explorative-analysis-of-travis-c
- **Summary:** Analysed 2,640,825 Java and Ruby builds on Travis CI. **Testing is the single most important reason builds fail.** The language strongly affects how many tests run, how long they take and how often they fail. Running in multiple integration environments catches about **10% more failures**. CI testing is **not a substitute for local testing** in the IDE. The paper introduced the TravisTorrent dataset.
- **Takeaway:** Most red builds are test failures. Speeding up test feedback, and making it trustworthy, is the main CI lever.
- **Read:** abstract only (the PDF link redirected to HTML).

### B5. Ghaleb, da Costa, Zou — "An Empirical Study of the Long Duration of Continuous Integration Builds" (EMSE 2019)
- **Citation:** *Empirical Software Engineering* 24:2102–2139, 2019. DOI 10.1007/s10664-019-09695-9.
- **URL fetched:** https://danielcalencar.github.io/journal%20papers/2019/05/01/emse-19-taher.html (abstract; Springer redirected to a login)
- **Summary:** Mixed-effects models over 104,442 builds from 67 projects. Many projects have builds "that far exceed the acceptable build duration (i.e., 10 minutes)."
- **Quantitative and qualitative:**
  - Besides the obvious factors (project size, team size, config size, test density), **re-running failed commands several times is the factor most associated with long builds**.
  - Builds run faster when configured to **cache content that rarely changes** or to **finish as soon as the required jobs finish**. About **40% of projects don't use, or misuse, these configurations**.
  - Builds triggered on weekdays or during the daytime are more likely to be long, which suggests queueing for resources.
- **Takeaway:** Retries and poor cache configuration are the first things to audit.
- **Read:** abstract only.

### B6. Ghaleb et al. — "The Promise and Reality of Continuous Integration Caching: An Empirical Study of Travis CI Builds" (EASE 2026)
- **Citation:** T. A. Ghaleb et al. EASE '26. arXiv:2601.19146.
- **URL fetched:** https://arxiv.org/abs/2601.19146
- **Quantitative:**
  - Covers 513,384 builds from 1,279 projects. **Only 30% adopt CI caching.** When the authors opened PRs enabling caching, nearly half were accepted.
  - **About one third of projects see substantial build-time reductions.**
  - Cache uploads happen in 97% of builds, and **27% of projects hold stale cached artifacts**.
- **Takeaway:** Caching helps, but it isn't free. It needs maintenance and verification.
- **Read:** abstract.

### B7. Felidré, Furtado, da Costa, Cartaxo, Pinto — "Continuous Integration Theater" (ESEM 2019)
- **Citation:** ESEM 2019. arXiv:1907.01602.
- **URL fetched:** https://arxiv.org/pdf/1907.01602
- **Summary:** 1,270 Travis projects (534,417 build jobs) checked against CI "bad practices."
- **Quantitative:**
  - About 60% of projects commit infrequently.
  - Mean coverage was 78% for the 51 projects with coverage data.
  - **85% of projects have at least one broken build that took more than 4 days to fix.**
  - For most projects, builds stay within the **10-minute rule of thumb**. Among large projects, 43 of 261 (16%) had at least one build over 10 minutes.
  - The paper quotes Fowler: "every minute you reduce off the build time is a minute saved for each developer every time they commit."
- **Takeaway:** In open source, how long a build stays red is a bigger problem than how long it runs.
- **Read:** full text.

### B8. Widder, Hilton, Kästner, Vasilescu — "I'm Leaving You, Travis: A Continuous Integration Breakup Story" (MSR 2018)
- **Citation:** MSR 2018. DOI 10.1145/3196398.3196422.
- **URL fetched:** https://cmustrudel.github.io/papers/msr18ci.pdf
- **Summary:** 1,819 projects that left Travis. More complex configurations made abandonment *less* likely, and larger projects left more often. The paper discusses long build times as a push factor.
- **Takeaway:** CI tooling that doesn't fit a project's scale gets replaced. Build time is one of the pressures.
- **Read:** full text (skimmed).

---

## Part C. CI at industrial scale

### C1. Memon, Gao, Nguyen, Dhanda, Nickell, Siemborski, Micco — "Taming Google-Scale Continuous Testing" (ICSE-SEIP 2017)
- **Citation:** ICSE-SEIP 2017, pp. 233–242. DOI 10.1109/ICSE-SEIP.2017.16.
- **URL fetched:** https://research.google.com/pubs/archive/45861.pdf
- **Quantitative:**
  - In an average day, TAP (Google's Test Automation Platform) tests **13K+ projects, with 800K builds and 150 million test runs**.
  - Even so, Google cannot test each change on its own. It runs **"milestones" about every 45 minutes** at peak, with milestones of up to 4.2 million tests and **delays of up to 9 hours**.
  - Of 5.5 million affected tests over one month, **only 63K ever failed**. Per changelist, **91.3% of test targets passed and never failed**, and only **1.23% actually found a breakage**.
  - Code recently changed by more than 3 developers breaks more often.
- **Takeaway:** Most test executions carry no new information. Selection and prioritisation, based on history and on "distance" to the changed code, can cut latency without giving up much safety.
- **Read:** full text.

### C2. Winters, Manshreck, Wright (eds.) — *Software Engineering at Google* (O'Reilly 2020), ch. 11 "Testing Overview"
- **URL fetched:** https://abseil.io/resources/swe-book/html/ch11.html
- **Summary:** Defines **test sizes** by resource constraints:
  - **small**: single process, single thread, no sleep, no I/O, no network or disk
  - **medium**: one machine, localhost network only
  - **large**: multiple machines
  
  It also defines test *scope* separately.
- **Quantitative:**
  - The target mix is roughly **80% unit, 15% integration, 5% end-to-end**.
  - The flaky rate "hovers around 0.15%," which still means "thousands of flakes every day." "As you approach 1% flakiness, the tests begin to lose value."
  - More than 2 billion lines of code, and about 25 million lines changed per week.
- **Takeaway:** Enforce test speed and hermeticity **by construction** (size limits), not by asking people to be careful.
- **Read:** full text.

### C3. *Software Engineering at Google*, ch. 12 "Unit Testing", ch. 13 "Test Doubles", ch. 14 "Larger Testing"
- **URLs fetched:** https://abseil.io/resources/swe-book/html/ch12.html, https://abseil.io/resources/swe-book/html/ch13.html, https://abseil.io/resources/swe-book/html/ch14.html
- **Key points:**
  - **Ch. 12:** "Small tests are fast and deterministic, allowing developers to run them frequently … and get immediate feedback." The rule of thumb is **80% unit / 20% broader**.
  - **Ch. 13:** "A real implementation is preferred if it is fast, deterministic, and has simple dependencies." Otherwise use a fake, and use mocks as a last resort, because overused mocks make tests brittle and lock the API.
  - **Ch. 14:** Large tests have a "default timeout of 15 minutes or 1 hour." A developer-friendly test must be reliable, "fast enough to not interrupt the developer workflow," and scalable. With low-fidelity doubles (10% accurate each), the chance of a bug when components are combined is 99%. That is why a few larger tests are still needed.
- **Read:** full text.

### C4. *Software Engineering at Google*, ch. 23 "Continuous Integration"
- **URL fetched:** https://abseil.io/resources/swe-book/html/ch23.html
- **Quantitative:**
  - Google runs fast tests on presubmit and the rest post-submit. "A change that passes the presubmit has a very high likelihood (**95%+**) of passing the rest of the tests."
  - "The **average wait time to submit a change is around 11 minutes**, often run in the background."
  - "The difference in waiting time between a change that triggers 100 tests and one that triggers 1,000 can be tens of minutes on a busy day." This pushes engineers toward **smaller changes**.
  - Takeout case study: moving checks to presubmit **prevented 95% of broken servers** from bad configuration and **cut nightly deploy failures by 50%**. Moving end-to-end tests from nightly to every 2 hours cut the "culprit set" by **12×**.
  - "A 100% green rate on CI … is awfully expensive."
- **Takeaway:** Split the work. A fast, high-signal presubmit blocks the change; a slower post-submit runs asynchronously and bisects failures automatically. Moving checks earlier in the pipeline pays off even when they can't reach presubmit.
- **Read:** full text.

### C5. Micco — "Flaky Tests at Google and How We Mitigate Them" (Google Testing Blog, 27 May 2016)
- **URL fetched:** https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html
- **Quantitative:**
  - About **1.5% of all test runs** report a flaky result.
  - **Almost 16% of tests** have some level of flakiness.
  - **About 84% of observed pass→fail transitions involve a flaky test.**
  - Flakes are inserted at about the same rate they are fixed.
- **Note:** A WebFetch summary of this page wrongly said there were no numbers. I verified the figures by grepping the raw HTML.
- **Takeaway:** Flakiness is the main noise in CI signal. It costs reruns, wall-clock time and trust.
- **Read:** full text.

### C6. Wacker — "Just Say No to More End-to-End Tests" (Google Testing Blog, 22 Apr 2015)
- **URL fetched:** https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html
- **Summary:** A worked example of an E2E-heavy team losing days to slow, flaky, hard-to-debug failures. Recommends a pyramid of roughly **70% unit / 20% integration / 10% E2E**, while noting that the exact mix varies.
- **Takeaway:** E2E tests are expensive per bit of signal: slow, flaky and hard to localise. Keep them to a small number of critical journeys.
- **Read:** full text.

### C7. Ananthanarayanan et al. (Uber) — "Keeping Master Green at Scale" (EuroSys 2019)
- **Citation:** EuroSys 2019. DOI 10.1145/3302424.3303970.
- **URL fetched:** https://www.masoud.io/docs/eurosys19.pdf
- **Summary:** SubmitQueue keeps a monorepo mainline always green. It speculatively builds likely outcomes of pending changes in parallel, using a logistic-regression success model and a conflict analyzer.
- **Quantitative:**
  - With just 2 concurrent, potentially conflicting changes, there is a 5% chance of a real conflict; with 16 it rises to 40%.
  - Even changes only 1–10 hours stale have a 10–20% chance of breaking mainline.
  - A single queue at 1,000 changes a day and 30 minutes each gives the last change a turnaround of "over 20 days."
  - With enough workers (500 workers for 500 changes an hour), SubmitQueue's P50, P95 and P99 turnaround are within **1.2×** of an oracle. A single queue is 80–132× worse.
- **Takeaway:** At high merge rates, a serial "rebase-and-retest" queue can't keep up. You need batching or speculation, which is what merge queues provide.
- **Read:** full text.

### C8. GitHub Docs — "Managing a merge queue"
- **URL fetched:** https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue
- **Summary:** A merge queue "ensur[es] the branch is never broken by incompatible changes." It tests each PR against the latest target branch *plus the PRs ahead of it* in the queue, so authors don't have to keep rebasing and waiting for CI. It is aimed at branches with many merges per day.
- **Takeaway:** A product version of the SubmitQueue idea (C7) for teams not at Uber scale.
- **Read:** full text.

### C9. Machalica, Samylkin, Porth, Chandra (Facebook) — "Predictive Test Selection" (ICSE-SEIP 2019)
- **Citation:** ICSE-SEIP 2019, pp. 91–100. arXiv:1810.05286.
- **URL fetched:** https://arxiv.org/pdf/1810.05286
- **Quantitative:** A model trained on historical test outcomes **halves the total infrastructure cost of testing changes** while still reporting **over 95% of individual test failures and over 99.9% of faulty changes**. It explicitly accounts for flakiness.
- **Takeaway:** ML-based test selection is production-proven, but only at scale and with good historical data.
- **Read:** full text (abstract and introduction).

### C10. Fallahzadeh, Bavand, Rigby — "Accelerating Continuous Integration with Parallel Batch Testing" (ESEC/FSE 2023)
- **Citation:** ESEC/FSE 2023. arXiv:2308.13129.
- **URL fetched:** https://arxiv.org/pdf/2308.13129
- **Quantitative:**
  - Uses Ericsson data and 276 million Chrome test outcomes.
  - Parallelism has a **non-linear effect** on feedback time.
  - ConstantBatching (batch size 4) keeps the same average feedback time with **up to 72% fewer machines**. BatchAll does so with **up to 91% fewer**, reducing executions by up to 75%.
  - Prior work cited: batching with bisection pays off when **fewer than 40% of builds fail**.
- **Takeaway:** Batching with bisection is an underused alternative to test selection. Every test still runs, but at far lower cost.
- **Read:** abstract plus introduction.

### C11. Gallaba, Ewart, Junqueira, McIntosh — "Accelerating Continuous Integration by Caching Environments and Inferring Dependencies" (TSE 2022)
- **Citation:** *IEEE TSE* 48(6):2040–2052, 2022. DOI 10.1109/TSE.2020.3048335.
- **URL fetched:** https://rebels.cs.uwaterloo.ca/papers/tse2020_gallaba.pdf
- **Summary:** KOTINOS infers build dependencies without build specs, caches the environment and skips unaffected steps. It is in production in a commercial CI service. The paper motivates speed directly: "If CI feedback is too slow, developers may switch contexts to other tasks, which is known to be a costly operation."
- **Quantitative:**
  - Covers 14,364 builds from 10 projects. **87.9% of builds trigger at least one acceleration.**
  - **74% of accelerated builds are at least 2× faster.**
  - Overhead is under 1% median CPU, and build outcomes are not compromised.
- **Takeaway:** Caching the environment and skipping unaffected steps is a cheap, language-agnostic way to get about 2× faster CI.
- **Read:** full text.

### C12. Yin, Kashiwa, Gallaba, Alfadel, Kamei, McIntosh — "Developer-Applied Accelerations in Continuous Integration: A Detection Approach and Catalog of Patterns" (ASE 2024)
- **Citation:** ASE 2024. DOI 10.1145/3691620.3695533.
- **URL fetched:** https://rebels.cs.uwaterloo.ca/papers/ase2024_yin.pdf
- **Summary:** Detects hand-written CI shortcuts in 2,896 CircleCI jobs (F1 up to 0.64). Catalogues **14 purpose patterns, 16 mechanism patterns and 3 magnitude categories**. Examples: skip steps for `docs/` or `ui/` branches, skip on changes to `.yml` or `.json` only, and avoid redundant calls to costly external services.
- **Takeaway:** A checklist for auditing your own pipeline for waste.
- **Read:** full text (abstract and examples).

### C13. Zeng, Xiao, Lamothe, Hata, McIntosh — "A Mutation-Guided Assessment of Acceleration Approaches for Continuous Integration: An Empirical Study of YourBase" (MSR 2024)
- **URL fetched:** https://rebels.cs.uwaterloo.ca/papers/msr2024_zeng.pdf
- **Summary:** Uses mutation testing to check whether a commercial CI accelerator ever skips tests it should have run. The authors note that developers "prioritize correct build behaviour over efficiency," so an accelerator nobody trusts won't be adopted.
- **Takeaway:** Any selection or skip mechanism must be checked for *safety*, for example by injecting faults and confirming they are still caught.
- **Read:** introduction (partial).

### C14. Shopify Engineering — three posts on CI speed
- **Posts:**
  - (a) C. Bruckmayer, "Keeping Developers Happy with a Fast CI," 24 Feb 2021: https://shopify.engineering/faster-shopify-ci
  - (b) "Spark Joy by Running Fewer Tests," 11 Jun 2020: https://shopify.engineering/spark-joy-by-running-fewer-tests
  - (c) "Test Budget: Time Constrained CI Feedback," 7 Mar 2022: https://shopify.engineering/test-budget-time-constrained-ci-feedback
- **Quantitative:**
  - **(a)** The goal was **p95 under 10 minutes** for a monolith with more than 170,000 tests (growing 20–30% a year; more than 41 hours on one machine). p95 went from **45 to 18 minutes**. **68% of CI time was overhead before any test ran**: 31% preparing agents and 37% building dependencies. Container start at p95 went from 90 s to 25 s. Test selection raised builds that didn't run the full suite from 45% to over 60%, and stability from 88% to 97%. A few slow or hanging tests dominated the slowest builds.
  - **(b)** Selection has **99.94% recall**, selects about 60% of tests overall, and **40% of builds run fewer than 20% of tests**. It saves about 25% of compute. Only 0.06% of PRs with failing tests reached main. Developers ask for the full suite on under 2% of PRs.
  - **(c)** Prioritised tests under a time budget find failures after running only **70% of the selected suite**. With the failure-rate criterion, 80% of failures appear within 60% of the suite. Uneven CI times cause more context switching.
- **Takeaway:** Measure where CI time actually goes; overhead is often the biggest part. Target p95, not the average. Test selection with near-perfect recall is achievable.
- **Read:** full text (all three).

---

## Part D. Test levels, test economics, and flaky tests

### D1. Vocke — "The Practical Test Pyramid" (martinfowler.com, 26 Feb 2018)
- **URL fetched:** https://martinfowler.com/articles/practical-test-pyramid.html
- **Summary:** Restates Mike Cohn's pyramid (from *Succeeding with Agile*) in two rules: "write tests with different granularity" and "the more high-level you get the fewer tests you should have." Put "fast-running tests in the earlier stages" of the pipeline. Keep E2E tests to "a bare minimum," since they are "notoriously flaky." Use **consumer-driven contract tests** (such as Pact) instead of broad integration environments across services.
- **Takeaway:** Order the pipeline by speed and scope. Replace cross-service E2E tests with contract tests.
- **Read:** full text.

### D2. Dodds — "The Testing Trophy and Testing Classifications" (2021)
- **URL fetched:** https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications
- **Summary:** The layers, from bottom to top, are Static (types and lint), Unit, **Integration (the largest)**, and E2E. The guiding rule is "the more your tests resemble the way your software is used, the more confidence they can give you." The trophy's shape reflects confidence per unit of cost. Justin Searls is quoted: arguing about percentages "is a distraction."
- **Takeaway:** In frontend and JS stacks, cheap static checks plus fast integration tests (jsdom or component-level) often give the best confidence per second. The pyramid and the trophy agree that E2E tests should be few.
- **Read:** full text.

### D3. Luo, Hariri, Eloussi, Marinov — "An Empirical Analysis of Flaky Tests" (FSE 2014)
- **Citation:** FSE 2014, pp. 643–653. DOI 10.1145/2635868.2635920.
- **URL fetched:** https://mir.cs.illinois.edu/lamyaa/publications/fse14.pdf
- **Quantitative:**
  - Studied 201 flaky-test fixes in 51 projects. The top causes are **Async Wait (74 of 161 commits, 45%)**, Concurrency and Test Order Dependency.
  - **78% of flaky tests are flaky from the moment they are written.**
  - Almost all concurrency flakes involve only two threads.
- **Takeaway:** Ban fixed sleeps and wait on explicit conditions. Check new tests for flakiness when they are added, for example by running them many times or in shuffled order.
- **Read:** full text.

### D4. Eck, Palomba, Castelluccio, Bacchelli — "Understanding Flaky Tests: The Developer's Perspective" (ESEC/FSE 2019)
- **URL fetched:** https://arxiv.org/pdf/1907.01466
- **Summary:** 21 Mozilla developers classified 200 flaky tests they had fixed, and 121 developers answered a survey. Flakiness is "perceived as significant by the vast majority of developers." It affects resource allocation, scheduling and how reliable developers think the suite is. The hardest parts are reproducing the flake and finding its cause. The study found four causes not reported before, and these were among the costliest to fix.
- **Read:** full text (abstract and introduction).

---

## Part E. Adjacent test-efficiency techniques

### E1. Petrović & Ivanković — "State of Mutation Testing at Google" (ICSE-SEIP 2018)
- **Citation:** DOI 10.1145/3183519.3183521.
- **URL fetched:** https://research.google.com/pubs/archive/46584.pdf
- **Summary:** Diff-based, probabilistic mutation testing shown during code review. It skips uncovered lines and **"arid" lines** (logging, boilerplate) using AST heuristics tuned by developer feedback.
- **Quantitative:**
  - Covers 1,159,723 mutants in seven languages. **Over 87% of test runs against mutants kill the mutant.**
  - Survival rates range from 8.3% (TypeScript) to 14.7% (Python).
  - Suppressing arid lines raised the **usefulness of surfaced findings from 20% to 80%**, and **75% of findings with feedback were rated useful**.
  - The system processes about 30% of all diffs at Google.
- **Takeaway:** Mutation testing becomes affordable when it runs only on the diff, one mutant per line, and filters out noise.
- **Read:** full text.

### E2. Petrović, Ivanković, Fraser, Just — "Practical Mutation Testing at Scale: A view from Google" (IEEE TSE 2021)
- **URL fetched:** https://arxiv.org/pdf/2102.11378
- **Summary:** Mutation testing is incremental (changed code during review), filtered (few mutants per line and per review) and selected by how well each operator has performed historically. It is used by **more than 24,000 developers on more than 1,000 projects** at Google, where **more than 500 million tests run daily**. It produces "orders of magnitude fewer mutants."
- **Read:** abstract plus introduction.

### E3. Petrović, Ivanković, Fraser, Just — "Does Mutation Testing Improve Testing Practices?" (ICSE 2021)
- **URL fetched:** https://arxiv.org/pdf/2103.07189
- **Summary:** Almost 15 million mutants. Google runs "500,000,000 tests … per day, gate-keeping 60,000 code changes." Developers shown mutants **write more tests and improve their suites over time**, and mutants are **coupled with real high-priority faults**: a surviving mutant would have flagged the bug-introducing change.
- **Takeaway:** This is causal-leaning evidence that mutation feedback improves test quality, which coverage alone doesn't give.
- **Read:** abstract plus introduction.

### E4. Beller, Wong, Bader, Scott, Machalica, Chandra, Meijer (Facebook) — "What It Would Take to Use Mutation Testing in Industry—A Study at Facebook" (ICSE-SEIP 2021)
- **URL fetched:** https://arxiv.org/pdf/2010.13464
- **Quantitative:** Mutation operators were learned from real bug patterns. Across more than 15,000 mutants, **more than half survived** Facebook's unit, integration and system tests. Of 26 developers, 24 said the mutant revealed a testing gap, and **almost half would act on it**.
- **Takeaway:** Mutants modelled on real bugs find real gaps. How actionable they are is the bottleneck.
- **Read:** full text (abstract).

### E5. Ivanković, Petrović, Just, Fraser — "Code Coverage at Google" (ESEC/FSE 2019)
- **Citation:** DOI 10.1145/3338906.3340459, pp. 955–963.
- **URL fetched:** https://research.google/pubs/code-coverage-at-google/
- **Summary:** Coverage is computed for **one billion lines of code daily** in seven languages and made actionable at **changeset and code-review level**. The paper covers five years of adoption data and a survey (**512 responses from 3,000 developers**).
- **Takeaway:** Show coverage on the *diff*, in review, rather than as a project-wide target. Combine it with mutation testing (E1–E3), because covered is not the same as tested.
- **Read:** abstract only.

### E6. Goldstein, Cutler, Dickstein, Pierce, Head — "Property-Based Testing in Practice" (ICSE 2024)
- **Citation:** DOI 10.1145/3597503.3639581.
- **URL fetched:** https://harrisongoldste.in/papers/icse24-pbt-in-practice.pdf
- **Summary:** 30 interviews at Jane Street. PBT's strengths are "testing complex code and … increasing confidence beyond … conventional testing." Most use falls into a few high-leverage idioms, such as differential testing against a reference and round-trips. The weaknesses are that properties and generators are hard to write, and that it's hard to judge how effective they are. Hypothesis had about 500K users in 2021, about 4% of Python users.
- **Takeaway:** Use PBT for parsers, serialisers, data structures and "model vs implementation" checks. Keep example counts bounded in the inner loop and run deeper sweeps nightly.
- **Read:** full text (abstract and introduction).

### E7. Böhme & Falk — "Fuzzing: On the Exponential Cost of Vulnerability Discovery" (ESEC/FSE 2020)
- **URL fetched:** https://mboehme.github.io/paper/FSE20.EmpiricalLaw.pdf
- **Summary:** Based on more than 4 CPU-years of campaigns on nearly 300 programs. Finding the *same* bugs linearly faster takes linearly more machines: 2× machines finds them in half the time. Finding *linearly more* bugs in the same time takes **exponentially more machines**, for example "for every new bug … in 24 hours, we might need twice more machines."
- **Takeaway:** Fuzzing gives quickly diminishing returns on compute. Run short fuzz sessions in CI to catch regressions, and long campaigns asynchronously.
- **Read:** full text (abstract).

### E8. Ding & Le Goues — "An Empirical Study of OSS-Fuzz Bugs" (MSR 2021)
- **URL fetched:** https://squareslab.github.io/materials/DingOSSFuzz21.pdf
- **Quantitative:**
  - Covers 23,907 bugs in 316 projects. The **median time-to-detect a regression is 5 days**.
  - Flaky bugs take much longer to detect: a **median of 34 vs 4 days**.
  - Bugs still unfixed at collection time had been open a median of 437 days.
  - Timeouts and out-of-memory errors are a problem, and CVEs are rarely filed.
- **Read:** full text.

### E9. OSS-Fuzz README and "Large-Scale Empirical Analysis of Continuous Fuzzing: Insights from 1 Million Fuzzing Sessions" (arXiv 2510.16433, 2025)
- **URLs fetched:** https://raw.githubusercontent.com/google/oss-fuzz/master/README.md and https://arxiv.org/pdf/2510.16433
- **Quantitative:**
  - The README says: "As of May 2025, OSS-Fuzz has helped identify and fix over **13,000 vulnerabilities and 50,000 bugs** across 1,000 projects."
  - The arXiv study covers about 1.12 million fuzzing sessions from 878 projects. Many fuzzing bugs existed *before* continuous fuzzing was adopted, so detection is high early on. Coverage keeps rising over time, and coverage changes help detect bugs.
- **Read:** README full text; arXiv paper abstract.

### E10. Fujita, Kashiwa, Lin, Iida — "An Empirical Study on the Use of Snapshot Testing" (ICSME 2023)
- **URL fetched:** https://sdlab.naist.jp/en/post/fujita-icsme2023/
- **Quantitative:** Projects that use snapshot tests alongside unit tests have many more test cases than unit-only projects with similar unit-test counts. **8.2% of commits update snapshot files**, and code often changes together with snapshots.
- **Takeaway:** Snapshots are cheap to write but carry an update cost. A snapshot that gets updated automatically on every change is effectively not a test. Keep snapshots small and review them.
- **Read:** abstract (preliminary study).

---

## Part F. Delivery performance, cost and energy of CI

### F1. DORA — *Accelerate State of DevOps Report 2024*
- **URLs fetched:** https://dora.dev/research/2024/dora-report/ (summary) and https://getdx.com/blog/2024-dora-report/ (benchmark table, secondary)
- **Summary:** AI adoption raises individual productivity, flow and job satisfaction but "negatively impacts software delivery stability and throughput, reminding teams that fundamentals like **small batch sizes and robust testing** remain crucial."
- **Benchmarks (from the secondary DX table):** Elite performers have a lead time of **under one day**, deploy multiple times a day, have a 0–15% change failure rate, and recover in under an hour. Low performers have lead times of one to six months.
- **Takeaway:** In the AI era, the constraint on delivery is verification. Small batches only work if each batch gets fast test feedback.
- **Read:** DORA summary page full text; benchmark table from a secondary source.

### F2. Bouzenia & Pradel — "Resource Usage and Optimization Opportunities in Workflows of GitHub Actions" (ICSE 2024)
- **Citation:** ICSE 2024, pp. 268–279. DOI 10.1145/3597503.3623303.
- **URL fetched:** https://software-lab.org/publications/icse2024_workflows.pdf
- **Quantitative:**
  - Covers 1.3M runs and 3.7M jobs. CI costs about **$504 a year for an average paid-tier repository**.
  - **91.2% of resources go to testing and building**, triggered by PRs (50.7%), pushes (30.9%) and schedules (15.5%).
  - Caching is used by only 32.9% of paid-tier repos.
  - Simple platform changes, such as turning off scheduled workflows on inactive repos, would cut execution time by 1.1–31.6% on the affected workflows.
- **Read:** full text (abstract).

### F3. Perez, Lefeuvre, Degueule, Barais, Combemale — "Software Frugality in an Accelerating World: the Case of Continuous Integration" (arXiv 2410.15816, 2024)
- **URL fetched:** https://arxiv.org/pdf/2410.15816
- **Quantitative:** 838 workflows from 396 Java repos were reproduced and instrumented. The average pipeline run uses **about 10 Wh**, but the total **per project averages 22 kWh**, which is **about 10.5 kg CO₂**. The authors compare that to driving about 100 km.
- **Read:** abstract.

### F4. Saavedra et al. — "Environmental Impact of CI/CD Pipelines" (arXiv 2510.26413, 2025)
- **URL fetched:** https://arxiv.org/pdf/2510.26413
- **Quantitative:**
  - Covers 2.2M+ workflow runs from 18,000+ repositories. The 2024 GitHub Actions carbon footprint is estimated at **150.5 to 994.9 MTCO₂e**, with **456.9 MTCO₂e most likely**. The water footprint is estimated at 5,738.2 kL.
  - Recommendations: choose low-carbon runner regions, deactivate scheduled runs more strictly, and **reduce wasted computation**.
- **Read:** abstract.

---

## Synthesis

### (a) What latency thresholds matter for humans, and what waiting costs

**The thresholds, from fastest to slowest:**

| Band | Evidence | What happens to the developer |
|---|---|---|
| **≤ 0.1–1 s** | Nielsen/Miller (A4): 0.1 s feels instant; 1 s keeps "flow of thought … uninterrupted." WatchDog (A10): the median IDE test run is about 0.5 s. | Tests feel like part of editing, so short TDD-style cycles happen naturally (A9). |
| **≤ 10 s** | Nielsen (A4): 10 s is the limit of focused attention. WatchDog (A10): more than 75% of IDE test runs finish within 5 s. | Developers still wait on purpose. Past about 10 s they start doing something else. |
| **~1–10 min** | Meyer (A5): developers switch tasks about every 6 minutes anyway. Google (C4): average presubmit wait about 11 minutes, "often run in the background." Jaspan & Green (A3): what developers choose to do depends on the time they *expect* to wait. | A context switch is now likely. Getting back into the task is costly: only 10% of sessions resume within 1 minute (A6), and there is extra stress and effort (A7). |
| **≥ 10 min** | Hilton 2017 (B2): 10 minutes is the most common "maximum acceptable" CI build time, and 78–96% of teams actively worked to cut build time. Ghaleb (B5), CI Theater (B7) and Shopify's target (C14) use the same 10-minute ceiling. | Practitioners start calling it "too slow." PRs get batched, bigger changes pile up, and bisecting gets harder (C4, C7). |
| **hours** | TAP delays of up to 9 hours (C1). Takeout's nightly E2E runs (C4). | The culprit set grows. Moving to every 2 hours cut it 12× (C4). |

The Google experiment (A3) matters most here: **there is no cliff**. Every improvement helps, even a few seconds, and predictability counts nearly as much as raw speed.

**What it costs:**
- **People.** Stripe estimates a 31.6% efficiency loss overall (A8, survey). Google measured 11–14% faster completion of small and medium changes from a small speed-up (A3). Shopify found 68% of CI time was overhead before any test ran (C14).
- **Signal quality.** At Google, 84% of pass→fail transitions involve a flaky test (C5). 12% of tests in the field are flaky (A10). Re-running failed commands is the factor most associated with long builds (B5).
- **Compute and money.** About $504 a year per average paid GitHub Actions repo, with 91% of that spent on build and test (F2). At Google, only 1.23% of affected test runs find a breakage (C1).
- **Carbon.** About 22 kWh (about 10.5 kg CO₂) per Java project (F3). About 457 tCO₂e a year for GitHub Actions open-source usage (F4).

### (b) Practical targets and the evidence behind each

| Loop | Target | Evidence |
|---|---|---|
| Save → affected unit tests (inner loop) | **≤ 1 s typical, ≤ 10 s worst case** | Nielsen's 1 s and 10 s limits (A4). The observed median IDE run is about 0.5 s and 75% finish under 5 s (A10). Granularity and uniformity drive TDD's benefits (A9). |
| Full local suite before pushing | **≤ 1–2 min**, or a per-change selected subset | Below the typical task-switch interval of about 6 minutes (A5). Google's small-test constraints make this achievable by construction (C2). *This number is my inference; no paper states it.* |
| Pre-merge CI (blocking) | **p95 ≤ 10 min**; aim for ≤ 5 min at the median | The 10-minute consensus (B2, B5, B7). Shopify's explicit p95 target (C14). Google's presubmit averages about 11 minutes (C4). Use **p95**, because uneven CI times cause more context switching (C14c, A3). |
| Post-merge / broader suites | **≤ 1–2 h**, run asynchronously, auto-bisected | Takeout's 2-hour post-submit cut the culprit set 12× (C4). TAP-style milestone batching (C1). Batching with bisection (C10). |
| Merge throughput | **Merge queue** once many PRs land per day | Serial queues blow up (C7). GitHub merge queue (C8). |
| Flakiness | **< 1% of test runs**, and < 0.15% as a stretch goal | Google: tests "lose value" as flakiness approaches 1%; Google runs at about 0.15% (C2); earlier at 1.5% (C5). |
| Lead time for changes | **< 1 day** | DORA elite band (F1). |

### (c) Adjacent techniques worth adopting, and when

1. **Enforce test size by construction** (C2, C3): no network, disk or sleep in unit tests, and per-size timeouts. Adopt from day one. It is the cheapest way to keep the inner loop fast and to prevent flakes (D3: async waits cause 45% of flake fixes).
2. **Prefer real or fake implementations to mocks** (C3 ch. 13), and **contract tests instead of cross-service E2E** (D1). Adopt when you have more than one service or a heavily mocked API.
3. **Keep a pyramid or trophy shape, with E2E limited to critical journeys** (C2, C6, D1, D2). Always. Put static checks first (D2).
4. **Fix CI overhead before the tests themselves**: cache the environment, skip unaffected steps, finish early, and don't retry blindly (C11, C14a, B5, B6, C12). Adopt once CI goes over about 5 minutes. Expect about 2× from caching (C11). Keep caches maintained (B6: 27% of projects hold stale artifacts).
5. **Test selection or impact analysis** (C1, C9, C14b). Adopt once the full suite no longer fits the pre-merge budget. Require near-perfect recall (Shopify 99.94%; Facebook over 99.9% of faulty changes caught) and keep a full post-merge run as a safety net. Check safety by injecting faults (C13).
6. **Prioritise under a time budget and fail fast** (C14c): run historically failing or high-risk tests first. Cheap once you have test history.
7. **Batching with bisection, and merge queues** (C7, C8, C10). Adopt when merge volume is high and most builds pass (under about 40% failing).
8. **Quarantine and track flaky tests** (C5, D3, D4). Adopt as soon as flakes appear: check new tests many times on first commit (78% are flaky from birth) and quarantine automatically so they stop blocking merges.
9. **Diff-based mutation testing in code review** (E1–E4). Adopt when coverage is already high and you want to know whether tests actually *assert* anything. It is especially useful when tests are AI-generated. Keep it to the diff with arid-line filtering; usefulness went from 20% to 80%.
10. **Coverage on the diff, in review** (E5), not as a global target.
11. **Property-based testing** (E6) for complex logic, parsers and serialisers, and model-vs-implementation checks. Use small example counts in presubmit and larger sweeps nightly.
12. **Continuous fuzzing** (E7–E9) for anything that parses untrusted input. Run short sessions in CI to catch regressions and long campaigns asynchronously; the returns on compute fall off exponentially.
13. **Snapshot tests, used sparingly** (E10). They are cheap to add, but 8.2% of commits have to update them. Review diffs and keep them small.
14. **Make latency predictable and visible** (A3): show an ETA for CI, keep durations stable, and announce improvements. It costs little and has evidence behind it.
15. **Count energy and cost** (F2–F4). Deactivate idle scheduled workflows and cut redundant runs. The same waste-reduction steps make CI both faster and greener.

### Caveats
- Several key primary texts were read only as abstracts or through secondary summaries: DevEx (A1), SPACE (A2), Jaspan & Green (A3), Beller 2017 (B4), Ghaleb 2019 (B5) and Coverage at Google (E5). Their headline claims are consistent across sources, but some details, especially A3's percentages, come from Abi Noda's summary.
- The "10 minutes" CI threshold is a **practitioner norm** (XP, Fowler, and survey answers), not a measured cognitive threshold. The measured human thresholds (A4, A6, A10) point to seconds for the inner loop.
- Industrial numbers (Google, Facebook, Uber, Shopify) come from very large monorepos. The ratios, such as test selection recall and the share of time spent on overhead, are more transferable than the absolute numbers.
