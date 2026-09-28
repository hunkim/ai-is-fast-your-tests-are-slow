# AI is fast. Your tests are slow.

**Your AI is waiting on your tests.** In the AI coding era, generating a change takes seconds; verifying it is the
bottleneck. And most of that verification time is not work at all: it is waiting.

> 🚧 Work in progress. The research survey, tutorial and full agent skill are being written. What is here now:

- [`CASE-STUDY.md`](CASE-STUDY.md) — a real production monorepo: **12 minutes → 24 seconds** (~30×), and why test
  selection was the least effective fix.
- [`examples/`](examples) — a tiny suite with the three waits we found in practice (`slow-suite`, 12.0 s) and the same
  suite fixed (`fast-suite`, 1.1 s).
- [`skills/fast-tests/scripts/profile_tests.py`](skills/fast-tests/scripts/profile_tests.py) — profile any test
  suite file by file: wall time vs CPU time, which files are *waiting*, the long pole, and projected time per
  worker count. Language-agnostic, Python standard library only.
- [`skills/fast-tests/scripts/scan_test_smells.py`](skills/fast-tests/scripts/scan_test_smells.py) — find sleeps,
  fixed ports and paths, real network calls, retry annotations and serial-only settings in test code.

## Try it in one minute

```bash
git clone https://github.com/hunkim/ai-is-fast-your-tests-are-slow && cd ai-is-fast-your-tests-are-slow/examples/slow-suite
python3 ../../skills/fast-tests/scripts/profile_tests.py --cmd "node --test {file}" "test/*.test.mjs"
```

```
test/lingering-timer.test.mjs      5.1      0.1     2%  WAITING
test/retry.test.mjs                3.6      0.1     2%  WAITING
test/sleepy.test.mjs               2.2      0.1     4%  WAITING
test/busy.test.mjs                 1.0      1.0    98%
…
waiting: 3 units spend ~10.6 s (85% of serial time) not using the CPU
```

The same profiler works for pytest, Jest, Vitest, Go, cargo, RSpec: anything you can run one file (or package) at
a time: `--cmd "python -m pytest -q {file}"`, `--cmd "npx jest {file}"`, `--cmd "go test ./{file}"`.

## License

MIT
