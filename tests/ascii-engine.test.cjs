const assert = require('node:assert/strict');
const { performance } = require('node:perf_hooks');
const engine = require('../desktop/screensavers/AsciiEngine.js');

for (let scene = 0; scene < 4; scene++) {
  for (const [cols, rows] of [[48, 28], [80, 40], [160, 56], [180, 76]]) {
    const a = engine.frame(cols, rows, 0, scene);
    const b = engine.frame(cols, rows, 2.25, scene);
    assert.equal(a.text.length, cols * rows);
    assert.match(a.text, /OMARCHY/);
    assert.match(a.text, /^[\x20-\x7e]+$/);
    assert.notEqual(a.text, b.text, `${scene} must animate`);
    assert(a.runs.some(r => r[2].includes('#')), 'Large OMARCHY lettering must be drawn');
    for (const [x, y, text, ink] of a.runs) {
      assert(x >= 0 && x + text.length <= cols && y >= 0 && y < rows);
      assert(ink >= 0 && ink < engine.palette.length);
    }
  }
}
assert.equal(new Set(engine.scenes.map((_, i) => engine.frame(160, 56, 1, i).text)).size, 4);
const frames = 240;
const start = performance.now();
for (let i = 0; i < frames; i++) engine.frame(160, 56, i / 24, i % 4);
const ms = (performance.now() - start) / frames;
assert(ms < 35, `ASCII engine exceeded a 24 FPS frame budget: ${ms}ms`);
console.log(`ASCII: 4 scenes × 4 sizes passed; ${ms.toFixed(2)} ms/frame generation average (${frames} frames).`);
