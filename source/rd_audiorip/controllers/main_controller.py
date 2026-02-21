from pathlib import Path
from PyQt6.QtCore import QObject, QThread
from rd_audiorip.services.downloader import DownloadWorker, get_video_info, get_video_metrics
from rd_audiorip.models.stats import Stats
from rd_audiorip.ui.main_window import MainWindow

class MainController(QObject):
    def __init__(self, window: MainWindow, stats: Stats) -> None:
        super().__init__()
        self.window = window
        self.stats = stats
        self._thread: QThread | None = None
        self.worker: DownloadWorker | None = None
        self.pending_size_mb: float = 0.0
        self.pending_duration_sec: int = 0
        
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
        
        self.window.set_status("Fetching video info...")
        info = get_video_info(url)
        display_text = info if info else url
        self.window.add_to_queue(display_text)
        
        self.pending_size_mb, self.pending_duration_sec = get_video_metrics(url)
        
        self.window.set_busy(True)
        self.window.set_progress(0)
        self.window.set_status("Starting download...")
        
        self._thread = QThread()
        self.worker = DownloadWorker(
            url=url,
            output_dir=output_dir,
            preferred_format=self.window.config.preferred_format,
            embed_thumbnail=self.window.config.album_art,
            embed_metadata=self.window.config.metadata,
            flac_compression_level=self.window.config.flac_compression_level
        )
        self.worker.moveToThread(self._thread)
        
        self._thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.window.set_progress)
        self.worker.status.connect(self.window.set_status)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        
        self.worker.finished.connect(self._thread.quit)
        self.worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self.cleanup)
        
        self._thread.start()
    
    def on_finished(self, message: str) -> None:
        self.stats.add_successful_download(
            size_mb=self.pending_size_mb,
            duration_sec=self.pending_duration_sec
        )
        self.pending_size_mb = 0.0
        self.pending_duration_sec = 0
        self.window.on_download_success(message)
        self.window.set_busy(False)
    
    def on_error(self, message: str) -> None:
        self.pending_size_mb = 0.0
        self.pending_duration_sec = 0
        self.window.set_status(f"Error: {message}")
        self.window.set_busy(False)
    
    def cleanup(self) -> None:
        self.worker = None
        self._thread = None