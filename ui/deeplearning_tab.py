from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame


class DeepLearningTab(QFrame):
    def __init__(self,settingsmanager):
        super().__init__()
        # Tworzymy układ dla tej konkretnej zakładki
        self.settingsmanager = settingsmanager
        self.setProperty("cssClass", "panel")
        self.SetUpDeepLearning()
    def SetUpDeepLearning(self):
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Ustawiamy wyrównanie do góry
        self.label = QLabel("Panel DeepLearning w budowie... 📈")
        self.layout.addWidget(self.label)
