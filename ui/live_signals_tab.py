import numpy as np
import requests
from PyQt6.QtCore import pyqtSignal
from collections import deque
from PyQt6.QtCore import Qt
import pyqtgraph as pg
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QComboBox,
                             QHBoxLayout, QPushButton)
from resources import config
from ui import main_window


class LiveSignalsTab(QFrame):
    connection_status_changed = pyqtSignal(str)
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
        from PyQt6.QtCore import QTimer

        self.data_changed_flag = False

        # Zegar odświeżania GUI (33ms = ok. 30 klatek na sekundę)
        self.gui_timer = QTimer()
        self.gui_timer.timeout.connect(self.update_charts_display)
        self.gui_timer.start(33)
        self.connection_state = "Disconected"
        self.recording_state = False
        self.pause_state = False
        self.charts_frozen = False
        self.recording_state = False
        self.recording_start_ts = None  # Czas startu nagrywania
        self.pause_state = False
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

        self.refresh_btn = QPushButton("Odśwież")
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
        esp_ip = self.settingsmanager.get_setting("connection", "esp_ip")
        udp_port = self.settingsmanager.get_setting("connection", "port")

        # Pobieramy ustawienia z SettingsManager
        sig_ekg = 1 if self.settingsmanager.get_setting("channels_ecg", "active") else 0
        rate_ekg = self.settingsmanager.get_setting("channels_ecg", "rate_hz") or 1000

        # DODANE: Pobranie ustawienia odprowadzenia (Lead)
        lead_ekg = self.settingsmanager.get_setting("channels_ecg", "lead") or "II (rytm)"
        # Jeśli z combo boxa przychodzi np. "II (rytm)", dla czystości na ESP możemy uciąć tekst po spacji,
        # ale na razie wyślijmy całość lub tylko pierwszy wyraz. Najbezpieczniej wymienić spacje:
        lead_ekg_safe = lead_ekg.replace(" ", "_")

        sig_ppg = 1 if self.settingsmanager.get_setting("channels_ppg", "raw_active") else 0
        rate_ppg = self.settingsmanager.get_setting("channels_ppg", "rate_hz") or 100

        if self.connection_state == 'Disconected':
            print(f"Próba połączenia z {esp_ip}...")

            # DODANE: Parametr &leadEkg do zapytania HTTP
            url = (f"http://{esp_ip}/api/stream?state=1"
                   f"&sigEkg={sig_ekg}&rateEkg={rate_ekg}&leadEkg={lead_ekg_safe}"
                   f"&sigPpgWave={sig_ppg}&ratePpg={rate_ppg}"
                   f"&port={udp_port}")

            try:
                response = requests.get(url, timeout=2.0)

                if response.status_code == 200:
                    print(f"ESP32 Zaakceptowało: {response.text}")
                    print(f"Przyjete parametry: sigEkg={sig_ekg}, rateEkg={rate_ekg}, leadEkg={lead_ekg_safe}, sigPpgWave={sig_ppg}, ratePpg={rate_ppg}, port={udp_port}")
                    # 3. Jeśli ESP32 jest gotowe, uruchamiamy nasz UDP Worker
                    from core.network_worker import UDPWorker  # (Jeśli nie masz importu na górze)
                    self.udp_worker = UDPWorker(port=udp_port)
                    # Tutaj podłączymy zaraz metodę do odbierania danych
                    self.udp_worker.data_received.connect(self.process_incoming_data)
                    self.udp_worker.start()

                    # Zmiana UI
                    self.connection_state = 'Connected'
                    self.connect_btn.setText('Rozlacz')
                    self.connect_btn.setProperty("cssClass", "primary")
                    self.status_label.setText("Polaczony")
                    self.status_label.setProperty("cssClass", "badge-ok")
                    self.baudrate_combo.setDisabled(True)
                    self.port_combo.setDisabled(True)
                    self.signal_combo.setDisabled(True)

                else:
                    print(f"Błąd ESP32: {response.status_code}")

            except requests.exceptions.RequestException as e:
                print(f"Błąd sieci (ESP32 nie odpowiada): {e}")

        else:
            # ROZŁĄCZANIE
            print("Zatrzymywanie strumienia...")
            try:
                # Wysyłamy state=0 do ESP32
                requests.get(f"http://{esp_ip}/api/stream?state=0", timeout=2.0)
            except Exception as e:
                print(f"Błąd wysyłania stop: {e}")

            # Wyłączamy Workera
            if hasattr(self, 'udp_worker') and self.udp_worker:
                self.udp_worker.stop()
                self.udp_worker.wait()  # Czekamy aż wątek bezpiecznie się zamknie
                self.udp_worker = None

            # Zmiana UI
            self.connection_state = 'Disconected'
            self.connect_btn.setText('Polacz')
            self.connect_btn.setProperty("cssClass", "")
            self.status_label.setText("Rozlaczony")
            self.status_label.setProperty("cssClass", "badge-err")

            self.baudrate_combo.setDisabled(False)
            self.port_combo.setDisabled(False)
            self.signal_combo.setDisabled(False)

        self.connect_btn.style().polish(self.connect_btn)
        self.status_label.style().polish(self.status_label)
        if self.connection_state == 'Connected':
            # Po udanym połączeniu:
            self.connection_status_changed.emit("Status: Połączono z ESP32")
        else:
            # Po rozłączeniu:
            self.connection_status_changed.emit("Status: Rozłączony - brak połączenia z ESP32")
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

        # Pobranie stanu filtrów DSP z SettingsManager
        self.filter_notch = self.settingsmanager.get_setting("dsp", "notch_50hz")
        self.filter_baseline = self.settingsmanager.get_setting("dsp", "baseline_wander_removal")
        self.filter_bandpass = self.settingsmanager.get_setting("dsp", "bandpass_enabled")
        self.filter_smoothing = self.settingsmanager.get_setting("dsp", "moving_average_smoothing")

        self.window_s = self.settingsmanager.get_setting("acquisition", "preview_window_s") or 5.0
        self.sampling_rate = self.settingsmanager.get_setting("channels_ecg", "rate_hz") or 1000
        self.buffer_size = int(self.window_s * self.sampling_rate)

        # --- Zmienne dla DSP EKG ---
        from collections import deque
        self.ecg_50hz_buffer = deque(maxlen=20)
        self.ecg_dc = 0.0
        self.ecg_lp = 0.0

        # --- Zmienne dla DSP PPG ---
        self.ppg_dc = 0.0
        self.smoothed_ppg = 0.0

        self.total_samples = 0

        # Kluczowe dla osi czasu
        self.time_buffer = np.full(self.buffer_size, np.nan)
        self.ecg_data = np.full(self.buffer_size, np.nan)
        self.ppg_data = np.full(self.buffer_size, np.nan)
        if y_scale is None: y_scale = 2.0

        self.graphs_widget.clear()

        # Inicjalizacja krzywych na None, aby zapobiec błędom
        self.ecg_curve = None
        self.ppg_curve = None
        plot_ecg = None
        plot_ppg = None

        if ecg_active:
            plot_ecg = self.graphs_widget.addPlot(title="EKG (AD8232)")
            plot_ecg.showGrid(x=True, y=True, alpha=0.3)
            plot_ecg.setLabel('left', 'Amplituda', units='mV')
            plot_ecg.setLabel('bottom', 'Czas', units='s')
            plot_ecg.setYRange(-y_scale, y_scale)
            self.ecg_curve = plot_ecg.plot(pen=pg.mkPen(color=config.Colors.SIGNAL_ECG, width=1.5))

            if ppg_active: self.graphs_widget.nextRow()

        if ppg_active:
            plot_ppg = self.graphs_widget.addPlot(title="PPG (MAX30102)")
            plot_ppg.showGrid(x=True, y=True, alpha=0.3)
            plot_ppg.setLabel('left', 'Sygnał', units='ADC')
            plot_ppg.setLabel('bottom', 'Czas', units='s')
            plot_ppg.enableAutoRange(axis='y')
            self.ppg_curve = plot_ppg.plot(pen=pg.mkPen(color=config.Colors.SIGNAL_PPG, width=1.5))

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

    def process_incoming_data(self, data_bytes):
        import struct
        import numpy as np

        packet_size = 8
        num_samples = len(data_bytes) // packet_size

        if num_samples == 0:
            return

        new_times = np.zeros(num_samples)
        new_ecg = np.zeros(num_samples)
        new_ppg = np.zeros(num_samples)

        for i in range(num_samples):
            chunk = data_bytes[i * 8: (i + 1) * 8]
            ts, ekg_raw, ppg_raw = struct.unpack('<Ihh', chunk)

            # ==========================================
            # 1. SUROWE DANE (Do zapisu i obliczeń)
            # ==========================================
            current_time_s = ts / 1000.0
            ecg_mv_raw = (ekg_raw - 2048.0) / 400.0

            if self.recording_state:
                if self.recording_start_ts is None:
                    self.recording_start_ts = ts
                record_time_s = (ts - self.recording_start_ts) / 1000.0

                # MIEJSCE NA ZAPIS: Tutaj w przyszłości przekażesz do funkcji zapisującej
                # czyste zmienne: record_time_s, ecg_mv_raw, ppg_raw

            # ==========================================
            # 2. FILTROWANIE DSP EKG (Tylko wizualizacja)
            # ==========================================
            processed_ecg = ecg_mv_raw

            if self.filter_notch:
                self.ecg_50hz_buffer.append(processed_ecg)
                if len(self.ecg_50hz_buffer) == 20:
                    processed_ecg = sum(self.ecg_50hz_buffer) / 20.0

            if self.filter_baseline:
                self.ecg_dc = 0.995 * self.ecg_dc + 0.005 * processed_ecg
                processed_ecg = processed_ecg - self.ecg_dc

            if self.filter_bandpass:
                self.ecg_lp = 0.6 * self.ecg_lp + 0.4 * processed_ecg
                processed_ecg = self.ecg_lp

            # ==========================================
            # 3. FILTROWANIE DSP PPG (Tylko wizualizacja)
            # ==========================================
            # Zawsze usuwamy DC (stałą), aby wykres nie uciekł poza ekran
            self.ppg_dc = 0.99 * self.ppg_dc + 0.01 * ppg_raw
            processed_ppg = ppg_raw - self.ppg_dc

            # Wygładzanie (opcjonalne, powiązane z ustawieniem moving_average_smoothing)
            if self.filter_smoothing:
                self.smoothed_ppg = 0.85 * self.smoothed_ppg + 0.15 * processed_ppg
                processed_ppg = self.smoothed_ppg

            # Zapis do tablic wyświetlających
            new_times[i] = current_time_s
            new_ecg[i] = processed_ecg
            new_ppg[i] = -processed_ppg

        # ==========================================
        # 4. PRZESUWANIE TAŚMY (Rolling)
        # ==========================================
        self.time_buffer = np.roll(self.time_buffer, -num_samples)
        self.time_buffer[-num_samples:] = new_times

        self.ecg_data = np.roll(self.ecg_data, -num_samples)
        self.ecg_data[-num_samples:] = new_ecg

        self.ppg_data = np.roll(self.ppg_data, -num_samples)
        self.ppg_data[-num_samples:] = new_ppg

        self.total_samples += num_samples

        # Informujemy zegar, że są nowe dane do narysowania
        self.data_changed_flag = True

    def update_charts_display(self):
        # Rysuj tylko wtedy, gdy pojawiły się nowe dane z UDP i wykresy nie są zamrożone
        if not self.charts_frozen and self.data_changed_flag:
            valid_mask = ~np.isnan(self.time_buffer)
            valid_times = self.time_buffer[valid_mask]
            valid_ecg = self.ecg_data[valid_mask]
            valid_ppg = self.ppg_data[valid_mask]

            if len(valid_times) > 0:
                latest_ts = valid_times[-1]

                if self.ecg_curve:
                    self.ecg_curve.setData(valid_times, valid_ecg)
                    self.ecg_curve.getViewBox().setXRange(latest_ts - self.window_s, latest_ts, padding=0)

                if self.ppg_curve:
                    self.ppg_curve.setData(valid_times, valid_ppg)
                    self.ppg_curve.getViewBox().setXRange(latest_ts - self.window_s, latest_ts, padding=0)

            # Po narysowaniu opuszczamy flagę, odciążając procesor komputera
            self.data_changed_flag = False

    def update_connection_state(self, new_state):
        self.connection_state = new_state
        # Emitujemy sygnał, który przechwyci MainWindow
        self.connection_status_changed.emit(f"Status: {new_state}")