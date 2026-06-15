import os
import csv
import json
from datetime import datetime
import numpy as np
import requests
from PyQt6.QtCore import pyqtSignal
from collections import deque
from PyQt6.QtCore import Qt
import pyqtgraph as pg
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QComboBox,
                             QHBoxLayout, QPushButton)
from resources import config


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

        self.gui_timer = QTimer()
        self.gui_timer.timeout.connect(self.update_charts_display)
        self.gui_timer.start(33)
        self.connection_state = "Disconected"
        self.recording_state = False
        self.pause_state = False
        self.charts_frozen = False
        self.recording_start_ts = None
        self.recorded_samples_count = 0

        # --- Zmienne do zapisu danych ---
        self.recording_file = None
        self.csv_writer = None
        self.ram_continuous_buffer = []
        self.retro_buffer = deque()

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

        self.refresh_btn = QPushButton("Odswiez")
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

        self.recording_btn = QPushButton("NAGRYWAJ")
        self.recording_btn.setProperty("cssClass", "danger")
        self.recording_btn.clicked.connect(self.toggle_recording)
        self.toolbox_layout.addWidget(self.recording_btn)

        self.pause_btn = QPushButton("Pauza")
        self.pause_btn.clicked.connect(self.toggle_pause_recording)
        self.toolbox_layout.addWidget(self.pause_btn)

        self.add_vertical_separator(self.toolbox_layout)

        self.retro_save_btn = QPushButton("Zapisz incydent")
        self.retro_save_btn.setProperty("cssClass", "primary")
        self.retro_save_btn.clicked.connect(self.save_incident_default)
        self.toolbox_layout.addWidget(self.retro_save_btn)

        self.add_vertical_separator(self.toolbox_layout)

        self.freeze_btn = QPushButton("Zamroz")
        self.freeze_btn.clicked.connect(self.toggle_freeze_charts)
        self.toolbox_layout.addWidget(self.freeze_btn)

        self.add_vertical_separator(self.toolbox_layout)

        # PRZYCISKI FORMATÓW DLA ZAPISU INCYDENTU
        self.export_edf_btn = QPushButton("EDF")
        self.export_csv_btn = QPushButton("CSV")
        self.export_json_btn = QPushButton("JSON")
        self.export_wfdb_btn = QPushButton("WFDB")

        self.export_edf_btn.clicked.connect(lambda: self.export_buffer("EDF"))
        self.export_csv_btn.clicked.connect(lambda: self.export_buffer("CSV"))
        self.export_json_btn.clicked.connect(lambda: self.export_buffer("JSON"))
        self.export_wfdb_btn.clicked.connect(lambda: self.export_buffer("WFDB"))

        self.toolbox_layout.addWidget(self.export_edf_btn)
        self.toolbox_layout.addWidget(self.export_csv_btn)
        self.toolbox_layout.addWidget(self.export_json_btn)
        self.toolbox_layout.addWidget(self.export_wfdb_btn)

        self.timer_label = QLabel("00:00:00")
        self.timer_label.setStyleSheet(
            f"color: {config.Colors.DARK_TEXT_SECONDARY}; font-size: 11pt; margin-left: 12px; letter-spacing: 1px; font-weight: bold;")
        self.toolbox_layout.addWidget(self.timer_label)
        self.toolbox_layout.addStretch()
        self.layout.addWidget(self.toolbar_container)

        # --- GLOWNA PRZESTRZEN ROBOCZA ---
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

    def update_format_buttons(self):
        """Podświetla przycisk odpowiadający domyślnemu formatowi zapisu"""
        fmt = self.settingsmanager.get_setting("storage", "default_format")
        btn_map = {
            "EDF": self.export_edf_btn,
            "CSV": self.export_csv_btn,
            "JSON": self.export_json_btn,
            "WFDB": self.export_wfdb_btn
        }
        for name, btn in btn_map.items():
            if name == fmt:
                btn.setProperty("cssClass", "primary")
            else:
                btn.setProperty("cssClass", "")
            btn.style().polish(btn)

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

        self.update_format_buttons()
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
        for p in ports: self.port_combo.addItem(p.device)

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

        sig_ekg = 1 if self.settingsmanager.get_setting("channels_ecg", "active") else 0
        rate_ekg = self.settingsmanager.get_setting("channels_ecg", "rate_hz") or 1000
        lead_ekg = self.settingsmanager.get_setting("channels_ecg", "lead") or "II (rytm)"
        lead_ekg_safe = lead_ekg.replace(" ", "_")

        sig_ppg = 1 if self.settingsmanager.get_setting("channels_ppg", "raw_active") else 0
        rate_ppg = self.settingsmanager.get_setting("channels_ppg", "rate_hz") or 100

        if self.connection_state == 'Disconected':
            url = (f"http://{esp_ip}/api/stream?state=1"
                   f"&sigEkg={sig_ekg}&rateEkg={rate_ekg}&leadEkg={lead_ekg_safe}"
                   f"&sigPpgWave={sig_ppg}&ratePpg={rate_ppg}"
                   f"&port={udp_port}")

            try:
                response = requests.get(url, timeout=2.0)
                if response.status_code == 200:
                    from core.network_worker import UDPWorker
                    self.udp_worker = UDPWorker(port=udp_port)
                    self.udp_worker.data_received.connect(self.process_incoming_data)
                    self.udp_worker.start()

                    self.connection_state = 'Connected'
                    self.connect_btn.setText('Rozlacz')
                    self.connect_btn.setProperty("cssClass", "primary")
                    self.status_label.setText("Polaczony")
                    self.status_label.setProperty("cssClass", "badge-ok")
                    self.baudrate_combo.setDisabled(True)
                    self.port_combo.setDisabled(True)
                    self.signal_combo.setDisabled(True)
            except requests.exceptions.RequestException as e:
                self.connection_status_changed.emit("Status: Blad sieci (ESP32 nie odpowiada)")

        else:
            try:
                requests.get(f"http://{esp_ip}/api/stream?state=0", timeout=2.0)
            except Exception:
                pass

            if hasattr(self, 'udp_worker') and self.udp_worker:
                self.udp_worker.stop()
                self.udp_worker.wait()
                self.udp_worker = None

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
            self.connection_status_changed.emit("Status: Polaczono z ESP32")
        else:
            self.connection_status_changed.emit("Status: Rozlaczony - brak polaczenia z ESP32")

    # ==========================================
    # ZAPIS DANYCH I OBSŁUGA PLIKÓW
    # ==========================================

    def _get_filename_prefix(self):
        """Generuje człon nazwy ze znacznikami aktywnych kanałów i ich częstotliwości"""
        ecg_active = self.settingsmanager.get_setting("channels_ecg", "active")
        ppg_active = self.settingsmanager.get_setting("channels_ppg", "raw_active")
        ecg_rate = self.settingsmanager.get_setting("channels_ecg", "rate_hz") or 1000
        ppg_rate = self.settingsmanager.get_setting("channels_ppg", "rate_hz") or 250

        parts = []
        if ecg_active:
            parts.append(f"ECG_{ecg_rate}Hz")
        if ppg_active:
            parts.append(f"PPG_{ppg_rate}Hz")

        if not parts:
            return "DATA"
        return "_".join(parts)

    def _save_to_edf(self, filename, buffer_data, ecg_active, ppg_active):
        import pyedflib

        channel_info = []
        data_list = []

        if ecg_active:
            ch = {'label': 'ECG', 'dimension': 'mV', 'sample_frequency': self.sampling_rate, 'physical_max': 5.0,
                  'physical_min': -5.0, 'digital_max': 32767, 'digital_min': -32768, 'transducer': 'AD8232',
                  'prefilter': ''}
            channel_info.append(ch)
            # Tworzymy jednowymiarową tablicę NumPy
            data_list.append(np.array([r[0] for r in buffer_data], dtype=np.float64))

        if ppg_active:
            ch = {'label': 'PPG', 'dimension': 'ADC', 'sample_frequency': self.sampling_rate, 'physical_max': 99999,
                  'physical_min': -99999, 'digital_max': 32767, 'digital_min': -32768, 'transducer': 'MAX30102',
                  'prefilter': ''}
            channel_info.append(ch)
            idx = 1 if ecg_active else 0
            # Tworzymy jednowymiarową tablicę NumPy
            data_list.append(np.array([r[idx] for r in buffer_data], dtype=np.float64))

        f = pyedflib.EdfWriter(filename, len(channel_info), file_type=pyedflib.FILETYPE_EDFPLUS)
        f.setSignalHeaders(channel_info)

        # Używamy poprawnej funkcji wysokopoziomowej, która przyjmuje listę tablic 1D
        f.writeSamples(data_list)
        f.close()

    def _save_to_wfdb(self, record_name, buffer_data, ecg_active, ppg_active, out_dir):
        import wfdb
        fmt_list = []
        units_list = []
        names_list = []
        matrix_cols = []

        if ecg_active:
            matrix_cols.append([r[0] for r in buffer_data])
            fmt_list.append('16')
            units_list.append('mV')
            names_list.append('ECG')

        if ppg_active:
            idx = 1 if ecg_active else 0
            matrix_cols.append([r[idx] for r in buffer_data])
            fmt_list.append('32')
            units_list.append('ADC')
            names_list.append('PPG')

        data_matrix = np.column_stack(matrix_cols)
        wfdb.wrsamp(record_name, fs=self.sampling_rate, units=units_list, sig_name=names_list, p_signal=data_matrix,
                    fmt=fmt_list, write_dir=out_dir)

    def toggle_recording(self):
        if not self.recording_state:
            out_dir = self.settingsmanager.get_setting("storage", "output_dir")
            os.makedirs(out_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = self._get_filename_prefix()

            self.current_recording_format = self.settingsmanager.get_setting("storage", "default_format")
            ecg_active = self.settingsmanager.get_setting("channels_ecg", "active")
            ppg_active = self.settingsmanager.get_setting("channels_ppg", "raw_active")

            try:
                if self.current_recording_format == "CSV":
                    self.recording_filename = os.path.join(out_dir, f"{prefix}_REC_{timestamp}.csv")
                    self.recording_file = open(self.recording_filename, 'w', newline='')
                    self.csv_writer = csv.writer(self.recording_file)

                    headers = ["Czas(s)"]
                    if ecg_active: headers.append("EKG_Surowe(mV)")
                    if ppg_active: headers.append("PPG_Surowe(ADC)")
                    self.csv_writer.writerow(headers)

                elif self.current_recording_format in ["JSON", "EDF", "WFDB"]:
                    self.recording_filename_base = f"{prefix}_REC_{timestamp}"
                    self.recording_full_path = os.path.join(out_dir, self.recording_filename_base)
                    self.ram_continuous_buffer = []

                self.recorded_samples_count = 0
                self.recording_state = True

                self.recording_btn.setText('ZATRZYMAJ')
                self.recording_btn.setProperty("cssClass", "danger-active")

                file_info = f"{self.recording_filename_base}.{self.current_recording_format.lower()}" if self.current_recording_format != "CSV" else os.path.basename(
                    self.recording_filename)
                self.connection_status_changed.emit(
                    f"Status: Nagrywanie ({self.current_recording_format}) -> {file_info}")

            except Exception as e:
                self.connection_status_changed.emit(f"Status: Blad utworzenia pliku: {e}")
                return
        else:
            # ZATRZYMYWANIE NAGRYWANIA I ZRZUT DANYCH
            self.recording_state = False
            ecg_active = self.settingsmanager.get_setting("channels_ecg", "active")
            ppg_active = self.settingsmanager.get_setting("channels_ppg", "raw_active")

            if self.current_recording_format == "CSV" and self.recording_file:
                self.recording_file.close()
                self.recording_file = None
                self.csv_writer = None

            elif self.current_recording_format in ["JSON", "EDF", "WFDB"]:
                try:
                    if self.current_recording_format == "JSON":
                        data = {
                            "metadata": {
                                "type": "Continuous Record",
                                "sampling_rate": self.sampling_rate,
                                "samples": len(self.ram_continuous_buffer),
                                "channels": []
                            },
                            "signals": {}
                        }
                        if ecg_active:
                            data["metadata"]["channels"].append("ECG (mV)")
                            data["signals"]["ECG"] = [r[0] for r in self.ram_continuous_buffer]
                        if ppg_active:
                            data["metadata"]["channels"].append("PPG (ADC)")
                            idx = 1 if ecg_active else 0
                            data["signals"]["PPG"] = [r[idx] for r in self.ram_continuous_buffer]

                        with open(self.recording_full_path + ".json", 'w') as f:
                            json.dump(data, f)

                    elif self.current_recording_format == "EDF":
                        self._save_to_edf(self.recording_full_path + ".edf", self.ram_continuous_buffer, ecg_active,
                                          ppg_active)

                    elif self.current_recording_format == "WFDB":
                        out_dir = self.settingsmanager.get_setting("storage", "output_dir")
                        self._save_to_wfdb(self.recording_filename_base, self.ram_continuous_buffer, ecg_active,
                                           ppg_active, out_dir)

                    self.ram_continuous_buffer = []

                except ImportError as ie:
                    self.connection_status_changed.emit(
                        f"Status: Brak paczki {ie.name}. Zainstaluj za pomoca: pip install pyedflib wfdb")
                except Exception as e:
                    print(f"Blad zapisu z RAM: {e}")

            self.recording_btn.setText('NAGRYWAJ')
            self.recording_btn.setProperty("cssClass", "danger")
            self.connection_status_changed.emit("Status: Zakonczono nagrywanie.")

        self.recording_btn.style().polish(self.recording_btn)

    def toggle_pause_recording(self):
        if not self.pause_state:
            self.pause_state = True
            self.pause_btn.setText('Wznow')
        else:
            self.pause_state = False
            self.pause_btn.setText('Pauza')

    def save_incident_default(self):
        fmt = self.settingsmanager.get_setting("storage", "default_format")
        self.export_buffer(fmt)

    def export_buffer(self, format_type):
        if not self.retro_buffer:
            self.connection_status_changed.emit("Status: Bufor jest pusty, brak danych.")
            return

        out_dir = self.settingsmanager.get_setting("storage", "output_dir")
        os.makedirs(out_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = self._get_filename_prefix()

        ecg_active = self.settingsmanager.get_setting("channels_ecg", "active")
        ppg_active = self.settingsmanager.get_setting("channels_ppg", "raw_active")

        try:
            if format_type == "CSV":
                filename = os.path.join(out_dir, f"{prefix}_INCIDENT_{timestamp}.csv")
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)

                    headers = ["Czas_Wzgledny(s)"]
                    if ecg_active: headers.append("EKG_Surowe(mV)")
                    if ppg_active: headers.append("PPG_Surowe(ADC)")
                    writer.writerow(headers)

                    for idx, row_data in enumerate(self.retro_buffer):
                        rel_time = idx / self.sampling_rate
                        row = [f"{rel_time:.3f}"]
                        if ecg_active: row.append(f"{row_data[0]:.3f}")
                        if ppg_active: row.append(row_data[1])
                        writer.writerow(row)

                self.connection_status_changed.emit(f"Status: Zapisano zrzut jako {os.path.basename(filename)}")

            elif format_type == "JSON":
                filename = os.path.join(out_dir, f"{prefix}_INCIDENT_{timestamp}.json")
                data = {
                    "metadata": {
                        "timestamp": timestamp,
                        "sampling_rate": self.sampling_rate,
                        "samples_count": len(self.retro_buffer),
                        "channels": []
                    },
                    "signals": {}
                }

                if ecg_active:
                    data["metadata"]["channels"].append("ECG (mV)")
                    data["signals"]["ECG"] = [round(r[0], 3) for r in self.retro_buffer]
                if ppg_active:
                    data["metadata"]["channels"].append("PPG (ADC)")
                    data["signals"]["PPG"] = [r[1] for r in self.retro_buffer]

                with open(filename, 'w') as f:
                    json.dump(data, f)
                self.connection_status_changed.emit(f"Status: Zapisano zrzut jako {os.path.basename(filename)}")

            elif format_type == "EDF":
                filename = os.path.join(out_dir, f"{prefix}_INCIDENT_{timestamp}.edf")
                self._save_to_edf(filename, self.retro_buffer, ecg_active, ppg_active)
                self.connection_status_changed.emit(f"Status: Zapisano zrzut jako {os.path.basename(filename)}")

            elif format_type == "WFDB":
                record_name = f"{prefix}_INCIDENT_{timestamp}"
                self._save_to_wfdb(record_name, self.retro_buffer, ecg_active, ppg_active, out_dir)
                self.connection_status_changed.emit(f"Status: Zapisano zrzut WFDB (rekord: {record_name})")

        except ImportError as ie:
            self.connection_status_changed.emit(
                f"Status: Brak paczki {ie.name}. Zainstaluj za pomoca: pip install pyedflib wfdb")
        except Exception as e:
            self.connection_status_changed.emit(f"Status: Blad zapisu {format_type}: {e}")

    def toggle_freeze_charts(self):
        if not self.charts_frozen:
            self.charts_frozen = True
            self.freeze_btn.setText("Odmroz")
            self.freeze_btn.setProperty("cssClass", "primary")
        else:
            self.charts_frozen = False
            self.freeze_btn.setText("Zamroz")
            self.freeze_btn.setProperty("cssClass", "")
        self.freeze_btn.style().polish(self.freeze_btn)

    # ==========================================
    # LOGIKA WYKRESÓW
    # ==========================================

    def setup_dynamic_charts(self):
        ecg_active = self.settingsmanager.get_setting("channels_ecg", "active")
        ppg_active = self.settingsmanager.get_setting("channels_ppg", "raw_active")
        y_scale = self.settingsmanager.get_setting("acquisition", "y_scale_mv")

        self.filter_notch = self.settingsmanager.get_setting("dsp", "notch_50hz")
        self.filter_baseline = self.settingsmanager.get_setting("dsp", "baseline_wander_removal")
        self.filter_bandpass = self.settingsmanager.get_setting("dsp", "bandpass_enabled")
        self.filter_smoothing = self.settingsmanager.get_setting("dsp", "moving_average_smoothing")

        self.window_s = self.settingsmanager.get_setting("acquisition", "preview_window_s") or 5.0
        self.sampling_rate = self.settingsmanager.get_setting("channels_ecg", "rate_hz") or 1000

        # POPRAWKA 1: Fizyczne wymuszenie gigantycznego rozmiaru bufora graficznego.
        # Niezależnie od tego, czy pracujemy na 250 Hz czy 1000 Hz, rezerwujemy pamięć
        # na 1.5-krotność okna przy MAKSYMALNEJ częstotliwości (1000 Hz).
        # Rozwiązuje to problem "wczesnego czyszczenia" (pustej lewej strony) w przypadku,
        # gdy ESP32 wysyła dane szybciej niż zakłada to wybrana w panelu częstotliwość.
        self.buffer_size = int(self.window_s * 1000 * 1.5)

        retro_min = self.settingsmanager.get_setting("storage", "retro_buffer_min") or 5
        retro_samples = int(retro_min * 60 * self.sampling_rate)
        self.retro_buffer = deque(maxlen=retro_samples)

        from collections import deque as inner_deque
        self.ecg_50hz_buffer = inner_deque(maxlen=20)
        self.ecg_dc = 0.0
        self.ecg_lp = 0.0

        self.ppg_dc = 0.0
        self.smoothed_ppg = 0.0
        self.total_samples = 0

        self.time_buffer = np.full(self.buffer_size, np.nan)
        self.ecg_data = np.full(self.buffer_size, np.nan)
        self.ppg_data = np.full(self.buffer_size, np.nan)
        if y_scale is None: y_scale = 2.0

        self.graphs_widget.clear()

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
            plot_ppg.setLabel('left', 'Sygnal', units='ADC')
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
                item.setTitle(item.titleLabel.text, color=label_color, size="10pt")
                item.showGrid(x=True, y=True, alpha=grid_alpha)

    def process_incoming_data(self, data_bytes):
        import struct
        import numpy as np

        packet_size = 8
        num_samples = len(data_bytes) // packet_size

        if num_samples == 0: return

        new_times = np.zeros(num_samples)
        new_ecg = np.zeros(num_samples)
        new_ppg = np.zeros(num_samples)

        batch_rows_to_save = []

        ecg_active = self.settingsmanager.get_setting("channels_ecg", "active")
        ppg_active = self.settingsmanager.get_setting("channels_ppg", "raw_active")

        for i in range(num_samples):
            chunk = data_bytes[i * 8: (i + 1) * 8]
            ts, ekg_raw, ppg_raw = struct.unpack('<Ihh', chunk)

            hardware_time_s = ts / 1000.0
            ecg_mv_raw = (ekg_raw - 2048.0) / 400.0

            self.retro_buffer.append((ecg_mv_raw, ppg_raw))

            if self.recording_state and not self.pause_state:
                record_time_s = self.recorded_samples_count / self.sampling_rate
                self.recorded_samples_count += 1

                row = []
                if self.current_recording_format == "CSV":
                    row.append(f"{record_time_s:.3f}")
                    if ecg_active: row.append(f"{ecg_mv_raw:.3f}")
                    if ppg_active: row.append(ppg_raw)
                    batch_rows_to_save.append(row)
                elif self.current_recording_format in ["JSON", "EDF", "WFDB"]:
                    if ecg_active and ppg_active:
                        row = [ecg_mv_raw, ppg_raw]
                    elif ecg_active:
                        row = [ecg_mv_raw]
                    elif ppg_active:
                        row = [ppg_raw]
                    self.ram_continuous_buffer.append(row)

            processed_ecg = ecg_mv_raw

            if self.filter_notch:
                self.ecg_50hz_buffer.append(processed_ecg)
                if len(self.ecg_50hz_buffer) == 20: processed_ecg = sum(self.ecg_50hz_buffer) / 20.0

            if self.filter_baseline:
                self.ecg_dc = 0.995 * self.ecg_dc + 0.005 * processed_ecg
                processed_ecg = processed_ecg - self.ecg_dc

            if self.filter_bandpass:
                self.ecg_lp = 0.6 * self.ecg_lp + 0.4 * processed_ecg
                processed_ecg = self.ecg_lp

            self.ppg_dc = 0.99 * self.ppg_dc + 0.01 * ppg_raw
            processed_ppg = ppg_raw - self.ppg_dc

            if self.filter_smoothing:
                self.smoothed_ppg = 0.85 * self.smoothed_ppg + 0.15 * processed_ppg
                processed_ppg = self.smoothed_ppg

            new_times[i] = hardware_time_s
            new_ecg[i] = processed_ecg
            new_ppg[i] = -processed_ppg

        if self.recording_state and self.current_recording_format == "CSV" and self.csv_writer and batch_rows_to_save and not self.pause_state:
            self.csv_writer.writerows(batch_rows_to_save)

        self.time_buffer = np.roll(self.time_buffer, -num_samples)
        self.time_buffer[-num_samples:] = new_times

        self.ecg_data = np.roll(self.ecg_data, -num_samples)
        self.ecg_data[-num_samples:] = new_ecg

        self.ppg_data = np.roll(self.ppg_data, -num_samples)
        self.ppg_data[-num_samples:] = new_ppg

        self.total_samples += num_samples
        self.data_changed_flag = True

    def update_charts_display(self):
        import time

        # 1. Obsługa Timera na podstawie rzeczywistego czasu komputera (time.time)
        if self.recording_state:
            # Inicjalizacja zegara przy pierwszym uruchomieniu nagrywania
            if getattr(self, '_rec_start_clock', None) is None:
                self._rec_start_clock = time.time()
                self._pause_clock_accum = 0.0
                self._last_clock = time.time()

            now = time.time()

            # Jeśli jest pauza, akumulujemy czas przestoju, aby go potem odjąć
            if self.pause_state:
                self._pause_clock_accum += (now - self._last_clock)

            self._last_clock = now

            # Obliczenie idealnego czasu trwania nagrania
            elapsed_s = int(now - self._rec_start_clock - self._pause_clock_accum)
            m, s = divmod(elapsed_s, 60)
            h, m = divmod(m, 60)
            self.timer_label.setText(f"{h:02d}:{m:02d}:{s:02d}")
        else:
            self.timer_label.setText("00:00:00")
            # Sprzątanie zmiennych po zakończeniu nagrywania
            if hasattr(self, '_rec_start_clock'):
                del self._rec_start_clock
                del self._pause_clock_accum
                del self._last_clock

        # 2. Odświeżanie Wykresów (bez zmian)
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

            self.data_changed_flag = False