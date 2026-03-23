from PyQt6.QtWidgets import QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from rd_audiorip.models.stats import Stats


class StatsDialog(QDialog):
    def __init__(self, parent, stats: Stats) -> None:
        super().__init__(parent)
        self.stats = stats
        self.setWindowTitle("My Statistics")
        self.resize(640, 460)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title = QLabel("Usage Statistics")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        subtitle = QLabel("A running snapshot of how often you use the app and how much audio you have pulled through it.")
        subtitle.setObjectName("dialogSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        cards_grid = QGridLayout()
        cards_grid.setHorizontalSpacing(12)
        cards_grid.setVerticalSpacing(12)

        cards = [
            ("Sessions", str(self.stats.data.get("total_sessions", 0)), "App launches recorded"),
            ("Tracks", str(self.stats.data.get("total_files_downloaded", 0)), "Successful downloads"),
            ("Total Size", self.stats.data.get("total_downloads_size_pretty", "0 B"), "Cumulative library size"),
            ("Listening Time", self.stats.data.get("total_downloads_duration_pretty", "00:00"), "Combined duration"),
        ]

        for index, (name, value, note) in enumerate(cards):
            cards_grid.addWidget(self._stat_card(name, value, note), index // 2, index % 2)

        layout.addLayout(cards_grid)

        timeline_card = QFrame()
        timeline_card.setObjectName("card")
        timeline_layout = QVBoxLayout(timeline_card)
        timeline_layout.setContentsMargins(18, 16, 18, 16)
        timeline_layout.setSpacing(10)

        timeline_title = QLabel("Timeline")
        timeline_title.setObjectName("cardTitle")
        timeline_layout.addWidget(timeline_title)

        timeline_layout.addLayout(self._detail_row("Created", self.format_date(self.stats.data.get("created_date", "N/A"))))
        timeline_layout.addLayout(self._detail_row("Last Run", self.format_date(self.stats.data.get("last_run_date", "N/A"))))

        note = QLabel("Statistics are cumulative across sessions and update after each completed download.")
        note.setObjectName("cardSubtitle")
        note.setWordWrap(True)
        timeline_layout.addWidget(note)
        layout.addWidget(timeline_card)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setObjectName("glassButton")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        self.apply_styles()

    def _stat_card(self, title: str, value: str, note: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        card_layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        card_layout.addWidget(value_label)

        note_label = QLabel(note)
        note_label.setObjectName("cardSubtitle")
        note_label.setWordWrap(True)
        card_layout.addWidget(note_label)
        return card

    def _detail_row(self, label_text: str, value_text: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        label = QLabel(label_text)
        label.setObjectName("miniTitle")
        value = QLabel(value_text)
        value.setObjectName("detailValue")

        row.addWidget(label)
        row.addWidget(value, stretch=1)
        return row

    @staticmethod
    def format_date(iso_string: str) -> str:
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(iso_string)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return iso_string

    def apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QDialog {
                background: qradialgradient(cx:0.2, cy:0.1, radius:1.15,
                    fx:0.22, fy:0.12,
                    stop:0 #16364f,
                    stop:0.25 #0a5b7d,
                    stop:0.62 #102b48,
                    stop:1 #060b14);
                color: #f0feff;
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
                color: #b4e8f6;
                font-size: 13px;
            }
            QLabel#cardTitle, QLabel#statTitle, QLabel#miniTitle {
                color: #d6fbff;
                font-weight: 700;
            }
            QLabel#statValue {
                color: #ffffff;
                font-size: 28px;
                font-weight: 700;
            }
            QLabel#detailValue {
                color: #fff2a9;
                font-weight: 700;
            }
            QLabel#cardSubtitle {
                color: #94cfe0;
            }
            QFrame#card {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(25, 73, 105, 0.84),
                    stop:1 rgba(8, 19, 35, 0.94));
                border: 1px solid rgba(103, 222, 255, 0.34);
                border-radius: 18px;
            }
            QPushButton {
                border-radius: 12px;
                padding: 9px 14px;
                font-weight: 700;
            }
            QPushButton#glassButton {
                color: #ebffff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(92, 214, 255, 0.28),
                    stop:1 rgba(16, 63, 95, 0.72));
                border: 1px solid rgba(108, 226, 255, 0.45);
            }
            QPushButton#glassButton:hover {
                border: 1px solid rgba(144, 255, 236, 0.7);
            }
            """
        )
