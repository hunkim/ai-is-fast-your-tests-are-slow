const RETRY_DELAYS = [500, 1000, 2000];
export async function getJson(path, { fetch = globalThis.fetch } = {}) {
  for (let attempt = 0; ; attempt++) {
    try {
      const res = await fetch(path);
      if (!res.ok) return undefined; // an HTTP error is an answer: not retried
      return await res.json();
    } catch {
      if (attempt >= RETRY_DELAYS.length) return undefined; // network error: retried with backoff
      await new Promise((r) => setTimeout(r, RETRY_DELAYS[attempt]));
    }
  }
}
