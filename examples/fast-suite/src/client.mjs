export const RETRY_DELAYS = [500, 1000, 2000];
export async function getJson(path, { fetch = globalThis.fetch, delays = RETRY_DELAYS } = {}) {
  for (let attempt = 0; ; attempt++) {
    try {
      const res = await fetch(path);
      if (!res.ok) return undefined; // an HTTP error is an answer: not retried
      return await res.json();
    } catch {
      if (attempt >= delays.length) return undefined; // network error: retried with backoff
      await new Promise((r) => setTimeout(r, delays[attempt]));
    }
  }
}
