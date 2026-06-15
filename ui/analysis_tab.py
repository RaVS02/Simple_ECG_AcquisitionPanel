from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QPushButton, QComboBox, QWidget, QSplitter, QScrollArea, QMessageBox, QCheckBox,
                             QDoubleSpinBox, QSpinBox)
import pyqtgraph as pg
import numpy as np
from resources import config
from core.analyzer import SignalAnalyzer, MEDICAL_NORMS


class MetricRow(QWidget):
    def __init__(self, name, default_val="---", status=""):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        self.name_lbl = QLabel(name)
        self.name_lbl.setStyleSheet(f"color: {config.Colors.DARK_TEXT_SECONDARY}; font-size: 10pt;")

        self.val_lbl = QLabel(default_val)
        self.val_lbl.setStyleSheet(f"color: {config.Colors.DARK_TEXT_PRIMARY}; font-size: 11pt; font-weight: bold;")

        self.status_lbl = QLabel(status)
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_status_style(status)

        layout.addWidget(self.name_lbl)
        layout.addStretch()
        layout.addWidget(self.val_lbl)
        layout.addSpacing(10)
        layout.addWidget(self.status_lbl)

    def set_value(self, val, status=""):
        self.val_lbl.setText(str(val))
        self.status_lbl.setText(status)
        self.set_status_style(status)

    def set_status_style(self, status):
        base_style = "font-size: 9pt; padding: 2px 6px; border-radius: 8px;"
        if status.lower() in ["norma", "ok", "dobry", "stłumione"]:
            self.status_lbl.setStyleSheet(
                f"background: {config.Colors.STATUS_OK_BG}; color: {config.Colors.STATUS_OK_TEXT}; {base_style}")
        elif status == "":
            self.status_lbl.setStyleSheet("background: transparent; color: transparent;")
        else:
            self.status_lbl.setStyleSheet(
                f"background: {config.Colors.STATUS_WARN_BG}; color: {config.Colors.STATUS_WARN_TEXT}; {base_style}")


class AnalysisTab(QFrame):
    def __init__(self, settingsmanager):
        super().__init__()
        self.setProperty("cssClass", "panel")
        self.settingsmanager = settingsmanager
        self.metrics = {}

        self.update_tick = 0
        self.TEXT_REFRESH_RATE = 20

        self.live_timer = QTimer()
        self.live_timer.timeout.connect(self.run_analysis)
        self.is_live_analyzing = False

        self.initUI()
        self.update_theme(self.settingsmanager.get_theme())
        self.on_source_changed()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- TOOLBAR GLOWNY ---
        toolbar = QFrame()
        toolbar.setProperty("cssClass", "toolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(15, 8, 15, 8)

        toolbar_layout.addWidget(QLabel("Zrodlo danych:"))
        self.source_combo = QComboBox()
        self.source_combo.addItems(["Ostatni zrzut z RAM (Live)", "Wczytany plik (SignalData)"])
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        toolbar_layout.addWidget(self.source_combo)

        toolbar_layout.addSpacing(20)

        # Opcje dla Live
        self.live_window_widget = QWidget()
        live_layout = QHBoxLayout(self.live_window_widget)
        live_layout.setContentsMargins(0, 0, 0, 0)
        live_layout.addWidget(QLabel("Okno (Live):"))
        self.window_combo = QComboBox()
        self.window_combo.addItems(["10 s", "30 s", "60 s", "Caly bufor"])
        live_layout.addWidget(self.window_combo)
        toolbar_layout.addWidget(self.live_window_widget)

        # Opcje dla Pliku
        self.file_range_widget = QWidget()
        file_layout = QHBoxLayout(self.file_range_widget)
        file_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_range = QLabel("Zakres [s]:")
        file_layout.addWidget(self.lbl_range)
        self.spin_start = QDoubleSpinBox()
        self.spin_start.setRange(0, 99999)
        self.spin_start.setSuffix(" s")
        self.spin_end = QDoubleSpinBox()
        self.spin_end.setRange(0, 99999)
        self.spin_end.setSuffix(" s")
        file_layout.addWidget(self.spin_start)
        file_layout.addWidget(QLabel("-"))
        file_layout.addWidget(self.spin_end)
        toolbar_layout.addWidget(self.file_range_widget)

        toolbar_layout.addSpacing(20)
        self.btn_analyze = QPushButton("Start Analizy Live")
        self.btn_analyze.setProperty("cssClass", "primary")
        self.btn_analyze.clicked.connect(self.toggle_analysis)
        toolbar_layout.addWidget(self.btn_analyze)

        toolbar_layout.addStretch()
        main_layout.addWidget(toolbar)

        # --- PASEK FILTROW KONFIGUROWALNYCH (GRID LAYOUT) ---
        filter_bar = QFrame()
        filter_bar.setStyleSheet(
            f"background-color: {config.Colors.DARK_CARD_BG}; border-bottom: 1px solid {config.Colors.DARK_BORDER};")
        filter_layout = QGridLayout(filter_bar)
        filter_layout.setContentsMargins(15, 6, 15, 6)
        filter_layout.setSpacing(10)

        filter_layout.addWidget(QLabel("Wlacz filtr:"), 0, 0)
        filter_layout.addWidget(QLabel("Czestotliwosc:"), 0, 1)
        filter_layout.addWidget(QLabel("Sila (Rzad / Q):"), 0, 2)

        self.chk_notch = QCheckBox("Notch")
        self.chk_notch.setChecked(True)
        self.spin_notch = QDoubleSpinBox()
        self.spin_notch.setRange(20.0, 100.0)
        self.spin_notch.setValue(50.0)
        self.spin_notch.setSuffix(" Hz")
        self.spin_notch_q = QDoubleSpinBox()
        self.spin_notch_q.setRange(0.0, 100.0)
        self.spin_notch_q.setValue(30.0)

        filter_layout.addWidget(self.chk_notch, 1, 0)
        filter_layout.addWidget(self.spin_notch, 1, 1)
        filter_layout.addWidget(self.spin_notch_q, 1, 2)

        self.chk_bandpass = QCheckBox("Low-pass")
        self.chk_bandpass.setChecked(True)
        self.spin_bandpass = QDoubleSpinBox()
        self.spin_bandpass.setRange(1.0, 250.0)
        self.spin_bandpass.setValue(40.0)
        self.spin_bandpass.setSuffix(" Hz")
        self.spin_bandpass_order = QSpinBox()
        self.spin_bandpass_order.setRange(1, 10)
        self.spin_bandpass_order.setValue(2)

        filter_layout.addWidget(self.chk_bandpass, 2, 0)
        filter_layout.addWidget(self.spin_bandpass, 2, 1)
        filter_layout.addWidget(self.spin_bandpass_order, 2, 2)

        self.chk_baseline = QCheckBox("High-pass")
        self.chk_baseline.setChecked(True)
        self.spin_baseline = QDoubleSpinBox()
        self.spin_baseline.setRange(0.01, 10.0)
        self.spin_baseline.setSingleStep(0.05)
        self.spin_baseline.setValue(0.5)
        self.spin_baseline.setSuffix(" Hz")
        self.spin_baseline_order = QSpinBox()
        self.spin_baseline_order.setRange(1, 10)
        self.spin_baseline_order.setValue(2)

        filter_layout.addWidget(self.chk_baseline, 3, 0)
        filter_layout.addWidget(self.spin_baseline, 3, 1)
        filter_layout.addWidget(self.spin_baseline_order, 3, 2)

        # CHECKBOX DO POKAZYWANIA FFT
        self.chk_show_fft = QCheckBox("Pokaz FFT (EKG)")
        self.chk_show_fft.setChecked(False)
        self.chk_show_fft.stateChanged.connect(self.toggle_fft_visibility)
        filter_layout.addWidget(self.chk_show_fft, 1, 3)

        main_layout.addWidget(filter_bar)

        # --- SPLITTER ---
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background-color: transparent; height: 10px; }")
        splitter.setChildrenCollapsible(False)

        # 1. WYKRESY
        self.graphs_widget = pg.GraphicsLayoutWidget()

        self.plot_ecg = self.graphs_widget.addPlot(title="EKG - Analiza (Przefiltrowane)")
        self.plot_ecg.setLabel('left', 'Amplituda', units='mV')
        self.graphs_widget.nextRow()

        self.plot_ppg = self.graphs_widget.addPlot(title="PPG - Analiza (Przefiltrowane)")
        self.plot_ppg.setLabel('left', 'Sygnal', units='ADC')
        self.plot_ppg.setXLink(self.plot_ecg)
        self.graphs_widget.nextRow()

        self.plot_fft = self.graphs_widget.addPlot(title="Widmo Amplitudowe FFT (EKG)")
        self.plot_fft.setLabel('left', 'Amplituda')
        self.plot_fft.setLabel('bottom', 'Czestotliwosc', units='Hz')
        self.plot_fft.setVisible(False)

        self.ecg_curve = self.plot_ecg.plot(pen=pg.mkPen(color=config.Colors.SIGNAL_ECG, width=1.5))
        self.ppg_curve = self.plot_ppg.plot(pen=pg.mkPen(color=config.Colors.SIGNAL_PPG, width=1.5))
        self.fft_curve = self.plot_fft.plot(pen=pg.mkPen(color=config.Colors.ANALYSIS_ACCENT, width=1.5))

        self.ecg_peaks = pg.ScatterPlotItem(size=8, pen=pg.mkPen(None), brush=pg.mkBrush(255, 68, 85, 200))
        self.ppg_peaks = pg.ScatterPlotItem(size=8, pen=pg.mkPen(None), brush=pg.mkBrush(0, 212, 170, 200))
        self.plot_ecg.addItem(self.ecg_peaks)
        self.plot_ppg.addItem(self.ppg_peaks)

        # 2. KARTY WYNIKOW
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("AnalysisScroll")
        scroll.setStyleSheet("#AnalysisScroll { border: none; background: transparent; }")

        scroll_content = QWidget()
        scroll_content.setObjectName("AnalysisContent")
        scroll_content.setStyleSheet("#AnalysisContent { background: transparent; }")

        cards_layout = QGridLayout(scroll_content)
        cards_layout.setContentsMargins(15, 15, 15, 15)
        cards_layout.setSpacing(15)

        card_ecg_time = self._create_card("EKG - PARAMETRY CZASOWE", config.Colors.SIGNAL_ECG)
        self._add_metric(card_ecg_time, "hr_ecg", "HR srednie", "--- bpm", "")
        self._add_metric(card_ecg_time, "hr_ecg_minmax", "HR min/max", "--- / ---", "")
        self._add_metric(card_ecg_time, "rr_avg", "RR srednie", "--- ms", "")
        self._add_metric(card_ecg_time, "sdnn", "SDNN (HRV)", "--- ms", "")
        self._add_metric(card_ecg_time, "qrs_dur", "QRS czas (estymacja)", "--- ms", "")
        self._add_metric(card_ecg_time, "qt_qtc", "QT / QTc (estymacja)", "--- / --- ms", "")
        cards_layout.addWidget(card_ecg_time, 0, 0)

        card_ppg = self._create_card("PPG / SPO2 - MAX30102", config.Colors.SIGNAL_PPG)
        self._add_metric(card_ppg, "spo2_avg", "SpO2 (estymacja algorytmiczna)", "--- %", "")
        self._add_metric(card_ppg, "hr_ppg", "HR (PPG)", "--- bpm", "")
        self._add_metric(card_ppg, "pi_index", "PI (Perf. Index)", "--- %", "")
        self._add_metric(card_ppg, "amp_ir", "Amplituda Sygnalu", "--- ADC", "")
        cards_layout.addWidget(card_ppg, 0, 1)

        card_quality = self._create_card("JAKOSC SYGNALU", config.Colors.DARK_TEXT_PRIMARY)
        self._add_metric(card_quality, "snr_ecg", "SNR EKG", "--- dB", "")
        self._add_metric(card_quality, "art_ecg", "Artefakty EKG", "--- %", "")
        self._add_metric(card_quality, "noise_50hz", "Odfiltrowany szum 50Hz", "--- dB", "")
        cards_layout.addWidget(card_quality, 1, 0)

        card_ecg_amp = self._create_card("EKG - AMPLITUDY", config.Colors.SIGNAL_ECG)
        self._add_metric(card_ecg_amp, "r_amp", "Pik R (sr.)", "--- mV", "")
        self._add_metric(card_ecg_amp, "p_wave", "Fala P (est.)", "--- mV", "")
        self._add_metric(card_ecg_amp, "t_wave", "Fala T (est.)", "--- mV", "")
        cards_layout.addWidget(card_ecg_amp, 1, 1)

        scroll.setWidget(scroll_content)
        splitter.addWidget(self.graphs_widget)
        splitter.addWidget(scroll)
        splitter.setSizes([300, 400])
        main_layout.addWidget(splitter)

    def _create_card(self, title, title_color):
        card = QFrame()
        card.setProperty("cssClass", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 12, 15, 12)
        lbl = QLabel(title)
        lbl.setStyleSheet(
            f"color: {title_color}; font-size: 10pt; font-weight: bold; text-transform: uppercase; margin-bottom: 5px;")
        layout.addWidget(lbl)
        return card

    def _add_metric(self, card, key, name, default_val, status):
        row = MetricRow(name, default_val, status)
        self.metrics[key] = row
        card.layout().addWidget(row)

    def update_file_range_limits(self):
        main_window = self.window()
        if not hasattr(main_window, 'tabs'): return
        files_tab = main_window.tabs['files']
        sig = files_tab.current_signal
        if sig and not sig.is_empty():
            max_dur = sig.duration_sec
            self.lbl_range.setText(f"Zakres [s] (Max: {max_dur:.1f}s):")
            self.spin_start.setRange(0.0, max_dur)
            self.spin_end.setRange(0.0, max_dur)
            if self.spin_end.value() == 0.0 or self.spin_end.value() > max_dur:
                self.spin_end.setValue(max_dur)
        else:
            self.lbl_range.setText("Zakres [s]:")

    def on_source_changed(self):
        if self.source_combo.currentIndex() == 0:
            self.live_window_widget.setVisible(True)
            self.file_range_widget.setVisible(False)
            self.btn_analyze.setText("Start Analizy Live")
            self.is_live_analyzing = False
            self.live_timer.stop()
        else:
            self.live_window_widget.setVisible(False)
            self.file_range_widget.setVisible(True)
            self.btn_analyze.setText("Analizuj wczytany plik")
            self.is_live_analyzing = False
            self.live_timer.stop()
            self.update_file_range_limits()

    def toggle_fft_visibility(self):
        is_visible = self.chk_show_fft.isChecked()
        self.plot_fft.setVisible(is_visible)
        if is_visible and not self.is_live_analyzing:
            self.run_analysis()

    def toggle_analysis(self):
        if self.source_combo.currentIndex() == 0:
            if self.is_live_analyzing:
                self.is_live_analyzing = False
                self.live_timer.stop()
                self.btn_analyze.setText("Start Analizy Live")
                self.btn_analyze.setProperty("cssClass", "primary")
            else:
                self.is_live_analyzing = True
                self.update_tick = 0
                self.live_timer.start(50)
                self.btn_analyze.setText("Stop Analizy Live")
                self.btn_analyze.setProperty("cssClass", "danger")

            self.btn_analyze.style().unpolish(self.btn_analyze)
            self.btn_analyze.style().polish(self.btn_analyze)
        else:
            self.update_tick = 0
            self.run_analysis()

    def run_analysis(self):
        main_window = self.window()
        if not hasattr(main_window, 'tabs'):
            return

        live_tab = main_window.tabs['live']
        files_tab = main_window.tabs['files']
        gain = float(self.settingsmanager.get_setting("acquisition", "gain") or 1.0)

        source_idx = self.source_combo.currentIndex()
        time_arr = None
        ecg_raw = None
        ppg_raw = None
        sr = 1000

        if source_idx == 0:
            if not live_tab.retro_buffer:
                if not self.is_live_analyzing:
                    QMessageBox.warning(self, "Brak danych", "Bufor RAM jest pusty.")
                return

            sr = live_tab.sampling_rate
            data = list(live_tab.retro_buffer)

            if self.window_combo.currentText() != "Caly bufor":
                seconds = int(self.window_combo.currentText().replace(" s", ""))
                samples_to_take = seconds * sr
                data = data[-samples_to_take:]

            ecg_raw = np.array([r[0] for r in data]) * gain
            ppg_raw = np.array([r[1] for r in data]) * gain

            total_samples = getattr(live_tab, 'total_samples', len(data))
            end_time = total_samples / sr
            start_time = end_time - (len(data) / sr)
            time_arr = np.linspace(start_time, end_time, len(data), endpoint=False)

        else:
            sig = files_tab.current_signal
            if not sig or sig.is_empty():
                QMessageBox.warning(self, "Brak danych", "Wczytaj najpierw plik w zakładce Wczytaj plik.")
                return

            self.update_file_range_limits()
            time_arr = sig.time

            start_s = self.spin_start.value()
            end_s = self.spin_end.value()
            mask = (time_arr >= start_s) & (time_arr <= end_s)
            time_arr = time_arr[mask]

            if sig.has_ecg:
                ecg_raw = sig.ecg[mask] * gain
                sr = sig.sampling_rate_ecg
            if sig.has_ppg:
                ppg_raw = sig.ppg[mask] * gain
                if not sig.has_ecg: sr = sig.sampling_rate_ppg

        dsp_settings = {
            "notch_on": self.chk_notch.isChecked(),
            "notch_freq": self.spin_notch.value(),
            "notch_q": self.spin_notch_q.value(),
            "bandpass_on": self.chk_bandpass.isChecked(),
            "bandpass_cut": self.spin_bandpass.value(),
            "bandpass_order": self.spin_bandpass_order.value(),
            "baseline_on": self.chk_baseline.isChecked(),
            "baseline_cut": self.spin_baseline.value(),
            "baseline_order": self.spin_baseline_order.value()
        }

        update_text = (source_idx != 0) or (self.update_tick % self.TEXT_REFRESH_RATE == 0)

        if ecg_raw is not None and np.any(ecg_raw):
            ecg_filtered = SignalAnalyzer.apply_dsp(ecg_raw, sr, dsp_settings)
            self.ecg_curve.setData(time_arr, ecg_filtered)

            if update_text:
                res_ecg = SignalAnalyzer.analyze_ecg(time_arr, ecg_filtered, sr, raw_signal=ecg_raw)

                self.metrics["hr_ecg"].set_value(f"{res_ecg['hr_avg']} bpm",
                                                 SignalAnalyzer.check_norm("hr", res_ecg['hr_avg']))
                self.metrics["hr_ecg_minmax"].set_value(f"{res_ecg['hr_min']} / {res_ecg['hr_max']}")
                self.metrics["rr_avg"].set_value(f"{res_ecg['rr_avg']} ms", "norma")
                self.metrics["sdnn"].set_value(f"{res_ecg['sdnn']} ms", "norma")
                self.metrics["qrs_dur"].set_value(f"{res_ecg['qrs_dur']} ms",
                                                  SignalAnalyzer.check_norm("qrs", res_ecg['qrs_dur']))
                self.metrics["qt_qtc"].set_value(res_ecg['qt_qtc'], "norma")

                self.metrics["r_amp"].set_value(f"{res_ecg['r_amp_avg']} mV", "norma")
                self.metrics["p_wave"].set_value(f"{res_ecg['p_wave']} mV", "norma")
                self.metrics["t_wave"].set_value(f"{res_ecg['t_wave']} mV", "norma")

                self.metrics["snr_ecg"].set_value(f"{res_ecg['snr']} dB",
                                                  SignalAnalyzer.check_norm("snr", res_ecg['snr']))
                self.metrics["art_ecg"].set_value(f"{res_ecg['artifacts_pct']} %",
                                                  SignalAnalyzer.check_norm("artifacts", res_ecg['artifacts_pct']))
                self.metrics["noise_50hz"].set_value(f"{res_ecg['noise_50hz']} dB", "stlumione")

                peak_times = time_arr[res_ecg["peaks"]]
                peak_vals = ecg_filtered[res_ecg["peaks"]]
                self.ecg_peaks.setData(peak_times, peak_vals)

                if self.chk_show_fft.isChecked():
                    freqs, fft_mag = SignalAnalyzer.calculate_fft(ecg_filtered, sr)
                    self.fft_curve.setData(freqs, fft_mag)
                    self.plot_fft.setXRange(0, 100, padding=0)
        else:
            self.ecg_curve.setData([], [])
            self.ecg_peaks.setData([], [])
            self.fft_curve.setData([], [])

        if ppg_raw is not None and np.any(ppg_raw):
            ppg_filtered = SignalAnalyzer.apply_dsp(ppg_raw, sr, dsp_settings)
            ppg_filtered = -ppg_filtered
            self.ppg_curve.setData(time_arr, ppg_filtered)

            if update_text:
                res_ppg = SignalAnalyzer.analyze_ppg(time_arr, ppg_filtered, sr)

                self.metrics["hr_ppg"].set_value(f"{res_ppg['hr_avg']} bpm",
                                                 SignalAnalyzer.check_norm("hr", res_ppg['hr_avg']))
                self.metrics["amp_ir"].set_value(f"{res_ppg['amp_avg']}", "")
                self.metrics["pi_index"].set_value(f"{res_ppg['pi']} %", SignalAnalyzer.check_norm("pi", res_ppg['pi']))
                self.metrics["spo2_avg"].set_value(f"{res_ppg['spo2_est']} %",
                                                   SignalAnalyzer.check_norm("spo2", res_ppg['spo2_est']))

                peak_times = time_arr[res_ppg["peaks"]]
                peak_vals = ppg_filtered[res_ppg["peaks"]]
                self.ppg_peaks.setData(peak_times, peak_vals)
        else:
            self.ppg_curve.setData([], [])
            self.ppg_peaks.setData([], [])

        if source_idx == 0:
            if time_arr is not None and len(time_arr) > 0:
                latest_ts = time_arr[-1]
                window_len = time_arr[-1] - time_arr[0]
                self.plot_ecg.getViewBox().setXRange(latest_ts - window_len, latest_ts, padding=0)
                self.plot_ppg.getViewBox().setXRange(latest_ts - window_len, latest_ts, padding=0)
        else:
            self.plot_ecg.getViewBox().autoRange()
            self.plot_ppg.getViewBox().autoRange()
            if self.chk_show_fft.isChecked():
                self.plot_fft.getViewBox().autoRange()

        self.update_tick += 1

    def update_theme(self, theme):
        is_dark = theme == 'dark'
        bg_color = config.Colors.DARK_BACKGROUND if is_dark else config.Colors.LIGHT_BACKGROUND
        label_color = config.Colors.DARK_TEXT_SECONDARY if is_dark else config.Colors.LIGHT_TEXT_SECONDARY
        grid_alpha = 0.3 if is_dark else 0.2

        self.graphs_widget.setBackground(bg_color)
        for plot in [self.plot_ecg, self.plot_ppg, self.plot_fft]:
            plot.getAxis('left').setPen(label_color)
            plot.getAxis('left').setTextPen(label_color)
            plot.getAxis('bottom').setPen(label_color)
            plot.getAxis('bottom').setTextPen(label_color)
            plot.setTitle(plot.titleLabel.text, color=label_color, size="10pt")
            plot.showGrid(x=True, y=True, alpha=grid_alpha)

        widgets_to_polish = [
            self.source_combo, self.window_combo, self.spin_notch,
            self.spin_notch_q, self.spin_bandpass, self.spin_bandpass_order,
            self.spin_baseline, self.spin_baseline_order,
            self.spin_start, self.spin_end
        ]
        for w in widgets_to_polish:
            w.style().unpolish(w)
            w.style().polish(w)
            w.update()