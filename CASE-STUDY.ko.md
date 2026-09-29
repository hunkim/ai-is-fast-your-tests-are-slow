# 케이스 스터디: 12분 → 24초

[English](CASE-STUDY.md) · **한국어** · [日本語](CASE-STUDY.ja.md) · [中文](CASE-STUDY.zh.md)

실제 프로덕션 TypeScript monorepo(Node 서버와 React 웹 앱, 대부분 AI 코딩 에이전트가 작성): 테스트 파일 120개,
테스트 ~900개, `tsx`를 통한 `node:test`. 팀의 불만은 "테스트가 너무 느리다. 이제 프로젝트가 커져서 테스트가 병목이다"였습니다.
요청은 변경 기반 테스트 selection에 관한 연구를 적용해 달라는 것이었습니다.

## 예상한 것 vs 실제로 발견한 것

**예상:** 테스트를 덜 돌린다 — 변경이 영향을 줄 수 있는 테스트만 고른다.

**발견:** repo에는 이미 정적인 파일 수준 selector(`check:changed`, Ekstazi/STARTS와 같은 아이디어)가 있었고,
거의 도움이 되지 않았습니다. 최근 커밋 세 개에 걸친 diff가 서버 파일 **56/59**개, 웹 파일 **54/61**개를 선택했습니다.
허브 모듈(`store.ts`, `db.ts`)이 직접 또는 전이적으로 거의 모든 테스트에서 import되기 때문입니다. 이것이 의존성 기반
selection의 알려진 약점입니다: 허브가 있는 코드베이스에서는 대부분의 변경이 대부분의 테스트에 닿습니다.

게다가 suite는 16코어 머신에서 **직렬로**(`--test-concurrency=1`) 돌고 있었습니다.

## 1단계 — 수정 방법을 고르기 전에 측정하기

| Suite | 테스트 | 직렬 wall time |
|---|---|---|
| server | 372 | 65 s |
| web | 522 | **667 s** |

파일별 profiling(wall time vs CPU time, 파일당 프로세스 하나)을 해보니 웹 쪽 수치는 대부분 유휴 시간이었습니다:

```
unit                      wall s   cpu s   cpu%
test/nav.test.ts            30.3     0.5     1%   ← 테스트 22개, 전부 30 ms 안에 끝남
test/store.test.ts          31.0     …       …
… 파일 22개가 ~30 s, 나머지는 < 1 s
```

테스트는 30 ms 만에 끝나는데 프로세스가 30 s 동안 살아 있는 파일은 일하는 게 아니라 **기다리는** 것입니다.
병렬화는 그 기다림을 겹쳐 놓았을 뿐이었을 겁니다.

## 2단계 — 기다림 제거하기 (가장 큰 성과)

| 근본 원인 | 위치 | 영향 | 수정 |
|---|---|---|---|
| 앱의 백그라운드 타이머(perf-metrics flush 30 s, polling 20 s, toast/mark-read debounce)가 이미 끝난 테스트 프로세스를 계속 살려 둠 | 웹 파일 22개 | 마지막 테스트 이후 파일당 ~30 s | 웹 테스트 setup에서 1 s 이상의 타이머는 `unref`하고, ref된 handle 하나가 파일의 테스트가 끝날 때까지(`after()`) 프로세스를 살려 두므로 타이머를 *기다리는* 테스트도 그대로 동작 |
| Mock API route가 `throw` → 클라이언트가 네트워크 에러로 처리 → GET retry backoff(0.5+1+2+3+4+5+5 s) | 웹 테스트 2개 | 각 ~20 s | `HTTP 500`으로 응답(retry되지 않음). retry 자체를 테스트할 때만 throw |
| 20 s 간격의 vault flush를 기다리려고 테스트에서 `sleep(21_000)` | 서버 테스트 1개 | 21 s | 간격을 env로 설정 가능하게(`VAULT_FLUSH_MS=500`), 테스트는 1 s 대기 |
| 5 s debounce 캐시 쓰기 타이머가 `unref`되지 않음 | 서버 파일 3개 | 각 5 s | `.unref()`(코드베이스에서 vault flush에는 이미 이렇게 하고 있었음) |

결과, 여전히 직렬 상태에서: 웹 **667 s → 79 s**, 서버 65 s → ~35 s.

## 3단계 — 병렬화 (테스트가 이미 격리되어 있었기에 안전)

모든 테스트 파일이 이미 DB/vault 파일용으로 자기만의 `mkdtemp` 디렉터리와 OS가 할당한 포트(`port 0`)를 쓰고 있었고,
`node:test`는 각 파일을 별도 프로세스에서 실행합니다. 그래서 동시성을 올리는 건 flag 하나 바꾸는 일이었습니다:
`--test-concurrency=${TEST_WORKERS:-10}`. selective runner는 두 앱을 동시에 실행하도록 변경했습니다.

| | Before | After |
|---|---|---|
| server | 65 s | 9 s |
| web | 667 s | ~15 s |
| 전체 gate(`typecheck + all tests`) | ~12 min | **~24 s** |

연속 세 번의 전체 실행: 실패 0, 취소 0. 병렬화만 했을 때(기다림 제거 전)는 12분 → 2분이었습니다.
24초가 된 건 기다림을 먼저 제거했기 때문입니다. long pole(30초짜리 유휴 파일)이 사라졌으니까요.

## 4단계 — 정책 바꾸기

전체 suite가 24초가 되자, gate로서의 selection은 그 위험을 감수할 가치가 없어졌습니다:

- pre-push hook이 이제 **모든** 테스트를 실행합니다(이전에는 type-check만 했고, auto-deploy도 type-check만 하므로
  테스트가 코드를 gate하는 곳은 hook입니다).
- `check:changed`는 편집 중의 inner loop용으로 남겨 두되, 절대 gate로 쓰지 않습니다.

## 5단계 — 고정하기

- regression 테스트가 30 s / 20 s 타이머를 남겨 두고 1.2 s 타이머를 기다리는 fixture 파일을 실행합니다. 이 파일은
  < 10 s 안에 종료되어야 합니다. setup 수정을 끄면 실패하고(프로세스가 종료되지 않음 → 10 s timeout), 켜면 1.5 s.
- 문서로 적은 테스트 가이드라인(독립성 규칙, "시계를 기다리지 말 것", profiling 방법).
- 프로젝트의 lessons 파일에 교훈 하나: *느린 테스트는 일이 아니라 기다림이다*.

## 핵심 정리

1. **먼저 파일별로 wall vs CPU를 profiling하라.** 이 suite 시간의 85–90%가 유휴 상태였습니다.
2. **허브가 많은 코드에서 selection은 기대에 못 미친다.** 가장 먼저 떠올린 아이디어였고, 여기서는 가장 효과가 적었습니다.
3. **병렬화에는 격리가 필요하고, long pole이 상한을 정한다.** 오래 기다리는 파일부터 없애세요.
4. **전체 suite가 빠르면 전부 돌려라.** selection은 inner loop용 도구이고, gate는 완전해야 합니다.
5. **에이전트가 이걸 더 중요하게 만든다.** 에이전트의 매 iteration과 에이전트가 작성한 모든 PR이 suite의 latency를
   치릅니다. 검사 한 번에 12분이면 시간당 검증된 iteration은 손에 꼽을 정도이고, 24초면 백 번이 넘습니다.
