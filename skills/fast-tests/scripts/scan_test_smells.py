#!/usr/bin/env python3
"""Find the test-code patterns that make suites slow or unsafe to run in parallel.

  scan_test_smells.py [paths...]          default: current directory
  scan_test_smells.py tests/ --json out.json

Reports, per file and line:
  sleep          fixed waits (sleep/setTimeout/Thread.sleep/waitForTimeout ≥ 100 ms): wait for a condition or fake the clock
  fixed-port     hard-coded ports: ask the OS for a free one (port 0) so files can run side by side
  fixed-path     hard-coded /tmp or shared paths: use a per-test temp directory
  real-network   calls to real hosts from tests: slow, flaky, and not isolated
  retry-flaky    retry/rerun annotations: hide flakiness instead of fixing it
  serial-only    settings that force serial execution: find the shared state instead
  focused        .only / fit / fdescribe left in: silently skips the rest of the suite

It is a heuristic grep, not a parser: treat hits as places to look. Only the Python standard library is used.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

TEST_FILE = re.compile(r"(^|/)(test_[^/]*\.py|[^/]*_test\.(py|go|rb|exs?)|[^/]*[._-](test|spec)\.[cm]?[jt]sx?|[^/]*Tests?\.(java|kt|cs|swift|scala)|[^/]*_spec\.rb|conftest\.py)$")
TEST_DIR = re.compile(r"(^|/)(tests?|__tests__|spec|e2e|integration)/")
SKIP_DIRS = {"node_modules", ".git", "dist", "build", "target", ".venv", "venv", "__pycache__", ".next", "coverage", "vendor"}
CONFIG_FILE = re.compile(r"(^|/)(jest\.config\.[cm]?[jt]s|vitest\.config\.[cm]?[jt]s|playwright\.config\.[cm]?[jt]s|pytest\.ini|setup\.cfg|tox\.ini|pyproject\.toml|package\.json|\.mocharc\.[a-z]+|build\.gradle(\.kts)?|pom\.xml)$")

MS = r"(\d[\d_]*)"
RULES: list[tuple[str, re.Pattern, callable | None]] = [
    # JS/TS: setTimeout(resolve, 2000), sleep(2000), delay(1500), page.waitForTimeout(3000), cy.wait(2000)
    ("sleep", re.compile(r"setTimeout\(\s*\w+\s*,\s*" + MS + r"\s*\)"), lambda m: int(m.group(1).replace("_", "")) >= 100),
    ("sleep", re.compile(r"\b(?:sleep|delay|wait|pause)\(\s*" + MS + r"\s*\)"), lambda m: int(m.group(1).replace("_", "")) >= 100),
    ("sleep", re.compile(r"\b(?:waitForTimeout|cy\.wait)\(\s*" + MS), lambda m: int(m.group(1).replace("_", "")) >= 100),
    # Python time.sleep(0.5) / asyncio.sleep(2)
    ("sleep", re.compile(r"\b(?:time|asyncio|gevent|trio)\.sleep\(\s*([\d.]+)\s*\)"), lambda m: float(m.group(1)) >= 0.1),
    # Java/Kotlin Thread.sleep(1000), TimeUnit.SECONDS.sleep(1)
    ("sleep", re.compile(r"Thread\.sleep\(\s*" + MS), lambda m: int(m.group(1).replace("_", "")) >= 100),
    ("sleep", re.compile(r"TimeUnit\.\w+\.sleep\("), None),
    # Go time.Sleep(2 * time.Second) / time.Sleep(500 * time.Millisecond)
    ("sleep", re.compile(r"time\.Sleep\(\s*(\d+)\s*\*\s*time\.(Second|Millisecond|Minute)"), lambda m: m.group(2) != "Millisecond" or int(m.group(1)) >= 100),
    # Ruby sleep 1 / sleep(0.5)
    ("sleep", re.compile(r"^\s*sleep[\s(]+([\d.]+)"), lambda m: float(m.group(1)) >= 0.1),
    # Rust std::thread::sleep(Duration::from_secs(1)) / tokio::time::sleep(Duration::from_millis(500))
    ("sleep", re.compile(r"sleep\(\s*Duration::from_(secs|millis)\(\s*(\d+)"), lambda m: m.group(1) == "secs" or int(m.group(2)) >= 100),
    ("fixed-port", re.compile(r"\b(?:listen|port\s*[:=]|PORT\s*[:=]|bind)\s*\(?\s*['\"]?(?:(?:localhost|127\.0\.0\.1|0\.0\.0\.0)?:)?(\d{4,5})\b"), lambda m: m.group(1) not in {"0"}),
    ("fixed-port", re.compile(r"(?:localhost|127\.0\.0\.1):(\d{4,5})\b"), None),
    ("fixed-path", re.compile(r"['\"](/tmp/[^'\"]+|/var/tmp/[^'\"]+|C:\\\\Temp\\\\[^'\"]+)['\"]"), None),
    # only URLs handed straight to a network call; URLs as test data are fine
    ("real-network", re.compile(r"\b(?:fetch|urlopen|axios(?:\.\w+)?|requests\.\w+|httpx\.\w+|http\.(?:Get|Post|get|request)|got|superagent\.\w+|RestTemplate\.\w+|HttpRequest\.newBuilder|reqwest::get|Net::HTTP\.\w+|open-uri|curl)\s*\(?\s*[\x27\x22`]https?://(?!localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|[\w.-]*example\.(?:com|org|net)|[\w.-]+\.(?:test|example|invalid|localhost)\b)"), None),
    ("retry-flaky", re.compile(r"@(?:flaky|pytest\.mark\.flaky|RepeatedTest|Retry|RetryingTest)\b|\bjest\.retryTimes\(|\bretries\s*:\s*[1-9]|\bthis\.retries\(|--reruns\b|rerunFailingTestsCount"), None),
    ("serial-only", re.compile(r"--runInBand|\b-i\b(?=.*jest)|--test-concurrency=1\b|maxWorkers\s*:\s*1\b|--maxWorkers=1\b|fileParallelism\s*:\s*false|singleThread\s*:\s*true|workers\s*:\s*1\b|-p\s+no:xdist|maxParallelForks\s*=\s*1\b|--test-threads=1\b|-parallel\s+1\b|-p\s+1\b(?=.*go test)"), None),
    ("focused", re.compile(r"\b(?:describe|it|test|context)\.only\(|\bf(?:it|describe)\(|@pytest\.mark\.only\b|\.only\s*=\s*true"), None),
]
ADVICE = {
    "sleep": "wait for the condition (poll with a deadline) or fake the clock; make app intervals configurable",
    "fixed-port": "bind port 0 and read the assigned port, so files can run side by side",
    "fixed-path": "use a per-test temp dir (mkdtemp / tmp_path / t.TempDir / Files.createTempDirectory)",
    "real-network": "stub the host or run a local fake; real hosts make tests slow and flaky",
    "retry-flaky": "find the root cause (timing, order, shared state) instead of rerunning",
    "serial-only": "find the shared state that forces serial runs, isolate it, then run in parallel",
    "focused": "remove before committing: the rest of the suite is silently skipped",
}


def scan_file(path: str, rules: list, is_config: bool) -> list[dict]:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return []
    hits = []
    for i, line in enumerate(lines, 1):
        if len(line) > 2000:
            continue
        for kind, rx, keep in rules:
            if is_config and kind not in ("serial-only", "retry-flaky"):
                continue
            for m in rx.finditer(line):
                try:
                    if keep and not keep(m):
                        continue
                except ValueError:
                    continue
                hits.append({"file": path, "line": i, "kind": kind, "text": line.strip()[:160]})
                break
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", default=["."])
    ap.add_argument("--json", metavar="PATH")
    ap.add_argument("--all-files", action="store_true", help="scan every source file, not only test files")
    args = ap.parse_args()

    hits: list[dict] = []
    for root in args.paths:
        walk = [(os.path.dirname(root), [], [os.path.basename(root)])] if os.path.isfile(root) else os.walk(root)
        for d, dirs, files in walk:
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            for name in files:
                p = os.path.join(d, name) if d else name
                rel = p.replace(os.sep, "/")
                is_config = bool(CONFIG_FILE.search(rel))
                is_test = bool(TEST_FILE.search(rel) or (TEST_DIR.search(rel) and re.search(r"\.(py|[cm]?[jt]sx?|go|rb|java|kt|rs|cs|swift|scala|exs?)$", rel)))
                if is_test or is_config or (args.all_files and re.search(r"\.(py|[cm]?[jt]sx?|go|rb|java|kt|rs)$", rel)):
                    hits.extend(scan_file(p, RULES, is_config and not is_test))

    by_kind: dict[str, list[dict]] = {}
    for h in hits:
        by_kind.setdefault(h["kind"], []).append(h)
    if not hits:
        print("no smells found")
    for kind, hs in sorted(by_kind.items(), key=lambda kv: -len(kv[1])):
        print(f"\n{kind} ({len(hs)}): {ADVICE[kind]}")
        for h in hs[:25]:
            print(f"  {h['file']}:{h['line']}  {h['text']}")
        if len(hs) > 25:
            print(f"  … {len(hs) - 25} more")
    if args.json:
        with open(args.json, "w") as f:
            json.dump(hits, f, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
