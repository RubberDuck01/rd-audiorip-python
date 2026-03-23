from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout

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
        self.resize(560, 320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title = QLabel("FFmpeg Manager")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Install or refresh the bundled FFmpeg binary used by this app. On Windows, FFmpeg is downloaded as a new archive and the local ffmpeg.exe is replaced."
        )
        subtitle.setObjectName("dialogSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        status_card = QFrame()
        status_card.setObjectName("card")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(18, 16, 18, 16)
        status_layout.setSpacing(10)

        status_layout.addLayout(self._info_row("Target path", str(get_tools_ffmpeg_path())))
        self.install_status_value = QLabel("Checking...")
        self.version_value = QLabel("Checking...")
        self.version_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        status_layout.addLayout(self._info_row("Installed in target dir", self.install_status_value))
        status_layout.addLayout(self._info_row("Current version", self.version_value))
        layout.addWidget(status_card)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("glassButton")
        self.install_update_btn = QPushButton("Install / Update FFmpeg")
        self.install_update_btn.setObjectName("primaryButton")
        close_btn = QPushButton("Close")
        close_btn.setObjectName("glassButton")
        action_row.addWidget(self.refresh_btn)
        action_row.addWidget(self.install_update_btn)
        action_row.addStretch()
        action_row.addWidget(close_btn)
        layout.addLayout(action_row)

        self.refresh_btn.clicked.connect(self.refresh_status)
        self.install_update_btn.clicked.connect(self.install_or_update)
        close_btn.clicked.connect(self.accept)

        self.apply_styles()
        self.refresh_status()

    def _info_row(self, label_text: str, value_widget_or_text) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        label = QLabel(label_text)
        label.setObjectName("miniTitle")
        row.addWidget(label)

        if isinstance(value_widget_or_text, QLabel):
            value = value_widget_or_text
        else:
            value = QLabel(str(value_widget_or_text))
        value.setObjectName("detailValue")
        value.setWordWrap(True)
        row.addWidget(value, stretch=1)
        return row

    def refresh_status(self) -> None:
        installed = get_tools_ffmpeg_path().exists()
        if installed:
            self.install_status_value.setText("Installed")
            self.install_status_value.setStyleSheet("color: #92e7cf; font-weight: 700;")
        else:
            self.install_status_value.setText("Not installed")
            self.install_status_value.setStyleSheet("color: #c5dfe8; font-weight: 700;")

        version = get_ffmpeg_version()
        self.version_value.setText(version if version else "Not installed")

    def install_or_update(self) -> None:
        ok, message = install_or_update_ffmpeg()
        self.refresh_status()
        if ok:
            QMessageBox.information(self, "FFmpeg", "FFmpeg install/update completed.")
        else:
            QMessageBox.critical(self, "FFmpeg", message)

    def apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QDialog {
                background: qradialgradient(cx:0.2, cy:0.1, radius:1.15,
                    fx:0.22, fy:0.12,
                    stop:0 #17374b,
                    stop:0.22 #0c5768,
                    stop:0.6 #132d43,
                    stop:1 #070c15);
                color: #effcff;
            }
            QLabel {
                color: #effcff;
            }
            QLabel#dialogTitle {
                font-size: 22px;
                font-weight: 700;
                color: #ffffff;
            }
            QLabel#dialogSubtitle {
                color: #a7ccd3;
                font-size: 13px;
            }
            QLabel#miniTitle {
                color: #d4f4fb;
                font-weight: 700;
            }
            QLabel#detailValue {
                color: #f7ffff;
            }
            QFrame#card {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(23, 65, 82, 0.84),
                    stop:1 rgba(10, 19, 34, 0.94));
                border: 1px solid rgba(86, 177, 170, 0.34);
                border-radius: 18px;
            }
            QPushButton#primaryButton {
                color: #eafcff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3c9c9c,
                    stop:1 #2a648f);
                border: 1px solid #74c7bd;
            }
            QPushButton#primaryButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #49a8a7,
                    stop:1 #33739d);
            }
            """
        )
