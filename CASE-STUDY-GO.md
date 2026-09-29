# Case study (Go): 15 s → 1 s, and the wait that wasn't in the tests

**English** · [한국어](CASE-STUDY-GO.ko.md)

A Go service embedded in a desktop app, written largely by AI coding agents: 16 packages (chat-protocol clients,
an IMAP client, a SQLite full-text index, an HTTP/WebSocket AI client), 374 tests, on a 16-core Mac. Go already
runs packages in parallel, and the tests use `httptest` fakes and `t.TempDir()`, so it looked like there was
nothing to win. There was, and the biggest part wasn't in the test code at all.

## Step 1 — baseline, and the per-test view

```
$ time go test -count=1 ./...
real 14.9s   user 9.3s   sys 9.1s        # 374 tests
```

Per-test durations (`go test -json`, sum of top-level `Elapsed`) added up to 18 s, and three tests were most of it:

| Test | Time | What it waited on |
|---|---|---|
| a "server closed the socket early" error test | 5.00 s | the client's 5 s context timeout |
| a "sent IDs are capped at N" test | 2.65 s | 1,050 atomic file writes |
| a "two quick questions are answered together" test | 0.76 s | `time.Sleep(700 * time.Millisecond)` |

## Step 2 — remove the waits

**The fake that didn't hang up.** The test meant to check the error when the server drops a WebSocket mid-answer:
it called `srv.CloseClientConnections()` after 300 ms. But `httptest.Server` tracks only connections it still owns;
a WebSocket upgrade **hijacks** the connection, so `CloseClientConnections` never touched it. The client waited
for its 5 s context deadline, got a (different) error, and the test passed, for the wrong reason, in 5 s. Fix:
the fake handler returns right after sending its events, which closes the hijacked connection itself.
5.00 s → 0.00 s, now failing the way the test intends.

**Doing N slow things to test a cap.** To check that a list is trimmed to `maxSentIDs`, the test called
`markSent` 1,050 times, and each call saves the whole file atomically (write temp + rename). The behavior under
test is "one more than the cap drops the oldest": fill the list directly to the cap, call `markSent` once, and
assert the oldest is gone and the newest kept. 2.65 s → 0.02 s, with a stronger assertion than before.

**A fixed sleep.** `time.Sleep(700ms)` became a deadline loop that stops as soon as both answers are in, plus a
50 ms settle before asserting "exactly two calls" (so an extra call is still caught). 0.76 s → 0.22 s.

## Step 3 — the wait outside the tests

After Step 2, the tests themselves took about 1 s of CPU in total, yet `go test ./...` still took 7–12 s. Comparing
each package's elapsed time with the sum of its tests:

```
pkg time   tests    gap
  3.84 s   0.05 s   3.79 s   internal/…notify
  3.19 s   0.05 s   3.14 s   connectors/…
  2.88 s   0.00 s   2.88 s   internal/…api
  …
```

Packages with almost no test time spent 2–4 s each **before** their first test. Running one compiled test binary
directly showed why:

```
$ go test -c -o pkg.test ./internal/…api
$ time ./pkg.test   → 0.44 s   (first run of a new binary)
$ time ./pkg.test   → 0.01 s
$ time ./pkg.test   → 0.01 s
```

macOS scans every new executable on its first launch. `go test` links a fresh test binary per package, and with
`-count=1` it runs all 16 every time, so 16 first-launch scans queue up behind each other. No test change fixes
that, and turning off the OS scan isn't an option.

What does fix it: **don't run what didn't change.** The agents had been running `go test -count=1 ./...` by
habit, which disables Go's test cache. These tests are hermetic (fakes on `httptest`, `t.TempDir()`, live API tests
gated behind an env var), so the cache is safe:

| | wall |
|---|---|
| before (`-count=1`) | 14.9 s |
| after Step 2 (`-count=1`) | 7.3–11.8 s (three runs) |
| after, plain `go test ./...`, one package changed | **1.1 s** |

## What we took away

1. **Compare package time with test time.** `go test -json` gives both. A big gap is startup, not tests.
2. **`-count=1` is not "safer".** On hermetic tests it only throws away work; keep it for flaky-hunting or tests
   that touch the outside world, and make those opt-in.
3. **`httptest.Server.CloseClientConnections` doesn't close hijacked (WebSocket) connections.** A test that relies
   on it silently waits for a timeout, and may pass on the wrong error.
4. **To test a limit, start at the limit.** Doing N expensive operations tests the loop, not the limit.
5. **A 5 s test that passes is not fine.** Two of the three slow tests were passing for the wrong reason or with a
   weaker assertion than they could have had.

The same pass over the app's Swift (XCTest) suite took it from 26 s to 11–15 s: a source scan repeated by every
localization test, fixed sleeps in UI tests, a 1.5 s debounce made injectable, and a shared `UserDefaults` suite
that made the tests fail under `swift test --parallel`. It also turned up a real app bug: a "performance" test's
first half showed 400 list updates taking 5 s, which became 0.19 s.
