// Fix 1: control the clock instead of waiting for it (node:test mock timers; Jest/Vitest/sinon have the same).
import { test } from "node:test";
import assert from "node:assert/strict";
import { Cache } from "../src/cache.mjs";

test("the cache flushes to disk", (t) => {
  t.mock.timers.enable({ apis: ["setInterval"] });
  const cache = new Cache({ flushMs: 2000 });
  cache.set("a", 1);
  t.mock.timers.tick(2000); // two seconds pass instantly
  assert.equal(cache.flushed, 1);
  cache.close();
});
