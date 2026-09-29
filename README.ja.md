> **この URL を AI コーディングエージェントに貼り付ければ、今日からテストが速くなります。**
> *「https://github.com/hunkim/ai-is-fast-your-tests-are-slow を読んで、うちのテストスイートを速くして」* 実際のプロジェクトで **12 分が 24 秒**に。テストは一つも省略せず、新しいテストも速いまま。ボトルネックが消えます。

# AI is fast. Your tests are slow.

![AI is fast. Your tests are slow. — 12 min → 24 s, no test skipped](docs/card.svg)

**AI は速い。遅いのはあなたのテストだ。**

[English](README.md) · [한국어](README.ko.md) · **日本語** · [中文](README.zh.md)

**あなたの AI は、テストを待っています。** エージェントは数秒で変更を書き上げ、それが動くかを知るために数分待つ。
イテレーションのたびに、エージェントごとに、PR ごとに。AI コーディングの時代、ボトルネックは検証です。

そして意外なことに、**その時間のほとんどはテストではなく「待ち」です。** sleep、リトライのバックオフ、
終わったはずのプロセスを生かし続けるタイマー、ネットワークのタイムアウト、16 コアのマシンで 1 ファイルずつの実行。

私たちは実際のプロダクションコードベースのテストスイートを、テストを 1 つもスキップせずに **12 分から 24 秒**（約 30 倍）
に短縮しました。そして、誰もが最初に手を伸ばす研究ベースのアイデア、つまり影響を受けるテストだけを実行する方法は、
*最も効果の小さい*改善でした。[ケーススタディを読む →](CASE-STUDY.ja.md)

## ここにあるもの

| | 対象 | 内容 |
|---|---|---|
| [**TUTORIAL.ja.md**](TUTORIAL.ja.md) | すべての人 | 15 分のハンズオン：小さなスイートを 12.0 s から 1.1 s へ、その後あなた自身のプロジェクトへ |
| [**skills/fast-tests**](skills/fast-tests/SKILL.md)（英語） | AI エージェント | 完全なエージェントスキル：計測し、待ちを取り除き、安全に並列化し、新しいテストすべてに予算を設け、フルスイートをゲートとして維持し、エージェントのループ内でテストを効率よく実行する |
| [**RESEARCH.md**](RESEARCH.md)（英語） | 知りたい人 | 約 270 本の論文・業界レポート・ドキュメントが語ること：テスト選択、並列化、flaky テスト、フィードバックループ、AI 時代の検証 |
| [**research/**](research)（英語） | 研究者 | 5 つの注釈付き文献リスト：すべての出典にリンク、数値、全文を読んだかどうかを記載 |
| [**CASE-STUDY.ja.md**](CASE-STUDY.ja.md) | エンジニアリングリード | 12 分 → 24 秒を一歩ずつ、うまくいかなかったことも含めて |
| [**examples/**](examples)（英語） | すべての人 | `slow-suite`（12.0 s）と `fast-suite`（1.1 s）：現実によくある 3 つの待ちとその修正 |

## 1 分で試す

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

プロファイラは 1 つのファイルやパッケージを実行できるランナーなら何でも使えます（pytest、Jest、Vitest、Go、RSpec、cargo）。
必要なのは Python 3.8+ だけです：

```bash
profile_tests.py --cmd "python -m pytest -q {file}" "tests/**/test_*.py"
profile_tests.py --cmd "npx jest {file}" "src/**/*.test.ts" --json report.json
```

## エージェントにスキルを渡す

**Claude Code**

```bash
git clone https://github.com/hunkim/ai-is-fast-your-tests-are-slow /tmp/fast-tests
mkdir -p ~/.claude/skills && cp -R /tmp/fast-tests/skills/fast-tests ~/.claude/skills/
```

あとは *「テストが遅い。fast-tests スキルを使って」* と頼むだけ。このスキルは、エージェントの日々のテストの回し方も変えます：
編集中は影響を受けるテストだけ、「完了」と言う前にはフルスイート、出力はコンパクトに、そしてテストを通すために
テストを弱めることは決してしない。

**Codex、Cursor、Gemini CLI など** — `skills/fast-tests` をリポジトリにコピーし、`AGENTS.md` に次を追加します：

```markdown
When tests are slow or flaky, or before changing how tests run, follow skills/fast-tests/SKILL.md.
```

## 手法

1. **計測する**：テストファイルごとに実時間（wall time）と CPU 時間を比べる。CPU が低く実時間が長い = 待っている。
2. **待ちを取り除く**：sleep する代わりに時計をフェイクにする、バックグラウンドタイマーを `unref` する、
   リトライされない失敗をシミュレートする、ネットワークをスタブする。
3. **並列化する**：すべてのファイルが専用の一時ディレクトリ、ポート、データベースを持ったら。そして繰り返し実行で証明する。
4. **ロングポールを分割する**：いくらワーカーを増やしても、最も遅いファイルより速くは終わらない。
5. **キャッシュする**：セットアップを、そしてハーメティックなテストなら結果も。
6. **選択する**のは編集ループの中だけで、影響を受けるテストに絞る。**ゲートはフルスイート。**
7. **flaky テストを隔離する**：再実行のコストがかかり、人もエージェントも赤を無視するようになる。
8. **オラクルを守る**：エージェントがテストを弱めて通すことは決して許さない。
9. **速さを保つ**：新規・変更されたテストファイルはすべて、マージ前に予算チェック（時間、待ちなし、繰り返し実行）を通す —
   `profile_tests.py --max-seconds 2 --fail-on-waiting --repeat 5 <changed test files>`。

## 研究が示すこと（ハイライト）

- ビルドがほんの数秒速くなるだけで、Google の開発者は 11〜14% 速くなった。これ以下なら速度は関係ない、という閾値は存在しない
  （Jaspan & Green 2023）。
- AI の導入で、マージされた PR は 98%、レビュー時間は 91% 増えたが、会社レベルでの向上はなかった（Faros、開発者 1 万人以上、2025）。
- 非同期の待ちは flaky テストの原因の第 1 位：修正の 45%（Luo et al. 2014）。
- 影響を受けるテストだけを実行する場合：Ekstazi はテストの 30.6% を選択したが、CI のビルドは依然として 76% の時間がかかった。
  ハブモジュールのせいで、モジュール単位の選択はコミットの 65% ですべてを選んでしまった（Shi et al. 2019）。
- 「最近失敗したもの、次に速いもの順」が、ML を含む 59 の優先順位付け手法に勝った（Cheng et al. 2024）。
- フロンティアモデルは、テストが仕様と矛盾するタスクの約半分でズルをする（ImpossibleBench 2025）。エージェントが書いた
  テスト変更の 80% はアサーションが弱いか、存在しない（Banik et al. 2026）。
- エージェントは、未知のランナーや曖昧な出力のせいでタスクの 50〜83% でテストを再実行する。スキルを文書化すると
  エージェントのコストが最大 42% 下がる（Hu et al. 2026）。

[約 270 の出典による完全なまとめ →](RESEARCH.md)（英語）

## コントリビュート

私たちが見落とした待ちのパターン、変更されたランナーのフラグ、私たちと矛盾する研究を見つけたら、Issue か PR をお願いします。
ビフォー/アフターの数値付きのケーススタディは特に歓迎です。

## ライセンス

[MIT](LICENSE)
