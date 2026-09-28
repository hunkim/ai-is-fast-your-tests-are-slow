export class Cache {
  constructor({ flushMs = 20_000 } = {}) {
    this.data = new Map(); this.flushed = 0;
    this.timer = setInterval(() => this.flush(), flushMs);
  }
  set(k, v) { this.data.set(k, v); }
  flush() { this.flushed += this.data.size; this.data.clear(); }
  close() { clearInterval(this.timer); }
}
