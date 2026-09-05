import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import "AsciiEngine.js" as Ascii

Item {
  id: root
  property var shell: null
  property var manifest: null
  property string omarchyPath: ""
  property bool active: false
  property bool paused: false
  property bool manualPreview: false
  property int sceneIndex: 0
  property real elapsed: 0
  property real lastTick: 0
  property real openedAt: 0
  property string lastReason: "ready"
  property bool screensaverEnabled: false
  readonly property var lockService: shell ? shell.serviceFor("omarchy.lock") : null
  readonly property var idleService: shell && shell.pluginRegistry
    ? shell.serviceFor(shell.pluginRegistry.resolveEnabledId("omarchy.idle")) : null
  readonly property bool sessionLocked: lockService ? lockService.locked : false
  readonly property var screens: Quickshell.screens.filter(function(screen) { return screen.width > 0 && screen.height > 0; })

  function start(index, manual) {
    if (!lockService || sessionLocked) return "locked-or-not-ready";
    if (!manual && !screensaverEnabled) return "screensaver-disabled";
    var n = Number(index);
    if (!isFinite(n)) n = 0;
    sceneIndex = ((Math.floor(n) % Ascii.scenes.length) + Ascii.scenes.length) % Ascii.scenes.length;
    elapsed = 0;
    paused = false;
    manualPreview = !!manual;
    openedAt = Date.now();
    lastTick = openedAt;
    lastReason = manual ? "preview" : "idle";
    active = true;
    sceneTimer.restart();
    return "ok";
  }

  function dismiss(reason) {
    var wasActive = active;
    active = false;
    paused = false;
    sceneTimer.stop();
    lastReason = reason || "dismissed";
    if (wasActive && reason !== "lock" && idleService && idleService.idledThisCycle)
      idleService.cancelIdleCycle("funk-screensaver-dismissed");
    return "ok";
  }

  function next(direction) {
    sceneIndex = (sceneIndex + (direction || 1) + Ascii.scenes.length) % Ascii.scenes.length;
    elapsed = 0;
    sceneTimer.restart();
    return Ascii.scenes[sceneIndex];
  }

  function setPaused(value) {
    paused = !!value;
    lastTick = Date.now();
    if (paused) sceneTimer.stop(); else if (active) sceneTimer.restart();
  }

  function statusJson() {
    return JSON.stringify({ active: active, paused: paused, scene: sceneIndex,
      name: Ascii.scenes[sceneIndex], elapsed: elapsed, manualPreview: manualPreview,
      locked: sessionLocked, lastReason: lastReason, fps: 24, rotationSeconds: 18,
      screens: screens.length, screensaverEnabled: screensaverEnabled });
  }

  function refreshToggle() { if (!toggleProbe.running) toggleProbe.running = true; }
  Process {
    id: toggleProbe
    command: ["omarchy-toggle-enabled", "screensaver-off"]
    onExited: function(exitCode) { root.screensaverEnabled = exitCode === 1; }
  }
  FileView {
    path: Quickshell.env("HOME") + "/.local/state/omarchy/toggles"
    watchChanges: true
    printErrors: false
    onFileChanged: root.refreshToggle()
  }

  onSessionLockedChanged: if (sessionLocked) dismiss("lock")
  Timer {
    interval: 1000 / 24
    repeat: true
    running: root.active && !root.paused
    onTriggered: {
      var now = Date.now();
      root.elapsed += Math.min(0.15, (now - root.lastTick) / 1000);
      root.lastTick = now;
    }
  }
  Timer {
    id: sceneTimer
    interval: 18000
    repeat: true
    onTriggered: root.next(1)
  }
  Connections {
    target: root.idleService
    function onIdleEnabledChanged() {
      if (root.idleService && !root.idleService.idleEnabled && !root.manualPreview) root.dismiss("stay-awake");
    }
  }
  IpcHandler {
    target: "funk-saver"
    function preview(): string { return root.start(0, true); }
    function scene(index: string): string { return root.start(index, true); }
    function dismiss(): string { return root.dismiss("ipc"); }
    function next(): string { return root.next(1); }
    function pause(): string { root.setPaused(!root.paused); return root.paused ? "paused" : "playing"; }
    function status(): string { return root.statusJson(); }
  }
  Variants {
    model: root.screens
    PanelWindow {
      id: saverWindow
      required property var modelData
      screen: modelData
      visible: root.active && !root.sessionLocked
      color: "#180D20"
      anchors { top: true; bottom: true; left: true; right: true }
      exclusionMode: ExclusionMode.Ignore
      WlrLayershell.namespace: "funk-screensaver"
      WlrLayershell.layer: WlrLayer.Overlay
      WlrLayershell.keyboardFocus: root.active ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

      Loader {
        anchors.fill: parent
        active: root.active
        sourceComponent: AsciiView { sceneIndex: root.sceneIndex; elapsed: root.elapsed }
      }
      Text {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 16
        visible: root.paused
        text: "[ PAUSED ]"
        color: "#D6FF62"
        font.family: "monospace"
        font.pixelSize: 14
      }
      FocusScope {
        anchors.fill: parent
        focus: root.active
        Keys.onPressed: function(event) {
          if (event.isAutoRepeat) { event.accepted = true; return; }
          if (event.key === Qt.Key_Space || event.key === Qt.Key_Right) root.next(1);
          else if (event.key === Qt.Key_Left) root.next(-1);
          else if (event.key === Qt.Key_P) root.setPaused(!root.paused);
          else if (event.key >= Qt.Key_1 && event.key <= Qt.Key_4) root.start(event.key - Qt.Key_1, true);
          else root.dismiss("keyboard");
          event.accepted = true;
        }
      }
      MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.AllButtons
        property real baselineX: -1
        property real baselineY: -1
        onVisibleChanged: { baselineX = -1; baselineY = -1; }
        onClicked: root.dismiss("pointer");
        onPositionChanged: function(mouse) {
          if (!root.active || Date.now() - root.openedAt < 700 || baselineX < 0) {
            baselineX = mouse.x; baselineY = mouse.y; return;
          }
          if (Math.abs(mouse.x - baselineX) + Math.abs(mouse.y - baselineY) > 8) root.dismiss("pointer-movement");
        }
      }
    }
  }
  Component.onCompleted: root.refreshToggle()
  Component.onDestruction: root.dismiss("unloaded")
}
