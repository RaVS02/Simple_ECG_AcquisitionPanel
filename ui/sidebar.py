# ui/sidebar.py
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QRadioButton, QButtonGroup
from PyQt6.QtCore import Qt
from resources import config


class Sidebar(QFrame):
    def __init__(self,settingsmanager):
        super().__init__()
        self.setFixedWidth(220)  # Stała szerokość zgodna z mockupem
        self.settingsmanager=settingsmanager
        self.setObjectName("Sidebar")  # Kluczowe dla stylizacji QSS
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- SEKCJA: ŹRÓDŁO SYGNAŁU ---
        self.add_section_title(layout, "ŹRÓDŁO SYGNAŁU")

        self.src_group = QButtonGroup(self)

        self.radio_live = QRadioButton("Na żywo")
        self.radio_live.setChecked(True)  # Domyślnie wybrane
        self.src_group.addButton(self.radio_live)
        layout.addWidget(self.radio_live)

        self.radio_file = QRadioButton("Wczytaj plik")
        self.src_group.addButton(self.radio_file)
        layout.addWidget(self.radio_file)

        self.add_separator(layout)

        # --- SEKCJA: PARAMETRY DSP (Placeholder na przyszłość) ---
        self.add_section_title(layout, "PARAMETRY DSP")
        # Tu później dodamy statyczne etykiety z wartościami

        self.add_separator(layout)

        # --- SEKCJA: ODPROWADZENIA ---
        self.add_section_title(layout, "ODPROWADZENIA")
        self.radio_i = QRadioButton("I (RA–LA)")
        self.radio_ii = QRadioButton("II (RA–LL)")
        self.radio_v1 = QRadioButton("V1")
        layout.addWidget(self.radio_i)
        layout.addWidget(self.radio_ii)
        layout.addWidget(self.radio_v1)

    def add_section_title(self, layout, text):
        lbl = QLabel(text)
        # Specyficzny styl dla nagłówków sekcji w sidebarze
        lbl.setStyleSheet(f"""
            color: {config.Colors.DARK_TEXT_SECONDARY}; 
            font-size: 9pt; 
            font-weight: bold; 
            letter-spacing: 1px;
            text-transform: uppercase;
            padding: 0px;
            margin-bottom: 5px;
        """)
        layout.addWidget(lbl)

    def add_separator(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        # Nadajemy ID, żeby ostylować to w theme.py
        line.setObjectName("SidebarSeparator")
        layout.addWidget(line)