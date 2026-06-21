import os
import numpy as np
import scipy.signal
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QPushButton, QComboBox, QWidget, QSplitter,
                             QListWidget, QListWidgetItem, QProgressBar, QMessageBox, QCheckBox, QDoubleSpinBox)
import pyqtgraph as pg
from resources import config
from core.analyzer import SignalAnalyzer

try:
    import torch
    import torch.nn.functional as F

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class DLInferenceWorker(QThread):
    progress = pyqtSignal(int)
    log_msg = pyqtSignal(str)
    result_ready = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, signal_ecg, signal_ppg, sr_ecg, sr_ppg, model_path, architecture, ae_threshold):
        super().__init__()
        self.signal_ecg = signal_ecg
        self.signal_ppg = signal_ppg
        self.sr_ecg = sr_ecg
        self.sr_ppg = sr_ppg

        self.model_path = model_path
        self.architecture = architecture
        self.ae_threshold = ae_threshold

        self.target_window_s = 10.0
        self.target_sr = 500
        self.gain_multiplier = 1.0
        self.overlap_s = 2.0

        self.running = True

    def run(self):
        if not TORCH_AVAILABLE:
            self.error.emit("Brak biblioteki PyTorch! Zainstaluj ja w srodowisku.")
            return

        try:
            self.log_msg.emit(f"Przygotowanie srodowiska. Oczekiwane okno: 10s, {self.target_sr} Hz")

            real_model = None

            # Wczytanie surowego slownika wag
            state_dict = torch.load(self.model_path, map_location=torch.device('cpu'), weights_only=False)
            sd_raw = state_dict.get("model_state_dict", state_dict)

            # CZYSZCZENIE KLUCZY (Usuwa _orig_mod.)
            sd = {}
            for k, v in sd_raw.items():
                clean_k = k.replace("_orig_mod.", "").replace("module.", "")
                sd[clean_k] = v

            # DYNAMICZNE WYKRYWANIE LICZBY KLAS
            n_classes_detected = 8
            for key in list(sd.keys()):
                if key.endswith("classifier.4.weight") or key.endswith("dense.weight") or key.endswith("final.weight"):
                    n_classes_detected = sd[key].shape[0]
                    break

            in_channels_detected = 1
            for key in ["stem.0.weight", "first_conv.conv.weight", "enc_ppg.conv_layers.0.block.0.weight"]:
                if key in sd:
                    in_channels_detected = sd[key].shape[1]
                    break

            use_bn_detected = any("first_bn.weight" in k or "bn1.weight" in k for k in sd.keys())

            fname_lower = os.path.basename(self.model_path).lower()
            if n_classes_detected == 2 or "binary" in fname_lower:
                class_names = ["NORM", "ANORM"]
                normal_classes = ["NORM"]
            elif n_classes_detected == 5 or "arrhythmia" in fname_lower:
                class_names = ["SBRAD", "SR", "STACH", "AFLT", "SARRH"]
                normal_classes = ["SR"]
            else:
                class_names = [f"Klasa {i}" for i in range(n_classes_detected)]
                normal_classes = ["Klasa 0"]

            try:
                if "CustomECGNet" in self.architecture:
                    from models.architectures.custom_network import CustomECGNet
                    real_model = CustomECGNet(in_channels=in_channels_detected, n_classes=n_classes_detected)

                elif "Net1D" in self.architecture:
                    from models.architectures.ecg_net1d import Net1D
                    real_model = Net1D(in_channels=in_channels_detected, base_filters=64, ratio=1,
                                       filter_list=[64, 160, 160, 400, 400, 1024, 1024],
                                       m_blocks_list=[2, 2, 2, 3, 3, 4, 4], kernel_size=16,
                                       stride=2, groups_width=16, n_classes=n_classes_detected,
                                       verbose=False, use_bn=use_bn_detected, use_do=False)

                elif "Autoencoder" in self.architecture:
                    if "vae" in fname_lower:
                        from models.architectures.anomaly_autoencoder import build_multimodal_vae
                        real_model = build_multimodal_vae(kl_weight=0.001)
                    else:
                        from models.architectures.anomaly_autoencoder import build_multimodal_autoencoder
                        real_model = build_multimodal_autoencoder()

                # --- SHAPE MATCHING FILTER (Omijanie Size Mismatch) ---
                model_state = real_model.state_dict()
                filtered_sd = {}
                mismatched_keys = 0
                for k, v in sd.items():
                    if k in model_state:
                        if v.shape == model_state[k].shape:
                            filtered_sd[k] = v
                        else:
                            mismatched_keys += 1
                    else:
                        filtered_sd[k] = v

                real_model.load_state_dict(filtered_sd, strict=False)
                real_model.eval()

                info_msg = f"Zaladowano: {self.architecture.split()[0]} ({in_channels_detected} kanały)."
                if mismatched_keys > 0:
                    info_msg += f" [Pominieto {mismatched_keys} niezgodnych wag]"
                self.log_msg.emit(info_msg)

            except Exception as e:
                err_str = str(e).split('\n')[0]
                self.log_msg.emit(f"Blad ladowania: {err_str[:60]}... -> SYMULACJA")
                real_model = None

            window_samples_original = int(self.target_window_s * self.sr_ecg)
            step_samples_original = int((self.target_window_s - self.overlap_s) * self.sr_ecg)
            total_samples = len(self.signal_ecg)

            results = []
            num_windows = (total_samples - window_samples_original) // step_samples_original + 1
            if num_windows <= 0: num_windows = 1

            for i in range(num_windows):
                if not self.running: break

                start_idx = i * step_samples_original
                end_idx = start_idx + window_samples_original

                if end_idx > total_samples:
                    end_idx = total_samples
                    start_idx = max(0, end_idx - window_samples_original)

                chunk_ecg = self.signal_ecg[start_idx:end_idx]
                chunk_ecg = np.nan_to_num(chunk_ecg, nan=0.0, posinf=0.0, neginf=0.0)

                chunk_ppg = None
                if "Autoencoder" in self.architecture and self.signal_ppg is not None:
                    start_t = start_idx / self.sr_ecg
                    end_t = end_idx / self.sr_ecg
                    start_idx_ppg = int(start_t * self.sr_ppg)
                    end_idx_ppg = int(end_t * self.sr_ppg)
                    chunk_ppg = self.signal_ppg[start_idx_ppg:end_idx_ppg]
                    chunk_ppg = np.nan_to_num(chunk_ppg, nan=0.0, posinf=0.0, neginf=0.0)

                target_length = int(self.target_window_s * self.target_sr)

                if len(chunk_ecg) > 0:
                    if self.sr_ecg != self.target_sr:
                        chunk_ecg_proc = scipy.signal.resample(chunk_ecg, target_length)
                    else:
                        chunk_ecg_proc = chunk_ecg

                    chunk_ecg_proc = chunk_ecg_proc * self.gain_multiplier
                    tensor_ecg = torch.tensor(chunk_ecg_proc, dtype=torch.float32).unsqueeze(0).unsqueeze(0)

                    if in_channels_detected > 1:
                        tensor_ecg = tensor_ecg.repeat(1, in_channels_detected, 1)

                    tensor_ppg = None
                    if chunk_ppg is not None and len(chunk_ppg) > 0:
                        if self.sr_ppg != self.target_sr:
                            chunk_ppg_proc = scipy.signal.resample(chunk_ppg, target_length)
                        else:
                            chunk_ppg_proc = chunk_ppg
                        chunk_ppg_proc = chunk_ppg_proc * self.gain_multiplier
                        tensor_ppg = torch.tensor(chunk_ppg_proc, dtype=torch.float32).unsqueeze(0).unsqueeze(0)

                    if real_model is not None:
                        with torch.no_grad():
                            if "Autoencoder" in self.architecture and tensor_ppg is not None:
                                error = real_model.reconstruction_error(tensor_ppg, tensor_ecg, mode='sum')
                                err_val = error.item()

                                is_anom = err_val > self.ae_threshold
                                label = "Anomalia (V-AE)" if is_anom else "Normalny (V-AE)"
                                conf_val = min((err_val / max(self.ae_threshold, 0.001)) * 0.5, 0.99) if is_anom else (
                                            1.0 - min(err_val / max(self.ae_threshold, 0.001), 1.0))
                                is_anomaly_flag = is_anom

                            else:
                                logits = real_model(tensor_ecg)
                                probs = torch.sigmoid(logits).squeeze(0)

                                active_indices = (probs > 0.5).nonzero(as_tuple=True)[0]

                                if len(active_indices) > 0:
                                    detected_labels = [class_names[idx] for idx in active_indices if
                                                       idx < len(class_names)]
                                    label = " + ".join(detected_labels)
                                    conf_val = probs[active_indices[0]].item()
                                else:
                                    conf_val, pred_idx = torch.max(probs, dim=0)
                                    idx_val = pred_idx.item()
                                    label = class_names[idx_val] if idx_val < len(class_names) else f"Klasa {idx_val}"

                                is_anomaly_flag = any(c not in normal_classes for c in label.split(" + "))

                    else:
                        is_anomaly_flag = np.random.rand() > 0.90
                        label = "Arytmia (SYM)" if is_anomaly_flag else "Normalny (SYM)"
                        conf_val = np.random.uniform(0.6, 0.99)

                    results.append({
                        "start_s": start_idx / self.sr_ecg,
                        "end_s": end_idx / self.sr_ecg,
                        "label": label,
                        "conf": conf_val,
                        "is_anomaly": is_anomaly_flag
                    })

                prog = int(((i + 1) / num_windows) * 100)
                self.progress.emit(prog)

            self.result_ready.emit(results)

        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self.running = False


class DeepLearningTab(QFrame):
    def __init__(self, settingsmanager):
        super().__init__()
        self.settingsmanager = settingsmanager
        self.setProperty("cssClass", "panel")

        self.worker = None
        self.anomaly_regions = []

        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        toolbar = QFrame()
        toolbar.setProperty("cssClass", "toolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(15, 8, 15, 8)

        toolbar_layout.addWidget(QLabel("Architektura:"))
        self.combo_arch = QComboBox()
        self.combo_arch.addItems([
            "CustomECGNet (Klasyfikacja CNN)",
            "Net1D (ECGFounder)",
            "Autoencoder (Detekcja Anomalii)"
        ])
        self.combo_arch.currentIndexChanged.connect(self.refresh_models_list)
        toolbar_layout.addWidget(self.combo_arch)

        toolbar_layout.addSpacing(15)

        toolbar_layout.addWidget(QLabel("Wagi modelu (.pth):"))
        self.combo_models = QComboBox()
        toolbar_layout.addWidget(self.combo_models)

        self.btn_refresh = QPushButton("Odswiez")
        self.btn_refresh.clicked.connect(self.refresh_models_list)
        toolbar_layout.addWidget(self.btn_refresh)

        toolbar_layout.addSpacing(20)

        self.chk_use_filtered = QCheckBox("Uzyj przefiltrowanego sygnalu")
        self.chk_use_filtered.setChecked(False)
        toolbar_layout.addWidget(self.chk_use_filtered)

        toolbar_layout.addSpacing(15)

        toolbar_layout.addWidget(QLabel("Prog bledu (Autoencoder):"))
        self.spin_ae_thresh = QDoubleSpinBox()
        self.spin_ae_thresh.setRange(0.001, 10.0)
        self.spin_ae_thresh.setSingleStep(0.01)
        self.spin_ae_thresh.setValue(0.05)
        self.spin_ae_thresh.setFixedWidth(60)
        toolbar_layout.addWidget(self.spin_ae_thresh)

        toolbar_layout.addSpacing(20)

        self.btn_analyze = QPushButton("Uruchom klasyfikacje")
        self.btn_analyze.setProperty("cssClass", "primary")
        self.btn_analyze.clicked.connect(self.start_analysis)
        toolbar_layout.addWidget(self.btn_analyze)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedWidth(150)
        self.progress_bar.setVisible(False)
        toolbar_layout.addWidget(self.progress_bar)

        toolbar_layout.addStretch()
        main_layout.addWidget(toolbar)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background-color: transparent; height: 10px; }")
        splitter.setChildrenCollapsible(False)

        self.graphs_widget = pg.GraphicsLayoutWidget()
        self.plot_ecg = self.graphs_widget.addPlot(title="Sygnal EKG (Detekcja Deep Learning)")
        self.plot_ecg.setLabel('left', 'Amplituda', units='mV')
        self.plot_ecg.setLabel('bottom', 'Czas', units='s')

        self.ecg_curve = self.plot_ecg.plot(pen=pg.mkPen(color=config.Colors.SIGNAL_ECG, width=1.5))

        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(15, 10, 15, 15)

        log_frame = QFrame()
        log_frame.setProperty("cssClass", "card")
        log_layout = QVBoxLayout(log_frame)

        lbl_log = QLabel("WYNIKI KLASYFIKACJI (Kliknij wpis, aby przyblizyc)")
        lbl_log.setStyleSheet(f"color: {config.Colors.DARK_TEXT_SECONDARY}; font-size: 9pt; font-weight: bold;")
        log_layout.addWidget(lbl_log)

        self.log_list = QListWidget()
        self.log_list.itemClicked.connect(self.on_log_clicked)
        log_layout.addWidget(self.log_list)

        bottom_layout.addWidget(log_frame, stretch=2)

        stats_frame = QFrame()
        stats_frame.setProperty("cssClass", "card")
        stats_layout = QVBoxLayout(stats_frame)

        lbl_stats = QLabel("PODSUMOWANIE ANALIZY")
        lbl_stats.setStyleSheet(f"color: {config.Colors.DARK_TEXT_SECONDARY}; font-size: 9pt; font-weight: bold;")
        stats_layout.addWidget(lbl_stats)

        self.lbl_total_windows = QLabel("Przeanalizowane fragmenty (10s): 0")
        self.lbl_total_windows.setStyleSheet(f"color: {config.Colors.DARK_TEXT_PRIMARY}; font-size: 11pt;")

        self.lbl_anomalies = QLabel("Wykryte Anomalie: 0")
        self.lbl_anomalies.setStyleSheet(f"color: {config.Colors.HEART_COLOR}; font-size: 11pt; font-weight: bold;")

        self.lbl_status = QLabel("Oczekuje na start...")
        self.lbl_status.setStyleSheet(f"color: {config.Colors.DARK_TEXT_MUTED}; font-size: 10pt; margin-top: 10px;")

        stats_layout.addWidget(self.lbl_total_windows)
        stats_layout.addWidget(self.lbl_anomalies)
        stats_layout.addWidget(self.lbl_status)
        stats_layout.addStretch()

        bottom_layout.addWidget(stats_frame, stretch=1)

        splitter.addWidget(self.graphs_widget)
        splitter.addWidget(bottom_panel)
        splitter.setSizes([350, 250])
        main_layout.addWidget(splitter)

        self.update_theme(self.settingsmanager.get_theme())
        self.refresh_models_list()

    def refresh_models_list(self):
        self.combo_models.clear()
        weights_dir = "models/weights"
        arch_selected = self.combo_arch.currentText()

        if os.path.exists(weights_dir):
            files = [f for f in os.listdir(weights_dir) if f.endswith(".pth") or f.endswith(".pt")]

            filtered_files = []
            for f in files:
                f_lower = f.lower()
                if "CustomECGNet" in arch_selected and "custom" in f_lower:
                    filtered_files.append(f)
                elif "Net1D" in arch_selected and ("ecgfound" in f_lower or "net1d" in f_lower or "ecg" in f_lower):
                    if "custom" not in f_lower:
                        filtered_files.append(f)
                elif "Autoencoder" in arch_selected and "anomaly" in f_lower:
                    filtered_files.append(f)

            if filtered_files:
                self.combo_models.addItems(filtered_files)
            else:
                self.combo_models.addItem(f"Brak wag dla {arch_selected.split()[0]}")
        else:
            self.combo_models.addItem("Katalog models/weights/ nie istnieje")

    def clear_anomalies(self):
        for region in self.anomaly_regions:
            self.plot_ecg.removeItem(region)
        self.anomaly_regions.clear()
        self.log_list.clear()

    def start_analysis(self):
        if not TORCH_AVAILABLE:
            QMessageBox.warning(self, "Brak PyTorch",
                                "Do uruchomienia modeli wymagana jest biblioteka PyTorch.\\nZainstaluj ja: pip install torch")
            return

        main_window = self.window()
        if not hasattr(main_window, 'tabs'):
            return

        files_tab = main_window.tabs['files']
        sig = files_tab.current_signal

        if not sig or sig.is_empty() or not sig.has_ecg:
            QMessageBox.warning(self, "Brak sygnalu", "Wczytaj najpierw plik z sygnalem EKG w zakladce Wczytaj plik.")
            return

        architecture = self.combo_arch.currentText()

        if "Autoencoder" in architecture and not sig.has_ppg:
            QMessageBox.warning(self, "Brak kanalu PPG",
                                "Multimodalny Autoenkoder wymaga do dzialania zarowno kanalu EKG jak i PPG.")
            return

        model_name = self.combo_models.currentText()
        if not model_name.endswith(".pth") and not model_name.endswith(".pt"):
            QMessageBox.warning(self, "Brak modelu", "Prosze pobrac i wybrac prawidlowy plik wag (.pth).")
            return

        model_path = os.path.join("models/weights", model_name)

        self.clear_anomalies()
        self.btn_analyze.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Trwa analiza sieci neuronowej...")

        time_arr = sig.time
        ecg_data = sig.ecg
        ppg_data = sig.ppg if sig.has_ppg else None

        if self.chk_use_filtered.isChecked():
            dsp_settings = {
                "notch_on": self.settingsmanager.get_setting("dsp", "notch_50hz"),
                "bandpass_on": self.settingsmanager.get_setting("dsp", "bandpass_enabled"),
                "baseline_on": self.settingsmanager.get_setting("dsp", "baseline_wander_removal")
            }
            ecg_data = SignalAnalyzer.apply_dsp(ecg_data, sig.sampling_rate_ecg, dsp_settings)
            if ppg_data is not None:
                ppg_data = SignalAnalyzer.apply_dsp(ppg_data, sig.sampling_rate_ppg, dsp_settings)

            self.plot_ecg.setTitle(f"Sygnal EKG (Przefiltrowany) - {architecture.split()[0]}")
        else:
            self.plot_ecg.setTitle(f"Sygnal EKG (Surowy) - {architecture.split()[0]}")

        self.ecg_curve.setData(time_arr, ecg_data)
        self.plot_ecg.getViewBox().autoRange()

        self.worker = DLInferenceWorker(
            signal_ecg=ecg_data,
            signal_ppg=ppg_data,
            sr_ecg=sig.sampling_rate_ecg,
            sr_ppg=sig.sampling_rate_ppg if sig.has_ppg else 0,
            model_path=model_path,
            architecture=architecture,
            ae_threshold=self.spin_ae_thresh.value()
        )
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log_msg.connect(lambda msg: self.lbl_status.setText(msg))
        self.worker.error.connect(self.on_dl_error)
        self.worker.result_ready.connect(self.on_dl_finished)
        self.worker.start()

    def on_dl_error(self, err_msg):
        self.btn_analyze.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("Blad analizy.")
        QMessageBox.critical(self, "Blad modelu", f"Wystapil blad podczas inferencji:\\n{err_msg}")

    def on_dl_finished(self, results):
        self.btn_analyze.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("Analiza zakonczona.")

        main_window = self.window()
        sig = main_window.tabs['files'].current_signal
        total_windows = len(results)

        anomalies_count = sum(1 for r in results if r["is_anomaly"])

        self.lbl_total_windows.setText(f"Przeanalizowane okna 10-sekundowe: {total_windows}")
        self.lbl_anomalies.setText(f"Wykryte Anomalie/Zdarzenia: {anomalies_count}")

        for res in results:
            start_t = res["start_s"]
            end_t = res["end_s"]
            lbl = res["label"]
            conf = res["conf"]
            is_anomaly = res["is_anomaly"]

            if is_anomaly:
                region = pg.LinearRegionItem(values=[start_t, end_t], brush=(255, 68, 85, 40), movable=False)
                self.plot_ecg.addItem(region)
                self.anomaly_regions.append(region)

            item = QListWidgetItem(self.log_list)
            item.setData(Qt.ItemDataRole.UserRole, (start_t, end_t))

            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(10, 6, 10, 6)

            lbl_time = QLabel(f"[{start_t:.1f}s - {end_t:.1f}s]")
            lbl_time.setStyleSheet(
                f"color: {config.Colors.DARK_TEXT_SECONDARY}; font-size: 10pt; font-weight: bold; border: none; background: transparent;")
            lbl_time.setFixedWidth(120)

            lbl_name = QLabel(lbl)
            color = config.Colors.HEART_COLOR if is_anomaly else "#00d4aa"
            lbl_name.setStyleSheet(
                f"color: {color}; font-size: 10pt; font-weight: bold; border: none; background: transparent;")

            lbl_conf = QLabel(f"Pewnosc: {conf * 100:.1f}%")
            lbl_conf.setStyleSheet(
                f"color: {config.Colors.DARK_TEXT_SECONDARY}; font-size: 9pt; border: none; background: transparent;")
            lbl_conf.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            layout.addWidget(lbl_time)
            layout.addWidget(lbl_name, stretch=1)
            layout.addWidget(lbl_conf)

            item.setSizeHint(widget.sizeHint())
            self.log_list.addItem(item)
            self.log_list.setItemWidget(item, widget)

    def on_log_clicked(self, item):
        start_t, end_t = item.data(Qt.ItemDataRole.UserRole)
        self.plot_ecg.getViewBox().setXRange(start_t - 2.0, end_t + 2.0, padding=0)

    def update_theme(self, theme):
        is_dark = theme == 'dark'
        bg_color = config.Colors.DARK_BACKGROUND if is_dark else config.Colors.LIGHT_BACKGROUND
        label_color = config.Colors.DARK_TEXT_SECONDARY if is_dark else config.Colors.LIGHT_TEXT_SECONDARY
        grid_alpha = 0.3 if is_dark else 0.2

        self.graphs_widget.setBackground(bg_color)

        plot = self.plot_ecg
        plot.getAxis('left').setPen(label_color)
        plot.getAxis('left').setTextPen(label_color)
        plot.getAxis('bottom').setPen(label_color)
        plot.getAxis('bottom').setTextPen(label_color)
        plot.setTitle(plot.titleLabel.text, color=label_color, size="10pt")
        plot.showGrid(x=True, y=True, alpha=grid_alpha)

        recent_hover_bg = config.Colors.DARK_BORDER_HOVER if is_dark else "#f0f2f5"
        card_bg = config.Colors.DARK_CARD_BG if is_dark else config.Colors.LIGHT_CARD_BG
        border = config.Colors.DARK_BORDER if is_dark else config.Colors.LIGHT_BORDER
        accent = config.Colors.DARK_ACCENT

        self.log_list.setStyleSheet(f"""
            QListWidget {{ background: transparent; border: none; outline: none; }}
            QListWidget::item {{ background: {card_bg}; border-radius: 4px; margin-bottom: 4px; }}
            QListWidget::item:hover {{ background: {recent_hover_bg}; }}
            QListWidget::item:selected {{ background: {border}; border-left: 2px solid {accent}; }}
        """)

        widgets_to_polish = [self.combo_models, self.combo_arch, self.spin_ae_thresh]
        for w in widgets_to_polish:
            w.style().unpolish(w)
            w.style().polish(w)
            w.update()