from PyQt6.QtCore import Qt
import pyqtgraph as pg
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QComboBox,
                             QHBoxLayout, QPushButton)
from resources import config


class LiveSignalsTab(QFrame):
    def __init__(self, settingsmanager):
        super().__init__()
        self.setProperty("cssClass", "panel")
        self.settingsmanager = settingsmanager
        self.loading = True

        self.SetUpLiveMonitoring()
        self.settingsmanager.settings_changed.connect(self.sync_ui_with_settings)

        self.loading = False
        self.sync_ui_with_settings()
        self.setup_dynamic_charts()

    def SetUpLiveMonitoring(self):
        self.connection_state = "Disconected"
        self.recording_state = False
        self.pause_state = False
        self.charts_frozen = False

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # --- PANEL POŁĄCZENIA ---
        self.conn_container = QFrame()
        self.conn_container.setProperty("cssClass", "conn-panel")
        self.conn_main_layout = QVBoxLayout(self.conn_container)
        self.conn_main_layout.setContentsMargins(16, 12, 16, 12)
        self.conn_main_layout.setSpacing(8)

        self.conn_layout1row = QHBoxLayout()
        self.signal_label = QLabel("Sygnał:")
        self.signal_combo = QComboBox()
        self.signal_combo.addItems(["ECG", "PPG", "ECG+PPG"])
        self.signal_combo.setFixedWidth(150)
        self.signal_combo.currentTextChanged.connect(self.sync_settings_with_ui)
        self.conn_layout1row.addWidget(self.signal_label)
        self.conn_layout1row.addWidget(self.signal_combo)

        self.port_label = QLabel("Port:")
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(320)

        self.refresh_btn = QPushButton("Odsweiz")
        self.refresh_btn.clicked.connect(self.refresh_ports)

        self.conn_layout1row.addWidget(self.port_label)
        self.conn_layout1row.addWidget(self.port_combo)
        self.conn_layout1row.addWidget(self.refresh_btn)
        self.conn_layout1row.addStretch()

        self.status_label = QLabel("Rozlaczony")
        self.status_label.setProperty("cssClass", "badge-err")
        self.conn_layout1row.addWidget(self.status_label)
        self.conn_main_layout.addLayout(self.conn_layout1row)

        self.conn_layout2row = QHBoxLayout()
        self.baudrate_label = QLabel("Baudrate:")
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
        self.baudrate_combo.setFixedWidth(120)
        self.baudrate_combo.setCurrentText("115200")

        self.connect_btn = QPushButton("Polacz")
        self.connect_btn.clicked.connect(self.toggle_connection)

        self.conn_layout2row.addWidget(self.baudrate_label)
        self.conn_layout2row.addWidget(self.baudrate_combo)
        self.conn_layout2row.addWidget(self.connect_btn)
        self.conn_layout2row.addStretch()
        self.conn_main_layout.addLayout(self.conn_layout2row)
        self.layout.addWidget(self.conn_container)

        # --- TOOLBAR ---
        self.toolbar_container = QFrame()
        self.toolbar_container.setProperty("cssClass", "toolbar")
        self.toolbox_layout = QHBoxLayout(self.toolbar_container)
        self.toolbox_layout.setContentsMargins(12, 6, 12, 6)

        # Standardowe nagrywanie
        self.recording_btn = QPushButton("NAGRYWAJ")
        self.recording_btn.setProperty("cssClass", "danger")
        self.recording_btn.clicked.connect(self.toggle_recording)
        self.toolbox_layout.addWidget(self.recording_btn)

        self.pause_btn = QPushButton("Pauza")
        self.pause_btn.clicked.connect(self.toggle_pause_recording)
        self.toolbox_layout.addWidget(self.pause_btn)

        self.add_vertical_separator(self.toolbox_layout)

        # Nowy przycisk do zrzutu bufora z pamięci (Incydent)
        self.retro_save_btn = QPushButton("Zapisz incydent (Zrzut bufora)")
        self.retro_save_btn.setProperty("cssClass", "primary")
        self.toolbox_layout.addWidget(self.retro_save_btn)

        self.add_vertical_separator(self.toolbox_layout)

        self.freeze_btn = QPushButton("Zamroz")
        self.freeze_btn.clicked.connect(self.toggle_freeze_charts)
        self.toolbox_layout.addWidget(self.freeze_btn)

        self.add_vertical_separator(self.toolbox_layout)

        self.export_edf_btn = QPushButton("EDF")
        self.export_csv_btn = QPushButton("CSV")
        self.export_wfdb_btn = QPushButton("WFDB")
        self.toolbox_layout.addWidget(self.export_edf_btn)
        self.toolbox_layout.addWidget(self.export_csv_btn)
        self.toolbox_layout.addWidget(self.export_wfdb_btn)

        self.timer_label = QLabel("00:00:00")
        self.timer_label.setStyleSheet(
            f"color: {config.Colors.DARK_TEXT_SECONDARY}; font-size: 11pt; margin-left: 12px; letter-spacing: 1px;")
        self.toolbox_layout.addWidget(self.timer_label)
        self.toolbox_layout.addStretch()
        self.layout.addWidget(self.toolbar_container)

        # --- GLOWNA PRZESTRZEN ROBOCZA ---
        # Wykresy zajmują teraz całą szerokość, brak panelu bocznego
        self.main_workspace_container = QWidget()
        self.main_workspace = QHBoxLayout(self.main_workspace_container)
        self.main_workspace.setContentsMargins(0, 0, 0, 0)

        self.graphs_widget = pg.GraphicsLayoutWidget()
        self.graphs_widget.setBackground(config.Colors.DARK_BACKGROUND)
        self.main_workspace.addWidget(self.graphs_widget, stretch=1)

        self.layout.addWidget(self.main_workspace_container, stretch=1)

        self.refresh_ports()
        self.port_combo.currentTextChanged.connect(self.check_baudrate_visibility)
        self.check_baudrate_visibility(self.port_combo.currentText())

    def add_vertical_separator(self, layout):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"border-left: 1px solid {config.Colors.DARK_BORDER}; margin: 2px 8px;")
        layout.addWidget(sep)

    # --- LOGIKA SYNCHRONIZACJI ---

    def sync_ui_with_settings(self):
        self.loading = True

        ecg_active = self.settingsmanager.get_setting("channels_ecg", "active")
        ppg_active = self.settingsmanager.get_setting("channels_ppg", "raw_active")

        target_text = ""
        if ecg_active and ppg_active:
            target_text = "ECG+PPG"
        elif ecg_active:
            target_text = "ECG"
        elif ppg_active:
            target_text = "PPG"

        if target_text and self.signal_combo.currentText() != target_text:
            self.signal_combo.setCurrentText(target_text)

        self.setup_dynamic_charts()
        self.loading = False

    def sync_settings_with_ui(self, selected_text):
        if self.loading: return
        if selected_text == "ECG":
            self.settingsmanager.update_setting("channels_ecg", "active", True)
            self.settingsmanager.update_setting("channels_ppg", "raw_active", False)
        elif selected_text == "PPG":
            self.settingsmanager.update_setting("channels_ecg", "active", False)
            self.settingsmanager.update_setting("channels_ppg", "raw_active", True)
        elif selected_text == "ECG+PPG":
            self.settingsmanager.update_setting("channels_ecg", "active", True)
            self.settingsmanager.update_setting("channels_ppg", "raw_active", True)

    # --- LOGIKA KONTROLEK ---

    def refresh_ports(self):
        import serial.tools.list_ports
        current_selection = self.port_combo.currentText()
        self.port_combo.clear()

        ip = self.settingsmanager.get_setting("connection", "esp_ip")
        port = self.settingsmanager.get_setting("connection", "port")
        ble_name = self.settingsmanager.get_setting("connection", "ble_name")

        self.port_combo.addItem(f"WiFi UDP - {ip}:{port}")
        self.port_combo.addItem(f"WiFi TCP - {ip}:{port}")
        self.port_combo.addItem(f"BLE - {ble_name}")
        self.port_combo.addItem("Symulator (demo)")

        ports = serial.tools.list_ports.comports()
        for p in ports:
            self.port_combo.addItem(p.device)

        index = self.port_combo.findText(current_selection)
        if index >= 0:
            self.port_combo.setCurrentIndex(index)
        elif self.port_combo.count() > 0:
            self.port_combo.setCurrentIndex(0)

    def check_baudrate_visibility(self, text):
        if "WiFi" in text or "BLE" in text or "Symulator" in text:
            self.baudrate_combo.setEnabled(False)
        else:
            self.baudrate_combo.setEnabled(True)

    def toggle_connection(self):
        if self.connection_state == 'Disconected':
            self.connection_state = 'Connected'
            self.connect_btn.setText('Rozlacz')
            self.connect_btn.setProperty("cssClass", "primary")
            self.connect_btn.style().polish(self.connect_btn)

            self.status_label.setText("Polaczony")
            self.status_label.setProperty("cssClass", "badge-ok")
            self.status_label.style().polish(self.status_label)

            self.baudrate_combo.setDisabled(True)
            self.port_combo.setDisabled(True)
            self.signal_combo.setDisabled(True)
        else:
            self.connection_state = 'Disconected'
            self.baudrate_combo.setDisabled(False)
            self.port_combo.setDisabled(False)
            self.signal_combo.setDisabled(False)
            self.connect_btn.setText('Polacz')
            self.connect_btn.setProperty("cssClass", "")
            self.connect_btn.style().polish(self.connect_btn)

            self.status_label.setText("Rozlaczony")
            self.status_label.setProperty("cssClass", "badge-err")
            self.status_label.style().polish(self.status_label)
            self.check_baudrate_visibility(self.port_combo.currentText())

    def toggle_recording(self):
        if not self.recording_state:
            self.recording_state = True
            self.recording_btn.setText('ZATRZYMAJ')
            self.recording_btn.setProperty("cssClass", "danger-active")
            self.recording_btn.style().polish(self.recording_btn)
        else:
            self.recording_state = False
            self.recording_btn.setText('NAGRYWAJ')
            self.recording_btn.setProperty("cssClass", "danger")
            self.recording_btn.style().polish(self.recording_btn)

    def toggle_pause_recording(self):
        if not self.pause_state:
            self.pause_state = True
            self.pause_btn.setText('Wznow')
        else:
            self.pause_state = False
            self.pause_btn.setText('Pauza')

    def toggle_freeze_charts(self):
        if not self.charts_frozen:
            self.charts_frozen = True
            self.freeze_btn.setText("Odmroz")
            self.freeze_btn.setProperty("cssClass", "primary")
            self.freeze_btn.style().polish(self.freeze_btn)
        else:
            self.charts_frozen = False
            self.freeze_btn.setText("Zamroz")
            self.freeze_btn.setProperty("cssClass", "")
            self.freeze_btn.style().polish(self.freeze_btn)

    # --- DYNAMICZNE WYKRESY I STYLE ---

    def setup_dynamic_charts(self):
        ecg_active = self.settingsmanager.get_setting("channels_ecg", "active")
        ppg_active = self.settingsmanager.get_setting("channels_ppg", "raw_active")
        y_scale = self.settingsmanager.get_setting("acquisition", "y_scale_mv")
        if y_scale is None: y_scale = 2.0

        self.graphs_widget.clear()

        plot_ecg = None
        plot_ppg = None

        if ecg_active:
            plot_ecg = self.graphs_widget.addPlot(title="EKG (AD8232)")
            plot_ecg.showGrid(x=True, y=True, alpha=0.3)
            plot_ecg.setLabel('left', 'Amplituda', units='mV')
            plot_ecg.setLabel('bottom', 'Czas', units='s')
            plot_ecg.setYRange(-y_scale, y_scale)
            if ppg_active: self.graphs_widget.nextRow()

        if ppg_active:
            plot_ppg = self.graphs_widget.addPlot(title="PPG (MAX30102)")
            plot_ppg.showGrid(x=True, y=True, alpha=0.3)
            plot_ppg.setLabel('left', 'Sygnal Surowy', units='ADC')
            plot_ppg.setLabel('bottom', 'Czas', units='s')
            plot_ppg.enableAutoRange(axis='y')

        if plot_ecg and plot_ppg:
            plot_ppg.setXLink(plot_ecg)

        self.update_theme(self.settingsmanager.get_theme())

    def update_theme(self, theme):
        if theme == 'dark':
            bg_color = config.Colors.DARK_BACKGROUND
            label_color = config.Colors.DARK_TEXT_SECONDARY
            grid_alpha = 0.3
        else:
            bg_color = config.Colors.LIGHT_BACKGROUND
            label_color = config.Colors.LIGHT_TEXT_SECONDARY
            grid_alpha = 0.2

        self.graphs_widget.setBackground(bg_color)

        for item in self.graphs_widget.scene().items():
            if isinstance(item, pg.PlotItem):
                item.getAxis('left').setPen(label_color)
                item.getAxis('left').setTextPen(label_color)
                item.getAxis('bottom').setPen(label_color)
                item.getAxis('bottom').setTextPen(label_color)

                title_text = item.titleLabel.text
                item.setTitle(title_text, color=label_color, size="10pt")
                item.showGrid(x=True, y=True, alpha=grid_alpha)