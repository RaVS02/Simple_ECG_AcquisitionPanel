# Dokumentacja Techniczna Systemu Monitorowania i Akwizycji Sygnałów EKG/PPG

**Autor:** Rafał S.  
**Projekt:** ECG Monitor v0.1  
**Rok:** 2026  

---

## 1. Wstęp i cele projektu
Niniejsza dokumentacja opisuje proces projektowania i implementacji zaawansowanego systemu komputerowego do akwizycji i analizy sygnałów biomedycznych. Głównym celem projektu jest stworzenie narzędzia umożliwiającego rejestrację sygnałów EKG (Elektrokardiografia) oraz PPG (Fotopletyzmografia) w czasie rzeczywistym z wykorzystaniem nowoczesnych technologii programistycznych.

Projekt adresuje potrzebę elastycznego oprogramowania zdolnego do współpracy z tanimi modułami AFE (np. AD8232) oraz mikrokontrolerami takimi jak ESP32 czy STM32. Kluczowe wyzwania obejmują zapewnienie wysokiej wydajności graficznej oraz gwarancję bezpieczeństwa i ciągłości zapisu danych medycznych.

## 2. Analiza dziedziny - Elektrokardiografia

### 2.1 Podstawy fizjologiczne
Sygnał EKG odzwierciedla czynność elektryczną mięśnia sercowego. Składa się on z szeregu załamków (P, QRS, T), których analiza pozwala na ocenę rytmu serca oraz wykrywanie anomalii patologicznych. Amplituda sygnału mierzona na powierzchni skóry wynosi zazwyczaj od 0.5 mV do 2 mV, co wymaga wysokiej klasy kondycjonowania sygnału przed jego digitalizacją.


## 3. Architektura systemu i technologie
System został zaprojektowany w architekturze modularnej, co umożliwia łatwą rozbudowę o nowe funkcjonalności (np. moduły Deep Learning). Do budowy aplikacji wykorzystano język Python oraz framework PyQt6.

| Komponent | Technologia / Rola |
| :--- | :--- |
| **GUI Framework** | PyQt6 - odpowiedzialny za interfejs i zdarzenia |
| **Silnik Graficzny** | PyQtGraph - wysokowydajne renderowanie sygnałów |
| **Zarządzanie Stanem** | SettingsManager - obsługa konfiguracji JSON |
| **Stylizacja** | QSS (Qt Style Sheets) - autorski silnik motywów |

### 3.1 Wykorzystanie modułu AD8232
W projekcie uwzględniono moduł AD8232 jako front-end analogowy. Jest to zintegrowany blok kondycjonowania sygnału, który zawiera wzmacniacz instrumentacyjny, filtry górnoprzepustowe oraz układ Right Leg Drive (RLD), minimalizujący zakłócenia wspólne oraz szumy sieciowe 50Hz.
### 3.2 Wykorzystanie mikrokontrolerów ESP32
ESP32, dzięki wbudowanym interfejsom komunikacyjnym (UART, Wi-Fi, Bluetooth), stanowi idealną platformę do przesyłania danych EKG/PPG do komputera. Jego zdolność do obsługi protokołów sieciowych umożliwia implementację elastycznych scenariuszy akwizycji, takich jak bezprzewodowe monitorowanie pacjenta.
### 3.3 Wykorzystanie MAX30102 do pomiaru PPG
MAX30102 to moduł optyczny przeznaczony do pomiaru sygnałów PPG, które są wykorzystywane do oceny tętna oraz saturacji krwi. Jego zastosowanie w projekcie pozwala na rozszerzenie funkcjonalności systemu o dodatkowe parametry życiowe, co zwiększa jego wartość diagnostyczną.
## 4. Projekt interfejsu użytkownika (UI/UX)
Interfejs aplikacji został zoptymalizowany pod kątem pracy w ciemnych pomieszczeniach laboratoryjnych (Dark Mode). Zastosowano paletę kolorystyczną o wysokim kontraście, gdzie akcenty morskie (`#00d4aa`) oznaczają stany poprawne, a czerwone (`#ff4455`) stany alarmowe lub nagrywanie.

Kluczowym elementem jest panel "Live Monitoring", który łączy w sobie opcje połączenia (Port, Baudrate) z paskiem narzędziowym (Toolbar) umożliwiającym pauzowanie wykresów bez przerywania zapisu w tle. Układ graficzny typu "Strip Chart" pozwala na jednoczesną obserwację wielu kanałów z synchronizacją czasu (X-Link).

## 5. Akwizycja i zarządzanie danymi
Wdrożono hybrydowy system zarządzania danymi. Podczas nagrywania dane są strumieniowane bezpośrednio do pliku na dysku (Safe-Streaming), co zapobiega ich utracie w przypadku awarii zasilania. System obsługuje standardowe formaty eksportu:

* **EDF (European Data Format):** Standard zapisu sygnałów polifazowych z metadanymi.
* **CSV:** Format tekstowy ułatwiający analizę w arkuszach kalkulacyjnych.
* **WFDB:** Format bazy danych PhysioNet.

## 6. Algorytmy przetwarzania sygnałów
W planowanej implementacji system będzie wykorzystywał potok DSP (Digital Signal Processing) obejmujący:

* **Filtry Notch:** Usuwanie zakłóceń sieciowych 50/60 Hz.
* **Filtry Pasmowoprzepustowe:** Ograniczenie sygnału do pasma 0.5 - 45 Hz (eliminacja szumów mięśniowych i dryfu linii).
* **Algorytm Pan-Tompkins:** Automatyczna detekcja zespołu QRS i wyznaczanie HR (Heart Rate).

## 7. Podsumowanie i wnioski
Opracowany system stanowi solidną bazę do budowy zaawansowanego narzędzia diagnostycznego. Dzięki zastosowaniu wydajnych bibliotek graficznych i bezpiecznej architektury zapisu, aplikacja spełnia wymagania stawiane systemom akwizycji danych biomedycznych czasu rzeczywistego.