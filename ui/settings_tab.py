from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from resources import config

class SettingsTab(QFrame):
    def __init__(self,settingsmanager):
        super().__init__()
        self.setProperty("cssClass", "panel")
        self.settingsmanager = settingsmanager
        self.SetUpLiveMonitoring()

    def SetUpLiveMonitoring(self):
        # Tworzymy układ dla tej konkretnej zakładki
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Ustawiamy wyrównanie do góry
        self.label = QLabel("Panel Settings w budowie... ⚙️")
        self.layout.setContentsMargins(10, 0, 10, 0)
        self.layout.addWidget(self.label)
        # Przykład użycia w settings_tab.py lub analysis_tab.py:
        self.section_akwizycja = QFrame()
        self.section_akwizycja.setProperty("cssClass", "card")  # BAM! Mamy wygląd z HTML!

        # Teraz tworzymy układ TYLKO dla tej karty i dajemy marginesy wewnętrzne:
        self.section_layout = QVBoxLayout(self.section_akwizycja)
        self.section_layout.setContentsMargins(14, 12, 14, 12)

        # Dodajemy tytuł sekcji:
        self.title = QLabel("AKWIZYCJA")
        self.title.setStyleSheet(f"color: {config.Colors.DARK_TEXT_SECONDARY}; font-size: 10px; font-weight: bold;")
        self.section_layout.addWidget(self.title)

        # ... tutaj dodajesz przyciski i comboboxy do section_layout ...

        # Na koniec wrzucasz gotową KARTĘ do głównego układu zakładki:
        self.layout.addWidget(self.section_akwizycja)