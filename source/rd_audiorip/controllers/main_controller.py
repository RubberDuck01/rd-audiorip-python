from pathlib import Path
from PyQt6.QtCore import QObject, QThread
from rd_audiorip.services.downloader import DownloadWorker, get_playlist_info, get_video_info, get_video_metrics
from rd_audiorip.models.stats import Stats
from rd_audiorip.ui.main_window import MainWindow

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
        self._pending_paths: list[str] = []  # paths emitted by output_file signal
        
        self.window.download_requested.connect(self.start_download)
    
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
            display_text = f"[Playlist] {playlist_title} ({track_count} tracks)"
            self.window.add_to_queue(display_text)
            self.track_duration = 0
        else:
            self.is_playlist = False
            info = get_video_info(url)
            display_text = info if info else url
            self.window.add_to_queue(display_text)
            _, self.track_duration = get_video_metrics(url)
        
        self.window.set_busy(True)
        self.window.set_progress(0)
        self.window.set_status("Starting download...")
        self._output_dir = output_dir
        self._pending_paths = []
        
        self._thread = QThread()
        self.worker = DownloadWorker(
            url=url,
            output_dir=output_dir,
            preferred_format=self.window.config.preferred_format,
            embed_thumbnail=self.window.config.album_art,
            embed_metadata=self.window.config.metadata,
            flac_compression_level=self.window.config.flac_compression_level,
            is_playlist=self.is_playlist,
        )
        self.worker.moveToThread(self._thread)
        
        self._thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.window.set_progress)
        self.worker.output_file.connect(self.on_output_file)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        
        self.worker.finished.connect(self._thread.quit)
        self.worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self.cleanup)
        
        self._thread.start()
    
    def on_output_file(self, path: str) -> None:
        # Just record the path — the file may not be fully written yet.
        # Actual stat is deferred to on_finished when yt-dlp has exited.
        self._pending_paths.append(path)

    def _stat_size(self, path: str) -> float:
        """Return file size in MB, 0.0 on any error."""
        p = Path(path)
        if not p.is_absolute():
            p = Path(self._output_dir) / p
        try:
            return p.stat().st_size / (1024 * 1024)
        except OSError:
            return 0.0

    def on_finished(self, message: str) -> None:
        if self.is_playlist:
            for path in self._pending_paths:
                self.stats.add_successful_download(size_mb=self._stat_size(path), duration_sec=0)
        else:
            size_mb = self._stat_size(self._pending_paths[0]) if self._pending_paths else 0.0
            self.stats.add_successful_download(size_mb=size_mb, duration_sec=self.track_duration)
        self._pending_paths = []
        self.track_duration = 0
        self.is_playlist = False
        self.window.on_download_success(message)
        self.window.set_busy(False)
    
    def on_error(self, message: str) -> None:
        self._pending_paths = []
        self.track_duration = 0
        self.is_playlist = False
        self.window.set_busy(False)
        self.window.show_download_error(message)
    
    def cleanup(self) -> None:
        self.worker = None
        self._thread = None