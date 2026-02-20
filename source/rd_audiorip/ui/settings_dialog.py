from pathlib import Path
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)
from rd_audiorip.models.config import Config


class SettingsDialog(QDialog):
    def __init__(self, parent, config: Config) -> None:
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 600, 300)
        self.setModal(True)

        layout = QVBoxLayout(self)

        #? Downloads directory:
        layout.addWidget(QLabel("Downloads Directory:"))
        dir_row = QHBoxLayout()
        self.dir_input = QLineEdit(self.config.downloads_dir)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(self.dir_input, stretch=1)
        dir_row.addWidget(browse_btn)
        layout.addLayout(dir_row)

        #? Album art:
        self.album_art_check = QCheckBox("Include Album Art")
        self.album_art_check.setChecked(self.config.album_art)
        layout.addWidget(self.album_art_check)

        #? Metadata:
        self.metadata_check = QCheckBox("Include Metadata")
        self.metadata_check.setChecked(self.config.metadata)
        layout.addWidget(self.metadata_check)

        #? Auto-update yt-dlp:
        self.auto_update_check = QCheckBox("Auto-Update yt-dlp")
        self.auto_update_check.setChecked(self.config.auto_update)
        layout.addWidget(self.auto_update_check)

        #? FLAC compression level:
        flac_row = QHBoxLayout()
        flac_row.addWidget(QLabel("FLAC Compression Level:"))
        self.flac_spinbox = QSpinBox()
        self.flac_spinbox.setRange(0, 12)
        self.flac_spinbox.setValue(self.config.flac_compression_level)
        flac_row.addWidget(self.flac_spinbox)
        flac_row.addStretch()
        layout.addLayout(flac_row)

        layout.addStretch()

        #? Buttons:
        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self._on_ok)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _browse_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Select Downloads Directory", self.dir_input.text()
        )
        if directory:
            self.dir_input.setText(directory)

    def _on_ok(self) -> None:
        self.config.set_downloads_dir(self.dir_input.text())
        self.config.set_album_art(self.album_art_check.isChecked())
        self.config.set_metadata(self.metadata_check.isChecked())
        self.config.set_auto_update(self.auto_update_check.isChecked())
        self.config.set_flac_compression_level(self.flac_spinbox.value())
        self.accept()