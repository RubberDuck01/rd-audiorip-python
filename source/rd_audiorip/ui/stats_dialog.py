from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)
from PyQt6.QtCore import Qt
from rd_audiorip.models.stats import Stats


class StatsDialog(QDialog):
    def __init__(self, parent, stats: Stats) -> None:
        super().__init__(parent)
        self.stats = stats
        self.setWindowTitle("My Statistics")
        self.setGeometry(100, 100, 500, 350)
        self.setModal(True)

        layout = QVBoxLayout(self)

        #? Title
        title = QLabel("Download Statistics")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        layout.addSpacing(15)

        #? Stats rows
        stats_data = [
            ("Total Sessions", str(self.stats.data.get("total_sessions", 0))),
            ("Files Downloaded", str(self.stats.data.get("total_files_downloaded", 0))),
            ("Total Size", self.stats.data.get("total_downloads_size_pretty", "0 B")),
            ("Total Duration", self.stats.data.get("total_downloads_duration_pretty", "00:00")),
            ("Created", self.format_date(self.stats.data.get("created_date", "N/A"))),
            ("Last Run", self.format_date(self.stats.data.get("last_run_date", "N/A"))),
        ]

        for label_text, value_text in stats_data:
            row = QHBoxLayout()
            label = QLabel(f"{label_text}:")
            label.setStyleSheet("font-weight: bold; min-width: 140px;")
            value = QLabel(value_text)
            value.setStyleSheet("color: #0066cc;")
            row.addWidget(label)
            row.addWidget(value, stretch=1)
            row.addStretch()
            layout.addLayout(row)

        layout.addSpacing(20)
        layout.addStretch()

        #? Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    @staticmethod
    def format_date(iso_string: str) -> str:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(iso_string)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return iso_string