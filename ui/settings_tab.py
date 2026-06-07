# ui/settings_tab.py
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QComboBox, QCheckBox, QLineEdit,
                             QPushButton, QScrollArea, QWidget)
from resources import config
import serial.tools.list_ports


class SettingsTab(QFrame):
    def __init__(self, settingsmanager):
        super().__init__()
        self.setProperty("cssClass", "panel")
        self.settingsmanager = settingsmanager
        self.loading = True

        self.initUI()
        self.settingsmanager.settings_changed.connect(self.load_settings_to_ui)
        self.loading = False

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.viewport().setStyleSheet("background: transparent;")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(20)

        theme_mode = self.settingsmanager.get_theme()
        input_style = self.get_input_style(theme_mode)

        # --- 1. SEKCJA: POŁĄCZENIE ESP32 ---
        conn_card = QFrame()
        conn_card.setProperty("cssClass", "card")
        conn_layout = QVBoxLayout(conn_card)
        conn_layout.setContentsMargins(16, 16, 16, 16)

        conn_title = QLabel("POŁĄCZENIE ESP32")
        conn_title.setProperty("cssClass", "card-title")
        conn_layout.addWidget(conn_title)
        conn_layout.addSpacing(10)

        conn_grid = QGridLayout()
        conn_grid.setSpacing(12)

        conn_grid.addWidget(QLabel("Tryb transmisji / Port:"), 0, 0)

        mode_layout = QHBoxLayout()
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["WiFi UDP", "WiFi TCP", "BLE (GATT)"])
        self.scan_ports_btn = QPushButton("↺ Zaktualizuj listę (Ustawienia + USB)")
        self.scan_ports_btn.setMinimumWidth(240)
        mode_layout.addWidget(self.combo_mode)
        mode_layout.addWidget(self.scan_ports_btn)
        conn_grid.addLayout(mode_layout, 0, 1)

        conn_grid.addWidget(QLabel("Adres IP ESP32:"), 1, 0)
        self.input_ip = QLineEdit()
        self.input_ip.setStyleSheet(input_style)
        conn_grid.addWidget(self.input_ip, 1, 1)

        conn_grid.addWidget(QLabel("Port UDP / TCP:"), 2, 0)
        self.input_port = QLineEdit()
        self.input_port.setStyleSheet(input_style)
        conn_grid.addWidget(self.input_port, 2, 1)

        conn_grid.addWidget(QLabel("Nazwa BLE:"), 3, 0)
        self.input_ble = QLineEdit()
        self.input_ble.setStyleSheet(input_style)
        conn_grid.addWidget(self.input_ble, 3, 1)

        conn_grid.addWidget(QLabel("Format pakietu:"), 4, 0)
        self.combo_format = QComboBox()
        self.combo_format.addItems(["JSON + Base64", "Binary (little-endian)", "CSV (tekstowy)"])
        conn_grid.addWidget(self.combo_format, 4, 1)

        conn_layout.addLayout(conn_grid)
        scroll_layout.addWidget(conn_card)

        # --- 2. SEKCJA: KANAŁY — EKG ---
        ecg_card = QFrame()
        ecg_card.setProperty("cssClass", "card")
        ecg_layout = QVBoxLayout(ecg_card)
        ecg_layout.setContentsMargins(16, 16, 16, 16)

        ecg_title = QLabel("KANAŁY — EKG (AD8232)")
        ecg_title.setProperty("cssClass", "card-title")
        ecg_layout.addWidget(ecg_title)
        ecg_layout.addSpacing(10)

        ecg_grid = QGridLayout()
        ecg_grid.setSpacing(12)

        self.check_ecg_active = QCheckBox("Aktywny")
        ecg_grid.addWidget(self.check_ecg_active, 0, 0, 1, 2)

        ecg_grid.addWidget(QLabel("Próbkowanie EKG:"), 1, 0)
        self.combo_ecg_rate = QComboBox()
        self.combo_ecg_rate.addItems(["250 Hz", "500 Hz", "1000 Hz"])
        ecg_grid.addWidget(self.combo_ecg_rate, 1, 1)

        ecg_grid.addWidget(QLabel("Odprowadzenie:"), 2, 0)
        self.combo_ecg_lead = QComboBox()
        self.combo_ecg_lead.addItems(["I", "II (rytm)", "III", "aVR", "aVL", "aVF"])
        ecg_grid.addWidget(self.combo_ecg_lead, 2, 1)

        ecg_layout.addLayout(ecg_grid)
        scroll_layout.addWidget(ecg_card)

        # --- 3. SEKCJA: KANAŁY — PPG ---
        ppg_card = QFrame()
        ppg_card.setProperty("cssClass", "card")
        ppg_layout = QVBoxLayout(ppg_card)
        ppg_layout.setContentsMargins(16, 16, 16, 16)

        ppg_title = QLabel("KANAŁY — PPG / SpO2 (MAX30102)")
        ppg_title.setProperty("cssClass", "card-title")
        ppg_layout.addWidget(ppg_title)
        ppg_layout.addSpacing(10)

        ppg_grid = QGridLayout()
        ppg_grid.setSpacing(12)

        self.check_ppg_raw = QCheckBox("Surowy PPG (wykres)")
        ppg_grid.addWidget(self.check_ppg_raw, 0, 0, 1, 2)

        self.check_ppg_spo2 = QCheckBox("SpO2 / HR na ESP32")
        ppg_grid.addWidget(self.check_ppg_spo2, 1, 0, 1, 2)

        ppg_grid.addWidget(QLabel("Próbkowanie PPG:"), 2, 0)
        self.combo_ppg_rate = QComboBox()
        self.combo_ppg_rate.addItems(["250 Hz", "500 Hz", "1000 Hz"])  # TAKIE SAME JAK EKG
        ppg_grid.addWidget(self.combo_ppg_rate, 2, 1)

        ppg_layout.addLayout(ppg_grid)
        scroll_layout.addWidget(ppg_card)

        # --- 4. SEKCJA: FILTROWANIE DSP ---
        dsp_card = QFrame()
        dsp_card.setProperty("cssClass", "card")
        dsp_layout = QVBoxLayout(dsp_card)
        dsp_layout.setContentsMargins(16, 16, 16, 16)

        dsp_title = QLabel("FILTROWANIE DSP (PYTHON)")
        dsp_title.setProperty("cssClass", "card-title")
        dsp_layout.addWidget(dsp_title)
        dsp_layout.addSpacing(10)

        self.check_notch = QCheckBox("Filtr notch 50 Hz (EKG)")
        self.check_bandpass = QCheckBox("Filtr pasmowy 0.5–40 Hz")
        self.check_baseline = QCheckBox("Usuwanie dryfu linii bazowej")

        dsp_layout.addWidget(self.check_notch)
        dsp_layout.addWidget(self.check_bandpass)
        dsp_layout.addWidget(self.check_baseline)

        scroll_layout.addWidget(dsp_card)
        # --- SEKCJA: WIZUALIZACJA I WYKRESY ---
        vis_card = QFrame()
        vis_card.setProperty("cssClass", "card")
        vis_layout = QVBoxLayout(vis_card)
        vis_layout.setContentsMargins(16, 16, 16, 16)

        vis_title = QLabel("WIZUALIZACJA I WYKRESY")
        vis_title.setProperty("cssClass", "card-title")
        vis_layout.addWidget(vis_title)
        vis_layout.addSpacing(10)

        vis_grid = QGridLayout()
        vis_grid.setSpacing(12)

        vis_grid.addWidget(QLabel("Wzmocnienie:"), 0, 0)
        self.combo_gain = QComboBox()
        self.combo_gain.addItems(["1.0x", "2.0x", "5.0x"])
        vis_grid.addWidget(self.combo_gain, 0, 1)

        vis_grid.addWidget(QLabel("Skala Y (mV):"), 1, 0)
        self.combo_scale = QComboBox()
        self.combo_scale.addItems(["±1 mV", "±2 mV", "±5 mV"])
        vis_grid.addWidget(self.combo_scale, 1, 1)

        vis_grid.addWidget(QLabel("Okno podglądu:"), 2, 0)
        self.combo_window = QComboBox()
        self.combo_window.addItems(["3 s", "5 s", "10 s"])
        vis_grid.addWidget(self.combo_window, 2, 1)

        vis_layout.addLayout(vis_grid)
        scroll_layout.addWidget(vis_card)
        # --- 5. SEKCJA: ZAPIS PLIKÓW ---
        storage_card = QFrame()
        storage_card.setProperty("cssClass", "card")
        storage_layout = QVBoxLayout(storage_card)
        storage_layout.setContentsMargins(16, 16, 16, 16)

        storage_title = QLabel("ZAPIS PLIKOW I BUFOR")
        storage_title.setProperty("cssClass", "card-title")
        storage_layout.addWidget(storage_title)
        storage_layout.addSpacing(10)

        storage_grid = QGridLayout()
        storage_grid.setSpacing(12)

        storage_grid.addWidget(QLabel("Domyslny format zapisu:"), 0, 0)
        self.combo_storage_format = QComboBox()
        self.combo_storage_format.addItems(["EDF", "WFDB", "CSV", "JSON"])
        storage_grid.addWidget(self.combo_storage_format, 0, 1)

        storage_grid.addWidget(QLabel("Lokalizacja bazowa (katalog):"), 1, 0)
        self.input_dir = QLineEdit()
        self.input_dir.setStyleSheet(input_style)
        storage_grid.addWidget(self.input_dir, 1, 1)

        storage_grid.addWidget(QLabel("Auto-zapis w tle (min):"), 2, 0)
        self.input_interval = QLineEdit()
        self.input_interval.setStyleSheet(input_style)
        storage_grid.addWidget(self.input_interval, 2, 1)

        storage_grid.addWidget(QLabel("Dlugosc bufora incydentow (min):"), 3, 0)
        self.input_retro_buffer = QLineEdit()
        self.input_retro_buffer.setStyleSheet(input_style)
        storage_grid.addWidget(self.input_retro_buffer, 3, 1)

        storage_layout.addLayout(storage_grid)
        scroll_layout.addWidget(storage_card)

        # --- DOLNY PANEL: AKCJE ---
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()

        self.btn_reset = QPushButton("Przywróć ustawienia domyślne")
        self.btn_reset.clicked.connect(self.reset_to_defaults)
        actions_layout.addWidget(self.btn_reset)

        scroll_layout.addLayout(actions_layout)

        self.connect_ui_signals()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        self.scan_com_ports()  # Inicjalne skanowanie
        self.load_settings_to_ui()

    def scan_com_ports(self):
        """Dynamiczne wyszukiwanie portów COM i scalanie z ustawieniami WiFi"""
        import serial.tools.list_ports
        current = self.combo_mode.currentText()

        ip = self.input_ip.text() or self.settingsmanager.get_setting("connection", "esp_ip")
        port = self.input_port.text() or self.settingsmanager.get_setting("connection", "port")
        ble_name = self.input_ble.text() or self.settingsmanager.get_setting("connection", "ble_name")

        options = [
            f"WiFi UDP — {ip}:{port}",
            f"WiFi TCP — {ip}:{port}",
            f"BLE — {ble_name}"
        ]

        ports = serial.tools.list_ports.comports()
        for p in ports:
            options.append(p.device)

        self.combo_mode.clear()
        self.combo_mode.addItems(options)

        if current in options:
            self.combo_mode.setCurrentText(current)

    def get_input_style(self, theme):
        if theme == 'dark':
            return f"""
                QLineEdit {{ border: 1px solid {config.Colors.DARK_BORDER}; border-radius: 5px; padding: 4px 10px; min-height: 20px; background-color: {config.Colors.DARK_PANEL_BG}; color: {config.Colors.DARK_TEXT_PRIMARY}; }}
                QLineEdit:hover, QLineEdit:focus {{ border: 1px solid {config.Colors.DARK_ACCENT}; }}
            """
        else:
            return f"""
                QLineEdit {{ border: 1px solid {config.Colors.LIGHT_BORDER}; border-radius: 5px; padding: 4px 10px; min-height: 20px; background-color: {config.Colors.LIGHT_PANEL_BG}; color: {config.Colors.LIGHT_TEXT_PRIMARY}; }}
                QLineEdit:hover, QLineEdit:focus {{ border: 1px solid {config.Colors.DARK_ACCENT}; }}
            """

    def update_theme(self, theme):
        style = self.get_input_style(theme)
        for w in [self.input_ip, self.input_port, self.input_ble, self.input_interval]:
            w.setStyleSheet(style)

    def connect_ui_signals(self):
        # 1. Połączenie
        self.combo_mode.currentTextChanged.connect(lambda v: self.update_config("connection", "mode", v))
        self.input_ip.textChanged.connect(lambda t: self.update_config("connection", "esp_ip", t))
        self.input_port.textChanged.connect(lambda t: self.update_config_numeric("connection", "port", t))
        self.input_ble.textChanged.connect(lambda t: self.update_config("connection", "ble_name", t))
        self.combo_format.currentTextChanged.connect(lambda v: self.update_config("connection", "packet_format", v))

        # 2. Kanały EKG
        self.check_ecg_active.stateChanged.connect(lambda s: self.update_config("channels_ecg", "active", s == 2))
        self.combo_ecg_rate.currentTextChanged.connect(
            lambda v: self.update_config("channels_ecg", "rate_hz", int(v.replace(" Hz", ""))))
        self.combo_ecg_lead.currentTextChanged.connect(lambda v: self.update_config("channels_ecg", "lead", v))

        # 3. Kanały PPG
        self.check_ppg_raw.stateChanged.connect(lambda s: self.update_config("channels_ppg", "raw_active", s == 2))
        self.check_ppg_spo2.stateChanged.connect(lambda s: self.update_config("channels_ppg", "spo2_esp32", s == 2))
        self.combo_ppg_rate.currentTextChanged.connect(
            lambda v: self.update_config("channels_ppg", "rate_hz", int(v.replace(" Hz", ""))))

        # 4. DSP
        self.check_notch.stateChanged.connect(lambda s: self.update_config("dsp", "notch_50hz", s == 2))
        self.check_bandpass.stateChanged.connect(lambda s: self.update_config("dsp", "bandpass_enabled", s == 2))
        self.check_baseline.stateChanged.connect(lambda s: self.update_config("dsp", "baseline_wander_removal", s == 2))
        # 5. Wizualizacja (zapis)
        self.combo_gain.currentTextChanged.connect(
            lambda v: self.update_config("acquisition", "gain", float(v.replace("x", ""))))
        self.combo_scale.currentTextChanged.connect(
            lambda v: self.update_config("acquisition", "y_scale_mv", float(v.replace("±", "").replace(" mV", ""))))
        self.combo_window.currentTextChanged.connect(
            lambda v: self.update_config("acquisition", "preview_window_s", float(v.replace(" s", ""))))
        # 6. Storage
        self.combo_storage_format.currentTextChanged.connect(
            lambda v: self.update_config("storage", "default_format", v))
        self.input_dir.textChanged.connect(lambda t: self.update_config("storage", "output_dir", t))
        self.input_interval.textChanged.connect(
            lambda t: self.update_config_numeric("storage", "auto_save_interval_min", t))
        self.input_retro_buffer.textChanged.connect(
            lambda t: self.update_config_numeric("storage", "retro_buffer_min", t))

    def update_config(self, category, key, value):
        if not self.loading:
            self.settingsmanager.update_setting(category, key, value)

    def update_config_numeric(self, category, key, value_str):
        if not self.loading:
            try:
                self.settingsmanager.update_setting(category, key, int(value_str))
            except ValueError:
                pass

    def load_settings_to_ui(self):
        self.loading = True
        mgr = self.settingsmanager

        # 1. Połączenie (Wpisujemy czyste, zresetowane dane w pola tekstowe)
        self.input_ip.setText(mgr.get_setting("connection", "esp_ip"))
        self.input_port.setText(str(mgr.get_setting("connection", "port")))
        self.input_ble.setText(mgr.get_setting("connection", "ble_name"))
        self.combo_format.setCurrentText(mgr.get_setting("connection", "packet_format"))

        # --- WYMUSZENIE AKTUALIZACJI LISTY POŁĄCZEŃ ---
        # Dopiero teraz, gdy pola mają domyślne wartości, przebudowujemy listę
        self.scan_com_ports()
        self.combo_mode.setCurrentText(mgr.get_setting("connection", "mode"))

        # 2. Kanały EKG
        self.check_ecg_active.setChecked(mgr.get_setting("channels_ecg", "active"))
        self.combo_ecg_rate.setCurrentText(f"{mgr.get_setting('channels_ecg', 'rate_hz')} Hz")
        self.combo_ecg_lead.setCurrentText(mgr.get_setting("channels_ecg", "lead"))

        # 3. Kanały PPG
        self.check_ppg_raw.setChecked(mgr.get_setting("channels_ppg", "raw_active"))
        self.check_ppg_spo2.setChecked(mgr.get_setting("channels_ppg", "spo2_esp32"))
        self.combo_ppg_rate.setCurrentText(f"{mgr.get_setting('channels_ppg', 'rate_hz')} Hz")

        # 4. DSP
        self.check_notch.setChecked(mgr.get_setting("dsp", "notch_50hz"))
        self.check_bandpass.setChecked(mgr.get_setting("dsp", "bandpass_enabled"))
        self.check_baseline.setChecked(mgr.get_setting("dsp", "baseline_wander_removal"))
        # 5. Wizualizacja (odczyt)
        self.combo_gain.setCurrentText(f"{mgr.get_setting('acquisition', 'gain')}x")
        self.combo_scale.setCurrentText(f"±{int(mgr.get_setting('acquisition', 'y_scale_mv'))} mV")
        self.combo_window.setCurrentText(f"{int(mgr.get_setting('acquisition', 'preview_window_s'))} s")
        # 6. Zapis plików
        self.combo_storage_format.setCurrentText(mgr.get_setting("storage", "default_format"))
        self.input_dir.setText(mgr.get_setting("storage", "output_dir"))
        self.input_interval.setText(str(mgr.get_setting("storage", "auto_save_interval_min")))
        self.input_retro_buffer.setText(str(mgr.get_setting("storage", "retro_buffer_min")))

        self.loading = False

    def reset_to_defaults(self):
        self.settingsmanager.reset_to_defaults()