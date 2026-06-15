# core/signal_data.py
import numpy as np

class SignalData:
    def __init__(self):
        self.filename=""
        self.format=""

        # Oś czasu i główne sygnały
        self.time = np.array([])
        self.ecg = np.array([])
        self.ppg = np.array([])

        # Metadane
        self.sampling_rate_ecg = 0
        self.sampling_rate_ppg = 0
        self.duration_sec = 0.0

        # Flagi obecności sygnałów
        self.has_ecg = False
        self.has_ppg = False
    def is_empty(self):
        return len(self.time) == 0
    def get_filename(self):
        return self.filename
    def get_format(self):
        return self.format

    def get_summary(self):
        """Zwraca krótki tekstowy opis wczytanego pliku dla GUI"""
        if self.is_empty():
            return "Brak danych"

        channels = []
        if self.has_ecg: channels.append(f"EKG ({self.sampling_rate_ecg}Hz)")
        if self.has_ppg: channels.append(f"PPG ({self.sampling_rate_ppg}Hz)")

        m, s = divmod(int(self.duration_sec), 60)
        return f"{' + '.join(channels)} | Czas: {m}m {s}s"