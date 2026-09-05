import QtQuick
import "AsciiEngine.js" as Ascii

Item {
  id: root
  property int sceneIndex: 0
  property real elapsed: 0
  property bool animating: true
  property int fps: 24
  readonly property int columns: Math.max(48, Math.min(180, Math.floor(width / 12)))
  readonly property int rows: Math.max(28, Math.min(76, Math.floor(height / 19)))
  property real renderMilliseconds: 0
  property int frameCount: 0

  Rectangle { anchors.fill: parent; color: "#180D20" }
  Canvas {
    id: canvas
    anchors.fill: parent
    renderTarget: Canvas.Image
    onPaint: {
      var begin = Date.now();
      var ctx = getContext("2d");
      ctx.fillStyle = "#180D20";
      ctx.fillRect(0, 0, width, height);
      var frame = Ascii.frame(root.columns, root.rows, root.elapsed, root.sceneIndex);
      var cellWidth = width / frame.columns;
      var cellHeight = height / frame.rows;
      var fontSize = Math.min(cellHeight * 0.88, cellWidth / 0.61);
      ctx.font = "bold " + Math.floor(fontSize) + "px monospace";
      ctx.textBaseline = "top";
      var advance = ctx.measureText("M").width;
      var left = (width - advance * frame.columns) / 2;
      for (var i = 0; i < frame.runs.length; i++) {
        var run = frame.runs[i];
        ctx.fillStyle = Ascii.palette[run[3]];
        ctx.fillText(run[2], left + run[0] * advance, run[1] * cellHeight);
      }
      root.renderMilliseconds = Date.now() - begin;
      root.frameCount++;
    }
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
  }
  onElapsedChanged: canvas.requestPaint()
  onSceneIndexChanged: canvas.requestPaint()
  Component.onCompleted: canvas.requestPaint()
}
