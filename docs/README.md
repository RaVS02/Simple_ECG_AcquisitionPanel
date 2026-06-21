# 🫀 ECG Monitor & Acquisition Panel v0.1

Zaawansowany system desktopowy do akwizycji, monitorowania, cyfrowego przetwarzania (DSP) oraz analizy sygnałów biomedycznych (EKG, PPG) z wykorzystaniem modeli Głębokiego Uczenia Maszynowego (Deep Learning). Projekt został zoptymalizowany pod kątem współpracy z tanimi modułami AFE (np. AD8232, MAX30102) oraz mikrokontrolerami ESP32.


## 📌 Główne Funkcjonalności

* **Akwizycja w Czasie Rzeczywistym:** Nasłuch danych z mikrokontrolerów przez sieć (UDP/WiFi) z wykorzystaniem dedykowanych wątków (`QThread`) oraz ekstremalnie szybkie renderowanie wykresów za pomocą akcelerowanej biblioteki `PyQtGraph`.
* **Safe-Streaming & Loop Recording:** Strumieniowanie bezpośrednio do plików na dysku chroniące przed utratą danych (Crash-proof) oraz funkcja "Retro-bufora" pozwalająca na zapis incydentów kardiologicznych wstecz (np. ostatnich 5 minut).
* **Obsługa Standardów Medycznych:** Wczytywanie i eksportowanie sygnałów w formatach badawczych: **EDF** (European Data Format), **WFDB** (PhysioBank), a także JSON i CSV.
* **Cyfrowe Przetwarzanie Sygnałów (DSP):** Implementacja filtrów zaporowych (Notch 50Hz/60Hz), pasmowoprzepustowych (0.5-40Hz) eliminujących dryf linii bazowej, analiza widmowa (FFT z oknem Hanninga) oraz estymacja SpO2 i indeksu perfuzji (PI) ze stosunku AC/DC.
* **Analiza Deep Learning (AI):** Wbudowany moduł inferencji modeli PyTorch. Obsługuje klasyfikatory arytmii (`CustomECGNet`, `Net1D` / ECGFounder) z funkcją aktywacji *Multilabel Sigmoid* oraz multimodalne wariacyjne autoenkodery (VAE) do wykrywania anomalii na podstawie błędów rekonstrukcji. 
* **Dynamiczny Parser Wag (Lazy-Peek):** Zabezpieczenie chroniące przed błędem *Size Mismatch*. Aplikacja w locie analizuje pliki `.pth`, wykrywa liczbę klas i kanałów, a następnie dopasowuje strukturę sieci neuronowej przed załadowaniem wag.

---

## 🛠️ Stos Technologiczny i Biblioteki
* **Język i GUI:** Python 3.x, PyQt6 (MVC/Zakładki, QSS Theming).
* **Grafika i Analiza:** PyQtGraph (akceleracja OpenGL), NumPy, SciPy (filtry IIR Butterworth, find_peaks).
* **Machine Learning:** PyTorch (`torch`, `torch.nn`).
* **Zarządzanie formatami:** `wfdb`, `pyEDFlib`, `pandas`.

---

## 🏗️ Architektura i Programowanie Obiektowe (OOP)

Aplikacja została zaprojektowana zgodnie z paradygmatem programowania obiektowego (OOP) oraz zasadami **SOLID**. System opiera się na modułowej architekturze warstwowej, gdzie logika biznesowa i akwizycyjna (`core/`) jest całkowicie odseparowana od warstwy prezentacji (`ui/`).

* **Hermetyzacja:** Konfiguracja systemu (`settings.json`) zarządzana jest centralnie przez klasę `SettingsManager`, ukrywającą bezpośredni dostęp do stanu i emitującą sygnały (`pyqtSignal`) o zmianach do reszty aplikacji.
* **Wzorce Projektowe:**
  * *Factory Method (Fabryka statyczna):* Zaimplementowana w module `FileParser`, który na podstawie rozszerzenia decyduje o logice ładowania (CSV/JSON/EDF/WFDB) i zwraca ustandaryzowany obiekt `SignalData`.
  * *Observer (Obserwator):* Asynchroniczna komunikacja w systemie (np. odświeżanie logów, status połączenia) realizowana przez system sygnałów i slotów (Qt Signals & Slots).
  * *Strategy (Strategia):* Parametry DSP są wstrzykiwane z UI do statycznej klasy `SignalAnalyzer`, która aplikuje odpowiednie filtry IIR bez przechowywania własnego stanu.
* **Wielowątkowość:** Operacje I/O (odbieranie ramek UDP) oraz ciężkie obliczenia tensorowe (inferencja PyTorch) zostały odizolowane od wątku graficznego przy pomocy mechanizmów `QThread` oraz bezpiecznych kolejek FIFO (`collections.deque`).

---

## 🗂️ Struktura Projektu

```text
Projekt/
├── core/                    # Silniki logiczne, analityczne i akwizycyjne
│   ├── __init__.py
│   ├── analyzer.py          # Algorytmy DSP i analizy sygnału (FFT, filtry)
│   ├── file_parser.py       # Parsowanie wczytywanych plików
│   ├── network_worker.py    # Wątek obsługujący nasłuch UDP (dane z ESP32)
│   ├── settings_manager.py  # Zarządzanie konfiguracją i preferencjami
│   └── signal_data.py       # Struktury danych przechowujące sygnały
├── data/                    # Lokalne zapisy sygnałów
│   └── EKG/                 # Zrzuty i nagrania (CSV, JSON, formaty WFDB/EDF)
├── docs/                    # Dokumentacja projektu
│   ├── context.md
│   ├── dokumentacja_shorted.md
│   └── README.md
├── io/                      # Katalog wejścia/wyjścia
├── models/                  # Modele sztucznej inteligencji
│   ├── architectures/       # Definicje architektur w PyTorch (CustomECGNet, Net1D)
│   └── weights/             # Wyuczone wagi modeli (.pth)
├── resources/               # Zasoby statyczne aplikacji
│   ├── icons/               # Ikony interfejsu
│   ├── config.py            # Stałe konfiguracyjne (np. paleta kolorów)
│   └── theme.py             # Ustawienia motywu (np. tryb ciemny)
├── ui/                      # Interfejs użytkownika (PyQt6)
│   ├── __init__.py
│   ├── analysis_tab.py      # Moduł post-processingu i analizy z plików
│   ├── deeplearning_tab.py  # Moduł inferencji modeli PyTorch
│   ├── file_view_tab.py     # Przeglądarka i ładowanie zapisanych nagrań
│   ├── live_signals_tab.py  # Nasłuch i rysowanie danych w czasie rzeczywistym
│   ├── main_window.py       # Główny kontener i spinacz zakładek
│   ├── settings_tab.py      # Interfejs ustawień aplikacji
│   └── sidebar.py           # Pasek nawigacji bocznej
├── LICENSE                  # Licencja projektu
├── main.py                  # Główny plik startowy aplikacji
├── pobieranie_wag.py        # Skrypt do pobierania modeli z HuggingFace
├── requirements.txt         # Zależności bibliotek Pythona
└──  settings.json            # Aktualny plik z zapisanymi ustawieniami