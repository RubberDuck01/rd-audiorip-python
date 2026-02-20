from pathlib import Path
from PyQt6.QtCore import QObject, QThread
from rd_audiorip.services.downloader import DownloadWorker
from rd_audiorip.ui.main_window import MainWindow

class MainController(QObject):
    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self.window = window
        self._thread: QThread | None = None
        self.worker: DownloadWorker | None = None
        
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
        
        self.window.set_busy(True)
        self.window.set_progress(0)
        self.window.set_status("Starting download...")
        
        self._thread = QThread()
        self.worker = DownloadWorker(url=url, output_dir=output_dir)
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
        self.window.on_download_success(message)
        self.window.set_busy(False)
    
    def on_error(self, message: str) -> None:
        self.window.set_status(f"Error: {message}")
        self.window.set_busy(False)
    
    def cleanup(self) -> None:
        self.worker = None
        self._thread = None