from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout

from rd_audiorip.services.downloader import (
    get_ffmpeg_version,
    get_tools_ffmpeg_path,
    install_or_update_ffmpeg,
)


class FfmpegDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("FFmpeg Manager")
        self.setModal(True)
        self.resize(500, 180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Status group
        status_group = QGroupBox("Status")
        status_form = QFormLayout(status_group)
        status_form.setContentsMargins(10, 12, 10, 10)
        status_form.setSpacing(6)

        status_form.addRow("Target path:", QLabel(str(get_tools_ffmpeg_path())))
        self.install_status_value = QLabel("Checking...")
        self.version_value = QLabel("Checking...")
        self.version_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        status_form.addRow("Installed:", self.install_status_value)
        status_form.addRow("Version:", self.version_value)
        layout.addWidget(status_group)

        # Actions
        action_row = QHBoxLayout()
        action_row.setSpacing(6)
        self.refresh_btn = QPushButton("Refresh")
        self.install_update_btn = QPushButton("Install / Update FFmpeg")
        close_btn = QPushButton("Close")
        action_row.addWidget(self.refresh_btn)
        action_row.addWidget(self.install_update_btn)
        action_row.addStretch()
        action_row.addWidget(close_btn)
        layout.addLayout(action_row)

        self.refresh_btn.clicked.connect(self.refresh_status)
        self.install_update_btn.clicked.connect(self.install_or_update)
        close_btn.clicked.connect(self.accept)

        self.refresh_status()

    def refresh_status(self) -> None:
        installed = get_tools_ffmpeg_path().exists()
        self.install_status_value.setText("Installed" if installed else "Not installed")
        version = get_ffmpeg_version()
        self.version_value.setText(version if version else "Not installed")

    def install_or_update(self) -> None:
        ok, message = install_or_update_ffmpeg()
        self.refresh_status()
        if ok:
            QMessageBox.information(self, "FFmpeg", "FFmpeg install/update completed.")
        else:
            QMessageBox.critical(self, "FFmpeg", message)

