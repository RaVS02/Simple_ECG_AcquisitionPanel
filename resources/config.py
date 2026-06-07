# resources/config.py

class MainProgramConfig:
    WINDOW_TITLE = "EKG Monitor v0.1"
    WINDOW_SIZE = (1280, 800)
    WINDOW_ICON = 'resources/icons/wave-square-solid.png'  # Ścieżka do ikony okna

class Colors:
    # ==========================================
    # DARK THEME
    # ==========================================

    # ==========================================
    # BRANDING & AKCENTY
    # ==========================================
    HEART_COLOR = "#ff4455"  # Czerwony akcent (nagrywanie/błędy)
    DARK_ACCENT = "#00d4aa"  # Główny zielony/morski akcent
    ANALYSIS_ACCENT = "#7c6af7"  # Fioletowy akcent (np. do drugiego wykresu)
    PPG_ACCENT="#277AAA"

    # ==========================================
    # KOLORY SYGNAŁÓW (Do wykresów pyqtgraph)
    # ==========================================
    SIGNAL_ECG = "#00d4aa"  # Klasyczny medyczny morski/zielony
    SIGNAL_PPG = "#ff6b6b"  # Koralowy czerwony/pomarańcz (pulsoksymetria/krew)
    SIGNAL_PCG = "#4da8da"  # Jasnoniebieski dla fal dźwiękowych (Fonokardiogram)

    # ==========================================
    # TŁA I POWIERZCHNIE (Surfaces)
    # ==========================================
    DARK_BACKGROUND = "#0a0c10"  # Główne tło aplikacji (najciemniejsze)
    DARK_PANEL_BG = "#090b14"  # Tło bocznego panelu (Sidebar)
    DARK_CARD_BG = "#0d0f1a"  # Tło dla kart (Karta Analizy, Ustawienia, Toolbar)
    DARK_CONN_BG = "#0a0c14"  # Tło panelu połączeń

    # ==========================================
    # RAMKI (Borders)
    # ==========================================
    DARK_BORDER = "#1a1c28"  # Standardowa ramka separująca
    DARK_BORDER_HOVER = "#1e2438"  # Jaśniejsza ramka (np. hover na listach)

    # ==========================================
    # TEKSTY (Typography)
    # ==========================================
    # Teksty
    DARK_TEXT_TITLE = "#ffffff"  # Czysta biel dla głównych tytułów
    DARK_TEXT_PRIMARY = "#c0c8d0"  # Jasnoszary
    DARK_TEXT_SECONDARY = "#8b9bb4"  # Znacznie jaśniejszy szary-niebieski (było #4a5570)
    DARK_TEXT_MUTED = "#5c6784"  # Widoczny wyciszony (było #2e3450)

    # ==========================================
    # STATUSY I ODZNAKI (Badges)
    # ==========================================
    STATUS_OK_TEXT = "#00a880"  # Ciemniejszy zielony do tekstów OK
    STATUS_OK_BG = "#041a14"  # Bardzo ciemne zielone tło odznaki
    POSITIVE_STATUS = "#00a880"
    STATUS_WARN_TEXT = "#cc8800"  # Pomarańczowy tekst ostrzeżenia
    STATUS_WARN_BG = "#1a1004"  # Ciemnopomarańczowe tło odznaki

    STATUS_ERR_TEXT = "#ff4455"  # Czerwony tekst błędu/rozłączenia
    STATUS_ERR_BG = "#220a0d"  # Ciemnoczerwone tło odznaki

    # ==========================================
    # LIGHT THEME
    # ==========================================

    LIGHT_BACKGROUND = "#f4f5f8"  # Główne tło (bardzo jasny szary)
    LIGHT_PANEL_BG = "#ffffff"  # Tła paneli i kart (czysta biel)
    LIGHT_CARD_BG = "#ffffff"
    LIGHT_CONN_BG = "#eef0f5"  # Tło panelu połączeń (lekko odcięte od bieli)
    LIGHT_ACCENT = "#e0f0f5"
    LIGHT_BORDER = "#d1d5db"  # Standardowa, delikatna szara ramka
    LIGHT_BORDER_HOVER = "#9ca3af"

    LIGHT_TEXT_TITLE = "#111827"  # Bardzo ciemny szary (prawie czarny) do nagłówków
    LIGHT_TEXT_PRIMARY = "#374151"  # Główny tekst
    LIGHT_TEXT_SECONDARY = "#4b5563"  # Etykiety
    LIGHT_TEXT_MUTED = "#9ca3af"  # Wyciszony tekst

    LIGHT_STATUS_OK_TEXT = "#047857"  # Ciemnozielony tekst
    LIGHT_STATUS_OK_BG = "#d1fae5"  # Bardzo jasne zielone tło odznaki
    LIGHT_STATUS_WARN_TEXT = "#b45309"
    LIGHT_STATUS_WARN_BG = "#fef3c7"
    LIGHT_STATUS_ERR_TEXT = "#be123c"  # Ciemnoczerwony tekst
    LIGHT_STATUS_ERR_BG = "#ffe4e6"  # Jasnoróżowe/czerwone tło odznaki


class FontsConfig:
    # W HTML używałeś JetBrains Mono / Courier New, zróbmy podobnie
    FONT_FAMILY = "Consolas"
    FONT_SIZE = 10  # Główny rozmiar (mniejszy, bardziej techniczny)
    TITLE_FONT_SIZE = 12  # Do nagłówków
    BADGE_FONT_SIZE = 9  # Do odznak statusu
    BOTTOM_BAR_FONT_SIZE = 8  # Do paska na dole


class DSPConfig:
    NATIVE_ECG_SAMPLING_RATE = 250  # Hz
    NATIVE_PPG_SAMPLING_RATE = 250  # Hz


