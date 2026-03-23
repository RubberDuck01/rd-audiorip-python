import os
import webbrowser
from pathlib import Path

from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtGui import QAction, QDesktopServices
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from rd_audiorip.models.config import Config
from rd_audiorip.models.stats import Stats
from rd_audiorip.ui.settings_dialog import SettingsDialog
from rd_audiorip.ui.stats_dialog import StatsDialog
from rd_audiorip.ui.ytdlp_dialog import YtdlpDialog


class MainWindow(QMainWindow):
    download_requested = pyqtSignal(str, str)

    def __init__(self, config: Config, stats: Stats) -> None:
        super().__init__()
        self.config = config
        self.stats = stats
        self.setWindowTitle("Rubber Duck's AudioRip")
        self.resize(860, 620)

        self._build_menu()
        self._build_ui()
        self.apply_styles()

    def _build_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        file_menu.addAction(QAction("&Open Downloads Directory", self, triggered=self.open_downloads_directory))
        file_menu.addAction(QAction("&Settings", self, triggered=self.open_settings))
        file_menu.addSeparator()
        file_menu.addAction(QAction("&Quit", self, triggered=self.close))

        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(QAction("&Clear Queue", self, triggered=self.clear_queue))

        view_menu = menubar.addMenu("&View")
        view_menu.addAction(QAction("&My Statistics", self, triggered=self.open_stats))

        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction(QAction("&Check yt-dlp Updates", self, triggered=self.open_ytdlp_manager))

        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(QAction("&View Source on GitHub", self, triggered=self.visit_github))
        help_menu.addAction(QAction("&About RD AudioRip", self, triggered=self.open_about))
        help_menu.addAction(QAction("&About Qt", self, triggered=self.open_about_qt))

    def _build_ui(self) -> None:
        root = QWidget(self)
        root.setObjectName("root")
        self.layout = QVBoxLayout(root)
        self.layout.setContentsMargins(24, 22, 24, 22)
        self.layout.setSpacing(16)

        hero_card = QFrame()
        hero_card.setObjectName("heroCard")
        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(22, 20, 22, 20)
        hero_layout.setSpacing(10)

        eyebrow = QLabel("PORTABLE AUDIO WORKFLOW")
        eyebrow.setObjectName("eyebrow")
        hero_layout.addWidget(eyebrow)

        header = QLabel("Dark Aero downloads with a bundled toolchain")
        header.setObjectName("header")
        hero_layout.addWidget(header)

        subtitle = QLabel(
            "Paste a YouTube link, keep your tools inside the app folder, and manage downloads from a glassy, modern workspace."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        hero_layout.addWidget(subtitle)

        action_bar = QHBoxLayout()
        action_bar.setSpacing(10)

        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.setObjectName("toolbarButton")
        self.open_folder_btn.clicked.connect(self.open_downloads_directory)
        action_bar.addWidget(self.open_folder_btn)

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setObjectName("toolbarButton")
        self.settings_btn.clicked.connect(self.open_settings)
        action_bar.addWidget(self.settings_btn)

        self.stats_btn = QPushButton("Statistics")
        self.stats_btn.setObjectName("toolbarButton")
        self.stats_btn.clicked.connect(self.open_stats)
        action_bar.addWidget(self.stats_btn)

        self.ytdlp_btn = QPushButton("yt-dlp Manager")
        self.ytdlp_btn.setObjectName("toolbarButton")
        self.ytdlp_btn.clicked.connect(self.open_ytdlp_manager)
        action_bar.addWidget(self.ytdlp_btn)

        action_bar.addStretch()
        hero_layout.addLayout(action_bar)
        self.layout.addWidget(hero_card)

        input_card = QFrame()
        input_card.setObjectName("sectionCard")
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(20, 18, 20, 18)
        input_layout.setSpacing(12)

        input_title = QLabel("New Download")
        input_title.setObjectName("sectionTitle")
        input_layout.addWidget(input_title)

        input_hint = QLabel(
            "Downloads are audio-only. yt-dlp is treated as bundled with the app so the whole setup stays removable in one folder."
        )
        input_hint.setObjectName("sectionHint")
        input_hint.setWordWrap(True)
        input_layout.addWidget(input_hint)

        url_label = QLabel("YouTube URL")
        url_label.setObjectName("fieldLabel")
        input_layout.addWidget(url_label)

        url_row = QHBoxLayout()
        url_row.setSpacing(10)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        url_row.addWidget(self.url_input, stretch=1)

        self.download_btn = QPushButton("Start Download")
        self.download_btn.setObjectName("primaryButton")
        self.download_btn.setMinimumWidth(150)
        self.download_btn.clicked.connect(self.on_download_clicked)
        url_row.addWidget(self.download_btn)
        input_layout.addLayout(url_row)

        output_label = QLabel("Output Directory")
        output_label.setObjectName("fieldLabel")
        input_layout.addWidget(output_label)

        out_row = QHBoxLayout()
        out_row.setSpacing(10)
        self.output_input = QLineEdit(self.config.downloads_dir)
        out_row.addWidget(self.output_input, stretch=1)

        browse_btn = QPushButton("Choose Folder")
        browse_btn.setObjectName("glassButton")
        browse_btn.clicked.connect(self.browse_output)
        out_row.addWidget(browse_btn)
        input_layout.addLayout(out_row)

        self.layout.addWidget(input_card)

        queue_card = QFrame()
        queue_card.setObjectName("sectionCard")
        queue_layout = QVBoxLayout(queue_card)
        queue_layout.setContentsMargins(20, 18, 20, 18)
        queue_layout.setSpacing(12)

        queue_header = QHBoxLayout()
        queue_title = QLabel("Session Queue")
        queue_title.setObjectName("sectionTitle")
        queue_header.addWidget(queue_title)
        queue_header.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("glassButton")
        clear_btn.clicked.connect(self.clear_queue)
        queue_header.addWidget(clear_btn)
        queue_layout.addLayout(queue_header)

        queue_hint = QLabel(
            "Resolved titles appear here. Locale-aware subprocess decoding preserves Cyrillic and other non-Latin characters."
        )
        queue_hint.setObjectName("sectionHint")
        queue_hint.setWordWrap(True)
        queue_layout.addWidget(queue_hint)

        self.queue_list = QListWidget()
        queue_layout.addWidget(self.queue_list, stretch=1)
        self.layout.addWidget(queue_card, stretch=1)

        footer_card = QFrame()
        footer_card.setObjectName("footerCard")
        footer_layout = QVBoxLayout(footer_card)
        footer_layout.setContentsMargins(18, 16, 18, 16)
        footer_layout.setSpacing(8)

        progress_title = QLabel("Transfer Progress")
        progress_title.setObjectName("fieldLabel")
        footer_layout.addWidget(progress_title)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        footer_layout.addWidget(self.progress)

        self.status_label = QLabel("Ready!")
        self.status_label.setObjectName("status")
        footer_layout.addWidget(self.status_label)
        self.layout.addWidget(footer_card)

        self.setCentralWidget(root)

    def browse_output(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.output_input.text())
        if directory:
            self.output_input.setText(directory)
            self.config.set_downloads_dir(directory)

    def open_downloads_directory(self) -> None:
        raw_path = (self.output_input.text() or self.config.downloads_dir).strip()
        path = Path(raw_path)

        if not path.exists():
            self.set_status("Downloads directory does not exist.")
            return

        folder = path if path.is_dir() else path.parent
        try:
            if os.name == "nt":
                os.startfile(str(folder))  # type: ignore[attr-defined]
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
            self.set_status("Opened downloads directory.")
        except Exception as ex:
            self.set_status(f"Failed to open directory: {ex}")

    def on_download_clicked(self) -> None:
        self.download_requested.emit(self.url_input.text().strip(), self.output_input.text().strip())

    def set_busy(self, busy: bool) -> None:
        self.download_btn.setEnabled(not busy)
        self.url_input.setEnabled(not busy)
        self.output_input.setEnabled(not busy)

    def set_progress(self, value: int) -> None:
        self.progress.setValue(max(0, min(100, value)))

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def add_to_queue(self, display_text: str) -> None:
        self.queue_list.addItem(display_text)

    def on_download_success(self, message: str) -> None:
        self.set_progress(100)
        self.set_status(message)
        self.url_input.clear()

    def open_settings(self) -> None:
        dialog = SettingsDialog(self, self.config)
        if dialog.exec():
            self.output_input.setText(self.config.downloads_dir)
            self.set_status("Settings saved!")

    def open_ytdlp_manager(self) -> None:
        dialog = YtdlpDialog(self)
        dialog.exec()

    def clear_queue(self) -> None:
        self.queue_list.clear()
        self.set_status("Download queue cleared.")

    def visit_github(self) -> None:
        webbrowser.open("https://github.com/RubberDuck01/rd-audiorip-python")

    def open_about(self) -> None:
        QMessageBox.about(
            self,
            "About RD AudioRip",
            "RD AudioRip\nPortable YouTube audio extraction with a dark Aero-style interface built in Python and PyQt6.",
        )

    def open_about_qt(self) -> None:
        QMessageBox.aboutQt(self)

    def open_stats(self) -> None:
        dialog = StatsDialog(self, self.stats)
        dialog.exec()

    def apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget#root {
                background: qradialgradient(cx:0.2, cy:0.05, radius:1.2,
                    fx:0.25, fy:0.1,
                    stop:0 #1a3b53,
                    stop:0.22 #0d5d7c,
                    stop:0.52 #11355b,
                    stop:0.8 #0a172b,
                    stop:1 #060b14);
            }
            QMainWindow {
                background: transparent;
                color: #f2fcff;
            }
            QLabel {
                color: #e4fbff;
                font-size: 12px;
            }
            QLabel#eyebrow {
                color: #8cf4d4;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
            }
            QLabel#header {
                font-size: 24px;
                font-weight: 700;
                color: #ffffff;
            }
            QLabel#subtitle {
                color: #b6efff;
                font-size: 13px;
            }
            QLabel#sectionTitle {
                font-size: 18px;
                font-weight: 700;
                color: #f6ffff;
            }
            QLabel#sectionHint {
                color: #9fd8e7;
                font-size: 12px;
            }
            QLabel#fieldLabel {
                color: #dffcff;
                font-size: 11px;
                font-weight: 700;
            }
            QLabel#status {
                color: #d7fff4;
                font-style: italic;
            }
            QFrame#heroCard, QFrame#sectionCard, QFrame#footerCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(28, 75, 110, 0.82),
                    stop:0.45 rgba(14, 43, 71, 0.9),
                    stop:1 rgba(8, 20, 37, 0.92));
                border: 1px solid rgba(107, 221, 255, 0.42);
                border-radius: 18px;
            }
            QLineEdit, QListWidget {
                background: rgba(3, 14, 28, 0.62);
                color: #f5ffff;
                border: 1px solid rgba(106, 226, 255, 0.5);
                border-radius: 12px;
                padding: 10px 12px;
                selection-background-color: rgba(28, 227, 255, 0.35);
            }
            QListWidget {
                outline: none;
            }
            QPushButton {
                border-radius: 12px;
                padding: 9px 14px;
                font-weight: 700;
            }
            QPushButton#toolbarButton, QPushButton#glassButton {
                color: #eaffff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(87, 210, 255, 0.28),
                    stop:1 rgba(15, 61, 92, 0.7));
                border: 1px solid rgba(110, 230, 255, 0.46);
            }
            QPushButton#toolbarButton:hover, QPushButton#glassButton:hover {
                border: 1px solid rgba(133, 255, 236, 0.72);
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(116, 235, 255, 0.4),
                    stop:1 rgba(20, 78, 114, 0.78));
            }
            QPushButton#primaryButton {
                color: #06233c;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fff6a3,
                    stop:0.34 #9cf9d9,
                    stop:1 #3ce1ff);
                border: 1px solid #9dfde2;
            }
            QPushButton#primaryButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fffac0,
                    stop:0.34 #b8ffe5,
                    stop:1 #5ee9ff);
            }
            QPushButton:pressed {
                padding-top: 10px;
            }
            QPushButton:disabled {
                color: #7895a5;
                background: rgba(31, 58, 74, 0.72);
                border: 1px solid rgba(91, 123, 142, 0.42);
            }
            QProgressBar {
                min-height: 22px;
                border-radius: 11px;
                background: rgba(4, 18, 33, 0.78);
                border: 1px solid rgba(110, 235, 255, 0.45);
                color: #efffff;
                text-align: center;
                font-weight: 700;
            }
            QProgressBar::chunk {
                border-radius: 11px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f4e06e,
                    stop:0.35 #4df1c4,
                    stop:1 #2cb9ff);
            }
            QMenuBar {
                background: rgba(5, 18, 33, 0.82);
                color: #e9ffff;
                border-bottom: 1px solid rgba(95, 218, 255, 0.28);
                padding: 4px;
            }
            QMenuBar::item {
                padding: 6px 10px;
                border-radius: 8px;
                background: transparent;
            }
            QMenuBar::item:selected {
                background: rgba(77, 210, 255, 0.2);
            }
            QMenu {
                background: rgba(7, 21, 38, 0.96);
                color: #efffff;
                border: 1px solid rgba(103, 223, 255, 0.35);
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 18px;
                border-radius: 8px;
            }
            QMenu::item:selected {
                background: rgba(54, 231, 220, 0.2);
            }
            """
        )
