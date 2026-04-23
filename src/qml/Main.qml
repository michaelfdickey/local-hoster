import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    visible: true
    title: "Local Hoster"
    width: 900
    height: 520
    minimumWidth: 780
    minimumHeight: 300
    color: "#1e1e2e"

    // ── Add / Edit dialog ──────────────────────────────────────
    AddAppDialog {
        id: addDialog
        onAccepted: {
            if (editIndex === -1) {
                appManager.addApp(appName, frontendUrl, backendUrl,
                                  projectFolder, githubRepo)
            } else {
                appManager.updateApp(editIndex, appName, frontendUrl,
                                     backendUrl, projectFolder, githubRepo)
            }
        }
        onDeleteRequested: function(index) {
            appManager.removeApp(index)
        }
    }

    // ── Header ─────────────────────────────────────────────────
    header: ToolBar {
        background: Rectangle { color: "#313244" }
        height: 48
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 16
            Label {
                text: "Local Hoster"
                font.pixelSize: 18
                font.bold: true
                color: "#cdd6f4"
            }
            Item { Layout.fillWidth: true }
            Label {
                text: "Tracked apps: " + appListView.count
                color: "#a6adc8"
                font.pixelSize: 13
            }
        }
    }

    // ── Sorting state ────────────────────────────────────────
    property string sortColumn: ""
    property bool sortAscending: true

    function toggleSort(column) {
        if (sortColumn === column) {
            sortAscending = !sortAscending
        } else {
            sortColumn = column
            sortAscending = true
        }
        appManager.sortApps(sortColumn, sortAscending)
    }

    // ── App list ───────────────────────────────────────────────
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 0

        // Column headers
        Rectangle {
            Layout.fillWidth: true
            height: 32
            color: "#313244"
            radius: 6
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 8

                // Sortable: Name
                Item {
                    Layout.preferredWidth: 220
                    implicitHeight: parent.height
                    RowLayout {
                        anchors.fill: parent
                        spacing: 2
                        Label { text: "Name"; color: "#a6adc8"; font.bold: true }
                        Label {
                            text: root.sortColumn === "name" ? (root.sortAscending ? "▲" : "▼") : ""
                            color: "#a6adc8"; font.pixelSize: 10
                            Layout.alignment: Qt.AlignBottom
                        }
                        Item { Layout.fillWidth: true }
                    }
                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.toggleSort("name") }
                }

                // Sortable: Frontend
                Item {
                    Layout.preferredWidth: 140
                    implicitHeight: parent.height
                    RowLayout {
                        anchors.fill: parent
                        spacing: 2
                        Label { text: "Frontend"; color: "#a6adc8"; font.bold: true }
                        Label {
                            text: root.sortColumn === "frontend" ? (root.sortAscending ? "▲" : "▼") : ""
                            color: "#a6adc8"; font.pixelSize: 10
                            Layout.alignment: Qt.AlignBottom
                        }
                        Item { Layout.fillWidth: true }
                    }
                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.toggleSort("frontend") }
                }

                Label { text: "Backend";      color: "#a6adc8"; font.bold: true; Layout.preferredWidth: 140 }
                Label { text: "Launcher";     color: "#a6adc8"; font.bold: true; Layout.preferredWidth: 50; Layout.rightMargin: 12 }

                // Sortable: Status
                Item {
                    Layout.preferredWidth: 65
                    implicitHeight: parent.height
                    RowLayout {
                        anchors.fill: parent
                        spacing: 2
                        Label { text: "Status"; color: "#a6adc8"; font.bold: true }
                        Label {
                            text: root.sortColumn === "status" ? (root.sortAscending ? "▲" : "▼") : ""
                            color: "#a6adc8"; font.pixelSize: 10
                            Layout.alignment: Qt.AlignBottom
                        }
                        Item { Layout.fillWidth: true }
                    }
                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.toggleSort("status") }
                }

                Item  { Layout.fillWidth: true }
                Label { text: "Actions";      color: "#a6adc8"; font.bold: true }
            }
        }

        // Scrollable list
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ListView {
                id: appListView
                model: appManager.apps
                spacing: 4

                delegate: Rectangle {
                    width: appListView.width
                    height: 48
                    radius: 6
                    color: index % 2 === 0 ? "#1e1e2e" : "#181825"

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 8

                        // Name (clickable link to GitHub repo)
                        Label {
                            text: model.name
                            color: "#cdd6f4"
                            font.pixelSize: 14
                            font.bold: true
                            elide: Text.ElideRight
                            Layout.preferredWidth: 220
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: model.githubRepo ? Qt.PointingHandCursor : Qt.ArrowCursor
                                onClicked: {
                                    if (model.githubRepo)
                                        Qt.openUrlExternally(model.githubRepo)
                                }
                            }
                        }

                        // Frontend URL (clickable)
                        Label {
                            text: model.frontendUrl || "—"
                            color: model.frontendUrl ? "#89b4fa" : "#585b70"
                            font.pixelSize: 13
                            elide: Text.ElideRight
                            Layout.preferredWidth: 140
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: model.frontendUrl ? Qt.PointingHandCursor : Qt.ArrowCursor
                                onClicked: {
                                    if (model.frontendUrl)
                                        Qt.openUrlExternally(model.frontendUrl)
                                }
                            }
                        }

                        // Backend URL (clickable)
                        Label {
                            text: model.backendUrl || "—"
                            color: model.backendUrl ? "#89b4fa" : "#585b70"
                            font.pixelSize: 13
                            elide: Text.ElideRight
                            Layout.preferredWidth: 140
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: model.backendUrl ? Qt.PointingHandCursor : Qt.ArrowCursor
                                onClicked: {
                                    if (model.backendUrl)
                                        Qt.openUrlExternally(model.backendUrl)
                                }
                            }
                        }

                        // Launcher status indicator
                        Label {
                            text: model.hasLauncher ? "✔" : "✘"
                            color: model.hasLauncher ? "#a6e3a1" : "#f38ba8"
                            font.pixelSize: 16
                            horizontalAlignment: Text.AlignHCenter
                            Layout.preferredWidth: 50
                            Layout.rightMargin: 12
                        }

                        // Running status
                        Label {
                            text: model.running ? "Running" : "Stopped"
                            color: model.running ? "#a6e3a1" : "#f38ba8"
                            font.pixelSize: 13
                            font.bold: true
                            Layout.preferredWidth: 65
                        }

                        Item { Layout.fillWidth: true }

                        // Action buttons
                        RowLayout {
                            spacing: 6

                            // Start
                            Button {
                                text: "▶"
                                enabled: !model.running && model.hasLauncher
                                ToolTip.visible: hovered
                                ToolTip.text: "Start"
                                onClicked: appManager.startApp(index)
                                background: Rectangle {
                                    radius: 4
                                    color: parent.enabled ? (parent.hovered ? "#a6e3a1" : "#313244") : "#45475a"
                                }
                                contentItem: Label {
                                    text: parent.text; color: "#cdd6f4"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                implicitWidth: 36; implicitHeight: 32
                            }

                            // Stop
                            Button {
                                text: "■"
                                enabled: model.running
                                ToolTip.visible: hovered
                                ToolTip.text: "Stop"
                                onClicked: appManager.stopApp(index)
                                background: Rectangle {
                                    radius: 4
                                    color: parent.enabled ? (parent.hovered ? "#f38ba8" : "#313244") : "#45475a"
                                }
                                contentItem: Label {
                                    text: parent.text; color: "#cdd6f4"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                implicitWidth: 36; implicitHeight: 32
                            }

                            // Reset
                            Button {
                                text: "⟳"
                                enabled: model.hasLauncher
                                ToolTip.visible: hovered
                                ToolTip.text: "Restart"
                                onClicked: appManager.resetApp(index)
                                background: Rectangle {
                                    radius: 4
                                    color: parent.hovered ? "#f9e2af" : "#313244"
                                }
                                contentItem: Label {
                                    text: parent.text; color: "#cdd6f4"
                                    font.pixelSize: 20
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                implicitWidth: 36; implicitHeight: 32
                            }

                            // Settings gear
                            Button {
                                text: "⚙"
                                ToolTip.visible: hovered
                                ToolTip.text: "Edit"
                                onClicked: {
                                    addDialog.openForEdit(index,
                                        appManager.getAppName(index),
                                        appManager.getAppFrontendUrl(index),
                                        appManager.getAppBackendUrl(index),
                                        appManager.getAppProjectFolder(index),
                                        appManager.getAppGithubRepo(index))
                                }
                                background: Rectangle {
                                    radius: 4
                                    color: parent.hovered ? "#89b4fa" : "#313244"
                                }
                                contentItem: Label {
                                    text: parent.text; color: "#cdd6f4"
                                    font.pixelSize: 20
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                implicitWidth: 36; implicitHeight: 32
                            }
                        }
                    }
                }

                // Empty state
                Label {
                    anchors.centerIn: parent
                    text: "No apps tracked yet.\nClick  ＋  below to add one."
                    color: "#585b70"
                    font.pixelSize: 15
                    horizontalAlignment: Text.AlignHCenter
                    visible: appListView.count === 0
                }
            }
        }

        // ── Footer: Add button ────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            height: 48
            color: "transparent"
            Button {
                anchors.centerIn: parent
                text: "＋  Add App"
                font.pixelSize: 15
                onClicked: addDialog.openForAdd()
                background: Rectangle {
                    radius: 8
                    color: parent.hovered ? "#89b4fa" : "#313244"
                }
                contentItem: Label {
                    text: parent.text
                    color: "#cdd6f4"
                    font.pixelSize: 15
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                implicitWidth: 160
                implicitHeight: 40
            }
        }
    }
}
