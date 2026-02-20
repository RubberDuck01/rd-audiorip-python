import sys
from PyQt6.QtWidgets import QApplication
from rd_audiorip.models.config import Config
from rd_audiorip.ui.main_window import MainWindow
from rd_audiorip.controllers.main_controller import MainController

def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Rubber Duck's AudioRip")
    
    config = Config()
    window = MainWindow(config)
    controller = MainController(window)
    window.controller = controller
    
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())