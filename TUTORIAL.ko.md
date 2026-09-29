# 튜토리얼: 느린 test suite를 15분 만에 빠르게 만들기

[English](TUTORIAL.md) · **한국어** · [日本語](TUTORIAL.ja.md) · [中文](TUTORIAL.zh.md)

작은 test suite를 테스트 하나 지우거나 건너뛰지 않고 **12.0 s에서 1.1 s로** 줄인 다음, 같은 단계를 당신의 프로젝트에
적용해 봅니다. Node.js 22+와 Python 3.8+만 있으면 됩니다. 설치할 패키지는 없습니다.

```bash
git clone https://github.com/hunkim/ai-is-fast-your-tests-are-slow
cd ai-is-fast-your-tests-are-slow/examples/slow-suite
```

## 한 문단으로 보는 핵심 아이디어

test suite가 느리면 본능적으로 테스트를 덜 돌리거나 더 큰 머신을 사려고 합니다. 하지만 느린 suite 대부분은 바쁜 게
아니라 **기다리는** 중입니다: sleep하거나, retry하거나, 테스트가 끝난 뒤에도 무언가가 프로세스를 붙잡고 있어서 멈춰 있는
거죠. 기다리는 테스트는 CPU를 거의 쓰지 않습니다. 그러니 첫 질문은 "어떤 테스트를 건너뛸까?"가 아니라
**"어떤 테스트가 CPU를 쓰고 있고, 어떤 테스트가 그냥 기다리고 있나?"**입니다.

## 1단계 — baseline 측정

```bash
npm test
```

```
# tests 10
# pass 10
real 12.0 s
```

테스트 10개에 12초. 대부분은 한 줄짜리입니다.

## 2단계 — 기다림 찾기

각 테스트 파일을 따로 실행해서 **wall time**(걸린 시간)과 **CPU time**(실제로 계산한 시간)을 비교합니다:

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

파일 세 개가 CPU를 2–4%만 씁니다: 기다리고 있다는 뜻입니다. `busy.test.mjs`는 진짜로 일하고 있으니(98% CPU)
그대로 두면 됩니다.

아무것도 실행하지 않고 의심스러운 패턴을 찾아주는 정적 스캐너도 써보세요:

```bash
python3 ../../skills/fast-tests/scripts/scan_test_smells.py .
```

`setTimeout(r, 2100)` sleep과 `package.json`의 `--test-concurrency=1` 설정을 잡아냅니다.

## 3단계 — 세 가지 기다림 제거하기

각 파일은 실제 프로젝트에서 아주 흔한 패턴을 하나씩 보여줍니다. 수정된 버전은 `examples/fast-suite`에 있습니다.

### 기다림 1: 주기만큼 sleep하기 — `sleepy.test.mjs` (2.2 s)

캐시가 2초마다 flush되니까, 테스트는 2.1초를 sleep합니다:

```js
const cache = new Cache({ flushMs: 2000 });
cache.set("a", 1);
await new Promise((r) => setTimeout(r, 2100)); // ✗ 실제로 기다림
assert.equal(cache.flushed, 1);
```

**수정: 시계를 통제하라.** fake timer를 쓰면 시간이 즉시 흐릅니다:

```js
test("the cache flushes to disk", (t) => {
  t.mock.timers.enable({ apis: ["setInterval"] });
  const cache = new Cache({ flushMs: 2000 });
  cache.set("a", 1);
  t.mock.timers.tick(2000); // ✓ 2초가 즉시 흐름
  assert.equal(cache.flushed, 1);
  cache.close();
});
```

(Jest: `jest.useFakeTimers()` + `jest.advanceTimersByTime()`. Vitest: `vi.useFakeTimers()`. Python: `time-machine`
또는 `freezegun`. Go 1.25+: `testing/synctest`. 코드가 다른 프로세스에서 돈다면, 대신 주기를 설정 가능하게 만들고
테스트에서는 짧게 설정하세요.)

### 기다림 2: 프로세스를 살려 두는 타이머 — `lingering-timer.test.mjs` (5.1 s)

테스트 자체는 1 ms 만에 끝납니다. 하지만 테스트 대상 코드가 5초 뒤에 metrics 업로드를 예약하고 취소하지 않아서,
타이머가 실행될 때까지 Node가 종료되지 못합니다:

```js
count(name) {
  this.pending.push(name);
  this.timer ??= setTimeout(() => this.upload(), 5000); // ✗ 프로세스를 붙잡아 둠
}
```

**수정: 백그라운드 타이머가 프로세스를 살려 두면 안 된다.** 소스에 한 줄:

```js
this.timer = setTimeout(() => this.upload(), 5000);
this.timer.unref?.(); // ✓ 프로세스를 붙잡지 않음 (브라우저에서는 no-op)
```

이게 가장 눈에 안 띄는 기다림입니다: 모든 테스트가 빨리 통과하는데도 파일은 몇 초씩 걸립니다. 실제 사례인
[케이스 스터디](CASE-STUDY.ko.md)에서는 이런 타이머 때문에 파일 22개가 마지막 테스트 이후 각각 30초씩 놀고 있었습니다.

### 기다림 3: 진짜 retry를 유발하는 가짜 실패 — `retry.test.mjs` (3.6 s)

클라이언트는 네트워크 에러를 backoff(0.5 s, 1 s, 2 s)와 함께 retry합니다. 테스트는 "서버가 다운됐다"를 throw로
흉내 내기 때문에 retry 세 번을 전부 기다립니다:

```js
const fetch = async () => { throw new Error("network down"); }; // ✗ 3번 retry됨
```

**수정: 의도한 실패를 시뮬레이션하라.** "로드 실패"는 HTTP 에러이고, 클라이언트는 이걸 retry하지 않습니다:

```js
const fetch = async () => new Response("{}", { status: 500 }); // ✓ 응답은 받았으니 retry 안 함
```

(retry 로직 자체를 테스트하고 싶을 때는 delay를 인자로 넘기세요: `getJson(path, { fetch, delays: [0, 0, 0] })`.)

## 4단계 — 모든 코어 쓰기

suite는 파일을 한 번에 하나씩 실행하고 있었습니다(`--test-concurrency=1`). 여기 있는 테스트 파일은 모두 독립적이니
(공유하는 파일, 포트, 데이터베이스 없음) 여러 개를 동시에 실행합니다:

```json
"test": "node --test --test-concurrency=8 'test/*.test.mjs'"
```

## 5단계 — 다시 측정하기

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

**12.0 s → 1.1 s.** 같은 테스트 10개, 전부 통과. 이제 남은 건 진짜 일(`busy.test.mjs`)뿐이고, 정확히 그것만
남아야 합니다.

순서에 주목하세요: 병렬화만 했다면 5초짜리 lingering 파일이 여전히 long pole이었을 겁니다 — worker를 아무리 늘려도
가장 느린 파일보다 빨리 끝날 수는 없습니다.

## 6단계 — 당신의 프로젝트에 적용하기

1. **Baseline.** CI가 실행하는 바로 그 명령의 시간을 잽니다.
2. **Profile.** profiler를 당신의 러너에 연결하세요 — 파일 하나를 실행할 수 있는 것이면 무엇이든 동작합니다:
   ```bash
   profile_tests.py --cmd "npx jest {file}"             "src/**/*.test.ts"
   profile_tests.py --cmd "npx vitest run {file}"       "src/**/*.test.ts"
   profile_tests.py --cmd "python -m pytest -q {file}"  "tests/**/test_*.py"
   profile_tests.py --cmd "go test ./{file}"            pkg/a pkg/b pkg/c
   profile_tests.py --cmd "bundle exec rspec {file}"    "spec/**/*_spec.rb"
   ```
3. **기다림 제거.** WAITING으로 표시된 모든 파일에서. 언어별 패턴과 수정 방법 카탈로그는
   [`skills/fast-tests/references/waits.md`](skills/fast-tests/references/waits.md)(영문)에 있습니다.
4. **병렬화** — 각 파일이 자기만의 temp dir, 포트, 데이터베이스를 쓰는지 확인한 뒤에
   ([격리 체크리스트](skills/fast-tests/references/parallel.md#isolation-checklist), 영문). suite를 세 번 실행해서
   안정적인지 증명하세요.
5. **long pole 쪼개기.** 파일 하나가 전체 시간을 결정하고 있다면.
6. **push 전에는 항상 전체 suite 실행.** 일단 빨라지면, 덜 돌릴 이유가 거의 없습니다.

## 7단계 — 테스트를 추가해도 빠르게 유지하기

빠른 suite는 새 테스트가 같은 규칙을 따를 때만 빠르게 유지됩니다. merge 전에 추가하거나 변경한 테스트 파일을 예산에
비춰 검사하세요 — 시간 제한, 기다림 없음, 그리고 flakiness를 잡기 위한 반복 실행:

```bash
python3 ../../skills/fast-tests/scripts/profile_tests.py --cmd "node --test {file}" \
  --max-seconds 2 --fail-on-waiting --repeat 5 test/sleepy.test.mjs
```

`slow-suite`에서는 실패하고(`OVER 2s`, `WAITING`), `fast-suite`에서는 통과합니다. 위반이 하나라도 있으면 exit code 1로
종료하므로 pull request용 CI job으로 쓸 수 있습니다
([예시](skills/fast-tests/references/new-tests.md#enforce-it-in-ci), 영문). 새 테스트를 위한 설계 체크리스트는
[`references/new-tests.md`](skills/fast-tests/references/new-tests.md)(영문)에 있습니다.

## 8단계 — AI 에이전트에게 맡기기

[`fast-tests` skill](skills/fast-tests/SKILL.md)(영문)은 이 방법 전체를 패키징해서 코딩 에이전트가 직접 할 수 있게
해주고 — 에이전트 자신의 루프에서도 테스트를 효율적으로 실행하게 합니다.

- **Claude Code:** 폴더를 skills 디렉터리에 복사하면, 테스트 이야기가 나올 때 Claude가 이 skill을 사용합니다:
  ```bash
  mkdir -p ~/.claude/skills && cp -R skills/fast-tests ~/.claude/skills/        # 모든 프로젝트
  mkdir -p .claude/skills && cp -R /path/to/skills/fast-tests .claude/skills/    # 프로젝트 하나
  ```
  그리고 이렇게 요청하세요: *"테스트가 느려 — fast-tests skill로 빠르게 만들어줘."*
- **다른 에이전트(Codex, Cursor, Gemini CLI, …):** `AGENTS.md`에 한 줄을 추가하세요:
  *"When tests are slow or flaky, or before changing how tests run, follow `skills/fast-tests/SKILL.md`."*
  gate 명령과 [AGENTS.md snippet](skills/fast-tests/references/agents.md#agentsmd-snippet)(영문)의 규칙도 함께
  추가하세요.

## 왜 지금 중요한가

AI 에이전트는 변경 사항을 몇 초 만에 작성할 수 있습니다. 그다음엔 테스트를 기다립니다 — 매 iteration마다, 모든
에이전트가, 모든 PR에서. 12분짜리 suite로는 시간당 검증된 iteration이 다섯 번 정도지만, 24초짜리 suite라면 150번입니다.
코드가 싸진 시대에는 **검증 속도가 곧 개발 속도**입니다. 근거는 [RESEARCH.md](RESEARCH.md)(영문)에 있습니다.
