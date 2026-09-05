import QtQuick
import Quickshell
import qs.Commons
import qs.Ui

BarWidget {
  id: root
  moduleName: "local.funk-master"
  implicitWidth: vertical ? barSize : 160
  implicitHeight: barSize

  Rectangle {
    anchors.fill: parent
    anchors.margins: 3
    radius: 15
    color: "#D6FF62"

    Rectangle {
      id: record
      width: 25; height: 25; radius: 13
      anchors.left: parent.left
      anchors.leftMargin: 4
      anchors.verticalCenter: parent.verticalCenter
      color: "#211329"
      border.color: "#57335F"
      border.width: 2
      Rectangle { anchors.centerIn: parent; width: 15; height: 15; radius: 8; color: "transparent"; border.color: "#AA8FB4" }
      Rectangle { anchors.centerIn: parent; width: 9; height: 9; radius: 5; color: "#FF67BE" }
      Rectangle { x: 15; y: 3; width: 3; height: 3; radius: 2; color: "#FFF0D0" }
      RotationAnimation on rotation {
        from: 0; to: 360; duration: 2400; loops: Animation.Infinite
        running: hit.tooltipHovered
      }
    }
    Text {
      anchors.left: record.right
      anchors.leftMargin: 7
      anchors.verticalCenter: parent.verticalCenter
      visible: !root.vertical
      text: "Funk Master"
      textFormat: Text.PlainText
      font.family: "C059"
      font.bold: true
      font.italic: true
      font.pixelSize: 18
      color: "#211329"
    }
  }
  WidgetButton {
    id: hit
    anchors.fill: parent
    bar: root.bar
    text: "Funk Master"
    labelVisible: false
    tooltipText: "FUNK MASTER · Left: themes / Right: animated OMARCHY ASCII"
    onPressed: function(button) {
      if (button === Qt.LeftButton) Quickshell.execDetached(["omarchy-theme-switcher"])
      else if (button === Qt.RightButton) Quickshell.execDetached(["omarchy-shell", "funk-saver", "preview"])
    }
  }
}
