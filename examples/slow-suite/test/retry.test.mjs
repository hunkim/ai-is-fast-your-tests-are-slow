// Anti-pattern 3: simulating a failure the client treats as retryable, so the test sits through the backoff.
import { test } from "node:test";
import assert from "node:assert/strict";
import { getJson } from "../src/client.mjs";

test("a failed load returns nothing", async () => {
  const fetch = async () => { throw new Error("network down"); }; // retried: 0.5 + 1 + 2 s
  assert.equal(await getJson("/x", { fetch }), undefined);
});
