# AI is fast. Your tests are slow.

**English** · [한국어](README.ko.md) · [日本語](README.ja.md) · [中文](README.zh.md)

**Your AI is waiting on your tests.** An agent writes a change in seconds, then waits minutes to find out if it
works — every iteration, every agent, every PR. In the AI coding era, the bottleneck is verification.

And here's the surprise: **most of that time isn't testing. It's waiting.** Sleeps, retry backoff, timers that keep
a finished process alive, network timeouts, one file at a time on a 16-core machine.

We took a real production codebase's suite from **12 minutes to 24 seconds** (~30×) without skipping a single test
— and the research-backed idea everyone reaches for first, running only the affected tests, was the *least*
effective fix. [Read the case study →](CASE-STUDY.md)

## What's here

| | For | What |
|---|---|---|
| [**TUTORIAL.md**](TUTORIAL.md) | Everyone | 15 minutes, hands-on: a small suite from 12.0 s to 1.1 s, then your own project |
| [**skills/fast-tests**](skills/fast-tests/SKILL.md) | AI agents | A complete agent skill: measure, remove waits, parallelize safely, budget every new test, keep the full suite as the gate, and run tests efficiently in the agent loop |
| [**RESEARCH.md**](RESEARCH.md) | The curious | What ~270 papers, industry reports and docs say — selection, parallelism, flakiness, feedback loops, AI-era verification |
| [**research/**](research) | Researchers | Five annotated bibliographies: every source with link, numbers, and whether we read the full text |
| [**CASE-STUDY.md**](CASE-STUDY.md) | Engineering leads | 12 min → 24 s, step by step, with what didn't work |
| [**CASE-STUDY-GO.md**](CASE-STUDY-GO.md) | Go teams | 15 s → 1 s: a WebSocket fake that never hung up, and a wait that wasn't in the tests |
| [**examples/**](examples) | Everyone | `slow-suite` (12.0 s) and `fast-suite` (1.1 s): three real-world waits, fixed |

## Try it in one minute

```bash
git clone https://github.com/hunkim/ai-is-fast-your-tests-are-slow
cd ai-is-fast-your-tests-are-slow/examples/slow-suite
python3 ../../skills/fast-tests/scripts/profile_tests.py --cmd "node --test {file}" "test/*.test.mjs"
```

```
unit                            wall s    cpu s   cpu%  note
test/lingering-timer.test.mjs      5.1      0.1     2%  WAITING
test/retry.test.mjs                3.6      0.1     2%  WAITING
test/sleepy.test.mjs               2.2      0.1     4%  WAITING
test/busy.test.mjs                 1.0      1.0    98%
…
waiting: 3 units spend ~10.6 s (85% of serial time) not using the CPU
long pole: test/lingering-timer.test.mjs (5.1 s) — no worker count can finish faster than this
```

The profiler works with any runner that can run one file or package — pytest, Jest, Vitest, Go, RSpec, cargo —
and needs only Python 3.8+:

```bash
profile_tests.py --cmd "python -m pytest -q {file}" "tests/**/test_*.py"
profile_tests.py --cmd "npx jest {file}" "src/**/*.test.ts" --json report.json
```

## Give the skill to your agent

**Claude Code**

```bash
git clone https://github.com/hunkim/ai-is-fast-your-tests-are-slow /tmp/fast-tests
mkdir -p ~/.claude/skills && cp -R /tmp/fast-tests/skills/fast-tests ~/.claude/skills/
```

Then: *"Our tests are slow. Use the fast-tests skill."* The skill also changes how the agent runs tests day to day:
affected tests while editing, the full suite before saying "done", compact output, never weakening a test to make
it pass.

**Codex, Cursor, Gemini CLI, and others** — copy `skills/fast-tests` into your repo and add to `AGENTS.md`:

```markdown
When tests are slow or flaky, or before changing how tests run, follow skills/fast-tests/SKILL.md.
```

## The method

1. **Measure** wall time vs CPU time per test file. Low CPU + high wall = waiting.
2. **Remove the waits**: fake the clock instead of sleeping, `unref` background timers, simulate failures that
   aren't retried, stub the network.
3. **Parallelize** once every file has its own temp dir, port and database — and prove it with repeated runs.
4. **Split the long pole**: no number of workers beats the slowest file.
5. **Cache** setup and, for hermetic tests, results.
6. **Select** affected tests only in the edit loop. **The full suite is the gate.**
7. **Quarantine flakes** — they cost reruns and teach people and agents to ignore red.
8. **Protect the oracle**: agents must never pass a test by weakening it.
9. **Keep it fast**: every new or changed test file gets a budget check (time, no waiting, repeated runs) before
   merge — `profile_tests.py --max-seconds 2 --fail-on-waiting --repeat 5 <changed test files>`.

## What the research says (highlights)

- Builds just a few seconds faster made Google developers 11–14% faster; there is no threshold below which speed
  stops mattering (Jaspan & Green 2023).
- With AI, PRs merged rose 98% and review time 91%, with no company-level gain (Faros, 10k+ developers, 2025).
- Async waits are the #1 cause of flaky tests: 45% of fixes (Luo et al. 2014).
- Running only affected tests: Ekstazi selected 30.6% of tests but builds still took 76% of the time in CI; hub
  modules made module-level selection pick everything in 65% of commits (Shi et al. 2019).
- "Recently failed, then fastest first" beat 59 prioritization techniques, including ML (Cheng et al. 2024).
- Frontier models cheat on about half of tasks whose tests contradict the spec (ImpossibleBench 2025); 80% of
  agent-written test changes have weak or no assertions (Banik et al. 2026).
- Agents re-run tests in 50–83% of tasks because of unknown runners and ambiguous output; written-down skills cut
  agent cost by up to 42% (Hu et al. 2026).

[Full synthesis with ~270 sources →](RESEARCH.md)

## Contributing

Found a wait pattern we missed, a runner flag that changed, or a study that contradicts us? Open an issue or PR.
Case studies with before/after numbers are especially welcome.

## License

[MIT](LICENSE)
