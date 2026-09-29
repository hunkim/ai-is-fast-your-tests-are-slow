# 教程：15 分钟让慢测试套件变快

[English](TUTORIAL.md) · [한국어](TUTORIAL.ko.md) · [日本語](TUTORIAL.ja.md) · **中文**

你将把一个小测试套件从 **12.0 s 提速到 1.1 s**，不删除、不跳过任何一个测试，然后把同样的步骤用到你自己的项目上。你需要 Node.js 22+ 和 Python 3.8+，无需安装任何包。

```bash
git clone https://github.com/hunkim/ai-is-fast-your-tests-are-slow
cd ai-is-fast-your-tests-are-slow/examples/slow-suite
```

## 一段话讲清核心思路

测试套件慢的时候，人的第一反应是少跑点测试，或者换更大的机器。但大多数慢测试套件并不忙——它们在**等待**：在 sleep、在重试，或者因为有东西让进程在测试结束后还活着而卡住。一个在等待的测试几乎不占用 CPU。所以第一个问题不是"哪些测试可以跳过？"，而是**"哪些测试在用 CPU，哪些只是在等？"**

## 第 1 步 — 测量基线

```bash
npm test
```

```
# tests 10
# pass 10
real 12.0 s
```

十个测试，十二秒。其中大多数只有一行。

## 第 2 步 — 找出等待

单独运行每个测试文件，比较 **wall time**（实际花了多久）和 **CPU time**（真正在计算的时间）：

```bash
python3 ../../skills/fast-tests/scripts/profile_tests.py --cmd "node --test {file}" "test/*.test.mjs"
```

```
unit                            wall s    cpu s   cpu%  note
test/lingering-timer.test.mjs      5.1      0.1     2%  WAITING
test/retry.test.mjs                3.6      0.1     2%  WAITING
test/sleepy.test.mjs               2.2      0.1     4%  WAITING
test/busy.test.mjs                 1.0      1.0    98%
test/fast1.test.mjs                0.1      0.1    80%
…
waiting: 3 units spend ~10.6 s (85% of serial time) not using the CPU
long pole: test/lingering-timer.test.mjs (5.1 s) — no worker count can finish faster than this
```

有三个文件只用了 2–4% 的 CPU：它们在等待。`busy.test.mjs` 是真的在干活（98% CPU）——这个没问题。

也可以试试静态扫描器，它不用运行任何东西就能找出可疑模式：

```bash
python3 ../../skills/fast-tests/scripts/scan_test_smells.py .
```

它会标记出 `setTimeout(r, 2100)` 这个 sleep，以及 `package.json` 里的 `--test-concurrency=1` 设置。

## 第 3 步 — 消除这三处等待

每个文件都展示了一种在真实项目中极其常见的模式。修复后的版本在 `examples/fast-suite` 中。

### 等待 1：按间隔 sleep — `sleepy.test.mjs`（2.2 s）

缓存每 2 秒刷新一次，所以测试 sleep 了 2.1 秒：

```js
const cache = new Cache({ flushMs: 2000 });
cache.set("a", 1);
await new Promise((r) => setTimeout(r, 2100)); // ✗ 真的在等
assert.equal(cache.flushed, 1);
```

**修复：掌控时钟。** 假定时器（fake timers）让时间瞬间流逝：

```js
test("the cache flushes to disk", (t) => {
  t.mock.timers.enable({ apis: ["setInterval"] });
  const cache = new Cache({ flushMs: 2000 });
  cache.set("a", 1);
  t.mock.timers.tick(2000); // ✓ 两秒瞬间过去
  assert.equal(cache.flushed, 1);
  cache.close();
});
```

（Jest：`jest.useFakeTimers()` + `jest.advanceTimersByTime()`。Vitest：`vi.useFakeTimers()`。Python：`time-machine` 或 `freezegun`。Go 1.25+：`testing/synctest`。如果代码运行在另一个进程里，那就把间隔改成可配置的，在测试中设短一些。）

### 等待 2：让进程无法退出的定时器 — `lingering-timer.test.mjs`（5.1 s）

测试本身 1 ms 就跑完了。但被测代码安排了一个 5 秒后的指标上传，而且从不取消，所以 Node 必须等定时器触发后才能退出：

```js
count(name) {
  this.pending.push(name);
  this.timer ??= setTimeout(() => this.upload(), 5000); // ✗ 让进程一直挂着
}
```

**修复：后台定时器不应该让进程保持存活。** 在源码里改一行：

```js
this.timer = setTimeout(() => this.upload(), 5000);
this.timer.unref?.(); // ✓ 不会拖住进程（在浏览器中是空操作）
```

这是最隐蔽的一种等待：每个测试都很快通过，但整个文件却要花好几秒。在我们的真实[案例研究](CASE-STUDY.zh.md)中，就因为这类定时器，有 22 个文件在最后一个测试结束后各自空等了 30 秒。

### 等待 3：假的失败触发了真的重试 — `retry.test.mjs`（3.6 s）

客户端会对网络错误做带退避的重试（0.5 s、1 s、2 s）。测试通过抛异常来模拟"服务器挂了"，于是要把三次重试全部熬完：

```js
const fetch = async () => { throw new Error("network down"); }; // ✗ 被重试 3 次
```

**修复：模拟你真正想表达的失败。** "加载失败"是一个 HTTP 错误，客户端不会重试它：

```js
const fetch = async () => new Response("{}", { status: 500 }); // ✓ 有响应，不重试
```

（如果你确实想测试重试逻辑本身，就把延迟传进去：`getJson(path, { fetch, delays: [0, 0, 0] })`。）

## 第 4 步 — 用上所有 CPU 核心

这个测试套件是一次只跑一个文件（`--test-concurrency=1`）。这里的每个测试文件都是相互独立的（没有共享的文件、端口或数据库），所以可以同时跑多个：

```json
"test": "node --test --test-concurrency=8 'test/*.test.mjs'"
```

## 第 5 步 — 再测一次

```bash
cd ../fast-suite
npm test
python3 ../../skills/fast-tests/scripts/profile_tests.py --cmd "node --test {file}" "test/*.test.mjs"
```

```
# tests 10
# pass 10
real 1.1 s

waiting: 0 units spend ~0.0 s (0% of serial time) not using the CPU
long pole: test/busy.test.mjs (1.1 s)
```

**12.0 s → 1.1 s。** 同样的十个测试，全部通过。现在剩下的只有真正的计算工作（`busy.test.mjs`），这正是应该剩下的部分。

注意顺序：如果我们只加了并行，那个拖了 5 秒的文件仍然会是长杆（long pole）——再多的 worker 也快不过最慢的那个文件。

## 第 6 步 — 用到你的项目上

1. **基线。** 给你的 CI 实际运行的那条命令计时。
2. **Profile。** 把 profiler 指向你的测试运行器——任何能单独运行一个文件的工具都可以：
   ```bash
   profile_tests.py --cmd "npx jest {file}"             "src/**/*.test.ts"
   profile_tests.py --cmd "npx vitest run {file}"       "src/**/*.test.ts"
   profile_tests.py --cmd "python -m pytest -q {file}"  "tests/**/test_*.py"
   profile_tests.py --cmd "go test ./{file}"            pkg/a pkg/b pkg/c
   profile_tests.py --cmd "bundle exec rspec {file}"    "spec/**/*_spec.rb"
   ```
3. **消除等待**，处理每一个标记为 WAITING 的文件。各语言的模式与修复清单见 [`skills/fast-tests/references/waits.md`](skills/fast-tests/references/waits.md)（英文）。
4. **并行化**——前提是确认每个文件都使用自己的临时目录、端口和数据库（[隔离检查清单](skills/fast-tests/references/parallel.md#isolation-checklist)（英文））。把测试套件跑三遍，证明它是稳定的。
5. **拆分长杆**，如果总时长被某一个文件卡住的话。
6. **每次 push 之前都跑完整测试套件。** 一旦它足够快，就没什么理由少跑了。

## 第 7 步 — 新增测试时保持快速

快速的测试套件只有在新测试也遵守同样规则时才能一直快下去。合并之前，用预算来检查你新增或修改的测试文件——时间上限、不许等待，并重复运行以捕捉 flaky 问题：

```bash
python3 ../../skills/fast-tests/scripts/profile_tests.py --cmd "node --test {file}" \
  --max-seconds 2 --fail-on-waiting --repeat 5 test/sleepy.test.mjs
```

在 `slow-suite` 中它会失败（`OVER 2s`、`WAITING`）；在 `fast-suite` 中则会通过。只要有任何违规，它就以退出码 1 退出，所以可以直接作为 pull request 的 CI 任务（[示例](skills/fast-tests/references/new-tests.md#enforce-it-in-ci)（英文））。新测试的设计检查清单见 [`references/new-tests.md`](skills/fast-tests/references/new-tests.md)（英文）。

## 第 8 步 — 交给你的 AI agent

[`fast-tests` skill](skills/fast-tests/SKILL.md)（英文）把这整套方法打包好了，让编程 agent 也能照着做——并且在它自己的循环里高效地跑测试。

- **Claude Code：** 把这个文件夹复制到你的 skills 目录，Claude 在涉及测试时就会用上它：
  ```bash
  mkdir -p ~/.claude/skills && cp -R skills/fast-tests ~/.claude/skills/        # 所有项目
  mkdir -p .claude/skills && cp -R /path/to/skills/fast-tests .claude/skills/    # 单个项目
  ```
  然后说：*"Our tests are slow — use the fast-tests skill to speed them up."*（我们的测试太慢了——用 fast-tests skill 把它们提速。）
- **其他 agent（Codex、Cursor、Gemini CLI……）：** 在 `AGENTS.md` 中加一行：
  *"When tests are slow or flaky, or before changing how tests run, follow `skills/fast-tests/SKILL.md`."*
  同时加上你的关卡命令，以及 [AGENTS.md 片段](skills/fast-tests/references/agents.md#agentsmd-snippet)（英文）中的规则。

## 为什么现在这件事很重要

AI agent 几秒钟就能写完一个改动，然后就得等测试——每一次迭代、每一个 agent、每一个 PR。12 分钟的测试套件每小时大约只允许五次经过验证的迭代；24 秒的测试套件则允许 150 次。当代码变得廉价，**验证速度就是开发速度**。证据见 [RESEARCH.md](RESEARCH.md)（英文）。
