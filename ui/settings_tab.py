from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame


class SettingsTab(QFrame):
    def __init__(self):
        super().__init__()
        self.setProperty("cssClass", "panel")
        self.SetUpLiveMonitoring()

    def SetUpLiveMonitoring(self):
        # Tworzymy układ dla tej konkretnej zakładki
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Ustawiamy wyrównanie do góry
        self.label = QLabel("Panel Settings w budowie... ⚙️")
        self.layout.setContentsMargins(10, 0, 10, 0)
        self.layout.addWidget(self.label)