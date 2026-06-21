# 🗺️ Rozszerzony Kontekst Projektu i Roadmapa: EKG Monitor v0.1

## 1. Cel i Założenia Projektu
Projekt ma na celu stworzenie profesjonalnego narzędzia desktopowego do akwizycji, monitorowania i analizy sygnałów biomedycznych (EKG, PPG). System został zaprojektowany z myślą o elastyczności sprzętowej (obsługa urządzeń embedded jak ESP32 przez UDP/Wi-Fi, planowane BLE) oraz zaawansowanym post-processingu z wykorzystaniem algorytmów sztucznej inteligencji.

## 2. Zrealizowany Stan Implementacji (Wersja v0.1)

### ✅ Interfejs Użytkownika (UI/UX)
* **Silnik Graficzny:** Implementacja `pyqtgraph` (z akceleracją OpenGL) zapewniająca płynne rysowanie sygnałów przy wysokim próbkowaniu (do 1000 Hz).
* **Architektura Zakładek:** System oparty na `QStackedWidget` z dynamiczną nawigacją przez pasek boczny (`Sidebar`).
* **System Stylizacji:** Autorski, podwójny motyw (Dark/Light Mode) zdefiniowany w `theme.py`, wykorzystujący zmienne z `config.py`.
* **Customowe Kontrolki:** W pełni ostylowane przyciski, interaktywne logi zdarzeń DL, listy rozwijane z filtrowaniem zawartości oraz kontrolki numeryczne (QSpinBox).

### ✅ Architektura Oprogramowania
* **Zarządzanie Stanem:** Wdrożenie klasy `SettingsManager` używającej sygnałów do globalnego rozgłaszania zmian oraz persystentnego zapisu do `settings.json`.
* **Wielowątkowość:** Izolacja operacji blokujących (nasłuch UDP, inferencja modeli AI) w osobnych wątkach (`QThread`), zapobiegająca zamrażaniu interfejsu graficznego.
* **Hermetyzacja i Modularność:** Jasny podział odpowiedzialności na pakiety: `ui/` (widoki), `core/` (logika, DSP, akwizycja), `models/` (architektury DL) i `resources/` (style).

## 3. Zrealizowane Etapy Rozwoju (Roadmapa)

### ✅ Etap 1: Logika i Konfiguracja
- [x] Pełna integracja `SettingsManager` z plikiem konfiguracyjnym.
- [x] Implementacja dynamicznego mapowania kanałów i tworzenia wykresów w locie.
- [x] Synchronizacja statusów UI (Sidebar, Settings, moduł Live).

### ✅ Etap 2: Komunikacja i Akwizycja
- [x] Implementacja gniazd UDP dla protokołu przesyłu danych z mikrokontrolera.
- [x] Stworzenie żądań REST (`requests.get`) do ESP32 sterujących rozpoczęciem i zakończeniem strumieniowania.
- [x] Zablokowanie kluczowych elementów UI w trakcie akwizycji.
- [x] Połączenie buforów kołowych (`deque` i `numpy.roll`) z wykresami `pyqtgraph` (Live Stream).

### ✅ Etap 3: Zarządzanie Danymi
- [x] Wdrożenie bufora kołowego `collections.deque` dla funkcji "Zapisz Incydent" (Loop Recording).
- [x] Implementacja architektury **Safe-Streaming** (zapis przyrostowy do plików CSV w locie).
- [x] Dynamiczny parser i funkcja eksportu do formatów medycznych (EDF, WFDB, JSON, CSV).
- [x] Czytnik historii nagrań z funkcją przeglądania wykresów historycznych.

### ✅ Etap 4: Analiza i Algorytmy (DSP)
- [x] Implementacja algorytmów detekcji załamka R w oparciu o adaptacyjne progi z `scipy.signal.find_peaks`.
- [x] Obliczanie statystyk czasowych (HR, HR min/max, RR Interval, SDNN, estymacja QRS i QTc).
- [x] Estymacja SpO2 i indeksu perfuzji (PI) ze stosunku AC/DC z kanału PPG.
- [x] Filtrowanie cyfrowe `scipy.signal` (Notch 50Hz, Bandpass 0.5-40Hz, usuwanie dryfu linii bazowej).
- [x] Implementacja Szybkiej Transformaty Fouriera (FFT) z oknem Hanninga do analizy częstotliwościowej.

### ✅ Etap 5: Implementacja Deep Learning (PyTorch)
- [x] Integracja architektur konwolucyjnych dla EKG: autorskiego `CustomECGNet` oraz bazowego `Net1D` (ECGFounder).
- [x] Implementacja wielomodalnego Autoenkodera VAE do estymacji błędu rekonstrukcji i detekcji anomalii.
- [x] Budowa mechanizmu *Lazy-Peek* (Shape Matching) automatycznie rekonfigurującego parametry architektury na podstawie wczytanych wag `.pth`.
- [x] Klasyfikacja arytmii w potoku *Multilabel* przy użyciu funkcji aktywacji Sigmoid.
- [x] Okienkowanie sygnałów, resamplowanie i nakładanie markerów czasowych bezpośrednio na interaktywny wykres EKG.

## 4. Dalsze Kroki (Future Work)
- **Diagnostyka Hardware/DSP:** Weryfikacja przesunięcia widmowego (zakłócenia 53 Hz) — stabilizacja zegara na ESP32 lub korekta interpolacji czasu po stronie odbiornika. 
- **Poprawa wcztywania i obslugi modeli DL oraz dostarczanych do nich sygnalu z naszego systemu.
- **Testy i Jakość Codebase:** Wdrożenie automatycznych testów jednostkowych (np. `pytest`) dla modułu `core/` i parserów danych.
- **Konteneryzacja:** Utworzenie pliku `Dockerfile` lub dystrybucja binarna za pomocą narzędzi PyInstaller/cx_Freeze.
- **Baza Danych:** Zastąpienie/rozbudowa zapisu plikowego bazą relacyjną (SQLite) lub TSDB dla lepszego indeksowania długoterminowych rejestrów.
- **Raportowanie:** Automatyczny eksport zestawień medycznych do PDF z wykorzystaniem biblioteki `weasyprint`.