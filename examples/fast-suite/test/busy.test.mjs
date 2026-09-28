// A test that is slow because it works (CPU-bound): parallelism helps this one, removing waits does not.
import { test } from "node:test";
import assert from "node:assert/strict";

test("prime sieve", () => {
  let count = 0;
  for (let n = 2; n < 6_000_000; n++) { let p = true; for (let d = 2; d * d <= n; d++) if (n % d === 0) { p = false; break; } if (p) count++; }
  assert.ok(count > 400_000);
});
