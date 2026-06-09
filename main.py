import sys
import pyqtgraph as pg
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication,QStyleFactory,QMainWindow
from ui.main_window import MainWindow
pg.setConfigOptions(useOpenGL=True, antialias=False)
def main():
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
if __name__ == "__main__":
    main()