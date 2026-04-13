from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QComboBox, QHBoxLayout, QPushButton,QCheckBox
from resources import config

class LiveSignalsTab(QFrame):
    def __init__(self):
        super().__init__()
        self.setProperty("cssClass", "panel")
        self.SetUpLiveMonitoring()


    def SetUpLiveMonitoring(self):
        # Tworzymy układ dla tej konkretnej zakładki
        self.connection_state = "Disconected"
        self.baudrate_value = "115200"
        self.recording_state = False
        self.pause_state = False
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Ustawiamy wyrównanie do góry
        self.label = QLabel("Panel LiveMonitoring")
        self.layout.setContentsMargins(10, 0, 10, 0)

        # --- PANEL POŁĄCZENIA (Poziomy układ) ---
        self.conn_layout1row = QHBoxLayout()

        # 1. Wybór typu sygnału
        self.signal_label = QLabel("Sygnał:")
        self.signal_combo = QComboBox()
        # ??? Tutaj musimy dodać opcje do listy rozwijanej ???
        self.signal_combo.addItem("ECG")
        self.signal_combo.addItem("PPG")
        self.signal_combo.addItem("ECG+PPG")

        self.conn_layout1row.addWidget(self.signal_label)
        self.conn_layout1row.addWidget(self.signal_combo)

        # 2. Wybór połączenia (Zrobimy to w następnym kroku)
        self.port_label = QLabel("Port:")
        self.port_combo = QComboBox()
        # ??? Tutaj musimy dodać opcje do listy rozwijanej ???
        self.port_combo.addItem("COM3")
        self.port_combo.addItem("COM4")
        self.port_combo.addItem("Wi-Fi")
        self.port_combo.addItem("Bluetooth")
        self.conn_layout1row.addWidget(self.port_label)
        self.conn_layout1row.addWidget(self.port_combo)
        self.refresh_btn = QPushButton("↺ Odśwież")
        self.conn_layout1row.addWidget(self.refresh_btn)
        self.refresh_btn.clicked.connect(self.refresh_ports)
        # Na koniec dodajemy nasz poziomy pasek do głównego pionowego układu
        self.conn_layout1row.addStretch()
        self.layout.addLayout(self.conn_layout1row)
        self.conn_layout2row = QHBoxLayout()
        self.baudrate_label = QLabel(f"Baudrate:")
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItem("9600")
        self.baudrate_combo.addItem("19200")
        self.baudrate_combo.addItem("38400")
        self.baudrate_combo.addItem("57600")
        self.baudrate_combo.addItem("115200")
        self.baudrate_combo.addItem("230200")
        self.baudrate_combo.addItem("460800")
        self.baudrate_combo.addItem("921600")
        self.connect_btn = QPushButton("Połącz")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.conn_layout2row.addWidget(self.baudrate_label)
        self.conn_layout2row.addWidget(self.baudrate_combo)
        self.conn_layout2row.addWidget(self.connect_btn)
        self.conn_layout2row.addStretch()
        self.layout.addLayout(self.conn_layout2row)
        #--ToolBox---
        self.toolbox_layout=QHBoxLayout()
        self.recording_btn=QPushButton("Nagrywaj")
        self.recording_btn.clicked.connect(self.toggle_recording)
        self.toolbox_layout.addWidget(self.recording_btn)
        self.pause_btn=QPushButton("Pauza")
        self.pause_btn.clicked.connect(self.toggle_pause_recording)
        self.toolbox_layout.addWidget(self.pause_btn)
        self.toolbox_layout.addStretch()
        self.layout.addLayout(self.toolbox_layout)
        self.main_workspace = QHBoxLayout()

        # --- 1. LEWY PANEL (Wybór i mapowanie kanałów) ---
        self.channels_panel = QFrame()
        self.channels_panel.setProperty("cssClass", "panel")
        self.channels_panel.setFixedWidth(200)
        self.channels_layout = QVBoxLayout(self.channels_panel)
        self.channels_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.channels_label = QLabel("MAPOWANIE KANAŁÓW")
        self.channels_layout.addWidget(self.channels_label)

        # (Tutaj w pętli będziemy dodawać Checkboxy i ComboBoxy dla każdego kanału)

        # --- 2. PRAWY PANEL (Wykresy pyqtgraph) ---
        self.graphs_widget = pg.GraphicsLayoutWidget()
        self.graphs_widget.setBackground(config.Colors.DARK_BACKGROUND)

        # Przykład dodawania wykresów jeden pod drugim:
        self.plot1 = self.graphs_widget.addPlot(title="CH 1")
        self.plot1.showGrid(x=True, y=True, alpha=0.3)

        self.graphs_widget.nextRow()  # Przejście do nowej linii!

        self.plot2 = self.graphs_widget.addPlot(title="CH 2")
        self.plot2.showGrid(x=True, y=True, alpha=0.3)
        self.plot2.setXLink(self.plot1)
        # Składamy przestrzeń roboczą
        self.main_workspace.addWidget(self.channels_panel)
        self.main_workspace.addWidget(self.graphs_widget, stretch=1)
        # Wewnątrz SetUpLiveMonitoring:
        #self.ch_ecg1.toggled.connect(self.plot1.setVisible)
        #self.ch_ecg2.toggled.connect(self.plot2.setVisible)
        self.layout.addLayout(self.main_workspace)

    def refresh_ports(self):
        print("Skanowanie dostępnych portów...")
        for port in ["COM3", "COM4", "Wi-Fi", "Bluetooth"]:
            print(f" - {port}")
    def toggle_connection(self):
        if self.connection_state=='Disconected':
            print(f"Próba połaczenia z urzadzeniem na porcie:{self.port_combo.currentText()}")
            self.connection_state='Connected'
            self.connect_btn.setText('Rozłącz')
            self.baudrate_combo.setDisabled(True)
            self.port_combo.setDisabled(True)
            self.signal_combo.setDisabled(True)
            #Zmiana Kolorów
        else:
            print("Rozłaczanie z Urządzeniem...")
            self.connection_state='Disconected'
            self.baudrate_combo.setDisabled(False)
            self.port_combo.setDisabled(False)
            self.signal_combo.setDisabled(False)
            self.connect_btn.setText('Połącz')
            # Zmiana Kolorów
    def toggle_recording(self):
        if self.recording_state==False:
            print("Start Nagrywania")
            self.recording_state=True
            self.recording_btn.setText('Zatrzymaj')
        else:
            print("Stop Nagrywania")
            self.recording_state=False
            self.recording_btn.setText('Nagrywaj')

    def toggle_pause_recording(self):
        if self.pause_state==False:
            self.pause_state=True
            print("Nagrywanie Zastopowane")
            self.pause_btn.setText('Wznów')
        else:
            self.pause_state = False
            print("Nagrywanie Wznowione")
            self.pause_btn.setText('Pauza')
    def ChangeChartVisible(self,chart):
        if chart.isChecked():
            chart.setVisible(True)
        else:
            chart.setVisible(False)





