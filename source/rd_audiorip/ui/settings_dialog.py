from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from rd_audiorip.models.config import Config


class SettingsDialog(QDialog):
    def __init__(self, parent, config: Config) -> None:
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Settings")
        self.resize(700, 470)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title = QLabel("Download Settings")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Choose where downloads land, what gets embedded into each audio file, and how yt-dlp should behave over time."
        )
        subtitle.setObjectName("dialogSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        destination_card = self._create_card("Destination", "This folder becomes the default output location for new downloads.")
        destination_layout = destination_card.layout()
        self.dir_input = QLineEdit(self.config.downloads_dir)
        browse_btn = QPushButton("Choose Folder")
        browse_btn.setObjectName("glassButton")
        browse_btn.clicked.connect(self._browse_dir)

        dir_row = QHBoxLayout()
        dir_row.setSpacing(10)
        dir_row.addWidget(self.dir_input, stretch=1)
        dir_row.addWidget(browse_btn)
        destination_layout.addLayout(dir_row)
        layout.addWidget(destination_card)

        metadata_card = self._create_card("Audio Tags", "These settings control extra information stored inside the downloaded file.")
        metadata_layout = metadata_card.layout()

        self.album_art_check = QCheckBox("Include Album Art")
        self.album_art_check.setChecked(self.config.album_art)
        metadata_layout.addWidget(self.album_art_check)
        metadata_layout.addWidget(self._description_label("Embed the thumbnail as cover art when the output format supports it."))

        self.metadata_check = QCheckBox("Include Metadata")
        self.metadata_check.setChecked(self.config.metadata)
        metadata_layout.addWidget(self.metadata_check)
        metadata_layout.addWidget(self._description_label("Write title, uploader, and other available tags into the saved audio file."))
        layout.addWidget(metadata_card)

        processing_card = self._create_card("Processing", "Fine-tune how bundled tools behave during conversion and maintenance.")
        processing_layout = processing_card.layout()

        self.auto_update_check = QCheckBox("Auto-Update yt-dlp")
        self.auto_update_check.setChecked(self.config.auto_update)
        processing_layout.addWidget(self.auto_update_check)
        processing_layout.addWidget(self._description_label("Keeps the bundled yt-dlp workflow current when you choose to manage updates."))

        flac_title = QLabel("FLAC Compression Level")
        flac_title.setObjectName("miniTitle")
        processing_layout.addWidget(flac_title)
        processing_layout.addWidget(self._description_label("Higher values reduce FLAC file size but do not change audio quality."))

        flac_row = QHBoxLayout()
        flac_row.setSpacing(10)
        self.flac_spinbox = QSpinBox()
        self.flac_spinbox.setRange(0, 12)
        self.flac_spinbox.setValue(self.config.flac_compression_level)
        flac_row.addWidget(self.flac_spinbox)
        flac_row.addStretch()
        processing_layout.addLayout(flac_row)
        layout.addWidget(processing_card)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("Save Settings")
        ok_btn.setObjectName("primaryButton")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("glassButton")
        ok_btn.clicked.connect(self._on_ok)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        self.apply_styles()

    def _create_card(self, title: str, subtitle: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        card_layout.addWidget(title_label)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("cardSubtitle")
        subtitle_label.setWordWrap(True)
        card_layout.addWidget(subtitle_label)
        return card

    def _description_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("description")
        label.setWordWrap(True)
        return label

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

    def apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QDialog {
                background: qradialgradient(cx:0.2, cy:0.1, radius:1.15,
                    fx:0.22, fy:0.12,
                    stop:0 #17364a,
                    stop:0.25 #0d5666,
                    stop:0.62 #10283e,
                    stop:1 #070c16);
                color: #effcff;
            }
            QLabel {
                color: #effcff;
            }
            QLabel#dialogTitle {
                font-size: 22px;
                font-weight: 700;
                color: #ffffff;
            }
            QLabel#dialogSubtitle {
                color: #abced6;
                font-size: 13px;
            }
            QLabel#cardTitle {
                font-size: 16px;
                font-weight: 700;
                color: #f7ffff;
            }
            QLabel#cardSubtitle {
                color: #91b8c1;
            }
            QLabel#description {
                color: #86aeb7;
                margin-left: 6px;
            }
            QLabel#miniTitle {
                color: #d8edef;
                font-weight: 700;
                margin-top: 6px;
            }
            QFrame#card {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(24, 66, 86, 0.84),
                    stop:1 rgba(8, 19, 35, 0.92));
                border: 1px solid rgba(89, 180, 176, 0.34);
                border-radius: 18px;
            }
            QLineEdit, QSpinBox {
                background: rgba(5, 16, 30, 0.72);
                color: #f2ffff;
                border: 1px solid rgba(90, 181, 176, 0.42);
                border-radius: 12px;
                padding: 9px 12px;
                selection-background-color: rgba(51, 176, 171, 0.35);
            }
            QCheckBox {
                color: #f4ffff;
                font-weight: 700;
                spacing: 8px;
            }
            QPushButton#primaryButton {
                color: #eefcff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d9fa0,
                    stop:0.4 #2f7891,
                    stop:1 #284e7e);
                border: 1px solid #79c8c2;
            }
            QPushButton#primaryButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #48aead,
                    stop:0.4 #38879f,
                    stop:1 #31598b);
            }
            """
        )
