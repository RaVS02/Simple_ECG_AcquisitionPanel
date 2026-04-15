from PyQt6.QtCore import Qt
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QComboBox, QHBoxLayout, QPushButton, QCheckBox, \
    QListView
from resources import config


class LiveSignalsTab(QFrame):
    def __init__(self, settingsmanager):
        super().__init__()
        self.setProperty("cssClass", "panel")
        self.settingsmanager = settingsmanager
        self.SetUpLiveMonitoring()

    def SetUpLiveMonitoring(self):
        # Inicjalizacja zmiennych stanu
        self.connection_state = "Disconected"
        self.baudrate_value = "115200"
        self.recording_state = False
        self.pause_state = False

        # Główny układ zakładki
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 1. ZEROWANIE MARGINESÓW - dzięki temu bloki rozciągają się od krawędzi do krawędzi
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # --- PANEL POŁĄCZENIA (Kontener .conn-panel) ---
        self.conn_container = QFrame()
        self.conn_container.setProperty("cssClass", "conn-panel")
        self.conn_main_layout = QVBoxLayout(self.conn_container)
        self.conn_main_layout.setContentsMargins(16, 12, 16, 12)  # Wewnętrzny padding (jak w CSS)
        self.conn_main_layout.setSpacing(8)

        # Rząd 1: Sygnał i Port
        self.conn_layout1row = QHBoxLayout()
        self.signal_label = QLabel("Sygnał:")
        self.signal_combo = QComboBox()
        self.signal_combo.addItem("ECG")
        self.signal_combo.addItem("PPG")
        self.signal_combo.addItem("ECG+PPG")
        self.signal_combo.setFixedWidth(150)
        self.conn_layout1row.addWidget(self.signal_label)
        self.conn_layout1row.addWidget(self.signal_combo)

        self.port_label = QLabel("Port:")
        self.port_combo = QComboBox()

        self.port_combo.addItem("COM3")
        self.port_combo.addItem("COM4")
        self.port_combo.addItem("Wi-Fi")
        self.port_combo.addItem("Bluetooth")
        self.port_combo.setFixedWidth(200)
        self.conn_layout1row.addWidget(self.port_label)
        self.conn_layout1row.addWidget(self.port_combo)

        self.refresh_btn = QPushButton("↺ Odśwież")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.conn_layout1row.addWidget(self.refresh_btn)
        self.conn_layout1row.addStretch()
        self.status_label = QLabel("Rozłączony")

        # Ręczne nałożenie stylu CSS dla odznaki błędu/rozłączenia:
        self.status_label.setProperty("cssClass", "badge-err")
        self.conn_layout1row.addStretch()
        self.conn_layout1row.addWidget(self.status_label)

        # Dodajemy rząd 1 do KONTENERA, nie do głównego layoutu
        self.conn_main_layout.addLayout(self.conn_layout1row)

        # Rząd 2: Baudrate i Przycisk Połącz
        self.conn_layout2row = QHBoxLayout()
        self.baudrate_label = QLabel("Baudrate:")
        self.baudrate_combo = QComboBox()
        for baud in ["9600", "19200", "38400", "57600", "115200", "230200", "460800", "921600"]:
            self.baudrate_combo.addItem(baud)
        self.baudrate_combo.setFixedWidth(120)
        self.connect_btn = QPushButton("Połącz")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.conn_layout2row.addWidget(self.baudrate_label)
        self.conn_layout2row.addWidget(self.baudrate_combo)
        self.conn_layout2row.addWidget(self.connect_btn)
        self.conn_layout2row.addStretch()

        # Dodajemy rząd 2 do KONTENERA
        self.conn_main_layout.addLayout(self.conn_layout2row)

        # Na koniec umieszczamy cały gotowy panel połączeń w głównym layoucie
        self.layout.addWidget(self.conn_container)

        # --- TOOLBAR (Pasek narzędziowy .toolbar) ---
        self.toolbar_container = QFrame()
        self.toolbar_container.setProperty("cssClass", "toolbar")
        self.toolbox_layout = QHBoxLayout(self.toolbar_container)
        self.toolbox_layout.setContentsMargins(12, 6, 12, 6)  # Marginesy z pliku HTML

        self.recording_btn = QPushButton("NAGRYWAJ")
        self.recording_btn.setProperty("cssClass", "danger")
        self.recording_btn.clicked.connect(self.toggle_recording)
        self.toolbox_layout.addWidget(self.recording_btn)

        self.pause_btn = QPushButton("Pauza")
        self.pause_btn.clicked.connect(self.toggle_pause_recording)
        self.toolbox_layout.addWidget(self.pause_btn)
        # -- PIONOWY SEPARATOR 1 --
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setStyleSheet(f"border-left: 1px solid {config.Colors.DARK_BORDER}; margin: 2px 8px;")
        self.toolbox_layout.addWidget(sep1)

        # 2. SEKCJA: PODGLĄD WIZUALNY (Freeze)
        self.charts_frozen = False  # Zmienna stanu dla zamrażania
        self.freeze_btn = QPushButton("❄ Zamroź")
        self.freeze_btn.clicked.connect(self.toggle_freeze_charts)
        self.toolbox_layout.addWidget(self.freeze_btn)
        # -- PIONOWY SEPARATOR 2 --
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet(f"border-left: 1px solid {config.Colors.DARK_BORDER}; margin: 2px 8px;")
        self.toolbox_layout.addWidget(sep2)

        # 3. SEKCJA: EKSPORT (Ze stylami ze screena!)
        self.export_edf_btn = QPushButton("↓ EDF")

        self.toolbox_layout.addWidget(self.export_edf_btn)

        self.export_csv_btn = QPushButton("↓ CSV")
        self.toolbox_layout.addWidget(self.export_csv_btn)

        self.export_wfdb_btn = QPushButton("↓ WFDB")
        self.toolbox_layout.addWidget(self.export_wfdb_btn)
        # 4. SEKCJA: TIMER NAGRYWANIA
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setStyleSheet(f"""
                    color: {config.Colors.DARK_TEXT_SECONDARY}; 
                    font-size: 11pt; 
                    margin-left: 12px;
                    letter-spacing: 1px;
                """)
        self.toolbox_layout.addWidget(self.timer_label)

        self.toolbox_layout.addStretch()
        self.layout.addWidget(self.toolbar_container)

        # --- GŁÓWNA PRZESTRZEŃ ROBOCZA (Kanały i Wykresy) ---
        # Tworzymy dodatkowy kontener (QWidget), by dodać padding dookoła wykresów
        self.main_workspace_container = QWidget()
        self.main_workspace = QHBoxLayout(self.main_workspace_container)
        self.main_workspace.setContentsMargins(0, 0, 10, 0)

        # 1. LEWY PANEL (Wybór i mapowanie kanałów)
        self.channels_panel = QFrame()
        self.channels_panel.setFixedWidth(120)
        self.channels_panel.setProperty(
            "cssClass",'kanaly' )
        self.channels_layout = QVBoxLayout(self.channels_panel)
        self.channels_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.channels_label = QLabel("KANAŁY")
        self.channels_layout.addWidget(self.channels_label)
        # 2. PRAWY PANEL (Wykresy pyqtgraph)
        self.graphs_widget = pg.GraphicsLayoutWidget()
        self.graphs_widget.setBackground(config.Colors.DARK_BACKGROUND)

        self.plot1 = self.graphs_widget.addPlot(title="ECG-CH 1")
        self.plot1.showGrid(x=True, y=True, alpha=0.3)

        self.graphs_widget.nextRow()

        self.plot2 = self.graphs_widget.addPlot(title="ECG-CH 2")
        self.plot2.showGrid(x=True, y=True, alpha=0.3)
        self.plot2.setXLink(self.plot1)

        # Składamy przestrzeń roboczą
        self.main_workspace.addWidget(self.channels_panel)
        self.main_workspace.addWidget(self.graphs_widget, stretch=1)

        # Dodajemy przestrzeń roboczą do głównego układu i pozwalamy jej zająć resztę okna (stretch=1)
        self.layout.addWidget(self.main_workspace_container, stretch=1)

    # --- METODY LOGIKI ZAKŁADKI ---

    def refresh_ports(self):
        print("Skanowanie dostępnych portów...")
        for port in ["COM3", "COM4", "Wi-Fi", "Bluetooth"]:
            print(f" - {port}")

    def toggle_connection(self):
        if self.connection_state == 'Disconected':
            print(f"Próba połaczenia z urzadzeniem na porcie: {self.port_combo.currentText()}")
            self.connection_state = 'Connected'
            self.connect_btn.setText('Rozłącz')

            # Wymuszenie odświeżenia stylu CSS dla przycisku (zmiana na klasę primary - zieloną)
            self.connect_btn.setProperty("cssClass", "primary")
            self.connect_btn.style().polish(self.connect_btn)
            self.status_label.setText("Połączony")
            # Zamiast setStyleSheet:
            self.status_label.setProperty("cssClass", "badge-ok")
            self.status_label.style().polish(self.status_label)
            self.baudrate_combo.setDisabled(True)
            self.port_combo.setDisabled(True)
            self.signal_combo.setDisabled(True)

        else:
            print("Rozłaczanie z Urządzeniem...")
            self.connection_state = 'Disconected'
            self.baudrate_combo.setDisabled(False)
            self.port_combo.setDisabled(False)
            self.signal_combo.setDisabled(False)
            self.connect_btn.setText('Połącz')

            # Reset stylu przycisku do domyślnego
            self.connect_btn.setProperty("cssClass", "")
            self.connect_btn.style().polish(self.connect_btn)
            self.status_label.setText("Rozłączony")
            self.status_label.setProperty("cssClass", "badge-err")
            self.status_label.style().polish(self.status_label)
    def toggle_recording(self):
        if self.recording_state == False:
            print("Start Nagrywania")
            self.recording_state = True
            self.recording_btn.setText('ZATRZYMAJ')

            # Wymuszenie ciemnoczerwonego, aktywnego stylu nagrywania
            self.recording_btn.setProperty("cssClass", "danger-active")
            self.recording_btn.style().polish(self.recording_btn)
        else:
            print("Stop Nagrywania")
            self.recording_state = False
            self.recording_btn.setText('NAGRYWAJ')

            # Powrót do standardowego, czerwonego przycisku
            self.recording_btn.setProperty("cssClass", "danger")
            self.recording_btn.style().polish(self.recording_btn)

    def toggle_pause_recording(self):
        if self.pause_state == False:
            self.pause_state = True
            print("Nagrywanie Zastopowane")
            self.pause_btn.setText('Wznów')
        else:
            self.pause_state = False
            print("Nagrywanie Wznowione")
            self.pause_btn.setText('Pauza')

    def ChangeChartVisible(self, chart):
        if chart.isChecked():
            chart.setVisible(True)
        else:
            chart.setVisible(False)

    def toggle_freeze_charts(self):
        if self.charts_frozen == False:
            self.charts_frozen = True
            print("Wykresy zamrożone (dane dalej mogą się zbierać w tle).")
            self.freeze_btn.setText("▶ Odmroź")
            # Podświetlamy na zielono, żeby użytkownik wiedział, że ekran "stoi"
            self.freeze_btn.setProperty("cssClass", "primary")
            self.freeze_btn.style().polish(self.freeze_btn)

            # W przyszłości tu dodamy pauzowanie timera odświerzającego wykresy w pyqtgraph
        else:
            self.charts_frozen = False
            print("Wykresy odmrożone (powrót do rysowania na żywo).")
            self.freeze_btn.setText("❄ Zamroź")
            # Wracamy do szarego przycisku
            self.freeze_btn.setProperty("cssClass", "")
            self.freeze_btn.style().polish(self.freeze_btn)