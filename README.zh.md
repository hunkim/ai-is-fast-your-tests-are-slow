# AI is fast. Your tests are slow.

**AI 很快，你的测试很慢。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · **中文**

**你的 AI 正在等你的测试。** Agent 几秒钟就写完一个改动，然后要等上好几分钟才知道它能不能用——每一次迭代、每一个 agent、每一个 PR 都是如此。在 AI 编程时代，瓶颈在于验证。

而令人意外的是：**这些时间大部分并不是在测试，而是在等待。** sleep、重试退避、让已经跑完的进程迟迟不退出的定时器、网络超时，以及在 16 核机器上一次只跑一个文件。

我们把一个真实生产代码库的测试套件从 **12 分钟降到了 24 秒**（约 30 倍），没有跳过任何一个测试——而大家最先想到、也有研究背书的那个办法，即只运行受影响的测试，反而是*效果最差*的。[阅读案例研究 →](CASE-STUDY.zh.md)

## 这里有什么

| | 面向 | 内容 |
|---|---|---|
| [**TUTORIAL.zh.md**](TUTORIAL.zh.md) | 所有人 | 15 分钟动手实践：把一个小测试套件从 12.0 s 提速到 1.1 s，然后用到你自己的项目上 |
| [**skills/fast-tests**](skills/fast-tests/SKILL.md)（英文） | AI agent | 一个完整的 agent skill：测量、消除等待、安全地并行化、为每个新测试设定预算、始终以完整测试套件作为关卡，并在 agent 循环中高效地运行测试 |
| [**RESEARCH.md**](RESEARCH.md)（英文） | 好奇的人 | 约 270 篇论文、行业报告和文档怎么说——测试选择、并行、flaky 测试、反馈循环、AI 时代的验证 |
| [**research/**](research)（英文） | 研究者 | 五份带注释的参考文献：每个来源都附有链接、数据，并注明我们是否读过全文 |
| [**CASE-STUDY.zh.md**](CASE-STUDY.zh.md) | 工程负责人 | 12 分钟 → 24 秒，逐步拆解，也包括哪些做法没用 |
| [**examples/**](examples)（英文） | 所有人 | `slow-suite`（12.0 s）和 `fast-suite`（1.1 s）：三种真实世界中的等待，以及修复方法 |

## 一分钟上手

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

这个 profiler 适用于任何能单独运行一个文件或一个包的测试运行器——pytest、Jest、Vitest、Go、RSpec、cargo——只需要 Python 3.8+：

```bash
profile_tests.py --cmd "python -m pytest -q {file}" "tests/**/test_*.py"
profile_tests.py --cmd "npx jest {file}" "src/**/*.test.ts" --json report.json
```

## 把这个 skill 交给你的 agent

**Claude Code**

```bash
git clone https://github.com/hunkim/ai-is-fast-your-tests-are-slow /tmp/fast-tests
mkdir -p ~/.claude/skills && cp -R /tmp/fast-tests/skills/fast-tests ~/.claude/skills/
```

然后说：*"Our tests are slow. Use the fast-tests skill."*（我们的测试太慢了，用 fast-tests skill。）这个 skill 还会改变 agent 日常跑测试的方式：编辑时只跑受影响的测试，说"完成"之前跑完整测试套件，输出保持精简，绝不为了让测试通过而削弱测试。

**Codex、Cursor、Gemini CLI 等** —— 把 `skills/fast-tests` 复制到你的仓库，并在 `AGENTS.md` 中加上：

```markdown
When tests are slow or flaky, or before changing how tests run, follow skills/fast-tests/SKILL.md.
```

## 方法

1. **测量**每个测试文件的 wall time 与 CPU time。CPU 低 + wall time 高 = 在等待。
2. **消除等待**：用假时钟代替 sleep，对后台定时器调用 `unref`，模拟不会被重试的失败，stub 掉网络。
3. **并行化**：前提是每个文件都有自己的临时目录、端口和数据库——并用多次重复运行来证明它是稳定的。
4. **拆分长杆（long pole）**：再多的 worker 也快不过最慢的那个文件。
5. **缓存**初始化过程，对于 hermetic 测试，还可以缓存结果。
6. **选择性运行**受影响的测试，只用在编辑循环里。**完整测试套件才是关卡。**
7. **隔离 flaky 测试**——它们会带来重跑成本，还会让人和 agent 习惯性地忽略红色失败。
8. **保护 oracle**：agent 绝不能通过削弱测试来让它通过。
9. **保持快速**：每个新增或修改的测试文件在合并前都要经过预算检查（时间、无等待、重复运行）——`profile_tests.py --max-seconds 2 --fail-on-waiting --repeat 5 <changed test files>`。

## 研究怎么说（要点）

- 构建哪怕只快几秒，也能让 Google 开发者的速度提升 11–14%；不存在一个"再快也没意义"的阈值（Jaspan & Green 2023）。
- 引入 AI 后，合并的 PR 增加了 98%，评审时间增加了 91%，但公司层面没有任何提升（Faros，1 万多名开发者，2025）。
- 异步等待是 flaky 测试的头号原因：占修复的 45%（Luo et al. 2014）。
- 只运行受影响的测试：Ekstazi 选出了 30.6% 的测试，但 CI 中的构建时间仍是原来的 76%；hub 模块导致模块级选择在 65% 的提交中选中了全部测试（Shi et al. 2019）。
- "最近失败的优先，然后最快的优先"击败了 59 种优先级排序技术，包括机器学习方法（Cheng et al. 2024）。
- 当测试与规格相矛盾时，前沿模型在大约一半的任务中会作弊（ImpossibleBench 2025）；agent 编写的测试改动中有 80% 断言很弱或根本没有断言（Banik et al. 2026）。
- 由于测试运行器未知、输出含糊，agent 在 50–83% 的任务中会重复跑测试；写成文档的 skill 可将 agent 成本最多降低 42%（Hu et al. 2026）。

[完整综述，约 270 个来源 →](RESEARCH.md)（英文）

## 参与贡献

发现了我们遗漏的等待模式、某个已经变更的运行器参数，或者与我们结论相悖的研究？欢迎提 issue 或 PR。特别欢迎附有前后对比数据的案例研究。

## 许可证

[MIT](LICENSE)
