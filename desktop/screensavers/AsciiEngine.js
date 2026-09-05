// Pure ASCII rasterizer shared by Quickshell and the offline verification suite.
// Original artwork: every visible mark is printable ASCII, including the logo.
var scenes = ["LIQUID TYPE", "MOTHERSHIP TUNNEL", "DISCO SUPERNOVA", "ACID GARDEN"];
var subtitles = ["LET THE LETTERS GET LOOSE", "TRANSMITTING FROM THE FUNK DIMENSION",
                 "EVERY CHARACTER IS A DANCE FLOOR", "STRANGE THINGS GROW AFTER MIDNIGHT"];
var palette = ["#211329", "#472650", "#66376D", "#985291", "#D6FF62", "#FF67BE", "#FF9B54", "#74E9DF", "#FFF0D0", "#C69AFF"];
var alphabet = {
  O: ["01110","11011","11011","11011","11011","11011","01110"],
  M: ["11011","11111","11111","11011","11011","11011","11011"],
  A: ["01110","11011","11011","11111","11011","11011","11011"],
  R: ["11110","11011","11011","11110","11100","11010","11011"],
  C: ["01111","11000","11000","11000","11000","11000","01111"],
  H: ["11011","11011","11011","11111","11011","11011","11011"],
  Y: ["11011","11011","11011","01110","00100","00100","00100"]
};

function mod(n, m) { return ((n % m) + m) % m; }
function hash(n) { var x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }

function frame(columns, lines, seconds, sceneIndex) {
  var cols = Math.max(48, Math.min(200, Math.floor(columns)));
  var rows = Math.max(28, Math.min(90, Math.floor(lines)));
  var scene = mod(Math.floor(sceneIndex), scenes.length);
  var t = Number(seconds) || 0;
  var cells = new Array(cols * rows), inks = new Array(cols * rows);
  var x, y, i;
  for (i = 0; i < cells.length; i++) { cells[i] = " "; inks[i] = 0; }
  function put(px, py, glyph, ink) {
    px = Math.round(px); py = Math.round(py);
    if (px < 1 || px >= cols - 1 || py < 3 || py >= rows - 3) return;
    var at = py * cols + px;
    cells[at] = glyph; inks[at] = ink;
  }
  function text(px, py, label, ink) {
    px = Math.round(px); py = Math.round(py);
    if (py < 0 || py >= rows) return;
    for (var j = 0; j < label.length; j++) {
      var at = py * cols + px + j;
      if (px + j >= 0 && px + j < cols) { cells[at] = label[j]; inks[at] = ink; }
    }
  }

  // A moving contour field, with a different mathematical surface per scene.
  for (y = 3; y < rows - 3; y++) {
    for (x = 1; x < cols - 1; x++) {
      var nx = (x - cols / 2) / (cols / 2);
      var ny = (y - rows / 2) / (rows / 2);
      var r = Math.sqrt(nx * nx + ny * ny * 0.64) + 0.025;
      var a = Math.atan2(ny * 0.8, nx);
      var v, g = " ", ink = 1;
      if (scene === 0) {
        v = Math.sin(nx * 9 + Math.sin(ny * 6 + t) * 2.5 - t * 1.5)
          + Math.sin(ny * 11 - nx * 3 + t * 1.4);
        if (Math.abs(v) < 0.20) { g = "~"; ink = 2; }
        if (Math.abs(v - 0.85) < 0.12) { g = ":"; ink = 3; }
        if (v > 1.78) { g = "o"; ink = 1; }
      } else if (scene === 1) {
        v = mod(1.65 / r + a / Math.PI * 1.5 + t * 1.6, 2.8);
        if (v < 0.23) { g = "#"; ink = r < 0.35 ? 3 : 2; }
        else if (v < 0.38) { g = ":"; ink = 1; }
        if (Math.abs(Math.sin(a * 12 + t * 0.3)) < 0.045 && r > 0.25) { g = "+"; ink = 3; }
      } else if (scene === 2) {
        v = Math.sin(a * 16 - t * 0.8 + r * 9) * Math.sin(r * 18 - t * 2);
        if (v > 0.8) { g = "+"; ink = 2; }
        else if (v < -0.85) { g = "."; ink = 3; }
      } else {
        var fx = mod(nx * 3 + Math.sin(t * 0.25) * 0.3, 1) - 0.5;
        var fy = mod(ny * 2 + t * 0.12, 1) - 0.5;
        var fr = Math.sqrt(fx * fx + fy * fy);
        var fa = Math.atan2(fy, fx);
        v = fr - 0.28 - Math.sin(fa * 6 + t * 1.2) * 0.1;
        if (Math.abs(v) < 0.035) { g = "*"; ink = 3; }
        else if (Math.abs(v + 0.06) < 0.025) { g = ":"; ink = 2; }
        if (fr < 0.07) { g = "@"; ink = 2; }
      }
      if (g !== " ") put(x, y, g, ink);
    }
  }

  // Large figures at the edges: flying sparks, warp stars, and dancing sprouts.
  for (i = 0; i < 65; i++) {
    var phase = mod(t * (0.11 + hash(i) * 0.18) + hash(i + 90), 1);
    var angle = hash(i + 210) * Math.PI * 2 + (scene === 2 ? t * 0.2 : 0);
    var px, py;
    if (scene === 1 || scene === 2) {
      var radius = scene === 1 ? phase * phase * 1.4 : 0.35 + phase * 0.9;
      px = cols / 2 + Math.cos(angle) * radius * cols / 2;
      py = rows / 2 + Math.sin(angle) * radius * rows / 2;
    } else {
      px = hash(i + 55) * cols + Math.sin(t + i) * 3;
      py = rows - phase * rows;
    }
    put(px, py, i % 3 === 0 ? "+" : ".", 4 + i % 6);
    if (i % 8 === 0) {
      put(px - 1, py, "-", 4 + i % 6); put(px + 1, py, "-", 4 + i % 6);
      put(px, py - 1, "|", 4 + i % 6); put(px, py + 1, "|", 4 + i % 6);
    }
  }

  var word = "OMARCHY";
  var scale = Math.max(1, Math.floor(cols * 0.82 / 41));
  var wordWidth = 41 * scale;
  var startX = Math.floor((cols - wordWidth) / 2);
  var startY = Math.floor(rows / 2 - 3.5 * scale);
  var voxels = [];
  for (var letter = 0; letter < word.length; letter++) {
    var glyphRows = alphabet[word[letter]];
    for (var gy = 0; gy < 7 * scale; gy++) {
      for (var gx = 0; gx < 5 * scale; gx++) {
        if (glyphRows[Math.floor(gy / scale)][Math.floor(gx / scale)] !== "1") continue;
        var wx = startX + letter * 6 * scale + gx;
        var wy = startY + gy;
        if (scene === 0) { wy += Math.round(Math.sin(wx * 0.07 + t * 1.8) * 2.8); wx += Math.round(Math.sin(gy * 0.2 + t) * 1.3); }
        if (scene === 1) wy += Math.round(Math.sin(t * 1.2 + letter * 0.3));
        if (scene === 2) wy += Math.round(Math.sin(t * 2.6 + letter * 0.65) * 2);
        if (scene === 3) wy += Math.round(Math.sin(t * 1.4 + letter * 0.7) * 2);
        var color = scene === 2 ? 4 + mod(letter + Math.floor(t * 0.75), 6)
          : [4, 8, 5, 6, 9, 7][mod(Math.floor(gy / Math.max(2, scale)) + Math.floor(t * 0.65), 6)];
        voxels.push([wx, wy, mod(gx + gy + Math.floor(t * 8), 7) === 0 ? "+" : "#", color]);
      }
    }
  }
  // Ink knockout + offset ASCII shadow make the moving word stay readable.
  for (i = 0; i < voxels.length; i++) {
    var b = voxels[i];
    for (var dy = -1; dy <= 2; dy++) {
      for (var dx = -1; dx <= 2; dx++) put(b[0] + dx, b[1] + dy, " ", 0);
    }
  }
  for (i = 0; i < voxels.length; i++) put(voxels[i][0] + 2, voxels[i][1] + 2, ":", 3);
  for (i = 0; i < voxels.length; i++) put(voxels[i][0], voxels[i][1], voxels[i][2], voxels[i][3]);

  // Oscilloscope ribbon: the visual beat along the bottom of every scene.
  for (x = 3; x < cols - 3; x++) {
    var waveY = rows - 8 + Math.sin(x * 0.12 + t * 3) * 1.5 + Math.sin(x * 0.05 - t * 2);
    put(x, waveY, scene === 3 ? "v" : "=", 4 + scene);
  }
  var title = "OMARCHY / FUNK MASTER";
  text(3, 1, title, 8);
  var sceneTitle = "0" + (scene + 1) + " / " + scenes[scene];
  text(cols - sceneTitle.length - 3, 1, sceneTitle, 4);
  var caption = subtitles[scene];
  text(Math.floor((cols - caption.length) / 2), rows - 4, caption, 8);
  var footer = "SPACE / NEXT     P / PAUSE     ESC / RETURN";
  text(Math.floor((cols - footer.length) / 2), rows - 2, footer, 3);

  // Batch runs by ink so Canvas draws tens/hundreds of strings, not a scenegraph
  // object or draw call for every individual character.
  var runs = [];
  for (y = 0; y < rows; y++) {
    x = 0;
    while (x < cols) {
      if (cells[y * cols + x] === " ") { x++; continue; }
      var first = x, chosenInk = inks[y * cols + x], str = "";
      while (x < cols && inks[y * cols + x] === chosenInk) { str += cells[y * cols + x]; x++; }
      runs.push([first, y, str, chosenInk]);
    }
  }
  return { columns: cols, rows: rows, runs: runs, text: cells.join(""), scene: scene };
}

if (typeof module !== "undefined") module.exports = { frame: frame, scenes: scenes, palette: palette, alphabet: alphabet };
