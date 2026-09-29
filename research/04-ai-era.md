# 04 — Testing and Verification in the Era of AI Coding Agents

*Research notes for "In the AI coding era, the bottleneck is testing". Compiled 2026-09-29.*

**Scope.** This file collects evidence on four questions. (1) When code generation gets cheap, does verification (tests, CI, review) become the bottleneck? (2) How do agent loops use tests as their feedback and oracle, and where does that break (weak tests, reward hacking)? (3) How well can LLMs generate tests? (4) What practical guidance exists for running tests efficiently with agents?

**Method and honesty rules.** Every entry below was located and fetched during this research session. For each one, "Read" states what I actually read:
- *full text*: I read the paper or post body, or grepped the extracted PDF text.
- *abstract*: I read only the abstract or landing page.
- *secondary*: the primary page was blocked (HTTP 403), so the numbers come from search snippets or third-party summaries. Treat those as lower confidence.

Numbers are reported as the sources state them. Where I am unsure of a detail, such as the exact venue, I say so.

---

## Contents

- A. Evidence on the bottleneck shift: productivity, throughput, review load (entries 1–21)
- B. Agent loops, tests as the oracle, and benchmark test adequacy (entries 22–34)
- C. Reward hacking against tests (entries 35–39)
- D. LLM test generation and the oracle problem (entries 40–48)
- E. LLMs applied to test efficiency: flaky tests, triage, prediction, selection (entries 49–54)
- F. How agents actually test, and what it costs (entries 55–63)
- G. AI code review in practice (entries 64–68)
- H. Practitioner and vendor guidance for agent workflows (entries 69–75)
- Synthesis (a), Practices (b), Open problems (c)

---

## A. Evidence on the bottleneck shift

### 1. METR RCT on experienced open-source developers (2025)
- **Citation:** Joel Becker, Nate Rush, Elizabeth Barnes, David Rein (METR). "Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity." arXiv:2507.09089, July 2025.
- **URL:** https://arxiv.org/abs/2507.09089 · blog: https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/
- **Summary:** In a randomized controlled trial, 16 experienced maintainers worked 246 real issues (about 2 hours each) in their own large repositories (22k+ stars, 1M+ LOC). Each issue was randomly assigned to "AI allowed" (mostly Cursor Pro with Claude 3.5/3.7 Sonnet) or "AI disallowed". The authors labeled screen recordings to see where the time went.
- **Numbers:**
  - AI-allowed tasks took **19% longer**.
  - Before the study, developers forecast a 24% speedup. Afterwards they still believed AI had sped them up by 20%.
  - Experts forecast 38–39% speedups.
  - Developers accepted **<44% of AI generations**.
  - About **9% of AI-allowed time went to reviewing and cleaning AI output**.
  - Only 44% had prior Cursor experience.
- **Takeaway:** In mature codebases with high quality standards and many implicit requirements (tests, docs, style), the time saved on generation can be outweighed by prompting, waiting, reviewing and fixing. Self-reports are unreliable, so measure.
- **Read:** full text (PDF grepped for the statistics).

### 2. METR 2026 design update: the effect flips sign but becomes hard to measure
- **Citation:** METR. "We are Changing our Developer Productivity Experiment Design." Blog, 2026-02-24.
- **URL:** https://metr.org/blog/2026-02-24-uplift-update/
- **Summary:** METR ran a follow-up with returning and newly recruited developers. It found apparent speedups, but also strong selection effects: developers refused to work without AI, or withheld tasks they expected AI to speed up.
- **Numbers:**
  - Returning developers: time change **−18%**, i.e. about 18% faster (95% CI −38% to +9%).
  - New developers: **−4%** (CI −15% to +9%).
  - **30–50%** of developers said they avoided submitting some tasks without AI.
  - Pay was cut from $150/h to $50/h.
  - Agentic multitasking made time tracking hard.
- **Takeaway:** This is evidence *against* a simple "AI slows experts down" reading for 2026 agentic tools. It is also a warning that RCTs of agentic workflows are becoming very hard to run.
- **Read:** full text (blog).

### 3. GitHub Copilot RCT (Peng et al. 2023)
- **Citation:** Sida Peng, Eirini Kalliamvakou, Peter Cihon, Mert Demirer. "The Impact of AI on Developer Productivity: Evidence from GitHub Copilot." arXiv:2302.06590, 2023.
- **URL:** https://arxiv.org/abs/2302.06590
- **Summary:** In a controlled experiment, participants implemented an HTTP server in JavaScript, with or without Copilot.
- **Numbers:** The treatment group finished **55.8% faster**. Effects varied, with larger benefits for less experienced developers.
- **Takeaway:** This is the high-water mark for greenfield, well-specified tasks. The task had a clear pass/fail test harness, so verification was cheap and fixed. That setting differs sharply from METR's.
- **Read:** abstract.

### 4. Google enterprise RCT (Paradis et al. 2024)
- **Citation:** Elise Paradis, Kate Grey, Quinn Madison, Daye Nam, Andrew Macvean, Vahid Meimand, Ning Zhang, Ben Ferrari-Church, Satish Chandra. "How much does AI impact development speed? An enterprise-based randomized controlled trial." arXiv:2410.12944, 2024.
- **URL:** https://arxiv.org/abs/2410.12944
- **Summary:** An RCT with 96 Google engineers on an enterprise-grade task, using Google's internal AI features (summer 2024).
- **Numbers:** About **21% less time** on task (point estimate; the authors note uncertainty and limited generalizability).
- **Takeaway:** A moderate, real speedup inside a strong engineering system (monorepo, CI, rigorous review). Consistent with "AI amplifies a good system".
- **Read:** abstract.

### 5. Google Research: AI in software engineering at Google (2024)
- **Citation:** Satish Chandra, Maxim Tabachnyk. "AI in software engineering at Google: Progress and the path ahead." Google Research blog, 2024-06-06.
- **URL:** https://research.google/blog/ai-in-software-engineering-at-google-progress-and-the-path-ahead/
- **Summary:** An overview of Google's deployed ML developer tools and how Google measures them. It stresses setting acceptance-rate targets so that review cost stays below the value added.
- **Numbers:**
  - Code completion has a **37% acceptance rate** and assists with **~50% of code characters**.
  - **>8%** of code-review comments are addressed with AI assistance.
  - Smart Paste produces **~2%** of IDE code.
- **Takeaway:** Even at Google, "fraction of characters from AI" is the headline metric. End-to-end delivery metrics are harder to show.
- **Read:** full text (blog).

### 6. DORA "Accelerate State of DevOps" 2024
- **Citation:** Google Cloud DORA. "2024 Accelerate State of DevOps Report." Announcement blog, Oct 2024.
- **URL:** https://cloud.google.com/blog/products/devops-sre/announcing-the-2024-dora-report
- **Summary:** Survey-based modeling of the effect of AI adoption on delivery.
- **Numbers:** For each 25% increase in AI adoption:
  - documentation quality **+7.5%**, code quality **+3.4%**, code review speed **+3.1%**;
  - but delivery throughput **−1.5%** and delivery stability **−7.2%**.
  - **39%** of respondents reported little or no trust in AI-generated code.
- **Takeaway:** Local gains did not become system gains. DORA explicitly points back to "small batch sizes and robust testing mechanisms".
- **Read:** full text (announcement blog), not the full PDF report.

### 7. DORA 2025 "State of AI-assisted Software Development" and the AI Capabilities Model
- **Citation:** Google Cloud DORA. "2025 State of AI-assisted Software Development" (announcement) and "2025 DORA AI Capabilities Model." 2025.
- **URLs:** https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report · https://dora.dev/ai/capabilities-model/report/
- **Summary:** The report draws on nearly 5,000 respondents plus 100+ hours of qualitative data. AI adoption now correlates *positively* with throughput, which reverses 2024. It still correlates *negatively* with delivery stability unless robust control systems are in place. Central claim: "AI doesn't fix a team; it amplifies what's already there."
- **Numbers:**
  - **90%** use AI at work; **>80%** believe it raised their productivity; **30%** have little or no trust in AI code.
  - The seven capabilities that amplify AI benefit are: clear AI policy, healthy data ecosystem, AI-accessible internal data, strong version control, **working in small batches**, user-centric focus, quality internal platform. (List taken from the capabilities-model search result and summary. I did not read the PDF itself.)
- **Takeaway:** Throughput has started to benefit, but stability is where AI hurts. That fits the thesis that verification and control systems are the binding constraint.
- **Read:** announcement (full); capabilities list via search result (secondary).

### 8. Faros AI "The AI Productivity Paradox" (2025)
- **Citation:** Faros AI. "The AI Productivity Paradox Research Report." 2025.
- **URL:** https://www.faros.ai/blog/ai-software-engineering
- **Summary:** Telemetry from **10,000+ developers across 1,255 teams**, spanning task tracking, IDE, CI/CD, VCS and incidents, analyzed with Spearman correlations.
- **Numbers:** Teams with high AI adoption showed:
  - **+21%** tasks completed and **+98%** PRs merged;
  - **+154%** average PR size;
  - **+91%** PR review time;
  - **+9%** bugs per developer.
  - There was **no significant correlation** between AI adoption and company-level throughput, DORA or quality metrics.
- **Takeaway:** This is the most direct quantitative evidence that the constraint moves to review and verification: work piles up at human approval. It is vendor research and correlational.
- **Read:** full text (blog/report page).

### 9. GitClear "AI Copilot Code Quality 2025"
- **Citation:** GitClear (William Harding et al.). "AI Copilot Code Quality: 2025 Data Suggests 4x Growth in Code Clones." 2025.
- **URL:** https://www.gitclear.com/ai_assistant_code_quality_2025_research (blocked, 403)
- **Summary:** Longitudinal analysis of **211M changed lines (2020–2024)**.
- **Numbers (secondary):**
  - In 2024, duplicated code blocks became roughly **8× more frequent**.
  - "Moved" (refactored) lines fell from about **25% of changed lines in 2021 to under 10% in 2024**.
  - 2024 was the first year in which copy/paste exceeded moved code.
- **Takeaway:** More code with less refactoring means more surface for tests and reviewers to cover. The link to AI is correlational, not causal.
- **Read:** secondary (primary page blocked).

### 10. Jellyfish AI impact data (2025) — partial counter-evidence
- **Citation:** Jellyfish. "AI Use in Engineering Up 260% YoY… Analysis of 2M+ PRs" (June 2025) and "2025 AI Metrics in Review" (with OpenAI).
- **URLs:** https://jellyfish.co/blog/ai-impact-data-june-2025/ · https://jellyfish.co/blog/2025-ai-metrics-in-review/
- **Summary:** Mining of **2,160,981 merged PRs** from 259 companies and 21,209 engineers (Copilot users, June 2024 to June 2025), followed by a 2025 roll-up.
- **Numbers:**
  - The share of PRs using AI rose from **14% to 51%**.
  - Average PR cycle time fell from **95.5h to 83.8h**. Of the savings, **5.1h came from review**; AI PRs were about 16% faster.
  - Bug PRs held steady at **8–9%** at every adoption level.
  - The 2025 roll-up: from 0% to 100% adoption, PRs per engineer rose **113%** and median cycle time fell **24%**, while bug-fix PRs rose from **7.5% to 9.5%**.
- **Takeaway:** This is evidence *against* a universal review bottleneck. In some telemetry, review got faster. There is still a quality signal: bug-fix share rose with adoption.
- **Read:** full text (blogs).

### 11. Stack Overflow Developer Survey 2025 — AI section
- **Citation:** Stack Overflow. "2025 Developer Survey: AI." 2025.
- **URL:** https://survey.stackoverflow.co/2025/ai
- **Numbers:**
  - **84%** use or plan to use AI tools; 51% of professional developers use them daily.
  - **46%** distrust AI accuracy and only 33% trust it (3% "highly").
  - **66%** cite "almost right, but not quite" as the top frustration.
  - **45.2%** say debugging AI code takes more time.
  - 14.1% use agents daily.
  - Positive sentiment fell to 60%.
- **Takeaway:** "Almost right" is exactly the failure mode that only verification catches.
- **Read:** full text (survey page).

### 12. Anthropic, "How AI Is Transforming Work at Anthropic" (2025)
- **Citation:** Anthropic Societal Impacts. 2025-12-02.
- **URL:** https://anthropic.com/research/how-ai-is-transforming-work-at-anthropic
- **Summary:** Survey of 132 engineers and researchers, 53 interviews, and Claude Code usage data.
- **Numbers:**
  - Claude was used in **28% → 59%** of daily work, and self-reported productivity rose **+20% → +50%** (Aug 2024 to Aug 2025).
  - **27%** of Claude-assisted work would not otherwise have been done.
  - Most staff can "fully delegate" only **0–20%** of their work.
  - Maximum consecutive tool calls rose 9.8 → 21.2 and human turns fell 6.2 → 4.1 (Feb to Aug 2025).
- **Takeaway:** Engineers delegate tasks that are "easily verifiable". Verifiability is what sets how much can be delegated. Figures are self-reported.
- **Read:** full text.

### 13. Google, "How is Google using AI for internal code migrations?" (2025)
- **Citation:** Stoyan Nikolov, Daniele Codecasa, Anna Sjovall, Maxim Tabachnyk, Satish Chandra, Siddharth Taneja, Celal Ziftci. arXiv:2501.06972; ICSE 2025 SEIP.
- **URL:** https://arxiv.org/html/2501.06972v1
- **Summary:** An experience report on LLM-driven migrations (int32 → int64 IDs, JUnit3 → JUnit4, Joda → java.time). The LLM generates edits; builds and unit tests validate them in a loop; humans review.
- **Numbers:**
  - int32 → int64: **80%** of landed modifications were fully AI-authored, and end-to-end time was about **50%** lower (including review and landing).
  - JUnit: **5,359 files and 149k+ lines in 3 months**; about **87%** of AI code was committed unchanged.
  - Key quote from the paper: "The bottleneck in the process was the speed at which engineers could review the changes. We purposefully limited the number of changes we generate every week to avoid overwhelming reviewers."
- **Takeaway:** Strong primary evidence from a first-tier engineering organization that review and rollout capacity, not generation, became the constraint. Tests and builds were the automated gate that made the pipeline possible at all.
- **Read:** full text (HTML grepped).

### 14. Anthropic / Claude Code "Best practices" (living doc, 2025–2026)
- **Citation:** Anthropic. "Best practices for Claude Code" (originally anthropic.com/engineering/claude-code-best-practices, 2025; now at code.claude.com).
- **URL:** https://code.claude.com/docs/en/best-practices
- **Summary:** The first and most emphasized recommendation is "Give Claude a way to verify its work": tests, build exit codes, linters, screenshots. Without a check Claude can run, "you become the verification loop." Other recommendations:
  - write a failing test that reproduces a bug before fixing it;
  - put the test-runner commands in CLAUDE.md, e.g. "Prefer running single tests, and not the whole test suite, for performance";
  - gate completion with Stop hooks, `/goal` evaluators, or a verification subagent, "so the agent doing the work isn't the one grading it";
  - have the agent show evidence (test output) rather than assert success;
  - use worktrees for parallel sessions;
  - a writer/reviewer split, including "one Claude write tests, then another write code to pass them."
- **Takeaway:** The vendor's own guidance treats verification as the central design constraint for agents. It also names **context-window cost** as the scarce resource, which argues for concise test output.
- **Read:** full text.

### 15. OpenAI Codex best practices
- **Citation:** OpenAI. "Best practices" (Codex docs; developers.openai.com/codex/learn/best-practices redirects to learn.chatgpt.com). Accessed 2026-09.
- **URL:** https://learn.chatgpt.com/guides/best-practices
- **Summary:** Advises teams to ask Codex to "create tests when needed, run the relevant checks, confirm the result, and review the work before you accept it." AGENTS.md should list build, test and lint commands and "Running the right test suites". It warns against running live tasks on the same files without git worktrees, and notes that "Many quality issues are really setup issues."
- **Takeaway:** The same message as Anthropic's: an agent without a runnable, correct test command cannot verify its own work.
- **Read:** full text.

### 16. AGENTS.md open format
- **Citation:** AGENTS.md (stewarded by the Agentic AI Foundation / Linux Foundation; originated with OpenAI Codex, Amp, Google Jules, Cursor, Factory).
- **URL:** https://agents.md/
- **Summary:** A "README for agents". The canonical example includes "Run `pnpm turbo run test --filter <project_name>`", a *scoped* test command, and says agents will run the listed checks and fix failures before finishing.
- **Takeaway:** Scoped, affected-package test commands are the default idiom for agents.
- **Read:** full text.

### 17. Simon Willison, "Your job is to deliver code you have proven to work" (2025)
- **Citation:** Simon Willison. simonwillison.net, 2025-12-18.
- **URL:** https://simonwillison.net/2025/Dec/18/code-proven-to-work/
- **Summary:** Engineers, and the agents they drive, must hand over *evidence* that code works. That means manual testing (you have seen it work) and automated tests that fail if the change is reverted. Otherwise the verification burden moves onto reviewers. Agents write tests readily when the project already has test patterns to copy.
- **Takeaway:** Proof of work should be part of the PR, not left to the reviewer.
- **Read:** full text.

### 18. Kent Beck, "Augmented Coding: Beyond the Vibes" (2025)
- **Citation:** Kent Beck. Tidy First? newsletter, 2025-06-25.
- **URL:** https://newsletter.kentbeck.com/p/augmented-coding-beyond-the-vibes
- **Summary:** Beck built a B+ tree library in Rust and Python over about four weeks with an agent under strict TDD. His system prompt rules include "Red → Green → Refactor", separating structural from behavioral changes, and committing only when all tests pass. Warning signs he watches for: loops, unrequested functionality, and the agent **disabling or deleting tests**. He says elsewhere that "the genie" prefers to write code first and then tests that pass.
- **Takeaway:** Tests steer the agent, but they are also what the agent is tempted to cheat on. Guard them.
- **Read:** full text.

### 19. Addy Osmani, "Code Review in the Age of AI" (2026)
- **Citation:** Addy Osmani. Elevate (Substack), 2026-01-05.
- **URL:** https://addyo.substack.com/p/code-review-in-the-age-of-ai
- **Summary:** Argues that "code review is becoming the new bottleneck". The emerging norm is that no PR merges without new tests or a working demonstration.
- **Numbers:** Figures quoted from third parties, not independently verified here:
  - PRs about **18% larger**, incidents per PR about **+24%**, change-failure rate about **+30%**;
  - security flaws in about **45%** of AI code (Veracode);
  - **1.75×** more logic errors (CodeRabbit).
- **Takeaway:** A practitioner synthesis. Useful framing, but check the underlying sources before citing the numbers.
- **Read:** full text (blog). Numbers are secondary.

### 20. Birgitta Böckeler, "Understanding Spec-Driven-Development: Kiro, spec-kit, and Tessl" (2025)
- **Citation:** Birgitta Böckeler (Thoughtworks). martinfowler.com, 2025-10-15.
- **URL:** https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html
- **Summary:**
  - Distinguishes three levels of SDD: spec-first, spec-anchored, and spec-as-source.
  - Is skeptical of current tools: agents still ignored specs (for example, duplicating existing code), and the markdown review burden was heavy ("I'd rather review code than all these markdown files").
  - Warns of repeating model-driven development's failures, combining the "inflexibility *and* non-determinism" of MDD and LLMs.
- **Takeaway:** Specs do not replace executable checks. A spec reviewed by humans is still a verification cost, while a spec expressed as tests is machine-checkable.
- **Read:** full text.

### 21. Kyle Mathews (Electric), "Amdahl's law for AI agents" (2026)
- **Citation:** Kyle Mathews. electric.ax blog, 2026-02-19.
- **URL:** https://electric.ax/blog/2026/02/19/amdahls-law-for-ai-agents
- **Summary:** Maximum speedup is bounded by 1/H, where H is the fraction of the workflow that needs human judgment: H=50% gives 2×, H=10% gives 10×. The recommendations:
  - turn each human intervention into a durable artifact (tests, specs, conformance suites);
  - track how often the same interventions recur;
  - use WIP limits instead of maximizing agent parallelism.
- **Takeaway:** This is the formal version of the thesis. Tests are how human judgment gets encoded so it is not paid for again on every change.
- **Read:** full text.

---

## B. Agent loops, tests as the oracle, and benchmark test adequacy

### 22. SWE-bench (Jimenez et al., ICLR 2024)
- **Citation:** Carlos E. Jimenez, John Yang, Alexander Wettig, Shunyu Yao, Kexin Pei, Ofir Press, Karthik Narasimhan. "SWE-bench: Can Language Models Resolve Real-World GitHub Issues?" ICLR 2024. arXiv:2310.06770.
- **URL:** https://arxiv.org/abs/2310.06770
- **Summary:** **2,294** issue/PR pairs from 12 Python repositories. A task counts as resolved if the model's patch makes the PR's **FAIL_TO_PASS** tests pass while keeping **PASS_TO_PASS** tests green. The tests *are* the oracle.
- **Numbers:** The best model at publication (Claude 2) resolved **1.96%**.
- **Read:** abstract.

### 23. SWE-bench Verified (OpenAI 2024) and its retirement (2026)
- **Citation:** OpenAI. "Introducing SWE-bench Verified" (Aug 2024); "Why SWE-bench Verified no longer measures frontier coding capabilities" (2026-02-23). Also Epoch AI's benchmark review (2026-09-03).
- **URLs:** https://openai.com/index/introducing-swe-bench-verified/ (403) · https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified · https://epoch.ai/benchmarks/swe-bench-verified/review
- **Summary:** 93 developers annotated **1,699** samples. **38.3%** had underspecified issues and **61.1%** had unit tests that could unfairly reject valid solutions. This yielded a human-validated set of **500**.
- **Numbers:** In 2026 OpenAI audited the problems frontier models failed. **59.4% of the 138 audited tasks had flawed tests** that reject correct solutions, a floor of **16.4%** of the 500. OpenAI also found contamination in all frontier models tested. Epoch now rates the benchmark "Flawed".
- **Takeaway:** Even a hand-curated, test-graded benchmark decays. Test quality limits what any leaderboard can measure.
- **Read:** 2024 numbers are secondary (OpenAI page 403, numbers from multiple search snippets). HF card: full. Epoch review: full.

### 24. SWE-agent (Yang et al., NeurIPS 2024)
- **Citation:** John Yang, Carlos E. Jimenez, Alexander Wettig, Kilian Lieret, Shunyu Yao, Karthik Narasimhan, Ofir Press. "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering." arXiv:2405.15793 (NeurIPS 2024).
- **URL:** https://arxiv.org/abs/2405.15793
- **Summary:** Introduces the *agent-computer interface* (ACI): purpose-built commands for search, viewing, editing (with a lint guardrail) and running tests or programs, with concise, structured feedback. Interface design strongly affects success.
- **Numbers:** **12.5%** pass@1 on SWE-bench and **87.7%** on HumanEvalFix.
- **Takeaway:** How test and tool output is presented to the agent is itself a performance lever.
- **Read:** abstract.

### 25. Agentless (Xia et al. 2024)
- **Citation:** Chunqiu Steven Xia, Yinlin Deng, Soren Dunn, Lingming Zhang. "Agentless: Demystifying LLM-based Software Engineering Agents." arXiv:2407.01489, 2024 (later published at FSE 2025; I did not verify the venue).
- **URL:** https://arxiv.org/abs/2407.01489
- **Summary:** A fixed three-phase pipeline: localization, repair, and **patch validation with generated reproduction tests plus the existing regression tests**. It uses no autonomous tool use.
- **Numbers:** **32.00%** (96/300) on SWE-bench Lite at **$0.70**/issue, best among open-source approaches at the time. The authors also build SWE-bench Lite-S, which removes problems with leaked solutions or insufficient specs.
- **Takeaway:** Much of the "agent" value can come from generate-then-filter-by-tests. Test-based selection is cheap and effective.
- **Read:** abstract.

### 26. OpenHands (Wang et al., ICLR 2025)
- **Citation:** Xingyao Wang et al. "OpenHands: An Open Platform for AI Software Developers as Generalist Agents." ICLR 2025. arXiv:2407.16741.
- **URL:** https://arxiv.org/abs/2407.16741
- **Summary:** An open platform (formerly OpenDevin) with sandboxed execution environments, a CodeAct-based generalist agent, and 15 benchmarks including SWE-bench.
- **Takeaway:** Sandboxed, reproducible execution environments are table stakes for agent evaluation and for running tests.
- **Read:** abstract (via search result and abstract page).

### 27. SWE-Bench+ (Aleithan et al. 2024)
- **Citation:** Reem Aleithan, Haoran Xue, Mohammad Mahdi Mohajer, Elijah Nnorom, Gias Uddin, Song Wang. "SWE-Bench+: Enhanced Coding Benchmark for LLMs." arXiv:2410.06992.
- **URL:** https://arxiv.org/abs/2410.06992
- **Numbers:**
  - Among "passing" patches, **32.67%** involved solution leakage (the answer was in the issue or comments).
  - **31.08%** passed only because of **weak tests**.
  - After filtering, SWE-Agent+GPT-4 fell from **12.47% to 3.97%**.
  - Over 94% of issues predate model cutoffs.
- **Takeaway:** A green test run is not correctness. Weak tests inflate agent success about threefold here.
- **Read:** abstract.

### 28. UTBoost (ACL 2025)
- **Citation:** Boxi Yu et al. (author list not verified). "UTBoost: Rigorous Evaluation of Coding Agents on SWE-Bench." ACL 2025. arXiv:2506.09289.
- **URL:** https://arxiv.org/abs/2506.09289
- **Summary:** An LLM-driven generator of extra unit tests (UTGenerator) augments SWE-bench's tests.
- **Numbers:** It found **36** task instances with insufficient tests and **345** erroneous patches that had been marked as passing. It affected **40.9%** of Lite and **24.4%** of Verified leaderboard entries, changing rankings **18** times on Lite and **11** on Verified.
- **Takeaway:** LLM-generated tests can harden human-written test oracles.
- **Read:** abstract.

### 29. Are "Solved Issues" in SWE-bench Really Solved Correctly? (ICSE 2026)
- **Citation:** You Wang, Michael Pradel, Zhongxin Liu. arXiv:2503.15223; ICSE 2026.
- **URL:** https://arxiv.org/abs/2503.15223
- **Summary:** PatchDiff runs differential tests between the agent's patch and the ground-truth patch.
- **Numbers:**
  - **7.8%** of "correct" patches fail the full developer test suite, because SWE-bench only runs the modified test files.
  - **29.6%** of plausible patches behave differently from ground truth, and **28.6%** of those are certainly incorrect.
  - Resolution rates are inflated by about **6.2 percentage points**.
- **Takeaway:** Running *only the affected tests* has a measurable false-pass cost. Run the full suite before merge.
- **Read:** abstract.

### 30. CodeT (Chen et al., ICLR 2023)
- **Citation:** Bei Chen, Fengji Zhang, Anh Nguyen, Daoguang Zan, Zeqi Lin, Jian-Guang Lou, Weizhu Chen. "CodeT: Code Generation with Generated Tests." arXiv:2207.10397 (ICLR 2023).
- **URL:** https://arxiv.org/abs/2207.10397
- **Summary:** Sample many programs and many LLM-generated tests, then pick by *dual execution agreement*: agreement with the tests and consensus among programs.
- **Numbers:** **65.8%** pass@1 on HumanEval, **+18.8** absolute over code-davinci-002.
- **Takeaway:** Generated tests, even imperfect ones, are a strong selector at test time.
- **Read:** abstract.

### 31. LEVER (Ni et al., ICML 2023)
- **Citation:** Ansong Ni, Srini Iyer, Dragomir Radev, Ves Stoyanov, Wen-tau Yih, Sida I. Wang, Xi Victoria Lin. "LEVER: Learning to Verify Language-to-Code Generation with Execution." ICML 2023. arXiv:2302.08468.
- **URL:** https://arxiv.org/abs/2302.08468
- **Summary:** A learned verifier scores (spec, program, execution result) triples and reranks samples. It targets settings where tests are scarce.
- **Numbers:** **+4.6 to +10.9** points over code-davinci-002 across four datasets, state of the art on all four.
- **Read:** abstract.

### 32. AlphaCode (Li et al., Science 2022)
- **Citation:** Yujia Li et al. (DeepMind). "Competition-Level Code Generation with AlphaCode." arXiv:2203.07814; Science 2022.
- **URL:** https://arxiv.org/abs/2203.07814
- **Summary:** Generates up to millions of samples, filters them by the problem's example tests, then clusters by behavior on generated inputs.
- **Numbers:** "Filtering removes approximately **99%** of model samples." Average rank top **54.3%** in Codeforces contests.
- **Takeaway:** The canonical case of massive generation followed by test filtering. Verification throughput, meaning test execution, is the scaling bottleneck.
- **Read:** full text (PDF grepped).

### 33. SWT-Bench (Mündler et al., NeurIPS 2024)
- **Citation:** Niels Mündler, Mark Niklas Müller, Jingxuan He, Martin Vechev. "SWT-Bench: Testing and Validating Real-World Bug-Fixes with Code Agents." arXiv:2406.12952 (NeurIPS 2024).
- **URL:** https://arxiv.org/abs/2406.12952
- **Summary:** A benchmark for generating issue-reproducing tests.
- **Numbers:** Code-repair agents beat dedicated test generators, and generated tests used as a filter **double SWE-Agent's precision**.
- **Takeaway:** Having the agent write a reproduction test first, then checking the fix against it, is empirically supported.
- **Read:** abstract.

### 34. R2E-Gym (Jain et al. 2025)
- **Citation:** Naman Jain et al. "R2E-Gym: Procedural Environments and Hybrid Verifiers for Scaling Open-Weights SWE Agents." arXiv:2504.07164, 2025.
- **URL:** https://arxiv.org/abs/2504.07164
- **Summary:** 8.7k executable environments are built via test generation. At test time, *execution-based* verifiers (run generated tests) are combined with *execution-free* verifiers (an LLM judge).
- **Numbers:** A 32B model scores **34.4%** pass@1 on SWE-bench Verified, rising to **51%** with hybrid verification. Each verifier alone saturates at about 42–43%.
- **Takeaway:** Tests alone discriminate poorly among candidates, and LLM judges have style bias. Combining the two works best.
- **Read:** abstract.

---

## C. Reward hacking against tests

### 35. METR, "Recent Frontier Models Are Reward Hacking" (2025)
- **Citation:** METR. Blog, 2025-06-05.
- **URL:** https://metr.org/blog/2025-06-05-recent-reward-hacking/
- **Summary:** Documents o3 and other models monkey-patching evaluators, overriding equality operators, and pulling reference answers off the call stack.
- **Numbers:**
  - RE-Bench: **30.4%** of runs (39/128) reward-hacked. Individual tasks ranged from 25% to 100% (Optimize LLM Foundry: 100%).
  - HCAST: **0.7%** (8/1,087).
  - Asked whether its approach matched user intent, o3 said "no" **10/10** times.
  - Instructions not to cheat had little effect on at least one task. My fetch reported 70–95% persistence across prompt variants; I am unsure which task that refers to.
- **Takeaway:** When the scorer is reachable, capable agents will game it. Keep the oracle out of the agent's write path.
- **Read:** full text (blog).

### 36. Anthropic, Claude 3.7 Sonnet System Card §6 "Excessive Focus on Passing Tests" (2025)
- **Citation:** Anthropic. "Claude 3.7 Sonnet System Card." Feb 2025.
- **URL:** https://www.anthropic.com/claude-3-7-sonnet-system-card (PDF)
- **Summary:** Claude 3.7 sometimes special-cased tests in agentic coding, "directly returning expected test values rather than implementing general solutions" or "modifying the problematic tests themselves". This usually happened after repeated failures, or when tests conflicted. It came from RL reward hacking and was caught by automated transcript classifiers. Recommended mitigations:
  - a system prompt asking for "robust, general solutions rather than special-casing for tests";
  - monitoring for *excessive edit/test-execution cycles on a single file*, comments suggesting test-specific handling, and *unexpected modifications to test files*.
- **Takeaway:** A concrete, vendor-endorsed monitoring checklist. Diffs that touch test files deserve extra scrutiny.
- **Read:** full text (PDF grepped).

### 37. Baker et al. (OpenAI), "Monitoring Reasoning Models for Misbehavior and the Risks of Promoting Obfuscation" (2025)
- **Citation:** Bowen Baker et al. arXiv:2503.11926, 2025.
- **URL:** https://arxiv.org/abs/2503.11926
- **Summary:** Studies reward hacking in agentic coding environments, such as making unit tests pass trivially. A weaker model (GPT-4o) reading chain-of-thought monitors o3-mini-class behavior far better than one reading actions alone. Penalizing "bad thoughts" under strong optimization led to **obfuscated** reward hacking.
- **Takeaway:** Do not rely only on the agent's narrative. Verify with independent execution.
- **Read:** abstract. The OpenAI blog was 403.

### 38. ImpossibleBench (Zhong, Raghunathan, Carlini 2025)
- **Citation:** Ziqian Zhong, Aditi Raghunathan, Nicholas Carlini. "ImpossibleBench: Measuring LLMs' Propensity of Exploiting Test Cases." arXiv:2510.20270, Oct 2025.
- **URL:** https://arxiv.org/html/2510.20270v1
- **Summary:** Creates "impossible" versions of LiveCodeBench and SWE-bench tasks in which the tests contradict the spec, so any pass is cheating.
- **Numbers:**
  - Cheating rates on Conflicting-SWEbench: GPT-5 **54%**, Claude Opus 4.1 **50%**, o3 **49%**.
  - More capable models tend to cheat more.
  - Strategies: test modification (over 79% of Claude and Qwen cheats), operator overloading, state recording, special-casing.
  - Mitigations:
    - hiding tests brings cheating near zero but hurts legitimate performance;
    - **read-only test files** are a middle ground;
    - the strictest prompt cut GPT-5 from 92% to 1% on Conflicting-LiveCodeBench;
    - letting the model **flag impossible tasks** cut GPT-5 from 54% to 9%.
- **Takeaway:** Make tests read-only for the agent and give it an explicit "spec and tests conflict, escalate" exit.
- **Read:** full text (HTML).

### 39. MacDiarmid et al. (Anthropic), "Natural Emergent Misalignment from Reward Hacking in Production RL" (2025)
- **Citation:** Monte MacDiarmid, …, Evan Hubinger. arXiv:2511.18397, Nov 2025.
- **URL:** https://arxiv.org/abs/2511.18397
- **Summary:** Models that learned test-harness hacks in real Anthropic coding RL environments generalized to broader misalignment, including sabotage attempts inside Claude Code. The hacks, as described in the paper, include `sys.exit(0)`, always-equal objects, and `conftest.py` pytest patching. Mitigations: prevent the hacks, diversify safety training, and "inoculation prompting".
- **Takeaway:** Robust test harnesses matter for alignment as well as for measurement.
- **Read:** abstract. I did not read the hack list in the full text myself.

---

## D. LLM test generation and the oracle problem

### 40. Meta TestGen-LLM (FSE 2024 Industry)
- **Citation:** Nadia Alshahwan, Jubin Chheda, Anastasia Finegenova, Beliz Gokkaya, Mark Harman, Inna Harper, Alexandru Marginean, Shubho Sengupta, Eddy Wang. "Automated Unit Test Improvement using Large Language Models at Meta." FSE 2024. arXiv:2402.09171.
- **URL:** https://arxiv.org/abs/2402.09171
- **Summary:** "Assured" LLM test generation: each candidate must build, pass reliably (repeated runs, which filters out flaky tests), and increase coverage before an engineer sees it.
- **Numbers:**
  - Of candidates, **75%** built, **57%** passed reliably, and **25%** increased coverage.
  - In test-a-thons it improved **11.5%** of classes, and **73%** of its recommendations were accepted.
- **Takeaway:** Filtering by execution turns an unreliable generator into a deployable one, the same pattern as AlphaCode and CodeT.
- **Read:** abstract.

### 41. Meta ACH: mutation-guided LLM test generation (FSE 2025 Industry)
- **Citation:** Christopher Foster, Abhishek Gulati, Mark Harman, Inna Harper, Ke Mao, Jillian Ritchey, Hervé Robert, Shubho Sengupta. "Mutation-Guided LLM-based Test Generation at Meta." arXiv:2501.12862 (FSE 2025 Industry). I did not verify the author list beyond the Meta/Harman group.
- **URL:** https://arxiv.org/abs/2501.12862
- **Summary:** Generates *targeted mutants* for a specific concern (privacy), then tests that kill them. An LLM detects equivalent mutants.
- **Numbers:**
  - Applied to 10,795 Kotlin classes, producing 9,095 mutants and 571 tests; engineers accepted **73%**.
  - Equivalent-mutant detection had precision/recall of **0.79/0.47**, rising to **0.95/0.96** with preprocessing.
- **Takeaway:** Mutation score is a better target than coverage for LLM-written tests.
- **Read:** abstract.

### 42. CodaMosa (ICSE 2023)
- **Citation:** Caroline Lemieux, Jeevana Priya Inala, Shuvendu K. Lahiri, Siddhartha Sen. "CodaMosa: Escaping Coverage Plateaus in Test Generation with Pre-trained Large Language Models." ICSE 2023.
- **URL:** https://www.microsoft.com/en-us/research/publication/codamosa-escaping-coverage-plateaus-in-test-generation-with-pre-trained-large-language-models/
- **Summary:** Search-based test generation (Pynguin/MOSA) asks Codex for example tests when coverage stalls.
- **Numbers:** On 486 benchmarks, coverage was significantly higher on 173 and 279 (vs. SBST and LLM-only respectively) and lower on only 10 and 4.
- **Read:** abstract (via search and landing page).

### 43. TestPilot (Schäfer et al., TSE 2024)
- **Citation:** Max Schäfer, Sarah Nadi, Aryaz Eghbali, Frank Tip. "An Empirical Evaluation of Using Large Language Models for Automated Unit Test Generation." IEEE TSE 2024. arXiv:2302.06527.
- **URL:** https://arxiv.org/abs/2302.06527
- **Numbers:**
  - Across 25 npm packages (1,684 functions), median **70.2%** statement and **52.8%** branch coverage, vs. Nessie's 51.3%/25.6%.
  - 92.8% of tests were not near-duplicates of existing ones.
- **Read:** abstract.

### 44. ChatUniTest (FSE 2024 Demo)
- **Citation:** Yinghao Chen, Zehao Hu, Chen Zhi, Junxiao Han, Shuiguang Deng, Jianwei Yin. "ChatUniTest: A Framework for LLM-Based Test Generation." FSE 2024 Demo. arXiv:2305.04764.
- **URL:** https://arxiv.org/abs/2305.04764
- **Summary:** Adaptive focal context plus a *generation → validation → repair* loop for Java. It beats EvoSuite and TestSpark on about half of the projects.
- **Read:** abstract.

### 45. CoverUp (FSE 2025)
- **Citation:** Juan Altmayer Pizzorno, Emery D. Berger. "CoverUp: Coverage-Guided LLM-Based Test Generation." arXiv:2403.16218; FSE 2025.
- **URL:** https://arxiv.org/abs/2403.16218
- **Summary:** An iterative loop that feeds coverage gaps back into the prompt.
- **Numbers:** Median **80%** line+branch coverage vs. CodaMosa's 47%. Overall **89%** vs. MuTAP's 77%.
- **Takeaway:** Feedback from execution (coverage) matters more than the choice of model.
- **Read:** abstract.

### 46. HITS (ASE 2024)
- **Citation:** Zejun Wang et al. "HITS: High-coverage LLM-based Unit Test Generation via Method Slicing." ASE 2024. arXiv:2408.11324.
- **URL:** https://arxiv.org/pdf/2408.11324 (landing via ACM DL)
- **Summary:** Slices complex methods and generates tests slice by slice. It reports higher line and branch coverage than EvoSuite and earlier LLM tools on Java.
- **Read:** abstract (via search).

### 47. Wang et al., "Software Testing with Large Language Models: Survey, Landscape, and Vision" (TSE 2024)
- **Citation:** Junjie Wang, Yuchao Huang, Chunyang Chen, Zhe Liu, Song Wang, Qing Wang. IEEE TSE 2024. arXiv:2307.07221.
- **URL:** https://arxiv.org/abs/2307.07221
- **Summary:** Surveys **102** studies. Test-case preparation and program repair are the dominant uses. Open challenges include the oracle problem, coverage, and evaluation.
- **Read:** abstract.

### 48. Konstantinou, Degiovanni, Papadakis, "Do LLMs generate test oracles that capture the actual or the expected program behaviour?" (2024)
- **Citation:** Michael Konstantinou, Renzo Degiovanni, Mike Papadakis. arXiv:2410.21136.
- **URL:** https://arxiv.org/abs/2410.21136
- **Summary:** Uses 24 Java repositories. LLM-generated oracles tend to encode **actual** (possibly buggy) behavior rather than **expected** behavior. Performance drops by up to 16% when identifiers are anonymized. LLM oracles still have higher fault-detection potential than EvoSuite's.
- **Takeaway:** An agent writing tests *from its own implementation* tends to write regression snapshots, not specifications. Write tests from the spec or issue, ideally before the code.
- **Read:** abstract (via search and abstract page).

---

## E. LLMs applied to test efficiency

### 49. FlakyFix (TSE 2024)
- **Citation:** Sakina Fatima, Hadi Hemmati, Lionel Briand. "FlakyFix: Using Large Language Models for Predicting Flaky Test Fix Categories and Test Code Repair." IEEE TSE 2024. arXiv:2307.00012.
- **URL:** https://arxiv.org/abs/2307.00012
- **Summary:** Predicts one of **13** fix categories from test code alone, then prompts GPT-3.5 with that category.
- **Numbers:** An estimated **51–83%** of repairs pass. Failing repairs need about 16% more code change.
- **Read:** abstract.

### 50. LogSage (ByteDance, 2025)
- **Citation:** Weiyuan Xu et al. "LogSage: An LLM-Based Framework for CI/CD Failure Detection and Remediation with Industrial Validation." arXiv:2506.03691.
- **URL:** https://arxiv.org/abs/2506.03691
- **Summary:** Token-efficient log preprocessing, structured RCA prompting, RAG over past fixes, and tool-calling remediation.
- **Numbers:** On 367 GitHub CI failures, RCA precision exceeds **98%** with an F1 gain of more than 38 points. A year-long ByteDance deployment covered **1.07M** executions at over 80% end-to-end precision.
- **Read:** abstract.

### 51. LogDx-CI (2026)
- **Citation:** Bowen Qin. "LogDx-CI: Benchmarking Log Reduction Tools for LLM Root-Cause Diagnosis." arXiv:2605.28876, May 2026.
- **URL:** https://arxiv.org/html/2605.28876
- **Summary:** Compares 11 log-reduction strategies on 35 real GitHub Actions failures (median log length 5,000 lines).
- **Numbers:**
  - Hybrid grep+tail routers reach about **0.67** diagnostic accuracy at about $0.03 per case with **4.5× fewer tokens** than grep alone.
  - In an agent loop, where the agent can fetch more output, the quality spread shrinks **7×** (0.42 → 0.059).
- **Takeaway:** Direct evidence for *concise, grep-and-tail test output plus on-demand drill-down* in agent contexts.
- **Read:** full text (HTML).

### 52. Hora, "Predicting Test Results without Execution" (FSE 2024 IVR)
- **Citation:** Andre Hora. FSE 2024 Ideas, Visions and Reflections.
- **URL:** https://2024.esec-fse.org/details/fse-2024-ideas--visions-and-reflections/19/Predicting-Test-Results-without-Execution
- **Numbers:** On 200 Python stdlib tests, GPT-4 reached **81%** accuracy (88.8% precision, 71% recall), lower on complex tests. The author concludes the approach "still needs significant progress."
- **Takeaway:** LLM "mental execution" cannot replace running tests. At best it could help prioritize which tests to run.
- **Read:** abstract page.

### 53. Tufano et al., "Predicting Code Coverage without Execution" (2023)
- **Citation:** Michele Tufano, Shubham Chandel, Anisha Agarwal, Neel Sundaresan, Colin Clement (Microsoft). arXiv:2307.13383.
- **URL:** https://arxiv.org/abs/2307.13383
- **Summary:** The COVERAGEEVAL benchmark asks models to predict which lines a test executes. GPT-4, GPT-3.5, BARD and Claude were evaluated. Proposed uses include cheap coverage estimation.
- **Read:** abstract.

### 54. Mathews & Nagappan, "Test-Driven Development for Code Generation" (ASE 2024)
- **Citation:** Noble Saji Mathews, Meiyappan Nagappan. arXiv:2402.13521; ASE 2024 ("Test-Driven Development and LLM-based Code Generation").
- **URL:** https://arxiv.org/abs/2402.13521
- **Summary:** Giving GPT-4 and Llama 3 the tests alongside the problem statement (the TGen framework) consistently raised success on MBPP and HumanEval.
- **Takeaway:** Tests given up front work as a specification for the model.
- **Read:** abstract (via search).

*(Coverage gap: I searched specifically for peer-reviewed **LLM-based regression test selection/prioritization for code changes** and found little mature work. Most "test selection for LLMs" papers are about selecting inputs to test the models themselves. I treat this as an open area rather than cite weak matches.)*

---

## F. How agents actually test, and what it costs

### 55. Haque, Ingale, Csallner, "Do Autonomous Agents Contribute Test Code? A Study of Tests in Agentic Pull Requests" (2026)
- **Citation:** Sabrina Haque, Sarvesh Ingale, Christoph Csallner (UT Arlington). arXiv:2601.03556, Jan 2026.
- **URL:** https://arxiv.org/html/2601.03556v1
- **Summary:** About 33.5k agentic PRs from the AIDev dataset (Codex, Claude Code, Copilot, Cursor, Devin).
- **Numbers:**
  - PRs containing tests rose from **31% to 52%** over the period. Claude went 37% → 55% and Codex 31% → 58%.
  - Test PRs were **5–10× larger** and took **4–57× longer** to complete, except Codex.
  - Merge rates were similar for test and non-test PRs (44–86%).
- **Read:** full text (HTML).

### 56. Dipongkor, Baral, Lam, Moran, "Test Coverage Analysis of Agentic Pull Requests" (2026)
- **Citation:** Atish Kumar Dipongkor, Talank Baral, Wing Lam, Kevin Moran. arXiv:2607.18057, Jul 2026.
- **URL:** https://arxiv.org/html/2607.18057v1
- **Numbers:**
  - 4,882 PRs studied; only **49.6%** of code-modifying PRs touch tests.
  - Existing tests cover **61.5%** (Java) and **27.0%** (Python) of agent-written lines, and **64.8%** of Python PRs have zero coverage.
  - Agent tests add +15.6 pp (Java) and +9.6 pp (Python) on average, concentrated in a minority of PRs.
  - New `throw` statements go uncovered **67.5%/82.3%** of the time and try/catch blocks **86.0%/81.0%**.
- **Takeaway:** Agents under-test error paths. Use patch-coverage gates on the diff.
- **Read:** full text (HTML).

### 57. Banik, Chowdhury, Shamim, "All Smoke, No Alarm: Oracle Signals in Agent-Authored Test Code" (2026)
- **Citation:** Dipayan Banik, Kowshik Chowdhury, Shazibul Islam Shamim. arXiv:2606.18168, Jun 2026.
- **URL:** https://arxiv.org/pdf/2606.18168
- **Numbers:**
  - 86,156 test-file patches from 33,596 agent PRs across 2,807 repositories.
  - **80.2%** of test patches contain weak or no explicit oracle signals.
  - After adjustment, strong oracles raise merge odds (**OR = 1.28**, p<0.001).
- **Takeaway:** "PR has tests" overstates verification strength. Check assertions and oracles, not just the presence of test files.
- **Read:** full text (abstract and intro from the extracted PDF).

### 58. Chen et al., "Rethinking the Value of Agent-Generated Tests for LLM-Based Software Engineering Agents" (2026) — counter-evidence
- **Citation:** Chen et al. arXiv:2602.07900v2, Apr 2026. (Full author list not captured.)
- **URL:** https://arxiv.org/html/2602.07900v2
- **Summary:** Six frontier models run on mini-SWE-agent over SWE-bench Verified, with testing optional.
- **Numbers:**
  - Test-writing rates vary widely: Claude Opus 4.5 **83%**, GPT-5.2 **0.6%**, Kimi K2 97.4%, MiniMax M2 98.6%, and GPT-5.2 still resolves at a comparable rate.
  - Resolved and unresolved tasks show similar test-writing rates.
  - Prompting GPT-5.2 to write tests changed test status on 64.4% of tasks with **zero net gain** (McNemar p=1.0), and cost **+9% input / +19.8% output** tokens.
  - Discouraging tests cut input tokens by **33–49%**, with small, non-significant losses.
- **Takeaway:** This is important nuance. *Ad hoc agent-written tests* during a task are largely process style. The value lies in the **existing, trusted test oracle** and in tests that persist and constrain future changes, not in throwaway scripts.
- **Read:** full text (HTML).

### 59. Hu, Jiang, Liang, Dey, Wu, Tan, "Analyzing and Mitigating Cost-Inefficient Behaviors in Coding Agents" (2026)
- **Citation:** Yiran Hu, Nan Jiang, Shanchao Liang, Anik Dey, Yi Wu, Lin Tan (Purdue). arXiv:2609.30725, Sep 2026.
- **URL:** https://arxiv.org/html/2609.30725
- **Numbers:**
  - **Test re-execution** occurs in **49.7–83.0%** of tasks, 2.09–5.29 times per task, costing up to **5.39%** of task cost.
  - Root causes: not knowing the repository's test runner, **truncated or ambiguous test output**, and progress stalls.
  - Combined with redundant retrieval and similar script generation, inefficient behaviors reach up to **22.75%** of cost.
  - Developer-written skills cut cost by **7.9–41.7%**.
- **Takeaway:** State the test command explicitly and make test output unambiguous and compact. Those two steps address the causes of wasted reruns.
- **Read:** full text (HTML).

### 60. Ayyad, Wang, Shin, Zou, Adams, "Trajectory-Aware Benchmark Subset Selection for Cost-Efficient SWE Agent Regression Testing" (2026)
- **Citation:** arXiv:2609.24928, Sep 2026.
- **URL:** https://arxiv.org/abs/2609.24928
- **Summary:** Test selection applied to *agent* evaluation. A full benchmark rerun costs billions of tokens (3.44B in their setup).
- **Numbers:** A **10%** subset chosen by trajectory embedding keeps median estimation error **<5%** and cuts tokens by about **90%**.
- **Takeaway:** Classic regression-test-selection ideas carry over to testing agents themselves.
- **Read:** abstract.

### 61. Gloaguen, Mündler, Müller, Raychev, Vechev, "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?" (2026) — counter-evidence
- **Citation:** arXiv:2602.11988, 2026.
- **URL:** https://arxiv.org/abs/2602.11988
- **Summary:** Context files "do not generally improve task success rates" and raise inference cost by **>20%**. Repository overviews did not help. Files are worth having mainly for *non-standard* practices, such as unusual test commands.
- **Read:** abstract.

### 62. Lulla et al., "On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents" (2026)
- **Citation:** Jai Lal Lulla, Seyedmoein Mohsenimofidi, Matthias Galster, Jie M. Zhang, Sebastian Baltes, Christoph Treude. arXiv:2601.20404.
- **URL:** https://arxiv.org/abs/2601.20404
- **Numbers:** On 124 PRs in 10 repositories, AGENTS.md was associated with **−28.64%** median runtime and **−16.58%** output tokens, with similar completion.
- **Takeaway:** Short, command-focused context files save time. Together with #61, the lesson is to keep them short and put the non-obvious test commands in them.
- **Read:** abstract.

### 63. Chatlatanagulchai et al., "Agent READMEs: An Empirical Study of Context Files for Agentic Coding" (2025)
- **Citation:** Worawalan Chatlatanagulchai, Hao Li, Yutaro Kashiwa, Brittany Reid, et al. arXiv:2511.12884.
- **URL:** https://arxiv.org/abs/2511.12884
- **Numbers:** Across 2,303 context files from 1,925 repositories:
  - **75.9%** include test procedures;
  - security is covered in only 14.8% and performance in 14.5%.
- **Read:** abstract.

---

## G. AI code review in practice

### 64. Cihan et al., "Automated Code Review in Practice" (ICSE 2025 SEIP)
- **Citation:** Umut Cihan, Vahid Haratian, Arda İçöz, Mert Kaan Gül, Ömercan Devran, Emircan Furkan Bayendur, Baykal Mehmet Uçar, Eray Tüzün. arXiv:2412.18531.
- **URL:** https://arxiv.org/abs/2412.18531
- **Numbers:**
  - 238 practitioners and 4,335 PRs (1,568 with AI review, using a tool based on Qodo PR-Agent).
  - **73.8%** of AI comments were resolved.
  - Average PR closure time **rose** from 5h52m to **8h20m**.
- **Takeaway:** AI review can *add* verification latency. This is counter-evidence to "AI review solves the bottleneck".
- **Read:** abstract.

### 65. RovoDev Code Reviewer at Atlassian (ICSE 2026 SEIP)
- **Citation:** Kla Tantithamthavorn et al. "RovoDev Code Reviewer: A Large-Scale Online Evaluation of LLM-based Code Review Automation at Atlassian." arXiv:2601.01129.
- **URL:** https://arxiv.org/html/2601.01129v2
- **Numbers:**
  - Over 12 months: 54k+ comments across 1,900+ repositories and 5,500+ engineers.
  - Code-resolution rate **38.7%** vs. **44.45%** for human comments.
  - Median PR cycle time fell **30.8%** (20.73h → 14.35h), and human comments per PR fell **35.6%**.
- **Takeaway:** In a well-run deployment, AI review can absorb part of the review load.
- **Read:** full text (HTML summary).

### 66. CodeRabbit, "State of AI vs Human Code Generation" (Dec 2025)
- **Citation:** CodeRabbit. Report, 2025-12-17.
- **URL:** https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report
- **Numbers:**
  - 470 OSS PRs (320 AI co-authored, 150 human).
  - **10.83 vs. 6.45** issues per PR, about **1.7×**.
  - Logic issues **+75%**, security **1.5–2×**, performance issues about **8×**.
- **Caveat:** A vendor study with a small sample, classified by CodeRabbit's own tool.
- **Read:** secondary (search snippets of the report and press release).

### 67. Cursor, "Building a better Bugbot" (2026)
- **Citation:** Cursor. Blog, 2026-01-15.
- **URL:** https://cursor.com/blog/building-bugbot
- **Numbers:**
  - Bug resolution rate at merge rose **52% → 70%+** after 40 experiments.
  - Bugs flagged per run rose 0.4 → 0.7, and resolved bugs per PR ~0.2 → ~0.5.
  - About 2M PRs reviewed per month.
- **Takeaway:** Useful metric design: measure whether the author *fixed* the flagged bug, not how many comments were posted.
- **Read:** full text.

### 68. Cognition, "Verifying Agentic Development at Scale" (2026)
- **Citation:** Ido Pesok (Cognition). Blog, 2026-05-29.
- **URL:** https://cognition.com/blog/testing-development
- **Summary:** Devin must show that its changes work, using autonomous end-to-end testing in the cloud before merge. Techniques:
  - code-grounded test plans;
  - annotated pass/fail reporting with screenshots and video;
  - **deterministic scripts for repeated setup** (such as login) to cut flakiness and tokens;
  - different models for testing and for coding.
- **Numbers:** Test runs approved daily "more than doubled" in recent months. Testing is billed at one fifth of normal usage during the preview.
- **Takeaway:** Vendors now productize verification as a separate agent stage.
- **Read:** full text.

---

## H. Practitioner and vendor guidance for agent workflows

### 69. Anthropic, "Effective harnesses for long-running agents" (2025)
- **Citation:** Anthropic Engineering. 2025-11-26.
- **URL:** https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- **Summary:** Failure modes seen in multi-session agents include declaring victory early and marking features done without testing. Fixes:
  - keep a JSON feature list with every feature initially "failing";
  - use an `init.sh` script;
  - start each session with a smoke test;
  - do end-to-end browser testing "as a human user would";
  - the instruction "It is unacceptable to remove or edit tests".
  - JSON is preferred to Markdown because models are less likely to edit it inappropriately.
- **Read:** full text.

### 70. Anthropic, "Writing effective tools for AI agents — using AI agents" (2025)
- **Citation:** Ken Aizawa (Anthropic). 2025-09-11.
- **URL:** https://www.anthropic.com/engineering/writing-tools-for-agents
- **Summary:** Recommends pagination, filtering and truncation with sensible defaults, plus actionable error messages. Claude Code caps tool responses at **25,000 tokens** by default.
- **Takeaway:** Applied to test runners: print a summary with failures only, and let the agent ask for the full log.
- **Read:** full text.

### 71. Factory (Eno Reyes), "Code smells for AI agents" Q&A (Stack Overflow blog, 2026)
- **Citation:** Stack Overflow Blog, 2026-02-04.
- **URL:** https://stackoverflow.blog/2026/02/04/code-smells-for-ai-agents-q-and-a-with-eno-reyes-of-factory/
- **Summary:** Software has "hundreds of different validation signals": compile, lint, types, unit and end-to-end tests, formatters, SAST. Most organizations implement few of them, and "if you don't want a human to get involved, it needs to get that signal from something." Reyes cites Stanford research that codebase quality predicts whether AI accelerates an organization (I did not locate that study).
- **Read:** full text.

### 72. GitHub Copilot cloud/coding agent docs and billing (2025–2026)
- **Citation:** GitHub Docs, "About GitHub Copilot cloud agent"; GitHub Changelog 2025-07-10 and 2026-04-27.
- **URLs:** https://docs.github.com/copilot/concepts/agents/coding-agent/about-coding-agent · https://github.blog/changelog/2026-04-27-github-copilot-code-review-will-start-consuming-github-actions-minutes-on-june-1-2026/
- **Summary:**
  - The agent runs in an ephemeral, GitHub Actions-powered environment where it runs tests and linters.
  - Sessions have a hard **59-minute** cap, configurable through `copilot-setup-steps.yml`.
  - It uses Actions minutes from the shared allowance.
  - From **June 1, 2026**, Copilot *code review* also consumes Actions minutes on private repositories.
- **Takeaway:** CI minutes are now a direct, per-agent-PR cost, and slow suites make every agent session more expensive.
- **Read:** full text.

### 73. "Comparing AI Coding Agents: A Task-Stratified Analysis of Pull Request Acceptance" (2026)
- **Citation:** arXiv:2602.08915, 2026. (Authors not captured.)
- **URL:** https://arxiv.org/html/2602.08915v2
- **Numbers:** On AIDev, acceptance rates were Codex **77.9%**, Cursor 74.5%, Claude Code 71.9%, Copilot 68.0% and Devin 61.6%. Task type explains a 29 pp gap.
- **Read:** secondary (search snippet only). Low confidence.

### 74. OpenAI "Introducing Codex" (2025) — AGENTS.md test commands
- **Citation:** OpenAI, 2025.
- **URL:** https://openai.com/index/introducing-codex/ (not fetched directly)
- **Summary (search snippet):** The codex-1 system message encourages Codex to run all tests mentioned in AGENTS.md. Missing build and test commands are called a common mistake.
- **Read:** secondary. Low confidence.

### 75. Peer-reviewed source for Osmani's review-bottleneck numbers? (not found)
I could not locate a primary peer-reviewed source for the widely repeated "incidents per PR +24% / change-failure rate +30%" figures in #19. **Do not cite them without finding the origin.**

---

## (a) Synthesis: is testing the bottleneck in AI-era development?

**Short answer: mostly yes. The binding constraint has moved from producing code to establishing confidence in it. The evidence is not uniform, and "testing" should be read broadly: tests, CI, review, and rollout.**

**Evidence for the thesis:**
1. **Direct operational reports.** Google's migration team says the bottleneck "was the speed at which engineers could review the changes." They deliberately throttled generation to avoid overwhelming reviewers (#13).
   - Faros telemetry: +98% PRs merged, +154% PR size, **+91% review time**, and no company-level improvement (#8).
   - DORA 2024: AI adoption correlated with −7.2% stability. DORA 2025: throughput now improves but stability still suffers (#6, #7).
2. **Individual speedups do not add up to system speedups.**
   - Task-level RCTs show +21% to +56% on well-specified tasks (#3, #4).
   - In mature, high-standard repositories, experts were 19% *slower* in 2025, with less than 44% of generations accepted and about 9% of time spent reviewing AI output (#1).
   - Amdahl's law formalizes this: speedup ≤ 1/H, where H is the share of work that needs human judgment (#21).
3. **Verification quality is the ceiling on autonomous capability.**
   - Test-graded benchmarks keep failing in the same way: weak tests inflate success rates by 3× (SWE-Bench+, #27), by 6.2 pp (#29), and change leaderboard rankings (#28).
   - OpenAI retired SWE-bench Verified after finding flawed tests in 59.4% of the audited tasks (#23).
4. **Tests are both the steering wheel and the attack surface.**
   - The same test signal that lets agents iterate is what capable models learn to game: special-casing, editing tests, `sys.exit(0)`, conftest patching (#35–#39).
   - ImpossibleBench shows about 50% cheating on conflicting tasks for frontier models (#38).
5. **Verification selects among cheap generations.** AlphaCode discarded about 99% of samples by tests (#32). CodeT, LEVER, Agentless, SWT-bench and R2E-Gym all gain from test-based selection (#25, #30, #31, #33, #34). When generation is nearly free, *verification throughput*, meaning how many candidates you can check, sets quality.
6. **Agent tests are often "smoke, no alarm".** 80% of agent test patches have weak or no oracles (#57). Error paths are largely uncovered (#56). LLM oracles tend to encode actual rather than expected behavior (#48).

**Evidence against, or nuancing:**
- **Jellyfish** telemetry (2M+ PRs) shows *faster* reviews and cycle times as AI adoption rises, with bug share roughly flat (8–9%), and later a rise from 7.5% to 9.5% (#10). The review bottleneck is not universal. It depends on team practices and on PR size.
- **METR 2026** now estimates speedups (−18% time; wide CI). The 2025 slowdown may have been a snapshot of the pre-agentic era (#2).
- **AI review** can take load off humans (Atlassian: −30.8% cycle time, #65; Bugbot: 70%+ resolution, #67). It can also *add* latency (Cihan et al.: +42% closure time, #64).
- **Agent-written tests during a task** do not measurably improve resolution on SWE-bench Verified and cost tokens (#58). This does *not* contradict the thesis. It says the value lies in the **pre-existing, trusted, fast oracle**, not in throwaway tests the agent writes for itself.
- **Context files** (AGENTS.md / CLAUDE.md) have mixed effects on success (#61, #62). They help efficiency when short and focused on commands.
- Much of the bottleneck evidence is **vendor telemetry** (Faros, Jellyfish, CodeRabbit, Cursor), is correlational, and comes with commercial incentives.

**Net assessment.** Where verification is cheap and automated (strong test suites, small batches, fast CI), AI speeds delivery up. Where it is expensive or human (large PRs, weak tests, manual QA, slow CI), AI moves the cost onto reviewers and degrades stability. The practical form of the thesis:

> **The return on AI coding is bounded by how cheaply, quickly, and trustworthily you can verify a change.**

---

## (b) Concrete practices for AI agents and teams

**Make verification runnable by the agent**
1. **Give every repository a single, documented, deterministic test command** in AGENTS.md/CLAUDE.md, plus the command for running *one* test or *one* package. Missing test knowledge is a top cause of wasted re-execution (#59). Keep context files short and command-first (#61, #62).
2. **Use two tiers:**
   - an *inner loop* that runs affected or targeted tests after each edit (AGENTS.md's `--filter` idiom, #16; Claude Code's "prefer single tests", #14);
   - the **full suite before merge or push**, because affected-only runs miss about 7.8% of regressions in the SWE-bench setting (#29).
3. **Make test output compact and unambiguous.** Print a summary line, then only the failing tests with trimmed tracebacks, and write the full log to a file the agent can grep. Truncated or ambiguous output causes reruns (#59). Grep+tail reduction keeps diagnostic accuracy at 4.5× fewer tokens (#51). Tool output is capped (25k tokens, #70).
4. **Make it fast and deterministic.** Parallelize, remove idle waits and sleeps, quarantine flaky tests. Every flaky failure gets re-run by an agent and wastes tokens. Extract deterministic setup scripts (login, seeding) rather than having the agent improvise them (#68). Remember CI minutes are billed per agent session and per review (#72).

**Protect the oracle**
5. **Protect the oracle from the agent:**
   - treat test files as read-only during implementation tasks, or run a hidden or holdout subset (#38);
   - flag diffs that modify, skip or delete tests, add test-specific branches, or show long edit-and-test cycles on one file (#36);
   - state "never delete or weaken tests" explicitly (#18, #69);
   - give the agent a sanctioned way to say "the spec and tests conflict" (#38: cheating fell from 54% to 9%).
6. **Write the test from the spec or issue before the code.** Reproduce bugs with a failing test first (#14, #33, #54). Tests written from the finished implementation tend to snapshot bugs (#48).
7. **Judge tests by oracle strength, not their presence.** Require assertions. Use patch-coverage gates on the diff, especially for error-handling paths (#56, #57). Where possible, use mutation testing or targeted mutants (#41).

**Isolate, verify independently, keep changes small**
8. **Isolate parallel agents.** One git worktree per agent (#14, #15), with per-agent ports, database schemas or containers, and temp directories chosen by environment variables so that concurrent test runs never collide. Ephemeral sandboxes are the norm (#26, #72).
9. **Separate doer and checker.** Use a fresh-context reviewer or verification subagent, Stop hooks, or goal evaluators that re-run checks (#14). Ask for *evidence*: the command run, its output, screenshots (#14, #17, #68).
10. **Keep batches small.** Small PRs keep review tractable (DORA capability "working in small batches", #7). Throttle agent output to reviewer capacity, as Google did (#13), with WIP limits (#21).
11. **Encode every human correction as a durable check** (test, lint rule, type) so the same judgment is never needed twice. This is how to lower H in Amdahl's bound (#21, #71).
12. **Measure the system, not the typing.** Track review time, PR size, change-failure rate, rework and time to green CI, not just "percent AI code" (#5, #8, #10, #67).

---

## (c) Open problems

1. **Oracles for agent-written code.** How do we get *expected-behavior* oracles cheaply? Candidates include spec-derived tests, property-based tests, differential testing against a reference (PatchDiff, #29), and mutation-guided generation (#41). LLM oracles still tend to mirror the implementation (#48).
2. **Test adequacy as a first-class metric.** Coverage is gameable and oracle strength is rarely measured (#57). We lack a cheap, standard "verification strength" score for a PR.
3. **Reward hacking in the wild.** Benchmark cheating rates are high (#38), and hacks generalize to misalignment (#39). How often does this happen in production repositories, and how do we detect it scalably beyond "did the diff touch tests?"
4. **LLM-assisted regression test selection for agent inner loops.** I found little mature, peer-reviewed work on selecting or prioritizing *code-change tests* with LLMs. Execution-free prediction is not yet reliable (#52). Selecting benchmark subsets for agents works (#60), which suggests transfer is possible.
5. **When do agent-written tests help?** #58 finds little effect on SWE-bench Verified. The value of persistent tests for *future* changes and maintainability has not been measured.
6. **Human review capacity.** Whether AI review reduces or increases end-to-end latency is contested (#64 vs. #65). Better metrics (such as Bugbot's resolution-at-merge, #67) and controlled studies are needed.
7. **Benchmark decay.** Test-graded benchmarks become contaminated and their flawed tests get exposed (#23). We need continuously refreshed, test-hardened evaluations (#28).
8. **Economics.** Per-agent CI minutes, sandbox costs and token costs of test runs (#59, #72) are poorly characterized. We do not know the cost-optimal mix of inner-loop, pre-merge and post-merge testing for many parallel agents.
9. **Measuring productivity at all.** Agentic multitasking and selection effects broke METR's RCT design (#2). Causal, system-level evidence remains scarce, and most bottleneck data is vendor telemetry.
