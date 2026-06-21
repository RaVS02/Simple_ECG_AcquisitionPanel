import json
import os
from PyQt6.QtCore import QObject, pyqtSignal

class SettingsManager(QObject):
    # Sygnał emitowany po każdej zmianie konfiguracji.
    # Pozwala na automatyczne odświeżenie UI (np. paska bocznego).
    settings_changed = pyqtSignal()

    def __init__(self, config_file="settings.json"):
        super().__init__()
        self.config_file = config_file

        # 1. Definicja domyślnych ustawień (Fallback)
        self.default_config = {
            "ui": {
                "theme": "dark"
            },
            "connection": {
                "mode": "WiFi UDP",
                "esp_ip": "192.168.1.50",
                "port": 5005,
                "ble_name": "SignalMonitor",
                "packet_format": "JSON + Base64"
            },
            "channels_ecg": {
                "active": True,
                "rate_hz": 1000,
                "lead": "II (rytm)"
            },
            "channels_ppg": {
                "raw_active": True,
                "spo2_esp32": True,
                "rate_hz": 1000  # Zgodnie z prośbą: takie same wartości jak EKG
            },
            "acquisition": {
                "gain": 1.0,
                "y_scale_mv": 2.0,
                "preview_window_s": 5.0
            },
            "dsp": {
                "notch_50hz": True,
                "bandpass_enabled": True,
                "baseline_wander_removal": True,
                "moving_average_smoothing": True
            },
            "storage": {
                "output_dir": "./data/signals",
                "default_format": "EDF",
                "auto_save_interval_min": 10,
                "retro_buffer_min": 5  # Zapis ostatnich 5 minut w tle
            }
        }

        # 2. Inicjalizacja: Wczytanie z pliku lub utworzenie nowego
        self.config = self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_file):
            self._save_config_internal(self.default_config)
            return self.default_config

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)

            merged_config = self.default_config.copy()
            for category, values in loaded_config.items():
                if category in merged_config and isinstance(values, dict):
                    merged_config[category].update(values)

            return merged_config
        except Exception as e:
            print(f"[Blad] Nie mozna odczytac {self.config_file}: {e}. Uzywam domyslnych.")
            return self.default_config

    def _save_config_internal(self, config_data):
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.config_file)), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[Blad] Nie udalo sie zapisac {self.config_file}: {e}")

    def save_settings(self):
        self._save_config_internal(self.config)
        self.settings_changed.emit()

    # ==========================================
    # GETTERY I SETTERY (API DLA APLIKACJI)
    # ==========================================

    def get_theme(self):
        return self.config["ui"]["theme"]

    def set_theme(self, new_theme):
        self.config["ui"]["theme"] = new_theme
        self.save_settings()

    def get_setting(self, category, key):
        return self.config.get(category, {}).get(key)

    def update_setting(self, category, key, value):
        if category in self.config and key in self.config[category]:
            self.config[category][key] = value
            self.save_settings()
    def reset_to_defaults(self):
        """Przywraca konfiguracje domyslna i zapisuje ja do pliku."""
        import copy
        self.config = copy.deepcopy(self.default_config)
        self.save_settings()