# チュートリアル：遅いテストスイートを 15 分で速くする

[English](TUTORIAL.md) · [한국어](TUTORIAL.ko.md) · **日本語** · [中文](TUTORIAL.zh.md)

小さなテストスイートを、テストを 1 つも削除・スキップせずに **12.0 s から 1.1 s** に縮め、同じ手順をあなた自身の
プロジェクトに適用します。必要なのは Node.js 22+ と Python 3.8+ だけ。インストールするパッケージはありません。

```bash
git clone https://github.com/hunkim/ai-is-fast-your-tests-are-slow
cd ai-is-fast-your-tests-are-slow/examples/slow-suite
```

## 一段落でわかる考え方

テストスイートが遅いと、テストを減らすか、マシンを大きくしたくなります。でも、遅いスイートのほとんどは忙しいのではなく
**待っている**のです：sleep している、リトライしている、あるいはテストが終わった後も何かがプロセスを生かし続けている。
待っているテストは CPU をほとんど使いません。だから最初に問うべきは「どのテストをスキップできるか？」ではなく、
**「どのテストが CPU を使っていて、どれがただ待っているだけか？」** です。

## ステップ 1 — ベースラインを計測する

```bash
npm test
```

```
# tests 10
# pass 10
real 12.0 s
```

10 個のテストで 12 秒。ほとんどは 1 行のテストです。

## ステップ 2 — 待ちを見つける

各テストファイルを単独で実行し、**実時間（wall time）**（どれだけ時間がかかったか）と **CPU 時間**（実際にどれだけ計算したか）
を比べます：

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

3 つのファイルは CPU を 2〜4% しか使っていません。待っているのです。`busy.test.mjs` は本当に仕事をしている（CPU 98%）ので、
これは問題ありません。

静的スキャナも試してみましょう。何も実行せずに怪しいパターンを見つけてくれます：

```bash
python3 ../../skills/fast-tests/scripts/scan_test_smells.py .
```

`setTimeout(r, 2100)` の sleep と、`package.json` の `--test-concurrency=1` 設定を指摘します。

## ステップ 3 — 3 つの待ちを取り除く

各ファイルは、実際のプロジェクトで非常によく見られるパターンを 1 つずつ示しています。修正版は `examples/fast-suite` にあります。

### 待ち 1：一定時間の sleep — `sleepy.test.mjs`（2.2 s）

キャッシュは 2 秒ごとにフラッシュされるので、テストは 2.1 秒 sleep します：

```js
const cache = new Cache({ flushMs: 2000 });
cache.set("a", 1);
await new Promise((r) => setTimeout(r, 2100)); // ✗ 本当に待ってしまう
assert.equal(cache.flushed, 1);
```

**修正：時計をコントロールする。** フェイクタイマーを使えば時間は一瞬で進みます：

```js
test("the cache flushes to disk", (t) => {
  t.mock.timers.enable({ apis: ["setInterval"] });
  const cache = new Cache({ flushMs: 2000 });
  cache.set("a", 1);
  t.mock.timers.tick(2000); // ✓ 2 秒が一瞬で過ぎる
  assert.equal(cache.flushed, 1);
  cache.close();
});
```

（Jest：`jest.useFakeTimers()` + `jest.advanceTimersByTime()`。Vitest：`vi.useFakeTimers()`。Python：`time-machine`
または `freezegun`。Go 1.25+：`testing/synctest`。コードが別プロセスで動く場合は、代わりに間隔を設定可能にして、
テストでは短く設定します。）

### 待ち 2：プロセスを生かし続けるタイマー — `lingering-timer.test.mjs`（5.1 s）

テスト自体は 1 ms で終わります。しかしテスト対象のコードが 5 秒後のメトリクスアップロードを予約し、それをキャンセルしないので、
タイマーが発火するまで Node は終了できません：

```js
count(name) {
  this.pending.push(name);
  this.timer ??= setTimeout(() => this.upload(), 5000); // ✗ プロセスを開いたままにする
}
```

**修正：バックグラウンドタイマーにプロセスを生かし続けさせない。** ソースに 1 行足すだけ：

```js
this.timer = setTimeout(() => this.upload(), 5000);
this.timer.unref?.(); // ✓ プロセスを保持しない（ブラウザでは何もしない）
```

これは最も見えにくい待ちです：どのテストもすぐに通るのに、ファイルには数秒かかる。私たちの実例である
[ケーススタディ](CASE-STUDY.ja.md)では、こうしたタイマーのせいで 22 個のファイルがそれぞれ最後のテストの後に 30 秒アイドル状態でした。

### 待ち 3：本物のリトライを引き起こす偽の失敗 — `retry.test.mjs`（3.6 s）

クライアントはネットワークエラーをバックオフ付き（0.5 s、1 s、2 s）でリトライします。テストは「サーバーがダウンしている」
状態を throw でシミュレートしているので、3 回のリトライをすべて待つことになります：

```js
const fetch = async () => { throw new Error("network down"); }; // ✗ 3 回リトライされる
```

**修正：意図した失敗をシミュレートする。** 「読み込みに失敗した」は HTTP エラーであり、クライアントはそれをリトライしません：

```js
const fetch = async () => new Response("{}", { status: 500 }); // ✓ 応答あり、リトライされない
```

（リトライのロジックそのものをテストしたいときは、遅延を渡します：`getJson(path, { fetch, delays: [0, 0, 0] })`。）

## ステップ 4 — すべてのコアを使う

スイートはファイルを 1 つずつ実行していました（`--test-concurrency=1`）。ここにある各テストファイルは独立している
（ファイル、ポート、データベースを共有しない）ので、複数を同時に実行します：

```json
"test": "node --test --test-concurrency=8 'test/*.test.mjs'"
```

## ステップ 5 — もう一度計測する

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

**12.0 s → 1.1 s。** 同じ 10 個のテストが、すべてパス。残っているのは本当の仕事（`busy.test.mjs`）だけで、
それこそが残るべきものです。

順番に注目してください：並列化だけを加えていたら、5 秒かかる lingering ファイルが依然としてロングポールのままでした。
ワーカーをいくら増やしても、最も遅いファイルより速くは終わりません。

## ステップ 6 — あなたのプロジェクトでやる

1. **ベースライン。** CI が実行するのとまったく同じコマンドの時間を計る。
2. **プロファイル。** プロファイラをあなたのランナーに向ける。1 ファイルを実行できるものなら何でも動きます：
   ```bash
   profile_tests.py --cmd "npx jest {file}"             "src/**/*.test.ts"
   profile_tests.py --cmd "npx vitest run {file}"       "src/**/*.test.ts"
   profile_tests.py --cmd "python -m pytest -q {file}"  "tests/**/test_*.py"
   profile_tests.py --cmd "go test ./{file}"            pkg/a pkg/b pkg/c
   profile_tests.py --cmd "bundle exec rspec {file}"    "spec/**/*_spec.rb"
   ```
3. **待ちを取り除く**：WAITING のファイルすべてで。言語ごとのパターンと修正のカタログは
   [`skills/fast-tests/references/waits.md`](skills/fast-tests/references/waits.md)（英語）にあります。
4. **並列化する**：各ファイルが専用の一時ディレクトリ、ポート、データベースを使っていることを確認してから
   （[分離チェックリスト](skills/fast-tests/references/parallel.md#isolation-checklist)（英語））。スイートを 3 回実行して
   安定していることを証明します。
5. **ロングポールを分割する**：1 つのファイルが全体の時間を決めているなら。
6. **push の前には毎回スイート全体を実行する。** 速くなれば、減らして実行する理由はほとんどありません。

## ステップ 7 — テストを追加しても速さを保つ

速いスイートが速いままでいられるのは、新しいテストが同じルールに従う場合だけです。マージ前に、追加・変更したテストファイルを
予算に照らしてチェックします。時間の上限、待ちなし、そして flaky さを捕まえるための繰り返し実行です：

```bash
python3 ../../skills/fast-tests/scripts/profile_tests.py --cmd "node --test {file}" \
  --max-seconds 2 --fail-on-waiting --repeat 5 test/sleepy.test.mjs
```

`slow-suite` ではこれは失敗し（`OVER 2s`、`WAITING`）、`fast-suite` ではパスします。違反があれば終了コード 1 で終わるので、
プルリクエスト用の CI ジョブとしてそのまま使えます
（[例](skills/fast-tests/references/new-tests.md#enforce-it-in-ci)（英語））。新しいテストの設計チェックリストは
[`references/new-tests.md`](skills/fast-tests/references/new-tests.md)（英語）にあります。

## ステップ 8 — AI エージェントに渡す

[`fast-tests` スキル](skills/fast-tests/SKILL.md)（英語）は、この手法全体をパッケージにしたもので、コーディングエージェントが
これを実行でき、さらに自分のループの中でテストを効率よく回せるようになります。

- **Claude Code：** フォルダをスキルディレクトリにコピーすれば、テストの話題になったときに Claude が使います：
  ```bash
  mkdir -p ~/.claude/skills && cp -R skills/fast-tests ~/.claude/skills/        # すべてのプロジェクト
  mkdir -p .claude/skills && cp -R /path/to/skills/fast-tests .claude/skills/    # 1 つのプロジェクト
  ```
  そして、こう頼みます：*「テストが遅い。fast-tests スキルを使って速くして」*
- **その他のエージェント（Codex、Cursor、Gemini CLI など）：** `AGENTS.md` に 1 行追加します：
  *"When tests are slow or flaky, or before changing how tests run, follow `skills/fast-tests/SKILL.md`."*
  あわせて、ゲートのコマンドと
  [AGENTS.md スニペット](skills/fast-tests/references/agents.md#agentsmd-snippet)（英語）のルールも追加してください。

## なぜ今これが重要なのか

AI エージェントは数秒で変更を書けます。そしてテストを待つ。イテレーションのたびに、エージェントごとに、PR ごとに。
12 分のスイートでは 1 時間に検証済みのイテレーションは約 5 回、24 秒のスイートなら 150 回。コードが安くなった今、
**検証の速度こそが開発の速度**です。根拠は [RESEARCH.md](RESEARCH.md)（英語）にあります。
