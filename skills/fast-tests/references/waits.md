# Idle waits: how to find them and how to remove them

A test file is **waiting** when its wall time is much larger than its CPU time. Async waits are the most common
root cause of flaky tests (45% of fixes in Luo et al. 2014), so removing them makes a suite faster *and* more
reliable. Google forbids sleeps in small tests.

## Diagnose: which kind of wait?

1. Get per-test durations from the runner and compare their sum with the file's wall time.
   - Node: `node --test --test-reporter=tap <file>` (each test prints `duration_ms`)
   - Jest: `npx jest <file> --verbose`; Vitest: `npx vitest run <file> --reporter=verbose`
   - pytest: `pytest <file> --durations=0 --durations-min=0.1`
   - Go: `go test -json ./pkg | grep '"Action":"pass"'` (per-test `Elapsed`)
   - RSpec: `rspec <file> --profile 20`; Gradle/JUnit: test report per method
2. **Sum of tests ≪ file wall time** → something outlives the tests (Pattern D).
3. **One test ≈ the wall time** → that test sleeps, backs off, or times out (Patterns A–C, E).

## Pattern A — fixed sleep to wait for something

```js
await new Promise((r) => setTimeout(r, 2100)); // ✗ waits the full time, and is flaky under load
```

Fix: wait for the **condition**, with a generous deadline (the deadline is an upper bound, not the expected time).

```js
// JS: a tiny helper (or testing-library waitFor / vi.waitFor)
async function waitFor(check, { timeout = 5000, interval = 10 } = {}) {
  const end = Date.now() + timeout;
  for (;;) {
    try { return await check(); } catch (e) { if (Date.now() > end) throw e; }
    await new Promise((r) => setTimeout(r, interval));
  }
}
await waitFor(() => assert.equal(cache.flushed, 1));
```

- Python: poll with `time.monotonic()` deadline; with asyncio, `await asyncio.wait_for(event.wait(), 5)`.
- JVM: Awaitility `await().atMost(Duration.ofSeconds(5)).until(() -> cache.flushed() == 1);`
- Go: `require.Eventually(t, func() bool { return c.Flushed() == 1 }, 5*time.Second, 10*time.Millisecond)` (testify),
  or a channel the code signals.
- Browser E2E: Playwright web-first assertions auto-wait (`await expect(locator).toBeVisible()`); never
  `page.waitForTimeout(ms)`. Capybara `expect(page).to have_content(...)` waits; Cypress `cy.get(...).should(...)`
  retries; never `cy.wait(2000)`.

## Pattern A2 — doing N slow things to test a limit

To check "the list keeps at most N" or "the 1000th call is rejected", tests often do the slow operation N times
(each one writing a file, a DB row, a request). Start at the limit instead: fill the state directly to N, do the
operation once, and assert what one more does (the oldest dropped, the call rejected). Faster and a sharper test.

## Pattern B — waiting out a real interval or timeout

The code flushes every 20 s, debounces for 5 s, expires after 30 s, and the test waits that long.

Fix 1 — **control the clock** (fast and deterministic):

| Runner | Fake timers |
|---|---|
| Node `node:test` | `t.mock.timers.enable({ apis: ["setTimeout", "setInterval", "Date"] }); t.mock.timers.tick(20_000);` |
| Jest | `jest.useFakeTimers(); jest.advanceTimersByTime(20_000);` (`await jest.advanceTimersByTimeAsync(ms)` when promises are involved) |
| Vitest | `vi.useFakeTimers(); vi.advanceTimersByTime(20_000);` / `await vi.advanceTimersByTimeAsync(ms)`; `vi.setSystemTime(date)` |
| sinon | `const clock = sinon.useFakeTimers(); clock.tick(20_000);` |
| Playwright | `await page.clock.install(); await page.clock.fastForward("00:20");` |
| Python | `time-machine` (`time_machine.travel(dt, tick=False)`) or `freezegun` (`@freeze_time(...)`) for wall-clock time; inject a clock or scheduler for timers |
| Go | inject a clock interface; Go 1.25+: `synctest.Test(t, func(t *testing.T) { ... })` runs code with a fake clock in a bubble |
| JVM | inject `java.time.Clock` (`Clock.fixed(...)`, or a mutable test clock); schedulers take the clock |
| Rust (tokio) | `#[tokio::test(start_paused = true)]` then `tokio::time::advance(Duration::from_secs(20)).await` |
| Rails | `travel_to(time) { ... }` (ActiveSupport TimeHelpers); `travel 20.seconds` |

Fix 2 — **make the interval configurable** and shorten it in tests (`FLUSH_MS=500` env var, constructor option).
Use this when the test runs a real server in a child process, where fake timers can't reach.

## Pattern C — retry with backoff triggered by the test

A mock that throws (network error) or returns a retryable status (502/503/504, 429) makes the client wait
0.5 + 1 + 2 + … seconds before giving up.

Fix:
- Simulate the failure you mean. "The load failed" is usually an HTTP error the client does *not* retry
  (`new Response("{}", { status: 500 })` when only 502–504 are retried). Throw only to test the retry itself.
- Inject the delays: `getJson(path, { delays: [0, 0, 0] })`, or `retries: 0` in the test client config
  (`urllib3.Retry(total=0)`, `axios-retry` `retries: 0`, OkHttp interceptor off).
- With fake timers, advance through the backoff.

## Pattern D — a finished test process that won't exit

Tests pass in milliseconds, but the process lives 5–30 s more (or forever). Something keeps the event loop or
interpreter alive: a `setInterval`/`setTimeout` scheduled by app code (metrics flush, polling, debounce), an open
socket or server, a DB pool, a child process, a non-daemon thread, a pending promise.

Find it:
- Jest: `npx jest --detectOpenHandles <file>`
- Node: `npx why-is-node-running` (or log `process.getActiveResourcesInfo()` in an `after` hook)
- Python: at session end, `threading.enumerate()`; `faulthandler.dump_traceback_later(10)` to see where it hangs
- Go: `go.uber.org/goleak` (`defer goleak.VerifyNone(t)`)
- JVM: thread dump (`jstack <pid>`) of the hanging fork

Fix, in order of preference:
1. **Stop it in teardown** (close the server, pool, socket; cancel the timer; `clearInterval`).
2. **Don't let background timers hold a process** — in app code: `setTimeout(...).unref?.()` (a no-op in browsers),
   `threading.Thread(daemon=True)`, `Timer` as daemon. A background flush or poll is never a reason for a process
   to stay alive.
3. **In the test setup, for code you can't change** (e.g. a browser app under a Node test runner): wrap
   `setTimeout`/`setInterval` so timers ≥ 1 s are `unref`'d, and keep one ref'd handle alive until the file's
   tests finish (`after(() => clearInterval(keepAlive))`), so tests that *await* a long timer still work.
   Guard it with a regression test: a fixture that leaves 30 s timers behind must exit in a few seconds.

Never "fix" it with `--forceExit` (Jest), `--exit` (Mocha), `--test-force-exit` (Node) or `os._exit` in
conftest: they hide leaks that can also leak state between tests.

## Pattern E — real network, DNS, or service boot

- Calls to real hosts: slow, flaky, and not isolated. Replace with a local fake server on port 0
  (`http.createServer().listen(0)`, `httptest.NewServer`, `pytest-httpserver`, WireMock dynamic port) or a stub.
- DNS lookups for unresolvable hosts can take seconds: use `127.0.0.1` / `.invalid` / `.test` names.
- Go: `httptest.Server.CloseClientConnections()` doesn't close **hijacked** connections (WebSocket, `Hijacker`).
  A test that "drops the connection" with it waits for the client's timeout instead, and may pass on the wrong
  error. Have the fake handler return (or close the conn) itself.
- Booting a DB/browser/container per test: boot **once per worker**, isolate by schema, transaction rollback, or
  temp dir. Testcontainers: a singleton container per JVM/worker; Playwright: one browser per worker, one context
  per test.

## Pattern F — slow imports and startup

Each test process pays interpreter start, transpile, and imports.
- Go: compare each package's elapsed time with the sum of its tests (`go test -json`). A package with ~0 s of tests
  and seconds of elapsed time is paying startup. On macOS the first launch of every freshly linked test binary is
  scanned by the OS (~0.4 s, much more when 16 queue up at once). Don't defeat Go's test cache with `-count=1` on
  hermetic tests: unchanged packages then cost nothing. [Case study](../../../CASE-STUDY-GO.md)
- Node/TS: prefer a fast transpiler (tsx/esbuild/swc); Vitest: `NODE_COMPILE_CACHE=...`; avoid jsdom where node
  env suffices.
- Python: `python -X importtime -c "import yourpkg" 2> import.log` to find heavy imports; import lazily in hot paths.
- JVM: reuse forks (Surefire `reuseForks=true`); Gradle daemon and configuration cache.
- Rails: Spring / bootsnap.

## Lint against regressions

Run `scripts/scan_test_smells.py` in CI (or a pre-commit hook) and fail on new `sleep` hits in unit-test
directories. Allow exceptions with an inline justification.
