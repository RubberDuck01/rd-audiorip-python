import sys
from PyQt6.QtWidgets import QApplication
from rd_audiorip.models.config import Config
from rd_audiorip.models.stats import Stats
from rd_audiorip.ui.main_window import MainWindow
from rd_audiorip.ui.theme import GLOBAL_STYLESHEET
from rd_audiorip.controllers.main_controller import MainController

def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Rubber Duck's AudioRip")
    app.setStyleSheet(GLOBAL_STYLESHEET)
    
    config = Config()
    stats = Stats()
    stats.register_session()
    
    window = MainWindow(config, stats)
    controller = MainController(window, stats)
    window.controller = controller
    
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
