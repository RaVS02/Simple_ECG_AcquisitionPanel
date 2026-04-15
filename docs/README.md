# ECG Monitor & Acquisition Panel v0.1

![UI Preview](https://via.placeholder.com/800x500.png?text=UI+Preview+Placeholder)

## 📌 Overview
**ECG Monitor** is a comprehensive, Python-based desktop application designed for real-time acquisition, visualization, and processing of biomedical signals (ECG, PPG). Built with a focus on modularity and high performance, it interfaces seamlessly with microcontrollers (Arduino, ESP32, STM32) and analog front-ends (e.g., AD8232) via multiple communication protocols.

## 🚀 Key Features (Current & Planned)
* **Real-Time Data Visualization:** High-performance plotting using `pyqtgraph`, capable of handling multi-channel high-frequency signals without UI blocking.
* **Hardware Connectivity:** Support for USB Serial (UART), Bluetooth, and Wi-Fi (UDP) data streaming.
* **Software Routing:** Dynamic channel mapping (e.g., mapping raw CH1 to Lead I, CH2 to PPG).
* **Data Management:** Hybrid streaming architecture ensuring data safety (crash-proof) with on-demand export to medical/research formats (EDF, WFDB, CSV).
* **Digital Signal Processing (DSP):** Planned integration of Notch filters (50/60Hz), Bandpass filtering, and baseline wander removal.
* **Modern UI/UX:** Fully custom, dark-themed interface built with `PyQt6`, featuring modular panels, toolbars, and responsive layouts.

## 🗂️ Project Structure
```text
/
├── core/
│   └── settings_manager.py     # State and JSON configuration management
├── resources/
│   ├── config.py               # Centralized UI variables, colors, and typography
│   └── theme.py                # QSS Stylesheets and dynamic CSS classes
├── ui/
│   ├── main_window.py          # Main application container and navigation
│   ├── sidebar.py              # Global metadata and routing sidebar
│   ├── live_signals_tab.py     # Real-time DAQ, connection, and charting panel
│   ├── analysis_tab.py         # Post-processing and metrics (WIP)
│   ├── file_view_tab.py        # File management and export (WIP)
│   └── settings_tab.py         # Hardware and DSP configuration (WIP)
└── main.py                     # Application entry point