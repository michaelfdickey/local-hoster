import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Dialog {
    id: dialog
    title: editIndex === -1 ? "Add Application" : "Edit Application"
    modal: true
    anchors.centerIn: parent
    width: 560
    height: 560
    padding: 20

    // ── public API ──────────────────────────────────────────────
    property int editIndex: -1
    property alias appName: nameField.text
    property alias frontendUrl: frontendField.text
    property alias backendUrl: backendField.text
    property alias projectFolder: folderField.text
    property alias githubRepo: githubField.text

    function openForAdd() {
        editIndex = -1
        nameField.text = ""
        frontendField.text = "http://localhost:"
        backendField.text = ""
        folderField.text = ""
        githubField.text = ""
        launcherStatus.text = ""
        dialog.open()
    }

    function openForEdit(idx, name, feUrl, beUrl, folder, repo) {
        editIndex = idx
        nameField.text = name
        frontendField.text = feUrl
        backendField.text = beUrl
        folderField.text = folder
        githubField.text = repo
        _checkLauncher()
        dialog.open()
    }

    // ── Folder picker ───────────────────────────────────────────
    FolderDialog {
        id: folderDialog
        title: "Select project folder"
        onAccepted: {
            // Convert file:///C:/... to C:/...
            var path = selectedFolder.toString()
            if (Qt.platform.os === "windows") {
                path = path.replace(/^file:\/\/\//, "")
            } else {
                path = path.replace(/^file:\/\//, "")
            }
            path = decodeURIComponent(path)
            folderField.text = path
            _checkLauncher()
        }
    }

    function _checkLauncher() {
        if (folderField.text.length > 0) {
            var found = appManager.hasLauncherScript(folderField.text)
            launcherStatus.text = found
                ? "✔ Launcher script found"
                : "✘ No launcher.sh or launcher.py found"
            launcherStatus.color = found ? "#a6e3a1" : "#f38ba8"
        } else {
            launcherStatus.text = ""
        }
    }

    // ── Visual styling ──────────────────────────────────────────
    background: Rectangle {
        color: "#1e1e2e"
        border.color: "#45475a"
        border.width: 1
        radius: 12
    }

    // ── Form ────────────────────────────────────────────────────
    contentItem: ColumnLayout {
        spacing: 14

        // Name
        Label { text: "Application Name"; color: "#cdd6f4"; font.pixelSize: 13 }
        TextField {
            id: nameField
            Layout.fillWidth: true
            placeholderText: "My Cool App"
            color: "#cdd6f4"
            background: Rectangle { color: "#313244"; radius: 6 }
        }

        // Frontend URL
        Label { text: "Frontend URL"; color: "#cdd6f4"; font.pixelSize: 13 }
        TextField {
            id: frontendField
            Layout.fillWidth: true
            placeholderText: "http://localhost:5173/"
            color: "#cdd6f4"
            background: Rectangle { color: "#313244"; radius: 6 }
        }

        // Backend URL
        Label { text: "Backend URL (optional)"; color: "#cdd6f4"; font.pixelSize: 13 }
        TextField {
            id: backendField
            Layout.fillWidth: true
            placeholderText: "http://localhost:8000/"
            color: "#cdd6f4"
            background: Rectangle { color: "#313244"; radius: 6 }
        }

        // Project folder + browse
        Label { text: "Project Folder"; color: "#cdd6f4"; font.pixelSize: 13 }
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            TextField {
                id: folderField
                Layout.fillWidth: true
                placeholderText: "/path/to/project"
                color: "#cdd6f4"
                background: Rectangle { color: "#313244"; radius: 6 }
                onTextChanged: dialog._checkLauncher()
            }
            Button {
                text: "Browse…"
                onClicked: folderDialog.open()
                background: Rectangle { color: "#313244"; radius: 6 }
                contentItem: Label { text: parent.text; color: "#cdd6f4"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                implicitWidth: 80; implicitHeight: 36
            }
        }

        // Launcher status
        Label {
            id: launcherStatus
            text: ""
            font.pixelSize: 12
        }

        // GitHub repo
        Label { text: "GitHub Repository URL (optional)"; color: "#cdd6f4"; font.pixelSize: 13 }
        TextField {
            id: githubField
            Layout.fillWidth: true
            placeholderText: "https://github.com/user/repo"
            color: "#cdd6f4"
            background: Rectangle { color: "#313244"; radius: 6 }
        }

        // ── Dialog buttons ──────────────────────────────────────
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 8
            Item { Layout.fillWidth: true }
            Button {
                text: "Cancel"
                onClicked: dialog.reject()
                background: Rectangle { color: "#45475a"; radius: 6 }
                contentItem: Label { text: parent.text; color: "#cdd6f4"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                implicitWidth: 90; implicitHeight: 36
            }
            Button {
                text: editIndex === -1 ? "Add" : "Save"
                enabled: nameField.text.length > 0
                onClicked: dialog.accept()
                background: Rectangle {
                    color: parent.enabled ? "#89b4fa" : "#45475a"
                    radius: 6
                }
                contentItem: Label { text: parent.text; color: "#1e1e2e"; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                implicitWidth: 90; implicitHeight: 36
            }
        }
    }
}
