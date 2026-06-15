# core/file_parser.py
import os
import json
import pandas as pd
import numpy as np
from core.signal_data import SignalData


class FileParser:
    @staticmethod
    def load_file(filepath):
        ext = os.path.splitext(filepath)[1].lower()

        if ext == '.csv':
            return FileParser._load_csv(filepath)
        elif ext == '.json':
            return FileParser._load_json(filepath)
        elif ext == '.edf':
            return FileParser._load_edf(filepath)
        elif ext == '.hea':
            return FileParser._load_wfdb(filepath)
        else:
            raise ValueError(f"Nieobsługiwany format pliku: {ext}")

    @staticmethod
    def _load_csv(filepath):
        data = SignalData()
        data.filename = os.path.basename(filepath)
        data.format = "CSV"

        df = pd.read_csv(filepath)
        time_col = [c for c in df.columns if "Czas" in c]
        ecg_col = [c for c in df.columns if "EKG" in c]
        ppg_col = [c for c in df.columns if "PPG" in c]

        if time_col:
            data.time = df[time_col[0]].to_numpy()
            data.duration_sec = data.time[-1] - data.time[0] if len(data.time) > 0 else 0
            if len(data.time) > 1:
                avg_dt = np.mean(np.diff(data.time))
                if avg_dt > 0:
                    sr = int(round(1.0 / avg_dt))
                    data.sampling_rate_ecg = sr
                    data.sampling_rate_ppg = sr

        if ecg_col:
            data.ecg = df[ecg_col[0]].to_numpy()
            data.has_ecg = True
        if ppg_col:
            data.ppg = df[ppg_col[0]].to_numpy()
            data.has_ppg = True

        return data

    @staticmethod
    def _load_json(filepath):
        data = SignalData()
        data.filename = os.path.basename(filepath)
        data.format = "JSON"

        with open(filepath, 'r') as f:
            j_data = json.load(f)

        meta = j_data.get("metadata", {})
        sigs = j_data.get("signals", {})
        sr = meta.get("sampling_rate", 1000)

        data.sampling_rate_ecg = sr
        data.sampling_rate_ppg = sr

        if "ECG" in sigs:
            data.ecg = np.array(sigs["ECG"])
            data.has_ecg = True
            data.time = np.arange(len(data.ecg)) / sr

        if "PPG" in sigs:
            data.ppg = np.array(sigs["PPG"])
            data.has_ppg = True
            if not data.has_ecg: data.time = np.arange(len(data.ppg)) / sr

        data.duration_sec = len(data.time) / sr if sr > 0 else 0
        return data

    @staticmethod
    def _load_edf(filepath):
        import pyedflib
        data = SignalData()
        data.filename = os.path.basename(filepath)
        data.format = "EDF"

        f = pyedflib.EdfReader(filepath)
        signal_labels = f.getSignalLabels()

        for i in range(f.signals_in_file):
            label = signal_labels[i].upper()
            sig = f.readSignal(i)
            sr = f.getSampleFrequency(i)

            if "ECG" in label or "EKG" in label:
                data.ecg = sig
                data.sampling_rate_ecg = sr
                data.has_ecg = True
            elif "PPG" in label:
                data.ppg = sig
                data.sampling_rate_ppg = sr
                data.has_ppg = True

        f.close()

        # Oś czasu na podstawie sygnału o najwyższym próbkowaniu
        sr_main = data.sampling_rate_ecg if data.has_ecg else data.sampling_rate_ppg
        length = len(data.ecg) if data.has_ecg else len(data.ppg)
        if sr_main > 0:
            data.time = np.arange(length) / sr_main
            data.duration_sec = length / sr_main

        return data

    @staticmethod
    def _load_wfdb(filepath):
        import wfdb
        data = SignalData()

        # WFDB zawsze wymaga samej nazwy rekordu, bez żadnego rozszerzenia
        if filepath.endswith('.hea'):
            record_name = filepath[:-4]
        else:
            record_name = filepath

        data.filename = os.path.basename(record_name)
        data.format = "WFDB"

        record = wfdb.rdrecord(record_name)
        sr = record.fs
        data.time = np.arange(record.sig_len) / sr
        data.duration_sec = record.sig_len / sr

        for i, name in enumerate([n.upper() for n in record.sig_name]):
            if "ECG" in name or "EKG" in name:
                data.ecg = record.p_signal[:, i]
                data.sampling_rate_ecg = sr
                data.has_ecg = True
            elif "PPG" in name:
                data.ppg = record.p_signal[:, i]
                data.sampling_rate_ppg = sr
                data.has_ppg = True

        return data