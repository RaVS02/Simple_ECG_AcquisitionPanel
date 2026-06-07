from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from resources import config


class Sidebar(QFrame):
    def __init__(self, settingsmanager):
        super().__init__()
        self.setFixedWidth(220)
        self.settingsmanager = settingsmanager
        self.setObjectName("Sidebar")

        self.hover_elements = []
        self.info_labels = {}

        self.initUI()

        # Podpiecie automatycznego odswiezania danych
        self.settingsmanager.settings_changed.connect(self.refresh_data)

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- SEKCJA: TRYB PRACY ---
        self.add_section_title(layout, "STATUS SYSTEMU")
        self.info_labels['mode'] = self.add_info_row(layout, "Sygnał:", "Rozłączony")

        self.sep0 = self.add_separator(layout)
        self.hover_elements.append(self.sep0)

        # --- SEKCJA: AKWIZYCJA ---
        self.add_section_title(layout, "PARAMETRY AKWIZYCJI")
        self.info_labels['active'] = self.add_info_row(layout, "Kanały:", "---")
        self.info_labels['ecg_rate'] = self.add_info_row(layout, "EKG próbk.:", "--- Hz")
        self.info_labels['ppg_rate'] = self.add_info_row(layout, "PPG próbk.:", "--- Hz")
        self.info_labels['lead'] = self.add_info_row(layout, "Odprow.:", "---")

        self.sep1 = self.add_separator(layout)
        self.hover_elements.append(self.sep1)

        # --- SEKCJA: FILTRY DSP ---
        self.add_section_title(layout, "PRZETWARZANIE (DSP)")
        self.info_labels['notch'] = self.add_info_row(layout, "Filtr 50Hz:", "---")
        self.info_labels['bandpass'] = self.add_info_row(layout, "Pasmowy:", "---")
        self.info_labels['baseline'] = self.add_info_row(layout, "Usuw. dryfu:", "---")
        self.info_labels['spo2'] = self.add_info_row(layout, "SpO2 ESP32:", "---")
        self.update_all_styles(active=False)
        self.refresh_data()

    def add_section_title(self, layout, text):
        lbl = QLabel(text)
        lbl.setProperty("cssClass", "section-title")
        layout.addWidget(lbl)
        return lbl

    def add_info_row(self, layout, label_text, default_val):
        lbl = QLabel(f"{label_text} {default_val}")
        lbl.setStyleSheet(f"color: {config.Colors.DARK_TEXT_PRIMARY}; font-size: 10pt;")
        layout.addWidget(lbl)
        return lbl

    def add_separator(self, layout):
        line = QFrame()
        line.setObjectName("SidebarSeparator")
        layout.addWidget(line)
        return line

    def refresh_data(self):
        # Pobieranie wartości ze ZAKTUALIZOWANEJ struktury SettingsManager
        ecg_rate = self.settingsmanager.get_setting("channels_ecg", "rate_hz")
        ppg_rate = self.settingsmanager.get_setting("channels_ppg", "rate_hz")
        lead = self.settingsmanager.get_setting("channels_ecg", "lead")

        # Pobieranie statusu aktywnosci kanalow
        ecg_active = self.settingsmanager.get_setting("channels_ecg", "active")
        ppg_active = self.settingsmanager.get_setting("channels_ppg", "raw_active")

        notch = self.settingsmanager.get_setting("dsp", "notch_50hz")
        spo2_esp = self.settingsmanager.get_setting("channels_ppg", "spo2_esp32")
        bp_enabled = self.settingsmanager.get_setting("dsp", "bandpass_enabled")
        baseline = self.settingsmanager.get_setting("dsp", "baseline_wander_removal")
        # Logika budowania tekstu aktywnych kanalow
        active_str = ""
        if ecg_active and ppg_active:
            active_str = "EKG + PPG"
        elif ecg_active:
            active_str = "Tylko EKG"
        elif ppg_active:
            active_str = "Tylko PPG"
        else:
            active_str = "Brak"

        # Aktualizacja etykiet
        self.info_labels['ecg_rate'].setText(f"EKG próbk.: {ecg_rate} Hz")
        self.info_labels['ppg_rate'].setText(f"PPG próbk.: {ppg_rate} Hz")
        self.info_labels['lead'].setText(f"Odprow.: {lead}")
        self.info_labels['active'].setText(f"Kanały: {active_str}")

        self.info_labels['notch'].setText(f"Filtr 50Hz: {'wł' if notch else 'wył'}")
        self.info_labels['spo2'].setText(f"SpO2 ESP32: {'wł' if spo2_esp else 'wył'}")

        self.info_labels['bandpass'].setText(f"Pasmowy: {'wł' if bp_enabled else 'wył'}")
        self.info_labels['baseline'].setText(f"Usuw. dryfu: {'wł' if baseline else 'wył'}")

        # Zarzadzanie kolorami
        theme = self.settingsmanager.get_theme()
        text_color = config.Colors.DARK_TEXT_PRIMARY if theme == 'dark' else config.Colors.LIGHT_TEXT_PRIMARY

        for key, label in self.info_labels.items():
            if key == 'ppg_rate' and ppg_active:
                label.setStyleSheet(f"color: {config.Colors.SIGNAL_PPG}; font-size: 10pt;")
            elif key == 'ecg_rate' and ecg_active:
                label.setStyleSheet(f"color: {config.Colors.SIGNAL_ECG}; font-size: 10pt;")
            elif key in ['notch', 'spo2', 'bandpass', 'baseline'] and "wł" in label.text():
                label.setStyleSheet(f"color: {config.Colors.POSITIVE_STATUS}; font-size: 10pt;")
            else:
                label.setStyleSheet(f"color: {text_color}; font-size: 10pt;")

    def enterEvent(self, event):
        self.update_all_styles(active=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update_all_styles(active=False)
        super().leaveEvent(event)

    def update_all_styles(self, active=False):
        current_theme = self.settingsmanager.get_theme()

        if current_theme == 'dark':
            color = config.Colors.DARK_ACCENT if active else config.Colors.DARK_BORDER
        else:
            color = config.Colors.LIGHT_ACCENT if active else config.Colors.LIGHT_BORDER

        style = f"background-color: {color}; min-height: 1px; max-height: 1px; margin: 5px 0px;"
        for element in self.hover_elements:
            element.setStyleSheet(style)