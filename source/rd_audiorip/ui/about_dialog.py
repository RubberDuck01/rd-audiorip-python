import webbrowser
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from rd_audiorip.version import __version__

_RESOURCES = Path(__file__).parent.parent.parent / "resources"

_UNLICENSE = (
    "This is free and unencumbered software released into the public domain.\n\n"
    "Anyone is free to copy, modify, publish, use, compile, sell, or distribute "
    "this software, either in source code form or as compiled binaries, for any "
    "purpose, commercial or non-commercial, and by any means.\n\n"
    "In jurisdictions that recognize copyright laws, the author or authors of this "
    "software dedicate any and all copyright interest in the software to the public "
    "domain. We make this dedication for the benefit of the public at large and to "
    "the detriment of our heirs and successors. We intend this dedication to be an "
    "overt act of relinquishment in perpetuity of all present and future rights to "
    "this software under copyright law.\n\n"
    "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR "
    "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, "
    "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE "
    "AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN "
    "ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION "
    "WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.\n\n"
    "For more information, please refer to <https://unlicense.org>"
)


class AboutDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("RD AudioRip - About")
        self.setModal(True)
        self.resize(480, 340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Icon + app name row
        header_row = QHBoxLayout()
        header_row.setSpacing(16)
        header_row.setAlignment(Qt.AlignmentFlag.AlignTop)

        icon_label = QLabel()
        icon_path = _RESOURCES / "rd_audiorip_logo.png"
        if icon_path.exists():
            pix = QPixmap(str(icon_path)).scaled(
                64, 64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            icon_label.setPixmap(pix)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        header_row.addWidget(icon_label)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        name_label = QLabel("RD AudioRip")
        name_font = name_label.font()
        name_font.setPointSize(name_font.pointSize() + 5)
        name_font.setBold(True)
        name_label.setFont(name_font)
        info_layout.addWidget(name_label)

        desc_label = QLabel("Powerful audio downloader & converter.\nBuilt with Python and Qt6.")
        info_layout.addWidget(desc_label)

        version_label = QLabel(f"Version: {__version__}")
        version_font = version_label.font()
        version_font.setItalic(True)
        version_label.setFont(version_font)
        version_label.setEnabled(False)
        info_layout.addWidget(version_label)

        header_row.addLayout(info_layout)
        header_row.addStretch()
        layout.addLayout(header_row)

        # License text
        license_edit = QTextEdit()
        license_edit.setReadOnly(True)
        license_edit.setPlainText(_UNLICENSE)
        layout.addWidget(license_edit)

        # Buttons
        btn_row = QHBoxLayout()
        github_btn = QPushButton("Source Code (GitHub)")
        github_btn.clicked.connect(
            lambda: webbrowser.open("https://github.com/RubberDuck01/rd-audiorip-python")
        )
        btn_row.addWidget(github_btn)
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)
