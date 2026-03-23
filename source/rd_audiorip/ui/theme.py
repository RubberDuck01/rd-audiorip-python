GLOBAL_STYLESHEET = """
QPushButton {
    border-radius: 12px;
    padding: 9px 14px;
    min-height: 24px;
    font-weight: 700;
}
QPushButton:hover {
    border: 1px solid rgba(118, 223, 214, 0.72);
}
QPushButton:pressed {
    padding-top: 10px;
}
QPushButton:disabled {
    color: #7c98a7;
    background: rgba(25, 49, 66, 0.72);
    border: 1px solid rgba(80, 111, 128, 0.36);
}
QMessageBox {
    background: qradialgradient(cx:0.2, cy:0.1, radius:1.15,
        fx:0.22, fy:0.12,
        stop:0 #153749,
        stop:0.24 #0d556c,
        stop:0.62 #10273d,
        stop:1 #060b14);
}
QMessageBox QLabel {
    color: #eefcff;
}
QDialogButtonBox QPushButton,
QMessageBox QPushButton,
QPushButton#dialogButton,
QPushButton#glassButton {
    color: #ecfeff;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(71, 169, 188, 0.3),
        stop:1 rgba(17, 59, 83, 0.74));
    border: 1px solid rgba(90, 190, 206, 0.46);
}
QPushButton#primaryButton {
    color: #ebfdff;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #369ea7,
        stop:1 #2b679c);
    border: 1px solid #72d2cc;
}
QLineEdit {
    min-height: 24px;
}
QMenuBar {
    background: rgba(6, 19, 34, 0.9);
    color: #e8fcff;
    border-bottom: 1px solid rgba(88, 194, 183, 0.28);
    padding: 4px 6px;
}
QMenuBar::item {
    padding: 6px 10px;
    border-radius: 8px;
}
QMenuBar::item:selected {
    background: rgba(63, 175, 167, 0.22);
}
QMenu {
    background: rgba(8, 21, 36, 0.96);
    color: #eefcff;
    border: 1px solid rgba(86, 188, 193, 0.34);
    border-radius: 12px;
    padding: 8px;
}
QMenu::item {
    padding: 8px 18px;
    border-radius: 8px;
}
QMenu::item:selected {
    background: rgba(67, 184, 168, 0.22);
}
"""
