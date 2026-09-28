// Anti-pattern 2: the code under test leaves a timer running, so the finished file cannot exit.
import { test } from "node:test";
import assert from "node:assert/strict";
import { Metrics } from "../src/metrics.mjs";

test("metrics are counted", () => {
  const m = new Metrics(); // schedules a 5 s upload it never cancels
  m.count("open");
  assert.equal(m.pending.length, 1);
}); // all assertions done in 1 ms; the process lives 5 more seconds
