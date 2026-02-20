import webbrowser
from pathlib import Path
from rd_audiorip.models.config import Config
from rd_audiorip.ui.settings_dialog import SettingsDialog
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget
)

class MainWindow(QMainWindow):
    download_requested = pyqtSignal(str, str)
    
    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self.setWindowTitle("Rubber Duck's AudioRip")
        self.resize(760, 500)
        
        #? Menu bar:
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("&File")
        file_menu.addAction("&Open Downloads Directory", self.browse_output)
        file_menu.addAction("&Settings", self.open_settings)
        file_menu.addSeparator()
        file_menu.addAction("&Quit", self.close)
        
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction("&Clear Queue", self.clear_queue)
        
        view_menu = menubar.addMenu("&View")
        view_menu.addAction("&My Statistics", lambda: self.set_status("Statistics view not implemented yet."))
        view_menu.addAction("&My Configuration", lambda: self.set_status("Configuration view not implemented yet."))
        
        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction("&Check for Updates", lambda: self.set_status("Update checker not implemented yet."))
        tools_menu.addAction("&yt-dlp Configuration", lambda: self.set_status("yt-dlp configuration not implemented yet."))
        tools_menu.addAction("&FFmpeg Configuration", lambda: self.set_status("FFmpeg configuration not implemented yet."))
        
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("&View on GitHub", self.visit_github)
        help_menu.addAction("&About RD AudioRip", self.open_about)
        help_menu.addAction("&About Qt", self.open_about_qt)
        
        #? Main UI:
        root = QWidget(self)
        self.layout = QVBoxLayout(root)
        
        #? URL input:
        url_row = QHBoxLayout()
        url_row.addWidget(QLabel("YouTube URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        url_row.addWidget(self.url_input, stretch=1)
        
        self.download_btn = QPushButton("Download")
        self.download_btn.setFixedWidth(120)
        self.download_btn.clicked.connect(self.on_download_clicked)
        url_row.addWidget(self.download_btn)
        self.layout.addLayout(url_row)
        
        #? Output directory:
        self.layout.addWidget(QLabel("Output directory:"))
        out_row = QHBoxLayout()
        self.output_input = QLineEdit(self.config.downloads_dir)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_output)
        out_row.addWidget(self.output_input, stretch=1)
        out_row.addWidget(browse_btn)
        self.layout.addLayout(out_row)
        
        #? Queue:
        self.layout.addWidget(QLabel("Download Queue:"))
        self.queue_list = QListWidget()
        self.layout.addWidget(self.queue_list, stretch=1)

        #? Progress bar:
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.layout.addWidget(self.progress)

        #? Status label:
        self.status_label = QLabel("Ready!")
        self.layout.addWidget(self.status_label)
        
        self.setCentralWidget(root)
    
    def browse_output(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.output_input.text())
        if directory:
            self.output_input.setText(directory)
            self.config.set_downloads_dir(directory)
    
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
    
    def clear_queue(self) -> None:
        self.queue_list.clear()
        self.set_status("Download queue cleared.")
    
    def visit_github(self) -> None:
        webbrowser.open("https://github.com/RubberDuck01/rd-audiorip-python")
    
    def open_about(self) -> None:
        self.set_status("RD AudioRip - A simple YouTube audio downloader built with Python and PyQt6.")
    
    def open_about_qt(self) -> None:
        self.set_status("This application uses Qt for its graphical user interface.")
    
    