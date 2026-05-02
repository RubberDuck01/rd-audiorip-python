import os
import webbrowser
from pathlib import Path

from PyQt6.QtCore import Qt, QEvent, QUrl, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QDesktopServices, QKeySequence, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from rd_audiorip.models.config import Config
from rd_audiorip.models.stats import Stats
from rd_audiorip.ui.about_dialog import AboutDialog
from rd_audiorip.ui.donation_dialog import DonationDialog
from rd_audiorip.ui.ffmpeg_dialog import FfmpegDialog
from rd_audiorip.ui.settings_dialog import SettingsDialog
from rd_audiorip.ui.stats_dialog import StatsDialog
from rd_audiorip.ui.update_dialog import UpdateAvailableDialog
from rd_audiorip.ui.ytdlp_dialog import YtdlpDialog
from rd_audiorip.resources import get_resources_dir
from rd_audiorip.version import __version__


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
        open_action = QAction("&Open Downloads Directory", self, triggered=self.open_downloads_directory)
        open_action.setShortcut(QKeySequence("Ctrl+E"))
        file_menu.addAction(open_action)
        settings_action = QAction("&Settings", self, triggered=self.open_settings)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        quit_action = QAction("&Exit", self, triggered=self.close)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        file_menu.addAction(quit_action)

        edit_menu = menubar.addMenu("&Edit")
        clear_action = QAction("&Clear Queue", self, triggered=self.clear_queue)
        clear_action.setShortcut(QKeySequence("Ctrl+Shift+Del"))
        edit_menu.addAction(clear_action)
        edit_menu.addSeparator()
        self._clipboard_paste_action = QAction("&Auto-paste URL from Clipboard", self)
        self._clipboard_paste_action.setCheckable(True)
        self._clipboard_paste_action.setChecked(self.config.clipboard_paste_enabled)
        self._clipboard_paste_action.toggled.connect(self._on_clipboard_paste_toggled)
        edit_menu.addAction(self._clipboard_paste_action)

        view_menu = menubar.addMenu("&View")
        stats_action = QAction("&My Statistics", self, triggered=self.open_stats)
        stats_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        view_menu.addAction(stats_action)

        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction(QAction("&yt-dlp Settings", self, triggered=self.open_ytdlp_manager))
        tools_menu.addAction(QAction("&FFmpeg Settings", self, triggered=self.open_ffmpeg_manager))

        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(QAction("&Check for Updates", self, triggered=self.check_for_update))
        help_menu.addSeparator()
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
        header_layout.setSpacing(4)
        header_layout.setContentsMargins(0, 0, 0, 8)
        branding_label = QLabel()
        branding_path = get_resources_dir() / "rd_audiorip_branding.png"
        if branding_path.exists():
            pix = QPixmap(str(branding_path))
            branding_label.setPixmap(pix.scaledToHeight(52, Qt.TransformationMode.SmoothTransformation))
        else:
            branding_label.setText("RD AudioRip")
            font = branding_label.font()
            font.setPointSize(font.pointSize() + 4)
            font.setBold(True)
            branding_label.setFont(font)
        branding_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(branding_label)
        subtitle_label = QLabel("Powerful audio downloader & converter — Made with \u2665 by Rubber Duck")
        subtitle_label.setEnabled(False)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)
        layout.addLayout(header_layout)

        # Download group
        download_group = QGroupBox("New Download")
        download_form = QFormLayout(download_group)
        download_form.setContentsMargins(10, 12, 10, 10)
        download_form.setSpacing(6)

        self.format_hint_label = QLabel()
        hint_font = self.format_hint_label.font()
        hint_font.setItalic(True)
        hint_font.setPointSize(hint_font.pointSize() - 1)
        self.format_hint_label.setFont(hint_font)
        self.format_hint_label.setEnabled(False)
        self._update_format_hint()
        download_form.addRow(self.format_hint_label)

        url_row = QHBoxLayout()
        url_row.setSpacing(6)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        url_row.addWidget(self.url_input, stretch=1)
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.on_download_clicked)
        url_row.addWidget(self.download_btn)
        download_form.addRow("YouTube URL:", url_row)

        out_row = QHBoxLayout()
        out_row.setSpacing(6)
        self.output_input = QLineEdit(self.config.downloads_dir)
        self.output_input.setReadOnly(True)
        out_row.addWidget(self.output_input, stretch=1)
        browse_btn = QPushButton("Choose...")
        browse_btn.clicked.connect(self.browse_output)
        out_row.addWidget(browse_btn)
        download_form.addRow("Download to:", out_row)

        layout.addWidget(download_group)

        # Queue group
        queue_group = QGroupBox("Queue")
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
        progress_group = QGroupBox("Download Progress")
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

        # Footer row
        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(2, 0, 2, 0)
        made_with_label = QLabel("Made with \u2665 by Rubber Duck")
        made_with_label.setEnabled(False)
        footer_font = made_with_label.font()
        footer_font.setPointSize(footer_font.pointSize() - 1)
        made_with_label.setFont(footer_font)
        footer_row.addWidget(made_with_label)
        footer_row.addStretch()
        version_label = QLabel(f"Version {__version__}")
        version_label.setEnabled(False)
        version_label.setFont(footer_font)
        footer_row.addWidget(version_label)
        layout.addLayout(footer_row)

        self.setCentralWidget(root)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.ActivationChange and self.isActiveWindow():
            if self.config.clipboard_paste_enabled and not self.url_input.text().strip():
                text = QApplication.clipboard().text().strip()
                if text.startswith("http"):
                    self.url_input.setText(text)
                    self.set_status("URL pasted from clipboard.")
        super().changeEvent(event)

    def _on_clipboard_paste_toggled(self, checked: bool) -> None:
        self.config.set_clipboard_paste_enabled(checked)

    def browse_output(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Downloads Directory", self.output_input.text())
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
            # self.set_status("Opened downloads directory.")
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

    def show_download_error(self, message: str) -> None:
        self.set_status("Download failed.")
        dlg = QDialog(self)
        dlg.setWindowTitle("Download Error")
        dlg.setModal(True)
        dlg.resize(520, 240)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        info = QLabel("yt-dlp reported the following error:")
        layout.addWidget(info)
        text_box = QTextEdit()
        text_box.setReadOnly(True)
        text_box.setPlainText(message)
        layout.addWidget(text_box)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setDefault(True)
        close_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)
        dlg.exec()

    def show_download_error(self, message: str) -> None:
        self.set_status("Download failed.")
        dlg = QDialog(self)
        dlg.setWindowTitle("Download Error")
        dlg.setModal(True)
        dlg.resize(520, 240)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        info = QLabel("yt-dlp reported the following error:")
        layout.addWidget(info)
        text_box = QTextEdit()
        text_box.setReadOnly(True)
        text_box.setPlainText(message)
        layout.addWidget(text_box)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setDefault(True)
        close_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)
        dlg.exec()

    def add_to_queue(self, display_text: str) -> int:
        self.queue_list.addItem(display_text)
        return self.queue_list.count() - 1

    def mark_queue_item_done(self, row: int) -> None:
        item = self.queue_list.item(row)
        if item is None:
            return
        text = item.text()
        if not text.startswith("\u2713 "):
            item.setText(f"\u2713 {text}")
        item.setForeground(QColor("#2e7d32"))

    def update_queue_item_progress(self, row: int, done: int, total_count: int) -> None:
        item = self.queue_list.item(row)
        if item is None:
            return
        text = item.text()
        # Replace or append the (X/Y tracks) counter
        import re as _re
        text = _re.sub(r"\s*\(\d+/\d+ done\)", "", text)
        item.setText(f"{text} ({done}/{total_count} done)")

    def on_download_success(self, message: str) -> None:
        self.set_progress(100)
        self.set_status(message)
        self.url_input.clear()

    def confirm_playlist(self, title: str, count: str) -> bool:
        result = QMessageBox.question(
            self,
            "Playlist Detected!",
            f"<b>{title}</b><br><br>"
            f"The provided URL is a playlist (album) with <b>{count} tracks</b>.<br>"
            f"All tracks will be downloaded into a subdirectory '{title}'.<br><br>"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        return result == QMessageBox.StandardButton.Yes

    def _update_format_hint(self) -> None:
        fmt = self.config.preferred_format.lower()
        if fmt == "flac":
            level = self.config.flac_compression_level
            self.format_hint_label.setText(f"Downloading to FLAC (compression level {level})")
        else:
            self.format_hint_label.setText("Downloading to MP3 (320 kbps)")

    def open_settings(self) -> None:
        dialog = SettingsDialog(self, self.config)
        if dialog.exec():
            self.output_input.setText(self.config.downloads_dir)
            self._update_format_hint()
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
        AboutDialog(self, config=self.config).exec()

    def show_donation_popup(self) -> None:
        if not self.config.i_have_donated:
            DonationDialog(self).exec()

    def show_update_available(self, latest_version: str) -> None:
        UpdateAvailableDialog(self, latest_version=latest_version).exec()

    def show_up_to_date(self) -> None:
        QMessageBox.information(self, "RD AudioRip", "You're already on the latest version!")

    def check_for_update(self) -> None:
        self.controller._check_for_app_update(manual=True)

    def open_about_qt(self) -> None:
        QMessageBox.aboutQt(self)

    def open_stats(self) -> None:
        dialog = StatsDialog(self, self.stats)
        dialog.exec()
