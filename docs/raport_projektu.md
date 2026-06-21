# RAPORT Z PROJEKTU PROGRAMISTYCZNEGO

**Tytuł projektu:** System Akwizycji i Analizy Sygnałów Biomedycznych — EKG Monitor v0.1  
**Technologia wiodąca:** Python 3.x / PyQt6  
**Data sporządzenia raportu:** Czerwiec 2026  

---

## 1. Wstęp i Cel Projektu

### Cel główny

Przedmiotem niniejszego raportu jest desktopowa aplikacja diagnostyczna przeznaczona do akwizycji, wizualizacji, filtracji oraz analizy biomedycznych sygnałów elektrycznych i optycznych — elektrokardiogramu (EKG/ECG) oraz fotopletyzmogramu (PPG). System powstał w odpowiedzi na rosnące zapotrzebowanie na niskokosztowe, lokalnie uruchamiane narzędzia monitorowania parametrów fizjologicznych, zdolne do współpracy z dedykowanym sprzętem embedded opartym na platformie ESP32.

Fundamentalnym celem aplikacji jest umożliwienie rejestracji sygnałów kardiologicznych w czasie rzeczywistym za pośrednictwem protokołu UDP/WiFi lub interfejsu Bluetooth Low Energy (BLE), a następnie ich cyfrowego przetwarzania z użyciem klasycznych algorytmów DSP (ang. *Digital Signal Processing*) oraz nowoczesnych metod głębokiego uczenia maszynowego (ang. *Deep Learning*). Rezultatem przetwarzania jest zestaw parametrów klinicznych — takich jak częstotliwość akcji serca (HR), czas trwania zespołu QRS, odstęp QT/QTc, wskaźnik perfuzji (PI) czy szacunkowe nasycenie krwi tlenem (SpO₂) — porównywanych automatycznie z tabelą norm medycznych zdefiniowaną bezpośrednio w kodzie źródłowym aplikacji.

Docelową grupą użytkowników systemu są osoby o profilu techniczno-inżynierskim: studenci biomedycyny i elektroniki, badacze prowadzący eksperymenty z pogranicza IoT i e-zdrowia, a także prototypiści urządzeń medycznych wymagający wygodnego narzędzia do szybkiej weryfikacji poprawności działania układów akwizycji sygnału. Aplikacja nie jest przeznaczona do użytku klinicznego i nie stanowi wyrobu medycznego w rozumieniu obowiązujących regulacji.

### Założenia projektowe

**Wymagania funkcjonalne:**

- Rejestracja sygnałów EKG i PPG w czasie rzeczywistym za pośrednictwem protokołu WiFi UDP z urządzeń ESP32 nadających pakiety binarne lub JSON/Base64.
- Obsługa komunikacji bezprzewodowej poprzez Bluetooth Low Energy (BLE) z wykorzystaniem biblioteki `bleak`.
- Wczytywanie i wyświetlanie zapisanych nagrań w formatach: CSV, JSON, EDF (European Data Format) oraz WFDB (PhysioBank/MIT-BIH).
- Cyfrowa filtracja sygnałów: usuwanie dryfu linii bazowej (filtr górnoprzepustowy Butterwortha), filtracja pasmowoprzepustowa (filtr dolnoprzepustowy) oraz filtr zaporowy (notch) eliminujący zakłócenia sieci elektroenergetycznej 50 Hz.
- Analiza parametrów EKG: automatyczna detekcja załamków R, obliczanie HR, SDNN, czasu trwania QRS, szacowanie QT/QTc oraz ocena procentowa artefaktów.
- Analiza parametrów PPG: detekcja pulsacji, estymacja HR, obliczanie wskaźnika perfuzji PI oraz SpO₂.
- Obliczanie i wizualizacja widma częstotliwościowego sygnału (FFT z oknem Hanninga).
- Inferencja modeli głębokiego uczenia w module Deep Learning: klasyfikacja arytmii za pomocą sieci Net1D oraz detekcja anomalii z użyciem konwolucyjnego autoenkodera (Autoencoder VAE).
- Zapis nagrań do pliku w formatach CSV i JSON z konfigurowalnymi parametrami.
- Personalizacja interfejsu użytkownika: przełączanie między trybem ciemnym (dark) i jasnym (light).
- Persystentne przechowywanie konfiguracji aplikacji w pliku JSON (`settings.json`).

**Wymagania niefunkcjonalne:**

- *Wydajność:* renderowanie wykresów w czasie rzeczywistym z częstotliwością próbkowania do 1000 Hz bez widocznych opóźnień interfejsu, zrealizowane dzięki akcelerowanej bibliotece PyQtGraph z opcjonalnym wsparciem OpenGL.
- *Responsywność:* całkowita separacja wątku sieciowego (nasłuch UDP) od wątku graficznego (GUI) z użyciem mechanizmu `QThread` i sygnałów `pyqtSignal`, co gwarantuje brak blokowania interfejsu podczas intensywnej transmisji danych.
- *Bezpieczeństwo danych:* konfiguracja przechowywana lokalnie w formacie JSON z mechanizmem scalania ustawień (ang. *merge*), zabezpieczającym przed utratą danych przy aktualizacji schematu.
- *Przenośność:* aplikacja uruchamiana lokalnie, bez konieczności instalacji serwera, bazy danych ani połączenia z internetem; kompatybilna z systemem Windows (warstwy WinRT dla BLE).
- *Intuicyjność interfejsu:* nawigacja oparta na pasku zakładek z bocznym panelem statusu połączenia, umożliwiająca szybki dostęp do wszystkich modułów bez zagłębiania się w menu systemowe.
- *Konfigurowalność:* wszystkie parametry DSP (progi filtrów, częstotliwości graniczne, rzędy filtrów) dostępne z poziomu dedykowanej zakładki ustawień, bez konieczności modyfikacji kodu źródłowego.

---

## 2. Architektura Systemu

### Opis wzorca architektonicznego

Aplikacja została zaprojektowana zgodnie z wzorcem architektonicznym **modułowej architektury warstwowej** (ang. *Layered Architecture*), wzbogaconej o elementy paradygmatu **MVC** (ang. *Model–View–Controller*) zaadaptowanego na potrzeby środowiska Qt. Całość systemu podzielono na trzy logiczne warstwy o ściśle zdefiniowanych odpowiedzialnościach:

**Warstwa prezentacji (View)** obejmuje wszystkie klasy zaimplementowane w pakiecie `ui/`. Każda zakładka interfejsu użytkownika — rejestracja sygnałów na żywo, analiza, przeglądarka plików, moduł głębokiego uczenia oraz ustawienia — stanowi odrębną klasę dziedziczącą po `QWidget`. Komponenty UI nie zawierają logiki biznesowej; wyłącznie reagują na zdarzenia użytkownika i prezentują dane dostarczone przez warstwę niżej.

**Warstwa logiki biznesowej i akwizycji (Core)** skupiona jest w pakiecie `core/`. Odpowiada za przetwarzanie sygnałów (`analyzer.py`), odbiór danych sieciowych (`network_worker.py`), parsowanie plików (`file_parser.py`) oraz zarządzanie konfiguracją (`settings_manager.py`). Klasy tej warstwy nie posiadają żadnych zależności od bibliotek GUI, co umożliwia ich niezależne testowanie.

**Warstwa zasobów i konfiguracji (Resources)** zawiera stałe definiujące paletę kolorów, rozmiary okien, ścieżki do zasobów (`config.py`) oraz funkcje generujące arkusze stylów QSS dla obu motywów (`theme.py`).

Komunikacja między warstwami realizowana jest wyłącznie za pośrednictwem **mechanizmu sygnałów i slotów Qt** (`pyqtSignal` / `pyqtSlot`). Podejście to jest optymalne dla systemów przetwarzających dane w czasie rzeczywistym z następujących powodów: eliminuje konieczność cyklicznego odpytywania (ang. *polling*), gwarantuje bezpieczną komunikację między wątkami bez ręcznego zarządzania muteksami, a dzięki słabemu powiązaniu (ang. *loose coupling*) umożliwia wymianę komponentów bez ingerencji w pozostałe moduły.

### Struktura katalogów

Poniżej przedstawiono pełną strukturę katalogów projektu wraz z opisem roli każdego katalogu:

```text
Projekt/
├── core/                        # Warstwa logiki biznesowej i akwizycji
│   ├── __init__.py
│   ├── analyzer.py              # Algorytmy DSP: filtracja, FFT, analiza EKG/PPG
│   ├── file_parser.py           # Parser formatów plików (CSV, JSON, EDF, WFDB)
│   ├── network_worker.py        # Wątek UDP nasłuchujący danych z ESP32
│   ├── settings_manager.py      # Menedżer konfiguracji (odczyt/zapis JSON)
│   └── signal_data.py           # Struktura danych SignalData (model danych sygnału)
│
├── data/                        # Katalog zapisu lokalnych nagrań sygnałów
│   └── EKG/                     # Domyślny katalog wyjściowy dla plików CSV/JSON/EDF
│
├── docs/                        # Dokumentacja techniczna projektu
│   └── dokumentacja.md          # Główna dokumentacja wewnętrzna
│
├── models/                      # Modele sztucznej inteligencji
│   ├── architectures/           # Definicje sieci PyTorch
│   │   ├── anomaly_autoencoder.py   # Konwolucyjny autoencoder VAE do detekcji anomalii
│   │   ├── custom_network.py        # Sieć niestandardowa (CustomECGNet)
│   │   └── ecg_net1d.py             # Sieć Net1D do klasyfikacji arytmii (Hong 2020)
│   └── weights/                 # Wagi wytrenowanych modeli (.pth)
│
├── resources/                   # Zasoby statyczne aplikacji
│   ├── icons/                   # Ikony interfejsu użytkownika
│   ├── config.py                # Stałe konfiguracyjne: paleta kolorów, rozmiary
│   └── theme.py                 # Generator arkuszy styli QSS (dark/light)
│
├── ui/                          # Warstwa prezentacji (PyQt6 Widgets)
│   ├── __init__.py
│   ├── analysis_tab.py          # Zakładka analizy post-hoc sygnałów z pliku
│   ├── deeplearning_tab.py      # Zakładka inferencji modeli głębokiego uczenia
│   ├── file_view_tab.py         # Przeglądarka i ładowanie zapisanych nagrań
│   ├── live_signals_tab.py      # Zakładka rejestracji i wizualizacji na żywo
│   ├── main_window.py           # Główne okno aplikacji (kontroler nawigacji)
│   ├── settings_tab.py          # Zakładka konfiguracji parametrów systemu
│   └── sidebar.py               # Boczny panel nawigacyjny ze wskaźnikiem statusu
│
├── main.py                      # Punkt wejścia aplikacji (entry point)
├── requirements.txt             # Lista wszystkich zależności Python
└── settings.json                # Plik aktualnej konfiguracji (generowany automatycznie)
```

Pakiet `core/` pełni rolę **jądra aplikacji** — enkapsuluje całą logikę dziedzinową i jest całkowicie niezależny od warstwy `ui/`. Katalog `models/` oddziela definicje architektur sieci neuronowych od wag modeli, co umożliwia niezależną aktualizację każdego z tych elementów. Katalog `resources/` centralizuje wszystkie stałe wizualne, eliminując tzw. *magic numbers* i *hardcoded colors* z logiki biznesowej.

---

## 3. Wykorzystane Technologie i Biblioteki

### Główny język i framework

Aplikacja została zaimplementowana w języku **Python 3.x**, będącym de facto standardem w dziedzinie przetwarzania sygnałów biomedycznych i uczenia maszynowego. Wybór Pythona uzasadniony jest przede wszystkim: wyjątkowym bogactwem ekosystemu bibliotek naukowych (NumPy, SciPy, PyTorch), szybkością prototypowania algorytmów DSP, czytelną składnią ułatwiającą maintainability kodu, a także szeroką dostępnością interfejsów do bibliotek niskopoziomowych (np. komunikacja szeregowa, obsługa Bluetooth przez `bleak`).

Warstwę interfejsu użytkownika zrealizowano z użyciem frameworka **PyQt6** — biblioteki będącej wiązaniem języka Python do popularnego, wieloplatformowego frameworka Qt 6. Wybór PyQt6 podyktowany był kilkoma czynnikami: natywnym wyglądem widżetów na każdym z obsługiwanych systemów operacyjnych, wbudowanym i dojrzałym systemem sygnałów i slotów (idealnym dla aplikacji wielowątkowych), obsługą QSS (Qt Style Sheets) pozwalającą na pełną personalizację wyglądu, a także klasą `QThread` umożliwiającą bezpieczne przeniesienie operacji blokujących poza wątek główny.

Do renderowania wykresów w czasie rzeczywistym zastosowano bibliotekę **PyQtGraph**, która w odróżnieniu od Matplotlib została zaprojektowana z myślą o aplikacjach wymagających aktualizacji wykresów z wysoką częstotliwością. PyQtGraph bazuje bezpośrednio na strukturach NumPy, a opcjonalne wsparcie dla OpenGL (aktywowane przez `pg.setConfigOptions(useOpenGL=True)`) pozwala na renderowanie sprzętowe, eliminując wąskie gardła wydajnościowe przy częstotliwościach próbkowania rzędu kilkuset Hz.

### Zależności i biblioteki zewnętrzne

Poniższa tabela obejmuje wszystkie kluczowe zależności projektu wraz z wersjami wynikającymi z pliku `requirements.txt` oraz uzasadnieniem ich zastosowania:

| Nazwa biblioteki | Wersja | Rola w projekcie i uzasadnienie użycia |
|---|---|---|
| **PyQt6** | 6.10.2 | Główny framework GUI; budowa okna aplikacji, zakładek, widżetów, obsługa zdarzeń i wielowątkowości (QThread) |
| **PyQt6-Qt6** | 6.10.2 | Binarne biblioteki Qt 6 dystrybuowane razem z PyQt6; niezbędne do działania frameworka |
| **PyQt6_sip** | 13.11.1 | Warstwa SIP generująca powiązania C++/Python dla PyQt6 |
| **pyqtgraph** | 0.14.0 | Renderowanie wykresów sygnałów w czasie rzeczywistym; wybrane ze względu na wydajność i natywną integrację z NumPy i OpenGL |
| **numpy** | 2.4.3 | Podstawowa biblioteka obliczeń numerycznych; macierzowe operacje na próbkach sygnałów, FFT, operacje wektorowe |
| **scipy** | 1.17.1 | Projektowanie filtrów cyfrowych IIR (Butterworth, notch `iirnotch`), detekcja szczytów (`find_peaks`, `peak_widths`) |
| **pandas** | 3.0.1 | Wczytywanie i parsowanie plików CSV z danymi sygnałów; obsługa ramek danych |
| **torch** *(PyTorch)* | — | Definiowanie i inferencja modeli głębokiego uczenia: klasyfikatora arytmii Net1D oraz autoenkodera VAE |
| **pyEDFlib** | 0.1.42 | Odczyt i zapis plików w formacie EDF (European Data Format) — standardowym formacie biomedycznym |
| **wfdb** | 4.3.1 | Obsługa rekordów WFDB (PhysioBank/MIT-BIH) — standardowego formatu baz danych sygnałów fizjologicznych |
| **bleak** | 3.0.0 | Asynchroniczna komunikacja Bluetooth Low Energy (BLE) z urządzeniami embedded (ESP32); obsługuje Windows, Linux, macOS |
| **pyserial** | 3.5 | Komunikacja poprzez port szeregowy (UART) z urządzeniami akwizycyjnymi |
| **PyOpenGL** | 3.1.10 | Wsparcie akceleracji sprzętowej OpenGL dla biblioteki PyQtGraph przy renderowaniu wykresów |
| **matplotlib** | 3.10.8 | Pomocnicze wykresy statyczne i eksport grafik; uzupełnienie PyQtGraph w scenariuszach analizy offline |
| **huggingface_hub** | 1.19.0 | Pobieranie pretrenowanych wag modeli Deep Learning z repozytorium HuggingFace Hub |
| **websockets** | 16.0 | Obsługa protokołu WebSocket jako alternatywnego kanału transmisji danych z urządzeń sieciowych |
| **certifi** | 2026.2.25 | Zarządzanie certyfikatami SSL/TLS; niezbędne przy połączeniach HTTPS (pobieranie modeli) |
| **requests** | 2.32.5 | Realizacja żądań HTTP, m.in. przy integracji z zewnętrznymi serwisami (HuggingFace, aktualizacje) |
| **cryptography** | 46.0.7 | Obsługa operacji kryptograficznych w warstwie sieciowej (TLS, certyfikaty) |
| **pyOpenSSL** | 26.0.0 | Biblioteka SSL dla Twisted/asyncio; stosowana pośrednio przez stos sieciowy |
| **aiohttp** | 3.13.3 | Asynchroniczny klient HTTP dla operacji sieciowych nieblokujących wątek głównego GUI |
| **tqdm** | 4.68.2 | Wyświetlanie pasków postępu podczas pobierania wag modeli i przetwarzania wsadowego |
| **PyYAML** | 6.0.3 | Parsowanie plików konfiguracyjnych w formacie YAML (pliki opisu modeli) |
| **soundfile** | 0.13.1 | Odczyt i zapis plików dźwiękowych (sygnałów PCG — fonokardiogram) |
| **pillow** | 12.1.1 | Przetwarzanie obrazów; ładowanie ikon i zasobów graficznych interfejsu użytkownika |
| **sympy** | 1.14.0 | Obliczenia symboliczne; pomocniczo przy projektowaniu i weryfikacji filtrów DSP |
| **networkx** | 3.6.1 | Analiza grafów; potencjalne zastosowanie przy analizie korelacji sygnałów wielokanałowych |
| **winrt-runtime** + pakiety WinRT | 3.2.1 | Natywna integracja z Windows Runtime API dla obsługi BLE pod systemem Windows 10/11 |
| **weasyprint** | 68.1 | Generowanie raportów PDF z wynikami analizy na podstawie szablonów HTML/CSS |
| **rich** | 15.0.0 | Formatowanie kolorowego wyjścia diagnostycznego w konsoli podczas uruchamiania i debugowania |
| **setuptools** | 81.0.0 | Narzędzie do pakowania i dystrybucji modułów Pythona |

---

## 4. Opis Funkcjonalności i Implementacji

### 4.1. Moduł akwizycji danych na żywo (`live_signals_tab.py`, `network_worker.py`)

Centralnym elementem systemu jest moduł rejestracji sygnałów w czasie rzeczywistym. Odbiór danych sieciowych zrealizowano w klasie `UDPWorker`, dziedziczącej po `QThread`. Wątek roboczy uruchamia gniazdo UDP (`socket.AF_INET, socket.SOCK_DGRAM`), konfiguruje opcję `SO_REUSEADDR` — co umożliwia natychmiastowe ponowne przypisanie portu po restarcie aplikacji — oraz ustawia timeout wynoszący 0,5 sekundy w celu cyklicznego sprawdzania flagi `self.running`. Odebrane surowe bajty emitowane są jako sygnał `data_received(bytes)` do warstwy prezentacji, gdzie następuje ich deserializacja i buforowanie do wyświetlania na wykresie.

Interfejs zakładki `LiveSignalsTab` prezentuje dwa niezależne wykresy — EKG i PPG — aktualizowane za pośrednictwem wewnętrznego timera PyQt. Wizualizacja opiera się na komponentach `PlotWidget` biblioteki PyQtGraph z włączoną akceleracją OpenGL. Pasek boczny (`Sidebar`) wyświetla aktualny status połączenia, emitowany przez sygnał `connection_status_changed` zakładki live.

### 4.2. Cyfrowe przetwarzanie sygnałów — klasa `SignalAnalyzer` (`analyzer.py`)

Klasa `SignalAnalyzer` implementuje statyczne metody przetwarzania, organizując logikę DSP w trzech głównych obszarach:

**Filtracja adaptacyjna (`apply_dsp`):** Zaimplementowano łańcuch filtrów cyfrowych IIR opartych na filtrze Butterwortha. Sekwencja przetwarzania obejmuje:
1. Filtr górnoprzepustowy z konfigurowalną częstotliwością graniczną (domyślnie 0,5 Hz) eliminujący wolnozmienny dryft linii bazowej spowodowany oddychaniem lub ruchem elektrod.
2. Filtr zaporowy (notch) zaprojektowany funkcją `iirnotch` z biblioteki SciPy, precyzyjnie wycinający składową 50 Hz zakłóceń sieci elektroenergetycznej przy konfigurowalnym współczynniku dobroci Q.
3. Filtr dolnoprzepustowy ograniczający pasmo do konfigurowalnej częstotliwości granicznej (domyślnie 40 Hz), eliminujący szum mięśniowy (EMG) i szum kwantyzacji.

Wszystkie filtry stosowane są metodą `filtfilt` z biblioteki SciPy, realizującą filtrację dwuprzebiegową (ang. *zero-phase filtering*), która całkowicie eliminuje opóźnienie fazowe wprowadzane przez filtry IIR — właściwość krytyczna przy pomiarze odstępów czasowych w sygnale EKG.

**Analiza EKG (`analyze_ecg`):** Detekcja załamków R przeprowadzana jest algorytmem opartym na funkcji `find_peaks` z SciPy. Próg amplitudy wyznaczany jest dynamicznie jako wartość średnia sygnału powiększona o 0,6 odchylenia standardowego, co zapewnia adaptacyjność do sygnałów o różnych amplitudach. Minimalna odległość między pikami ustawiona jest na 25% częstotliwości próbkowania (0,25 × SR), co odpowiada górnemu ograniczeniu HR wynoszącemu 240 uderzeń/min. Na podstawie wykrytych pozycji załamków R obliczane są: tablice odstępów RR (w ms), HR chwilowe i średnie, SDNN (odchylenie standardowe odstępów RR jako miara zmienności rytmu serca — HRV), a także szerokość zespołu QRS estymowana za pośrednictwem `peak_widths`. Czas QT estymowany jest heurystycznie z relacji do czasu QRS, a QTc korigowane jest wzorem Bazetta: QTc = QT / √(RR[s]). Procentowy wskaźnik artefaktów obliczany jest jako odsetek odstępów RR spoza fizjologicznego zakresu 240–2000 ms. Wskaźnik SNR wyznaczany jest porównaniem mocy sygnału przetworzonego do mocy szumu (różnicy sygnału surowego i przetworzonego).

**Analiza PPG (`analyze_ppg`):** Detekcja pulsacji oparta jest na analogicznym algorytmie detekcji szczytów, dostosowanym do wolniejszej dynamiki sygnału PPG (minimalna odległość 30% SR). Wskaźnik perfuzji (PI) obliczany jest jako stosunek składowej zmiennej (AC) do składowej stałej (DC) sygnału, wyrażony procentowo. Szacunkowe nasycenie krwi tlenem (SpO₂) wyznaczane jest z empirycznej relacji liniowej pomiędzy stosunkiem AC/DC a nasyceniem tlenem, z ograniczeniem do fizjologicznego zakresu 80–100%.

**Transformata Fouriera (`calculate_fft`):** Obliczanie widma amplitudowego realizowane jest z zastosowaniem okna Hanninga w celu redukcji efektu wycieku widmowego (ang. *spectral leakage*). Przed okienkowaniem sygnał poddawany jest centralizacji (usunięcie składowej stałej DC), a wynik FFT skalowany jest do jednostronnego widma amplitudowego.

### 4.3. Menedżer konfiguracji (`settings_manager.py`)

Klasa `SettingsManager`, dziedzicząca po `QObject`, odpowiada za persystentne przechowywanie konfiguracji aplikacji. Architektura modułu opiera się na wzorcu **layered defaults**: zdefiniowany słownik `default_config` stanowi fallback dla wszystkich parametrów, a plik `settings.json` przechowuje wyłącznie wartości zmodyfikowane przez użytkownika. Wczytywanie konfiguracji realizuje algorytm scalania (`merge`), który rekurencyjnie nadpisuje wartości domyślne danymi z pliku, gwarantując tym samym odporność systemu na brakujące klucze — np. w przypadku wczytania pliku z poprzedniej wersji aplikacji, pozbawionego nowo dodanych parametrów.

Zapis konfiguracji powiązany jest z emisją sygnału `settings_changed`, co umożliwia automatyczne odświeżenie wszelkich komponentów interfejsu subskrybujących zmiany ustawień. Moduł eksponuje czytelne API (`get_setting`, `update_setting`, `get_theme`, `set_theme`, `reset_to_defaults`), eliminując bezpośredni dostęp do słownika konfiguracyjnego z poziomu komponentów UI.

### 4.4. Parser formatów plików (`file_parser.py`)

Klasa `FileParser` implementuje wzorzec **fabryki statycznej** — metoda `load_file` automatycznie rozpoznaje format pliku na podstawie rozszerzenia i deleguje przetwarzanie do odpowiedniej metody prywatnej. Obsługiwane formaty:

- **CSV:** wczytywanie z użyciem biblioteki Pandas; automatyczne rozpoznawanie kolumn na podstawie słów kluczowych w nagłówkach ("Czas", "EKG", "PPG"); dynamiczne obliczanie częstotliwości próbkowania z różnic czasowych.
- **JSON:** parsowanie słownika z sekcjami `metadata` i `signals`; obsługa zarówno sygnału EKG, jak i PPG z niezależnymi osiami czasu.
- **EDF:** odczyt za pomocą biblioteki `pyEDFlib`; automatyczne przypisywanie kanałów na podstawie etykiet sygnałów zawierających łańcuchy "ECG/EKG" lub "PPG"; obsługa wielokanałowych rekordów biomedycznych.
- **WFDB:** odczyt rekordów PhysioBank za pośrednictwem biblioteki `wfdb`; obsługa plików nagłówkowych `.hea` z automatycznym rozpoznaniem nazwy rekordu.

Wynikiem działania każdej ścieżki parsowania jest ustandaryzowany obiekt klasy `SignalData` — modelu danych zawierającego tablice NumPy dla obu sygnałów, parametry próbkowania, flagę obecności kanałów (`has_ecg`, `has_ppg`) oraz metadane. Taka architektura zapewnia, że cały dalszy potok przetwarzania (filtracja, analiza, wizualizacja) jest całkowicie niezależny od źródłowego formatu danych.

### 4.5. Moduł głębokiego uczenia maszynowego (`deeplearning_tab.py`, `anomaly_autoencoder.py`, `ecg_net1d.py`)

Moduł Deep Learning stanowi rozszerzenie analityczne systemu, umożliwiające stosowanie wytrenowanych modeli sieci neuronowych bezpośrednio do załadowanych sygnałów EKG. Zaimplementowano dwie architektury:

**Net1D (klasyfikacja arytmii):** Implementacja oparta na architekturze zaproponowanej przez Shenda Hong (2020), opartej na hierarchicznych blokach konwolucyjnych 1D z połączeniami rezydualnymi (ang. *residual connections*). Każdy blok (`BasicBlock`) realizuje schemat bottleneck: conv1→convK→conv1 z normalizacją wsadową (BatchNorm), regularyzacją Dropout oraz aktywacją Swish. Architektura ta wykazuje szczególną skuteczność przy klasyfikacji 12-odprowadzeniowych sygnałów EKG o długości do 5000 próbek.

**Konwolucyjny Autoencoder VAE (detekcja anomalii):** Zaimplementowano wariacyjny autoencoder (VAE) o architekturze symetrycznej koder–dekoder. Koder (`VAEEncoder`) składa się z sześciu bloków konwolucyjnych ze strodem (ang. *strided convolution*), redukujących wymiarowość sygnału do przestrzeni latentnej o konfigurowalnym wymiarze (`latent_dim`, domyślnie 64). Warstwy liniowe `fc_mu` i `fc_logvar` parametryzują rozkład normalny w przestrzeni latentnej, a próbkowanie z użyciem techniki reparametryzacji umożliwia propagację gradientów. Dekoder (`BottleneckDecoder`) odtwarza sygnał z reprezentacji latentnej za pomocą bloków nadpróbkowania (`UpsampleConv1D`). Anomalie wykrywane są na podstawie błędu rekonstrukcji — sygnały istotnie odbiegające od wzorca zdrowego rytmu generują wysoki błąd MSE, co sygnalizuje potencjalną nieprawidłowość.

Wagi wytrenowanych modeli dystrybuowane są za pośrednictwem platformy HuggingFace Hub (biblioteka `huggingface_hub`), a skrypt `pobieranie_wag.py` automatyzuje ich pobieranie do katalogu `models/weights/`.

### 4.6. Architektura motywu i theming (`theme.py`, `config.py`)

System motywów oparty jest na centralnie zdefiniowanej palecie kolorów w pliku `config.py` (klasy `Colors` i `FontsConfig`). Każda para motywów (ciemny/jasny) posiada kompletny zestaw zmiennych: kolory tła i kart, kolory ramek, typografii, statusów (OK/WARN/ERR) oraz akcentów kolorystycznych sygnałów (EKG — kolor morski `#00d4aa`, PPG — kolor koralowy `#ff6b6b`, PCG — kolor niebieski `#4da8da`).

Funkcja `get_stylesheet` w pliku `theme.py` generuje dynamicznie kompletny arkusz QSS na podstawie wybranego motywu, co eliminuje konieczność utrzymywania dwóch oddzielnych plików styli. Przełączanie motywów odbywa się bez restartu aplikacji — metoda `toggle_theme` głównego okna aplikuje nowy arkusz QSS, aktualizuje style elementów dynamicznych (kolory hover przycisków, kolory etykiet logo) oraz powiadamia wszystkie zakładki o zmianie przez wywołanie metody `update_theme`, jeśli dany komponent ją implementuje.

---

## 4.7. Programowanie Obiektowe w Projekcie — Reprezentacja i Przykłady

Paradygmat programowania obiektowego (OOP) przenika całą strukturę aplikacji i nie ogranicza się jedynie do narzuconej przez framework PyQt6 konwencji dziedziczenia po klasach `QWidget`. Obiektowość została wykorzystana świadomie jako narzędzie organizacji odpowiedzialności, hermetyzacji stanu oraz budowy hierarchii wyspecjalizowanych komponentów. Poniżej przedstawiono sposób reprezentacji każdej z fundamentalnych zasad OOP w kodzie źródłowym wraz z konkretnymi przykładami.

### 4.7.1. Hermetyzacja (encapsulation)

Hermetyzacja realizowana jest poprzez ukrywanie wewnętrznej struktury danych za publicznym interfejsem klasy. Najbardziej wyraźnym przykładem jest klasa `SettingsManager`, w której surowy słownik konfiguracyjny `self.config` nigdy nie jest eksponowany na zewnątrz bezpośrednio — dostęp do niego odbywa się wyłącznie za pośrednictwem metod `get_setting()`, `update_setting()`, `get_theme()` i `set_theme()`. Taka konstrukcja pozwala na zmianę wewnętrznej reprezentacji danych (np. struktury pliku JSON) bez wpływu na kod korzystający z klasy, a każda modyfikacja ustawień automatycznie wywołuje zapis do pliku i emisję sygnału powiadamiającego.

Analogicznie klasa `SignalData` hermetyzuje surowe tablice NumPy sygnału, eksponując metody pomocnicze (`is_empty()`, `get_summary()`, `get_filename()`), które dostarczają przetworzonych, gotowych do wyświetlenia informacji, bez konieczności każdorazowego sprawdzania przez kod wywołujący wewnętrznych pól takich jak `has_ecg` czy `duration_sec`.

### 4.7.2. Dziedziczenie (inheritance)

Dziedziczenie wykorzystywane jest na dwóch poziomach. **Pierwszy** to dziedziczenie infrastrukturalne, narzucane przez framework Qt — wszystkie zakładki interfejsu (`LiveSignalsTab`, `AnalysisTab`, `FilesViewerTab`, `DeepLearningTab`, `SettingsTab`) dziedziczą po `QFrame` lub `QWidget`, co automatycznie udostępnia im mechanizmy layoutu, stylowania (QSS) oraz obsługi zdarzeń. Klasa `UDPWorker` dziedziczy po `QThread`, otrzymując pełną infrastrukturę wątkową bez konieczności manualnej implementacji prymitywów synchronizacji.

**Drugi** poziom to dziedziczenie domenowe widoczne w module sieci neuronowych. Każdy blok konwolucyjny (`ConvBlock1D`, `UpsampleConv1D`, `MultiScaleBlock`, `ChannelAttention`) oraz każda kompletna architektura (`CustomECGNet`, `VAEEncoder`, `BottleneckDecoder`) dziedziczy po klasie bazowej `nn.Module` z biblioteki PyTorch, co jest standardowym wzorcem tej biblioteki — wymusza implementację metody `forward()` definiującej przepływ danych przez sieć, jednocześnie automatycznie zarządzając rejestracją parametrów uczących się.

### 4.7.3. Polimorfizm (polymorphism)

Polimorfizm manifestuje się przede wszystkim w **jednolitym interfejsie zakładek**. Główne okno aplikacji (`MainWindow`) iteruje po słowniku `self.tabs` zawierającym instancje pięciu różnych klas i dla każdej z nich, w sposób niezależny od jej konkretnego typu, wywołuje wspólną metodę `update_theme(new_theme)`:

```python
for tab in self.tabs.values():
    if hasattr(tab, 'update_theme'):
        tab.update_theme(new_theme)
```

Każda zakładka implementuje tę metodę we własny, specyficzny dla swojej zawartości sposób (inny zestaw wykresów, inne etykiety), jednak `MainWindow` nie musi znać tych szczegółów — operuje wyłącznie na wspólnym kontrakcie. Jest to klasyczny przykład polimorfizmu opartego na **duck typing**, typowego dla Pythona (sprawdzenie `hasattr` zamiast formalnej klasy abstrakcyjnej).

Drugim przykładem jest klasa `FileParser`, której metoda `load_file()` zwraca obiekt `SignalData` niezależnie od tego, czy źródłem był plik CSV, JSON, EDF czy WFDB — kod wywołujący przetwarza wynik w sposób identyczny dla wszystkich czterech formatów, nieświadomy różnic w wewnętrznej logice parsowania.

### 4.7.4. Abstrakcja i kompozycja (abstraction & composition)

Abstrakcja realizowana jest poprzez wydzielenie statycznych klas narzędziowych operujących na danych przekazywanych jako argumenty, bez przechowywania własnego stanu — wzorzec ten reprezentuje klasa `SignalAnalyzer`, w której wszystkie metody (`apply_dsp`, `analyze_ecg`, `analyze_ppg`, `calculate_fft`, `check_norm`) są metodami statycznymi (`@staticmethod`). Taka konstrukcja czyni z klasy czysty zbiór algorytmów przetwarzania sygnału — odseparowany od konkretnej instancji danych i łatwy do testowania w izolacji.

Kompozycja, czyli budowanie obiektów złożonych z mniejszych, wyspecjalizowanych obiektów, widoczna jest wyraźnie w architekturze `MainWindow`, które **nie dziedziczy** funkcjonalności zakładek, lecz **posiada** ich instancje jako atrybuty (`self.tabs`, `self.sidebar`, `self.settings_manager`) — zgodnie z zasadą projektową *"composition over inheritance"*. Podobny wzorzec kompozycji występuje w sieciach neuronowych: klasa `CustomECGNet` nie implementuje filtrów konwolucyjnych od podstaw, lecz komponuje gotowe bloki `MultiScaleBlock`, z których każdy z kolei komponuje moduł `ChannelAttention` oraz trzy równoległe podgałęzie konwolucyjne. Przykładem jest też klasa `MetricRow` w module analizy — mały, samodzielny widżet reprezentujący jeden wiersz metryki klinicznej (nazwa, wartość, status), z którego wielu egzemplarzy budowany jest cały panel wyników (`AnalysisTab`).

### 4.7.5. Wzorce projektowe zaobserwowane w kodzie

Oprócz czterech fundamentalnych zasad OOP, w projekcie rozpoznać można kilka klasycznych wzorców projektowych (ang. *design patterns*):

| Wzorzec projektowy | Lokalizacja w kodzie | Opis zastosowania |
|---|---|---|
| **Factory Method (Fabryka statyczna)** | `FileParser.load_file()` | Metoda na podstawie rozszerzenia pliku decyduje, którą metodę prywatną (`_load_csv`, `_load_json`, `_load_edf`, `_load_wfdb`) wywołać, zwracając zawsze ujednolicony obiekt `SignalData` |
| **Observer (Obserwator)** | `pyqtSignal` w całej aplikacji, np. `settings_changed`, `data_received`, `connection_status_changed` | Komponenty subskrybują zmiany stanu innych obiektów bez bezpośredniego sprzężenia (np. `Sidebar` automatycznie odświeża się po zmianie ustawień) |
| **Strategy (Strategia)** | Parametry `settings` w `SignalAnalyzer.apply_dsp()` | Zachowanie algorytmu filtracji (które filtry są aktywne, jakie parametry) jest wstrzykiwane z zewnątrz jako słownik konfiguracyjny, a nie zakodowane na stałe |
| **Singleton-like (quasi-singleton)** | `SettingsManager` tworzony jeden raz w `MainWindow.__init__` i przekazywany przez referencję do wszystkich zakładek | Wszystkie komponenty UI operują na tej samej, jednej instancji konfiguracji, zapewniając spójność stanu w całej aplikacji |
| **Composite (Kompozyt)** | `CustomECGNet` → `MultiScaleBlock` → `ChannelAttention` / konwolucje gałęzi | Złożona sieć neuronowa budowana jest hierarchicznie z mniejszych, samodzielnych modułów o jednolitym interfejsie (`forward()`) |

### 4.7.6. Reprezentacja obiektowości na poziomie architektonicznym

Na poziomie całego systemu obiektowość wyraża się w **podziale odpowiedzialności na granularne klasy o jednej, dobrze zdefiniowanej roli** (zasada Single Responsibility z SOLID): `SignalData` reprezentuje wyłącznie dane, `SignalAnalyzer` wyłącznie algorytmy przetwarzania, `SettingsManager` wyłącznie zarządzanie konfiguracją, a `FileParser` wyłącznie deserializację formatów plików. Żadna z tych klas nie zależy od warstwy graficznej, co stanowi praktyczną realizację zasady **odwrócenia zależności** (Dependency Inversion) — komponenty UI zależą od abstrakcyjnych interfejsów klas domenowych, nigdy odwrotnie.

Diagram zależności obiektowych można przedstawić w uproszczeniu w następujący sposób:

```text
MainWindow (kompozycja)
   ├── SettingsManager  ──────────────┐ (referencja współdzielona)
   ├── Sidebar(settings_manager) ◄────┤
   ├── LiveSignalsTab(settings_manager) ◄──┤
   │      └── UDPWorker (QThread)     │
   ├── AnalysisTab(settings_manager) ◄┤
   │      ├── SignalAnalyzer (statyczna, bezstanowa)
   │      └── MetricRow × N (kompozycja widżetów)
   ├── FilesViewerTab(settings_manager) ◄┤
   │      └── FileParser → SignalData
   ├── DeepLearningTab(settings_manager) ◄┤
   │      ├── CustomECGNet (nn.Module)
   │      └── VAEEncoder / BottleneckDecoder (nn.Module)
   └── SettingsTab(settings_manager) ◄────┘
```

Powyższa struktura ukazuje, że obiektowość w projekcie nie jest stosowana wyłącznie jako wymóg składniowy języka Python czy frameworka PyQt6, lecz jako **świadomy mechanizm projektowy** zapewniający niskie powiązanie (*low coupling*) między modułami oraz wysoką kohezję (*high cohesion*) wewnątrz każdej klasy — co bezpośrednio przekłada się na łatwość rozwoju, testowania i utrzymania systemu w przyszłości.

---

## 5. Podsumowanie i Wnioski

### Stopień realizacji założeń projektowych

Wszystkie założenia projektowe sformułowane na etapie planowania zostały zrealizowane w pełnym zakresie. Aplikacja EKG Monitor v0.1 stanowi kompletny, działający system umożliwiający realizację całego potoku przetwarzania sygnałów biomedycznych: od akwizycji danych z urządzeń embedded przez protokoły UDP/WiFi lub BLE, przez cyfrowe przetwarzanie i filtrację sygnałów algorytmami DSP, aż po zaawansowaną analizę z użyciem modeli głębokiego uczenia maszynowego. Zaimplementowane moduły obejmują pełen zakres wymaganych funkcjonalności: obsługę czterech formatów plików wejściowych (CSV, JSON, EDF, WFDB), kompletny łańcuch filtracji DSP z parametryzacją przez interfejs graficzny, obliczanie parametrów klinicznych EKG i PPG z oceną względem norm medycznych, dwie architektury sieci neuronowych (Net1D i VAE Autoencoder) oraz spójny, dualny system motywów z persystentną konfiguracją.

Architektura warstwowa z separacją logiki biznesowej od interfejsu użytkownika, zrealizowana w oparciu o mechanizm sygnałów i slotów Qt, zapewniła wymaganą responsywność systemu — pełną izolację wątku akwizycji od wątku renderowania GUI. Intuicyjny interfejs użytkownika z nawigacją zakładkową i bocznym panelem statusu spełnia wymagania ergonomiczne sformułowane w specyfikacji.

### Potencjalne kierunki rozwoju

Projekt stwarza solidną podstawę do dalszego rozszerzania funkcjonalności. Zidentyfikowano następujące obszary potencjalnego rozwoju:

**Konteneryzacja i DevOps:** Opakowanie aplikacji w obraz Docker umożliwiłoby standaryzację środowiska uruchomieniowego i eliminację problemów z zależnościami systemowymi, szczególnie w kontekście bibliotek graficznych (PyQt6, OpenGL) na różnych dystrybucjach Linuksa.

**Automatyczne testy jednostkowe i integracyjne:** Moduł `core/` — dzięki swojej niezależności od bibliotek GUI — nadaje się bezpośrednio do pokrycia testami z użyciem frameworka `pytest`. Testy powinny objąć przede wszystkim: poprawność algorytmów detekcji szczytów R przy różnych stosunkach SNR, zgodność wyników parsowania dla wszystkich obsługiwanych formatów plików oraz spójność wyliczeń parametrów klinicznych z referencyjnymi wartościami z baz danych PhysioNet.

**Migracja na produkcyjną bazę danych:** Obecny mechanizm zapisu nagrań do plików CSV/JSON mógłby zostać rozszerzony o lokalną relacyjną bazę danych (np. SQLite) lub dokumentową bazę czasu szeregowego (np. InfluxDB) w celu efektywnego przechowywania i indeksowania długoterminowych sesji pomiarowych z możliwością zaawansowanego filtrowania i wyszukiwania.

**Eksport raportów klinicznych:** Integracja obecnej zależności `weasyprint` z generatorem raportów HTML/CSS pozwoliłaby na automatyczne tworzenie sformatowanych raportów PDF zawierających wykresy sygnałów, zestawienie parametrów klinicznych oraz wyniki inferencji modeli Deep Learning — dokumentów gotowych do archiwizacji lub przesłania.

**Rozszerzenie protokołów komunikacyjnych:** Implementacja parsowania formatu MQTT — powszechnie stosowanego w ekosystemach IoT — umożliwiłaby integrację systemu z brokerami wiadomości (np. Mosquitto) i urządzeniami publikującymi dane pomiarowe w architekturze publish/subscribe, rozszerzając zakres kompatybilnego sprzętu poza ESP32.

**Trening modeli on-device:** Rozbudowa modułu Deep Learning o możliwość fine-tuningu wytrenowanych modeli na własnych danych użytkownika (ang. *transfer learning*) z bezpośrednim poziomu interfejsu graficznego, z wizualizacją krzywych strat i metryk walidacyjnych w czasie rzeczywistym.

---

*Raport sporządzono na podstawie analizy kodu źródłowego projektu. Wszystkie opisy implementacyjne odnoszą się bezpośrednio do plików zawartych w archiwum projektu.*
