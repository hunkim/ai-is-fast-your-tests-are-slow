#!/usr/bin/env python3
"""Profile a test suite file by file: wall time vs CPU time, and what parallelism would buy.

A test file whose wall time is much larger than its CPU time is *waiting* (sleeps, retries with backoff, timers that
keep the process alive, network timeouts), not working. Removing those waits usually beats any amount of
parallelism or test selection, and it is what makes parallelism pay off at all.

Usage:
  profile_tests.py --cmd "node --test {file}" "test/**/*.test.js"
  profile_tests.py --cmd "python -m pytest -q {file}" "tests/test_*.py" --workers 8
  profile_tests.py --cmd "go test ./{file}" pkg/a pkg/b          # {file} can be any unit: file, package, module
  profile_tests.py --cmd "..." --json report.json "..."           # machine-readable output for agents

Only the Python 3.8+ standard library is used. Per-process CPU comes from os.wait4 (Linux, macOS, BSD).
"""
from __future__ import annotations

import argparse
import glob
import heapq
import json
import os
import shlex
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

WAITING_RATIO = 0.35  # CPU / wall below this, on a file that takes a while, means it mostly waits
WAITING_MIN_S = 1.5


def run_one(cmd_template: str, unit: str, cwd: str | None, timeout: float) -> dict:
    cmd = cmd_template.replace("{file}", shlex.quote(unit))
    t0 = time.perf_counter()
    # A new session, so a timeout can kill the whole process group (test runners spawn children).
    p = subprocess.Popen(cmd, shell=True, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, start_new_session=True)
    err_chunks: list[bytes] = []
    reader = threading.Thread(target=lambda: err_chunks.append(p.stderr.read() if p.stderr else b""), daemon=True)
    reader.start()
    timed_out = False
    deadline = t0 + timeout
    while True:
        pid, status, usage = os.wait4(p.pid, os.WNOHANG)
        if pid:
            break
        if time.perf_counter() > deadline:
            timed_out = True
            try:
                os.killpg(p.pid, 9)
            except ProcessLookupError:
                pass
            pid, status, usage = os.wait4(p.pid, 0)
            break
        time.sleep(0.02)
    wall = time.perf_counter() - t0
    reader.join(timeout=1)
    # rusage of the shell includes its waited-for children (the test runner and anything it spawned and reaped).
    cpu = usage.ru_utime + usage.ru_stime
    code = os.waitstatus_to_exitcode(status) if hasattr(os, "waitstatus_to_exitcode") else status >> 8
    return {
        "unit": unit,
        "wall_s": round(wall, 3),
        "cpu_s": round(cpu, 3),
        "cpu_ratio": round(cpu / wall, 3) if wall > 0 else 0.0,
        "exit": "timeout" if timed_out else code,
        "stderr_tail": b"".join(err_chunks).decode(errors="replace")[-400:] if (timed_out or code) else "",
    }


def lpt_makespan(durations: list[float], workers: int) -> float:
    """Longest-processing-time-first schedule: a good estimate of wall time with N workers."""
    loads = [0.0] * max(1, workers)
    heapq.heapify(loads)
    for d in sorted(durations, reverse=True):
        heapq.heappush(loads, heapq.heappop(loads) + d)
    return max(loads)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cmd", required=True, help='command template; {file} is replaced by each unit, e.g. "npx jest {file}"')
    ap.add_argument("units", nargs="+", help="test files/globs (** allowed) or any units the command accepts")
    ap.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 4), help="files profiled at once (default: min(8, CPUs))")
    ap.add_argument("--cwd", default=None, help="directory to run the command in")
    ap.add_argument("--timeout", type=float, default=600, help="seconds before a file is killed (default 600)")
    ap.add_argument("--top", type=int, default=15, help="rows to print (default 15)")
    ap.add_argument("--json", metavar="PATH", help="also write the full report as JSON")
    args = ap.parse_args()

    units: list[str] = []
    for u in args.units:
        matches = sorted(glob.glob(u, recursive=True, root_dir=args.cwd)) if any(c in u for c in "*?[") else [u]
        units.extend(m for m in matches if m not in units)
    if not units:
        print("no test files matched", file=sys.stderr)
        return 2

    print(f"profiling {len(units)} units, {args.workers} at a time …", file=sys.stderr)
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(lambda u: run_one(args.cmd, u, args.cwd, args.timeout), units))
    elapsed = time.perf_counter() - t0
    rows.sort(key=lambda r: r["wall_s"], reverse=True)

    total_wall = sum(r["wall_s"] for r in rows)
    total_cpu = sum(r["cpu_s"] for r in rows)
    waiting = [r for r in rows if r["wall_s"] >= WAITING_MIN_S and r["cpu_ratio"] < WAITING_RATIO]
    failed = [r for r in rows if r["exit"] != 0]
    wait_s = sum(r["wall_s"] - r["cpu_s"] for r in waiting)
    durations = [r["wall_s"] for r in rows]
    longest = rows[0]["wall_s"]
    cpus = os.cpu_count() or 1
    projections = {n: round(lpt_makespan(durations, n), 1) for n in sorted({1, 2, 4, 8, 10, 16, cpus})}

    w = max(len(r["unit"]) for r in rows[: args.top])
    print(f"\n{'unit':<{w}}  {'wall s':>7}  {'cpu s':>7}  {'cpu%':>5}  note")
    for r in rows[: args.top]:
        note = []
        if r in waiting:
            note.append("WAITING")
        if r["exit"] != 0:
            note.append(f"exit={r['exit']}")
        print(f"{r['unit']:<{w}}  {r['wall_s']:>7.1f}  {r['cpu_s']:>7.1f}  {r['cpu_ratio'] * 100:>4.0f}%  {' '.join(note)}")

    print(f"\n{len(rows)} units · serial sum {total_wall:.1f} s · CPU {total_cpu:.1f} s · profiled in {elapsed:.1f} s")
    print(f"waiting: {len(waiting)} units spend ~{wait_s:.1f} s ({wait_s / total_wall * 100 if total_wall else 0:.0f}% of serial time) not using the CPU")
    print("projected wall time by workers (LPT schedule): " + ", ".join(f"{n}→{s}s" for n, s in projections.items()))
    print(f"long pole: {rows[0]['unit']} ({longest:.1f} s) — no worker count can finish faster than this")
    if failed:
        print(f"\n{len(failed)} units failed or timed out when run alone (order/shared-state dependence?):")
        for r in failed[:10]:
            print(f"  {r['unit']} exit={r['exit']} {r['stderr_tail'].strip().splitlines()[-1] if r['stderr_tail'].strip() else ''}")
    print("\nnext: fix WAITING units first (sleeps, retry backoff, open timers/handles, network timeouts),"
          "\n      then split the long pole, then raise workers. See the fast-tests skill.")

    if args.json:
        with open(args.json, "w") as f:
            json.dump({"units": rows, "serial_wall_s": round(total_wall, 1), "cpu_s": round(total_cpu, 1), "waiting_units": [r["unit"] for r in waiting],
                       "waiting_s": round(wait_s, 1), "projected_wall_s": projections, "long_pole": rows[0]["unit"], "cpus": cpus}, f, indent=2)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
