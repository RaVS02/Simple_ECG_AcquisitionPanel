from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame


class FilesViewerTab(QFrame):
    def __init__(self):
        super().__init__()
        # Tworzymy układ dla tej konkretnej zakładki
        self.setProperty("cssClass", "panel")
        self.SetUpFilesViewer()
    def SetUpFilesViewer(self):
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Ustawiamy wyrównanie do góry
        self.label = QLabel("Panel Files Viewer w budowie... 📂")
        self.layout.addWidget(self.label)