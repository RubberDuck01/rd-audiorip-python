from pathlib import Path
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from rd_audiorip.services.downloader import DownloadWorker, find_ytdlp_exe, get_playlist_info, get_video_info, get_video_metrics, update_ytdlp
from rd_audiorip.models.stats import Stats
from rd_audiorip.ui.main_window import MainWindow


class AutoUpdateWorker(QObject):
    finished = pyqtSignal(str)  # status message for the window

    def run(self) -> None:
        ok, _ = update_ytdlp()
        if ok:
            self.finished.emit("yt-dlp is up to date, AudioRip ready!")
        else:
            self.finished.emit("yt-dlp auto-update failed. Go to Tools → yt-dlp Settings to update manually.")

class MainController(QObject):
    def __init__(self, window: MainWindow, stats: Stats) -> None:
        super().__init__()
        self.window = window
        self.stats = stats
        self._thread: QThread | None = None
        self.worker: DownloadWorker | None = None
        self.track_size: float = 0.0
        self.track_duration: int = 0
        self.is_playlist: bool = False
        self._output_dir: str = ""
        self._pending_paths: list[str] = []  # used only for playlist progress counter
        self._download_size_mb: float = 0.0
        self._current_queue_row: int = -1
        self._playlist_total: int = 0

        self.window.download_requested.connect(self.start_download)
        self._maybe_auto_update_ytdlp()

    def _maybe_auto_update_ytdlp(self) -> None:
        if not self.window.config.auto_update:
            return
        if not find_ytdlp_exe():
            self.window.set_status(
                "yt-dlp is not installed. Go to Tools → yt-dlp Settings to install it first."
            )
            return
        self.window.set_status("Checking for yt-dlp updates...")
        self._au_thread = QThread()
        self._au_worker = AutoUpdateWorker()
        self._au_worker.moveToThread(self._au_thread)
        self._au_thread.started.connect(self._au_worker.run)
        self._au_worker.finished.connect(self.window.set_status)
        self._au_worker.finished.connect(self._au_thread.quit)
        self._au_thread.finished.connect(self._au_thread.deleteLater)
        self._au_thread.start()
    
    def start_download(self, url: str, output_dir: str) -> None:
        if self._thread is not None:
            self.window.set_status("Download already in progress!")
            return
        
        if not url.startswith("http"):
            self.window.set_status("Invalid URL!")
            return
        
        if not Path(output_dir).exists():
            self.window.set_status("Output directory does not exist!")
            return

        # Detect playlist
        is_playlist, playlist_title, track_count = get_playlist_info(url)
        if is_playlist:
            if not self.window.confirm_playlist(playlist_title, track_count):
                return
            self.is_playlist = True
            self._playlist_total = track_count
            display_text = f"[Playlist] {playlist_title} ({track_count} tracks)"
            self._current_queue_row = self.window.add_to_queue(display_text)
            self.track_duration = 0
        else:
            self.is_playlist = False
            self._playlist_total = 0
            info = get_video_info(url)
            display_text = info if info else url
            self._current_queue_row = self.window.add_to_queue(display_text)
            _, self.track_duration = get_video_metrics(url)
        
        self.window.set_busy(True)
        self.window.set_progress(0)
        self.window.set_status("Now downloading...")
        self._output_dir = output_dir
        self._pending_paths = []
        self._download_size_mb = 0.0
        
        self._thread = QThread()
        self.worker = DownloadWorker(
            url=url,
            output_dir=output_dir,
            preferred_format=self.window.config.preferred_format,
            embed_thumbnail=self.window.config.album_art,
            embed_metadata=self.window.config.metadata,
            flac_compression_level=self.window.config.flac_compression_level,
            is_playlist=self.is_playlist,
            cookies_enabled=self.window.config.cookies_enabled,
            cookies_path=self.window.config.cookies_path,
        )
        self.worker.moveToThread(self._thread)
        
        self._thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.window.set_progress)
        self.worker.output_file.connect(self.on_output_file)
        self.worker.download_size_mb.connect(self.on_download_size)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        
        self.worker.finished.connect(self._thread.quit)
        self.worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self.cleanup)
        
        self._thread.start()
    
    def on_output_file(self, path: str) -> None:
        # Track count for playlist progress label — not used for sizing.
        self._pending_paths.append(path)
        if self.is_playlist:
            self.window.update_queue_item_progress(
                self._current_queue_row, len(self._pending_paths), self._playlist_total
            )

    def on_download_size(self, size_mb: float) -> None:
        self._download_size_mb = size_mb

    def on_finished(self, message: str) -> None:
        self.stats.add_successful_download(
            size_mb=self._download_size_mb,
            duration_sec=self.track_duration,
        )
        self._pending_paths = []
        self._download_size_mb = 0.0
        self.track_duration = 0
        self.is_playlist = False
        self._playlist_total = 0
        self.window.mark_queue_item_done(self._current_queue_row)
        self.window.on_download_success(message)
        self.window.set_busy(False)
        self.window.show_donation_popup()
    
    def on_error(self, message: str) -> None:
        self._pending_paths = []
        self._download_size_mb = 0.0
        self.track_duration = 0
        self.is_playlist = False
        self._playlist_total = 0
        self.window.set_busy(False)
        self.window.show_download_error(message)
    
    def cleanup(self) -> None:
        self.worker = None
        self._thread = None