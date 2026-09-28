export class Metrics {
  pending = [];
  count(name) {
    this.pending.push(name);
    if (!this.timer) {
      this.timer = setTimeout(() => this.upload(), 5000);
      this.timer.unref?.(); // Fix 2: a background upload must not keep a process alive (no-op in browsers)
    }
  }
  upload() { this.pending = []; this.timer = undefined; }
}
