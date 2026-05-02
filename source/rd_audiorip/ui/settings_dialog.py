from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
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
        self.setWindowTitle("RD AudioRip - Settings")
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
        dest_form.addRow("Downloads directory:", dir_row)
        layout.addWidget(dest_group)

        # Processing group
        proc_group = QGroupBox("Processing")
        proc_form = QFormLayout(proc_group)
        proc_form.setContentsMargins(10, 12, 10, 10)
        proc_form.setSpacing(6)

        self.auto_update_check = QCheckBox("Auto-update yt-dlp on launch")
        self.auto_update_check.setChecked(self.config.auto_update)
        proc_form.addRow(self.auto_update_check)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP3", "FLAC"])
        self.format_combo.setCurrentIndex(1 if self.config.preferred_format.lower() == "flac" else 0)
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        proc_form.addRow("Audio format:", self.format_combo)

        self.flac_spinbox = QSpinBox()
        self.flac_spinbox.setRange(0, 12)
        self.flac_spinbox.setValue(self.config.flac_compression_level)
        self.flac_spinbox.setEnabled(self.config.preferred_format.lower() == "flac")
        self.flac_spinbox.valueChanged.connect(self._on_flac_level_changed)
        proc_form.addRow("FLAC compression level:", self.flac_spinbox)

        self.flac_hint_label = QLabel()
        hint_font = self.flac_hint_label.font()
        hint_font.setItalic(True)
        hint_font.setPointSize(hint_font.pointSize() - 1)
        self.flac_hint_label.setFont(hint_font)
        self.flac_hint_label.setEnabled(self.config.preferred_format.lower() == "flac")
        self._on_flac_level_changed(self.flac_spinbox.value())
        proc_form.addRow("", self.flac_hint_label)
        layout.addWidget(proc_group)

        # Additional Features group
        tags_group = QGroupBox("Additional Features")
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
        
        # Cookies group
        cookies_group = QGroupBox("Bot Detection Bypass (Cookies)")
        cookies_form = QFormLayout(cookies_group)
        cookies_form.setContentsMargins(10, 12, 10, 10)
        cookies_form.setSpacing(6)

        self.cookies_check = QCheckBox("Use cookies")
        self.cookies_check.setChecked(self.config.cookies_enabled)
        self.cookies_check.toggled.connect(self._on_cookies_toggled)
        cookies_form.addRow(self.cookies_check)

        cookies_path_row = QHBoxLayout()
        cookies_path_row.setSpacing(6)
        self.cookies_input = QLineEdit(self.config.cookies_path)
        self.cookies_input.setPlaceholderText("Path to cookies.txt...")
        self.cookies_input.setEnabled(self.config.cookies_enabled)
        cookies_browse_btn = QPushButton("Browse...")
        cookies_browse_btn.setEnabled(self.config.cookies_enabled)
        cookies_browse_btn.clicked.connect(self._browse_cookies)
        self.cookies_browse_btn = cookies_browse_btn
        cookies_path_row.addWidget(self.cookies_input, stretch=1)
        cookies_path_row.addWidget(cookies_browse_btn)
        cookies_form.addRow("Cookies file:", cookies_path_row)

        cookies_hint = QLabel("Export cookies from your browser using a browser extension (e.g. \"cookies.txt\" for Firefox or \"Get cookies.txt LOCALLY\" for Chrome).")
        cookies_hint_font = cookies_hint.font()
        cookies_hint_font.setItalic(True)
        cookies_hint_font.setPointSize(cookies_hint_font.pointSize() - 1)
        cookies_hint.setFont(cookies_hint_font)
        cookies_hint.setEnabled(False)
        cookies_hint.setWordWrap(True)
        cookies_form.addRow("", cookies_hint)
        layout.addWidget(cookies_group)

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

    def _on_cookies_toggled(self, checked: bool) -> None:
        self.cookies_input.setEnabled(checked)
        self.cookies_browse_btn.setEnabled(checked)

    def _browse_cookies(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Cookies File", self.cookies_input.text(), "Text files (*.txt);;All files (*)"
        )
        if path:
            self.cookies_input.setText(path)

    def _on_format_changed(self, index: int) -> None:
        is_flac = index == 1
        self.flac_spinbox.setEnabled(is_flac)
        self.flac_hint_label.setEnabled(is_flac)

    def _on_flac_level_changed(self, value: int) -> None:
        if value == 0:
            hint = "No compression — largest file, fastest encoding"
        elif value <= 4:
            hint = "Light compression — good balance of speed and size"
        elif value <= 7:
            hint = "Moderate compression"
        elif value == 8:
            hint = "Default — recommended for most uses"
        elif value <= 11:
            hint = "High compression — slower encoding, smaller file"
        else:
            hint = "Maximum compression — smallest file, slowest encoding"
        self.flac_hint_label.setText(hint)

    def _browse_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Downloads Directory", self.dir_input.text())
        if directory:
            self.dir_input.setText(directory)

    def _on_ok(self) -> None:
        self.config.set_downloads_dir(self.dir_input.text())
        self.config.set_album_art(self.album_art_check.isChecked())
        self.config.set_metadata(self.metadata_check.isChecked())
        self.config.set_auto_update(self.auto_update_check.isChecked())
        self.config.set_preferred_format(self.format_combo.currentText().lower())
        self.config.set_flac_compression_level(self.flac_spinbox.value())
        self.config.set_cookies_enabled(self.cookies_check.isChecked())
        self.config.set_cookies_path(self.cookies_input.text().strip())
        self.accept()

