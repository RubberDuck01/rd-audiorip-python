import os
import webbrowser
from pathlib import Path

from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtGui import QAction, QDesktopServices
from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
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
from rd_audiorip.ui.about_dialog import AboutDialog
from rd_audiorip.ui.ffmpeg_dialog import FfmpegDialog
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
        self.resize(720, 500)

        self._build_menu()
        self._build_ui()

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
        tools_menu.addAction(QAction("&Manage FFmpeg", self, triggered=self.open_ffmpeg_manager))

        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(QAction("&View Source on GitHub", self, triggered=self.visit_github))
        help_menu.addAction(QAction("&About RD AudioRip", self, triggered=self.open_about))
        help_menu.addAction(QAction("&About Qt", self, triggered=self.open_about_qt))

    def _build_ui(self) -> None:
        root = QWidget(self)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(6)

        # App header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(1)
        header_layout.setContentsMargins(0, 0, 0, 8)
        title_label = QLabel("RD AudioRip")
        title_font = title_label.font()
        title_font.setPointSize(title_font.pointSize() + 4)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        subtitle_label = QLabel("Portable YouTube audio downloader — use the menu bar to access all features.")
        subtitle_label.setEnabled(False)
        header_layout.addWidget(subtitle_label)
        layout.addLayout(header_layout)

        # Download group
        download_group = QGroupBox("New Download")
        download_form = QFormLayout(download_group)
        download_form.setContentsMargins(10, 12, 10, 10)
        download_form.setSpacing(6)

        url_row = QHBoxLayout()
        url_row.setSpacing(6)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        url_row.addWidget(self.url_input, stretch=1)
        self.download_btn = QPushButton("Start Download")
        self.download_btn.clicked.connect(self.on_download_clicked)
        url_row.addWidget(self.download_btn)
        download_form.addRow("YouTube URL:", url_row)

        out_row = QHBoxLayout()
        out_row.setSpacing(6)
        self.output_input = QLineEdit(self.config.downloads_dir)
        self.output_input.setReadOnly(True)
        out_row.addWidget(self.output_input, stretch=1)
        browse_btn = QPushButton("Choose Folder")
        browse_btn.clicked.connect(self.browse_output)
        out_row.addWidget(browse_btn)
        download_form.addRow("Output Directory:", out_row)

        layout.addWidget(download_group)

        # Queue group
        queue_group = QGroupBox("Session Queue")
        queue_layout = QVBoxLayout(queue_group)
        queue_layout.setContentsMargins(10, 12, 10, 10)
        queue_layout.setSpacing(6)

        self.queue_list = QListWidget()
        queue_layout.addWidget(self.queue_list, stretch=1)

        clear_row = QHBoxLayout()
        clear_row.addStretch()
        clear_btn = QPushButton("Clear Queue")
        clear_btn.clicked.connect(self.clear_queue)
        clear_row.addWidget(clear_btn)
        queue_layout.addLayout(clear_row)

        layout.addWidget(queue_group, stretch=1)

        # Progress group
        progress_group = QGroupBox("Transfer Progress")
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setContentsMargins(10, 12, 10, 10)
        progress_layout.setSpacing(4)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        progress_layout.addWidget(self.progress)

        self.status_label = QLabel("Ready!")
        progress_layout.addWidget(self.status_label)

        layout.addWidget(progress_group)

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

    def open_ffmpeg_manager(self) -> None:
        dialog = FfmpegDialog(self)
        dialog.exec()

    def clear_queue(self) -> None:
        self.queue_list.clear()
        self.set_status("Download queue cleared.")

    def visit_github(self) -> None:
        webbrowser.open("https://github.com/RubberDuck01/rd-audiorip-python")

    def open_about(self) -> None:
        AboutDialog(self).exec()

    def open_about_qt(self) -> None:
        QMessageBox.aboutQt(self)

    def open_stats(self) -> None:
        dialog = StatsDialog(self, self.stats)
        dialog.exec()
