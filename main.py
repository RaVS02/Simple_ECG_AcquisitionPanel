import sys
from PyQt6.QtWidgets import QApplication,QStyleFactory
from ui.main_window import MainWindow
def main():
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
if __name__ == "__main__":
    main()