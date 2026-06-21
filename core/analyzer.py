import numpy as np
from scipy.signal import butter, filtfilt, iirnotch, find_peaks, peak_widths

MEDICAL_NORMS = {
    "hr_min": 60,
    "hr_max": 100,
    "qrs_max_ms": 120,
    "qt_max_ms": 440,
    "spo2_min": 95,
    "snr_min_db": 10,
    "pi_min": 1.0,
    "r_amp_min": 0.5,
    "artifacts_max_pct": 5.0
}


class SignalAnalyzer:

    @staticmethod
    def check_norm(key, value):
        if value is None or np.isnan(value):
            return "---"

        if key == "hr":
            return "norma" if MEDICAL_NORMS["hr_min"] <= value <= MEDICAL_NORMS["hr_max"] else "uwaga"
        elif key == "qrs":
            return "norma" if value <= MEDICAL_NORMS["qrs_max_ms"] else "uwaga"
        elif key == "spo2":
            return "norma" if value >= MEDICAL_NORMS["spo2_min"] else "uwaga"
        elif key == "snr":
            return "dobry" if value >= MEDICAL_NORMS["snr_min_db"] else "slaby"
        elif key == "pi":
            return "dobry" if value >= MEDICAL_NORMS["pi_min"] else "slaby"
        elif key == "artifacts":
            return "ok" if value <= MEDICAL_NORMS["artifacts_max_pct"] else "uwaga"
        return ""

    @staticmethod
    def apply_dsp(signal, sr, settings):
        processed = np.copy(signal)

        base_order = int(settings.get("baseline_order", 2))
        band_order = int(settings.get("bandpass_order", 2))
        notch_q = settings.get("notch_q", 10.0)

        if settings.get("baseline_on", True):
            nyq = 0.5 * sr
            cutoff = settings.get("baseline_cut", 0.5) / nyq
            if 0 < cutoff < 1.0:
                b, a = butter(base_order, cutoff, btype='high', analog=False)
                processed = filtfilt(b, a, processed)

        if settings.get("notch_on", True):
            nyq = 0.5 * sr
            freq = settings.get("notch_freq", 50.0)
            if nyq > freq:
                b, a = iirnotch(freq, notch_q, sr)
                processed = filtfilt(b, a, processed)

        if settings.get("bandpass_on", True):
            nyq = 0.5 * sr
            cutoff = settings.get("bandpass_cut", 40.0) / nyq
            if 0 < cutoff < 1.0:
                b, a = butter(band_order, cutoff, btype='low', analog=False)
                processed = filtfilt(b, a, processed)

        return processed

    @staticmethod
    def calculate_fft(signal, sr):
        if len(signal) == 0:
            return np.array([]), np.array([])

        sig_no_dc = signal - np.mean(signal)
        window = np.hanning(len(sig_no_dc))
        sig_win = sig_no_dc * window

        fft_vals = np.fft.rfft(sig_win)
        fft_mag = np.abs(fft_vals) * 2.0 / len(sig_win)
        freqs = np.fft.rfftfreq(len(sig_win), 1.0 / sr)

        return freqs, fft_mag

    @staticmethod
    def analyze_ecg(time_arr, signal, sr, raw_signal=None):
        distance = int(0.25 * sr)
        height = np.mean(signal) + 0.6 * np.std(signal)

        peaks, _ = find_peaks(signal, distance=distance, height=height)

        empty_res = {
            "hr_avg": 0, "hr_min": 0, "hr_max": 0, "rr_avg": 0, "sdnn": 0,
            "qrs_dur": 0, "qt_qtc": 0, "snr": 0, "noise_50hz": 0, "artifacts_pct": 0,
            "peaks": peaks, "r_amp_avg": 0, "r_amp_min": 0, "r_amp_max": 0,
            "p_wave": 0, "t_wave": 0
        }

        if len(peaks) < 2:
            return empty_res

        rr_intervals = np.diff(time_arr[peaks]) * 1000
        hr_array = 60000.0 / rr_intervals

        hr_avg = np.mean(hr_array)
        rr_avg = np.mean(rr_intervals)
        sdnn = np.std(rr_intervals)

        peak_vals = signal[peaks]
        r_amp_avg = np.mean(peak_vals)

        results_widths = peak_widths(signal, peaks, rel_height=0.5)
        qrs_dur_ms = np.mean(results_widths[0]) * (1000.0 / sr) * 2.0

        snr_db = 0.0
        noise_50hz_db = 0.0

        if raw_signal is not None and len(raw_signal) == len(signal):
            noise = raw_signal - signal
            noise_power = np.var(noise)
            signal_power = np.var(signal)

            if noise_power > 0 and signal_power > 0:
                snr_db = 10 * np.log10(signal_power / noise_power)

            power_raw = np.var(raw_signal)
            if power_raw > 0:
                ratio = signal_power / power_raw
                noise_50hz_db = 10 * np.log10(1 - ratio) if ratio < 1 else 0

        artifacts_pct = 0.0
        if len(rr_intervals) > 0:
            bad_rr = np.sum((rr_intervals < 240) | (rr_intervals > 2000))
            artifacts_pct = (bad_rr / len(rr_intervals)) * 100.0

        t_wave_amp = r_amp_avg * 0.25
        p_wave_amp = r_amp_avg * 0.10
        qt_est = qrs_dur_ms * 2.5
        qtc_est = qt_est / np.sqrt(rr_avg / 1000.0) if rr_avg > 0 else 0

        return {
            "hr_avg": int(hr_avg),
            "hr_min": int(np.min(hr_array)),
            "hr_max": int(np.max(hr_array)),
            "rr_avg": int(rr_avg),
            "sdnn": int(sdnn),
            "qrs_dur": int(qrs_dur_ms),
            "qt_qtc": f"{int(qt_est)} / {int(qtc_est)}",
            "snr": round(snr_db, 1),
            "noise_50hz": round(noise_50hz_db, 1),
            "artifacts_pct": round(artifacts_pct, 1),
            "peaks": peaks,
            "r_amp_avg": round(r_amp_avg, 3),
            "r_amp_min": round(np.min(peak_vals), 3),
            "r_amp_max": round(np.max(peak_vals), 3),
            "p_wave": round(p_wave_amp, 3),
            "t_wave": round(t_wave_amp, 3)
        }

    @staticmethod
    def analyze_ppg(time_arr, signal, sr):
        distance = int(0.3 * sr)
        height = np.mean(signal)

        peaks, _ = find_peaks(signal, distance=distance, height=height)

        empty_res = {"hr_avg": 0, "hr_min": 0, "hr_max": 0, "peaks": peaks, "amp_avg": 0, "pi": 0, "spo2_est": 0}
        if len(peaks) < 2:
            return empty_res

        rr_intervals = np.diff(time_arr[peaks]) * 1000
        hr_array = 60000.0 / rr_intervals

        hr_avg = np.mean(hr_array)
        peak_vals = signal[peaks]
        amp_avg = np.mean(peak_vals)

        ac_comp = np.max(signal) - np.min(signal)
        dc_comp = np.mean(signal)
        pi_index = abs((ac_comp / dc_comp) * 100) if dc_comp != 0 else 0

        ratio = ac_comp / dc_comp if dc_comp != 0 else 0
        spo2_est = 110 - 25 * ratio
        spo2_est = np.clip(spo2_est, 80, 100)

        return {
            "hr_avg": int(hr_avg),
            "hr_min": int(np.min(hr_array)),
            "hr_max": int(np.max(hr_array)),
            "peaks": peaks,
            "amp_avg": round(amp_avg, 1),
            "pi": round(pi_index, 2),
            "spo2_est": round(spo2_est, 1)
        }