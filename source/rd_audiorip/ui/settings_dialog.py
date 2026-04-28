from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
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
        self.resize(520, 320)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Destination group
        dest_group = QGroupBox("Destination")
        dest_form = QFormLayout(dest_group)
        dest_form.setContentsMargins(10, 12, 10, 10)
        dest_form.setSpacing(6)

        dir_row = QHBoxLayout()
        dir_row.setSpacing(6)
        self.dir_input = QLineEdit(self.config.downloads_dir)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(self.dir_input, stretch=1)
        dir_row.addWidget(browse_btn)
        dest_form.addRow("Downloads folder:", dir_row)
        layout.addWidget(dest_group)

        # Audio Tags group
        tags_group = QGroupBox("Audio Tags")
        tags_layout = QVBoxLayout(tags_group)
        tags_layout.setContentsMargins(10, 12, 10, 10)
        tags_layout.setSpacing(4)

        self.album_art_check = QCheckBox("Embed album art (thumbnail as cover art)")
        self.album_art_check.setChecked(self.config.album_art)
        tags_layout.addWidget(self.album_art_check)

        self.metadata_check = QCheckBox("Embed metadata (title, uploader, tags)")
        self.metadata_check.setChecked(self.config.metadata)
        tags_layout.addWidget(self.metadata_check)
        layout.addWidget(tags_group)

        # Processing group
        proc_group = QGroupBox("Processing")
        proc_form = QFormLayout(proc_group)
        proc_form.setContentsMargins(10, 12, 10, 10)
        proc_form.setSpacing(6)

        self.auto_update_check = QCheckBox("Auto-update yt-dlp on launch")
        self.auto_update_check.setChecked(self.config.auto_update)
        proc_form.addRow(self.auto_update_check)

        self.flac_spinbox = QSpinBox()
        self.flac_spinbox.setRange(0, 12)
        self.flac_spinbox.setValue(self.config.flac_compression_level)
        proc_form.addRow("FLAC compression level:", self.flac_spinbox)
        layout.addWidget(proc_group)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("Save")
        ok_btn.setDefault(True)
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self._on_ok)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _browse_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Downloads Directory", self.dir_input.text())
        if directory:
            self.dir_input.setText(directory)

    def _on_ok(self) -> None:
        self.config.set_downloads_dir(self.dir_input.text())
        self.config.set_album_art(self.album_art_check.isChecked())
        self.config.set_metadata(self.metadata_check.isChecked())
        self.config.set_auto_update(self.auto_update_check.isChecked())
        self.config.set_flac_compression_level(self.flac_spinbox.value())
        self.accept()

