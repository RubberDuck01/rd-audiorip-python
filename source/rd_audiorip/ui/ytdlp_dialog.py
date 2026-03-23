from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout

from rd_audiorip.services.downloader import (
    get_tools_ytdlp_path,
    get_ytdlp_version,
    install_ytdlp,
    update_ytdlp,
)


class YtdlpDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("yt-dlp Manager")
        self.setModal(True)
        self.resize(560, 360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title = QLabel("yt-dlp Manager")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "This app treats yt-dlp as bundled inside its own tools folder so the whole program can be removed cleanly in one go."
        )
        subtitle.setObjectName("dialogSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        status_card = QFrame()
        status_card.setObjectName("card")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(18, 16, 18, 16)
        status_layout.setSpacing(10)

        status_layout.addLayout(self._info_row("Target path", str(get_tools_ytdlp_path())))

        self.install_status_value = QLabel("Checking...")
        self.version_value = QLabel("Checking...")
        self.version_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        status_layout.addLayout(self._info_row("Installed in target dir", self.install_status_value))
        status_layout.addLayout(self._info_row("Current version", self.version_value))
        layout.addWidget(status_card)

        action_card = QFrame()
        action_card.setObjectName("card")
        action_layout = QVBoxLayout(action_card)
        action_layout.setContentsMargins(18, 16, 18, 16)
        action_layout.setSpacing(10)

        action_title = QLabel("Actions")
        action_title.setObjectName("cardTitle")
        action_layout.addWidget(action_title)

        action_note = QLabel(
            "Install downloads the standalone yt-dlp executable into the target tools directory. Update uses yt-dlp -U on that bundled copy."
        )
        action_note.setObjectName("cardSubtitle")
        action_note.setWordWrap(True)
        action_layout.addWidget(action_note)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("glassButton")
        self.install_btn = QPushButton("Install yt-dlp")
        self.install_btn.setObjectName("primaryButton")
        self.update_btn = QPushButton("Run yt-dlp -U")
        self.update_btn.setObjectName("glassButton")
        btn_row.addWidget(self.refresh_btn)
        btn_row.addWidget(self.install_btn)
        btn_row.addWidget(self.update_btn)
        action_layout.addLayout(btn_row)
        layout.addWidget(action_card)

        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setObjectName("glassButton")
        close_row.addWidget(close_btn)
        layout.addLayout(close_row)

        self.refresh_btn.clicked.connect(self.refresh_version)
        self.install_btn.clicked.connect(self.install_yt_dlp)
        self.update_btn.clicked.connect(self.update_yt_dlp)
        close_btn.clicked.connect(self.accept)

        self.apply_styles()
        self.refresh_version()

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

    def refresh_version(self) -> None:
        target_installed = get_tools_ytdlp_path().exists()

        if target_installed:
            self.install_status_value.setText("Installed")
            self.install_status_value.setStyleSheet("color: #9dffe3; font-weight: 700;")
        else:
            self.install_status_value.setText("Not installed")
            self.install_status_value.setStyleSheet("color: #ffd67d; font-weight: 700;")

        version = get_ytdlp_version()
        self.version_value.setText(version if version else "Not installed")
        self.update_btn.setEnabled(target_installed)

    def install_yt_dlp(self) -> None:
        if get_tools_ytdlp_path().exists():
            QMessageBox.information(self, "yt-dlp", "yt-dlp is already present in the target directory. Installation is not needed.")
            self.refresh_version()
            return

        ok, message = install_ytdlp()
        self.refresh_version()
        if ok:
            QMessageBox.information(self, "yt-dlp", "yt-dlp installation completed.")
        else:
            QMessageBox.critical(self, "yt-dlp", message)

    def update_yt_dlp(self) -> None:
        ok, message = update_ytdlp()
        self.refresh_version()
        if ok:
            QMessageBox.information(self, "yt-dlp", "yt-dlp update command completed.")
        else:
            QMessageBox.critical(self, "yt-dlp", message)

    def apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QDialog {
                background: qradialgradient(cx:0.2, cy:0.1, radius:1.15,
                    fx:0.22, fy:0.12,
                    stop:0 #17384d,
                    stop:0.25 #0c5a71,
                    stop:0.62 #10283f,
                    stop:1 #060b14);
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
                color: #a9d2d9;
                font-size: 13px;
            }
            QLabel#cardTitle, QLabel#miniTitle {
                color: #d6fbff;
                font-weight: 700;
            }
            QLabel#detailValue {
                color: #f7ffff;
            }
            QLabel#cardSubtitle {
                color: #8db8c1;
            }
            QFrame#card {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(23, 68, 89, 0.84),
                    stop:1 rgba(8, 19, 35, 0.94));
                border: 1px solid rgba(88, 181, 176, 0.34);
                border-radius: 18px;
            }
            QPushButton#primaryButton {
                color: #eefcff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d9fa0,
                    stop:0.4 #2f7891,
                    stop:1 #284e7e);
                border: 1px solid #79c8c2;
            }
            QPushButton#primaryButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #48aead,
                    stop:0.4 #38879f,
                    stop:1 #31598b);
            }
            QPushButton:disabled {
                color: #7d9bab;
                background: rgba(28, 53, 70, 0.72);
                border: 1px solid rgba(90, 122, 140, 0.36);
            }
            """
        )
