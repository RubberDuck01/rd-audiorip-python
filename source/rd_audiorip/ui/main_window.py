from pathlib import Path
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget
)
class MainWindow(QMainWindow):
    download_requested = pyqtSignal(str, str)
    
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Rubber Duck's AudioRip")
        self.resize(760, 240)
        
        root = QWidget(self)
        self.layout = QVBoxLayout(root)
        
        self.layout.addWidget(QLabel("YouTube URL"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.layout.addWidget(self.url_input)
        
        self.layout.addWidget(QLabel("Output Directory"))
        out_row = QHBoxLayout()
        self.output_input = QLineEdit(str(Path.home() / "Music"))
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_output)
        out_row.addWidget(self.output_input)
        out_row.addWidget(browse_btn)
        self.layout.addLayout(out_row)
        
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.on_download_clicked)
        self.layout.addWidget(self.download_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready!")
        self.layout.addWidget(self.status_label)
        
        self.setCentralWidget(root)
    
    def browse_output(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.output_input.text())
        if directory:
            self.output_input.setText(directory)
    
    def on_download_clicked(self) -> None:
        self.download_requested.emit(self.url_input.text().strip(), self.output_input.text().strip())
    
    def set_busy(self, busy: bool) -> None:
        self.download_btn.setEnabled(not busy)
        self.url_input.setEnabled(not busy)
        self.output_input.setEnabled(not busy)
    
    def set_progress(self, value: int) -> None:
        self.progress_bar.setValue(max(0, min(100, value)))
    
    def set_status(self, text: str) -> None:
        self.status_label.setText(text)
    
    def on_download_success(self, message: str) -> None:
        self.set_progress(100)
        self.set_status(message)
        self.url_input.clear()