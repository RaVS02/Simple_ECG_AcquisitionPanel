from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame


class AnalysisTab(QFrame):
    def __init__(self):
        super().__init__()
        self.setProperty("cssClass", "panel")
        self.SetUpAnalysis()

    def SetUpAnalysis(self):
        # Tworzymy układ dla tej konkretnej zakładki
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Ustawiamy wyrównanie do góry
        self.label = QLabel("Panel Analysis w budowie... 🔍")
        self.layout.addWidget(self.label)