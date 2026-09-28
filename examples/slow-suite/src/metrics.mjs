export class Metrics {
  pending = [];
  count(name) {
    this.pending.push(name);
    this.timer ??= setTimeout(() => this.upload(), 5000); // fine in a browser, holds a Node process open
  }
  upload() { this.pending = []; this.timer = undefined; }
}
