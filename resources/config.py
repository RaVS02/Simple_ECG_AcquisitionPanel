class MainProgramConfig:
    WINDOW_TITLE = "ECG Analysis Tool"
    WINDOW_SIZE = (1280, 800)
class Colors:
    Heart_COLOR = "#ff4a4a"
    #-- Dark Theme Colors ---
    DARK_BACKGROUND = "#0a0c10"
    DARK_ACCENT = "#00d4aa"
    DARK_TEXT_PRIMARY = "#ffffff"
    DARK_TEXT_SECONDARY = "#888888"
    DARK_BORDER= "#1a1c28"
    DARK_PANEL_BG='#090b14'
    ERROR = "#ff4a4a"
    WARNING = "#ffb84d"
    POSITIVE_STATUS = "#00a880"

    SUCCESS = "#00d4aa"
    ANALYSIS_ACCENT = "#7c6af7"

    #-- Light Theme Colors ---
    LIGHT_BACKGROUND = "#ffffff"
    LIGHT_ACCENT = "#00d4aa"
    LIGHT_TEXT_PRIMARY = "#000000"
    LIGHT_TEXT_SECONDARY = "#555555"
class FontsConfig:
    FONT_FAMILY = "Consolas"
    FONT_SIZE = 12
    BOTTOM_BAR_FONT_SIZE = 8
class DPSConfig:
    NATIVE_ECG_SAMPLING_RATE = 250 #Hz
    NATIVE_PPG_SAMPLING_RATE = 250 #HZ
