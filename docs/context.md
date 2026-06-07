# 🗺️ Rozszerzony Kontekst Projektu i Roadmapa: EKG Monitor v0.1

## 1. Cel i Założenia Projektu
Projekt ma na celu stworzenie profesjonalnego narzędzia desktopowego do akwizycji, monitorowania i analizy sygnałów biomedycznych (EKG, PPG). System jest projektowany z myślą o elastyczności sprzętowej (obsługa Arduino, ESP32, STM32 przez UART/Wi-Fi/Bluetooth) oraz bezpieczeństwie danych medycznych.

## 2. Aktualny Stan Implementacji (Baseline)

### ✅ Interfejs Użytkownika (UI/UX)
* **Silnik Graficzny:** Implementacja `pyqtgraph` zapewniająca płynne rysowanie sygnałów przy wysokim próbkowaniu.
* **Architektura Zakładek:** System oparty na `QStackedWidget` z nawigacją przez `QTabBar`.
* **System Stylizacji:** Autorski motyw Dark Mode zdefiniowany w `theme.py`, wykorzystujący zmienne z `config.py`.
* **Customowe Kontrolki:** W pełni ostylowane przyciski (klasy primary/danger), listy rozwijane (ComboBox) z naprawionymi artefaktami wizualnymi oraz pola wyboru (CheckBox/Radio).
* **Responsywność:** Zastosowanie `QFrame` jako kontenerów (.conn-panel, .toolbar, .card) z wyzerowanymi marginesami dla efektu "edge-to-edge".

### ✅ Architektura Oprogramowania
* **Zarządzanie Stanem:** Wdrożenie klasy `SettingsManager` (dziedziczącej po QObject) używającej sygnałów do globalnego rozgłaszania zmian.
* **Struktura Katalogowa:** Podział na `ui/` (widoki), `core/` (logika), `resources/` (style i konfiguracja).

## 3. Roadmapa Rozwoju

### 🟧 Etap 1: Logika i Konfiguracja (Najbliższe kroki)
- [x] Pełna integracja `SettingsManager` z plikiem `settings.json`.
- [x] Implementacja dynamicznego mapowania kanałów i tworzenia wykresów w locie.
- [x] Synchronizacja UI (Sidebar, Settings, Live).

### 🟧 Etap 2: Komunikacja i Akwizycja
- [ ] Definicja protokołu ramki danych (Header, Payload, CRC).
- [ ] Implementacja gniazd (Sockets) dla protokołu UDP w Pythonie.
- [ ] Stworzenie endpointów REST na ESP32 odbierających parametry akwizycji z Pythona przed startem strumieniowania.
- [ ] Zablokowanie UI i funkcji konfiguracyjnych na ESP32 w trakcie trwania akwizycji.
- [ ] Połączenie strumienia danych z wykresami `pyqtgraph` (Live Stream).

### 🟧 Etap 3: Zarządzanie Danymi
- [ ] Wdrożenie struktury bufora kołowego (`collections.deque`) dla funkcji "Zapisz Incydent" (Loop Recording).
- [ ] Implementacja architektury **Safe-Streaming** (zapis do pliku CSV/JSON w locie).
- [ ] Funkcja eksportu do formatów medycznych (EDF, WFDB).
- [ ] System automatycznego zapisu (Auto-save) zapobiegający utracie danych.

### 🟧 Etap 4: Analiza i Algorytmy
- [ ] Implementacja algorytmu Pan-Tompkins do detekcji załamka R w czasie rzeczywistym.
- [ ] Obliczanie statystyk HRV (HR, RR Interval, SDNN).
- [ ] Filtrowanie cyfrowe (Notch 50Hz, Bandpass 0.5-40Hz).

### 🟧 Etap 5: Implementacja Deep Learning 
- [ ] Klasyfikacja arytmii i analiza jakości sygnału.
---
*Dokument ten służy jako punkt odniesienia dla dalszych prac programistycznych i projektowych.*
