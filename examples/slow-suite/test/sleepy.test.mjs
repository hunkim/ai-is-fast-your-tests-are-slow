// Anti-pattern 1: sleeping for an interval instead of waiting for a condition.
import { test } from "node:test";
import assert from "node:assert/strict";
import { Cache } from "../src/cache.mjs";

test("the cache flushes to disk", async () => {
  const cache = new Cache({ flushMs: 2000 });
  cache.set("a", 1);
  await new Promise((r) => setTimeout(r, 2100)); // waits the real flush interval
  assert.equal(cache.flushed, 1);
  cache.close();
});
