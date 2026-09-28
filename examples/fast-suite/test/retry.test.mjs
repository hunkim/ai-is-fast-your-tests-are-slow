// Fix 3: simulate the failure you mean. "The load failed" is an HTTP error, which is not retried.
// (To test the retry itself, inject the delays: getJson(path, { fetch, delays: [0, 0, 0] }).)
import { test } from "node:test";
import assert from "node:assert/strict";
import { getJson } from "../src/client.mjs";

test("a failed load returns nothing", async () => {
  const fetch = async () => new Response("{}", { status: 500 });
  assert.equal(await getJson("/x", { fetch }), undefined);
});
