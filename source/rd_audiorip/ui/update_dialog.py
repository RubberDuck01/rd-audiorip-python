from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)
from rd_audiorip.services.updater import (
    UpdateWorker,
    get_installed_version,
    get_latest_ytdlp_version,
)


class UpdateDialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setWindowTitle("Download / Update Tools")
        self.setGeometry(100, 100, 560, 500)
        self.setModal(True)

        self._thread: QThread | None = None
        self._worker: UpdateWorker | None = None

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        #? yt-dlp group
        ytdlp_box = QGroupBox("yt-dlp")
        ytdlp_layout = QVBoxLayout(ytdlp_box)

        ytdlp_installed = get_installed_version("yt-dlp") or "Not installed"
        ytdlp_latest = get_latest_ytdlp_version() or "Unknown"

        info_row = QHBoxLayout()
        self._ytdlp_installed_lbl = QLabel(f"Installed: {ytdlp_installed}")
        self._ytdlp_latest_lbl = QLabel(f"Latest: {ytdlp_latest}")
        info_row.addWidget(self._ytdlp_installed_lbl)
        info_row.addStretch()
        info_row.addWidget(self._ytdlp_latest_lbl)
        ytdlp_layout.addLayout(info_row)

        self._ytdlp_btn = QPushButton("Download / Update yt-dlp")
        self._ytdlp_btn.clicked.connect(lambda: self._start_update("ytdlp"))
        ytdlp_layout.addWidget(self._ytdlp_btn)

        layout.addWidget(ytdlp_box)

        #? FFmpeg group
        ffmpeg_box = QGroupBox("FFmpeg")
        ffmpeg_layout = QVBoxLayout(ffmpeg_box)

        ffmpeg_installed = get_installed_version("ffmpeg") or "Not installed"

        ffmpeg_info_row = QHBoxLayout()
        self._ffmpeg_installed_lbl = QLabel(f"Installed: {ffmpeg_installed}")
        ffmpeg_info_row.addWidget(self._ffmpeg_installed_lbl)
        ffmpeg_info_row.addStretch()
        ffmpeg_layout.addLayout(ffmpeg_info_row)

        self._ffmpeg_btn = QPushButton("Download / Update FFmpeg")
        self._ffmpeg_btn.clicked.connect(lambda: self._start_update("ffmpeg"))
        ffmpeg_layout.addWidget(self._ffmpeg_btn)

        layout.addWidget(ffmpeg_box)

        #? Progress bar
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        layout.addWidget(self._progress)

        #? Log
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(140)
        layout.addWidget(self._log, stretch=1)

        #? Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        self._ytdlp_btn.setEnabled(enabled)
        self._ffmpeg_btn.setEnabled(enabled)

    def _append_log(self, text: str) -> None:
        self._log.append(text)

    def _start_update(self, tool: str) -> None:
        if self._thread is not None:
            return

        self._set_buttons_enabled(False)
        self._progress.setValue(0)

        self._thread = QThread()
        self._worker = UpdateWorker(tool)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._progress.setValue)
        self._worker.status.connect(self._append_log)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)

        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup)

        self._thread.start()

    def _on_finished(self, message: str) -> None:
        self._append_log(f"✓ {message}")
        self._progress.setValue(100)
        self._refresh_versions()
        self._set_buttons_enabled(True)

    def _on_error(self, message: str) -> None:
        self._append_log(f"✗ Error: {message}")
        self._set_buttons_enabled(True)

    def _cleanup(self) -> None:
        self._worker = None
        self._thread = None

    def _refresh_versions(self) -> None:
        ytdlp_ver = get_installed_version("yt-dlp") or "Not installed"
        ffmpeg_ver = get_installed_version("ffmpeg") or "Not installed"
        self._ytdlp_installed_lbl.setText(f"Installed: {ytdlp_ver}")
        self._ffmpeg_installed_lbl.setText(f"Installed: {ffmpeg_ver}")
