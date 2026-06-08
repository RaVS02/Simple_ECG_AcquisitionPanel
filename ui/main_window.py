# ui/main_window.py
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QLabel, QPushButton, QComboBox, QStatusBar, QStyleFactory, QStackedWidget,
                             QTabBar, QFrame)
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon
from PyQt6.QtCore import Qt, QTimer

#-- Custom imports
from resources import config
from resources.theme import get_stylesheet
from ui.live_signals_tab import LiveSignalsTab
from ui.analysis_tab import AnalysisTab
from ui.file_view_tab import FilesViewerTab
from ui.deeplearning_tab import DeepLearningTab
from  ui.settings_tab import SettingsTab
from ui.sidebar import Sidebar
from core.settings_manager import SettingsManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()  # Inicjalizacja przed UI
        self.setWindowTitle(config.MainProgramConfig.WINDOW_TITLE)
        self.resize(*config.MainProgramConfig.WINDOW_SIZE)
        self.setWindowIcon(QIcon(config.MainProgramConfig.WINDOW_ICON))
        self.SetUpGUI()
        self.ApplyTheme(self.settings_manager.get_theme())

    def SetUpGUI(self):
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.mainLayout = QVBoxLayout(self.centralWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        # 1. Nav Bar
        self.nav_bar = QHBoxLayout()
        self.nav_bar.setContentsMargins(15, 5, 15, 5)
        self.logo_label = QLabel("<3 ECG Monitor")
        self.logo_label.setFixedWidth(200)

        self.tab_bar = QTabBar()
        for tab_name in ["Rejestracja", "Analiza sygnału", "Wczytaj plik", "Deep Learning", "Ustawienia"]:
            self.tab_bar.addTab(tab_name)

        self.nav_bar.addWidget(self.logo_label)
        self.nav_bar.addWidget(self.tab_bar)
        self.nav_bar.addStretch()
        self.mainLayout.addLayout(self.nav_bar)

        # 2. Body Area
        self.contentLayout = QHBoxLayout()
        self.contentLayout.setSpacing(0)
        self.sidebar = Sidebar(self.settings_manager)

        self.stacked_widget = QStackedWidget()
        self.tabs = {
            'live': LiveSignalsTab(self.settings_manager),
            'analysis': AnalysisTab(self.settings_manager),
            'files': FilesViewerTab(self.settings_manager),
            'dl': DeepLearningTab(self.settings_manager),
            'settings': SettingsTab(self.settings_manager)
        }

        for tab in self.tabs.values():
            self.stacked_widget.addWidget(tab)

        self.contentLayout.addWidget(self.sidebar)
        self.contentLayout.addWidget(self.stacked_widget)
        self.mainLayout.addLayout(self.contentLayout)

        # 3. Status Bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # LABEL - to on trzyma tekst "Ready", showMessage go tylko tymczasowo zasłania
        self.status_info_label = QLabel("Status: Gotowy")
        self.statusBar.addPermanentWidget(self.status_info_label, 1)

        self.theme_btn = QPushButton("🌓")
        self.theme_btn.setToolTip("Przełącz motyw")
        self.theme_btn.setFixedWidth(40)
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.statusBar.addPermanentWidget(self.theme_btn)

        # Sygnały
        self.tab_bar.currentChanged.connect(self.stacked_widget.setCurrentIndex)
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.tabs['live'].connection_status_changed.connect(self.update_status_label)
        # Inicjalne style dla elementów dynamicznych
        self.update_dynamic_styles()

    def update_status_label(self, text):
        """Aktualizuje stały label w pasku stanu."""
        self.status_info_label.setText(text)
        is_connected = "Połączono" in text
        self.sidebar.update_connection_status(is_connected)
    def update_dynamic_styles(self):
        """Aktualizuje style, które zależą od motywu, a nie są w QSS"""
        current = self.settings_manager.get_theme()
        is_dark = current == 'dark'

        # Kolor tekstu logo i statusu
        acc_color = config.Colors.DARK_ACCENT if is_dark else "#2C3E50"
        self.logo_label.setStyleSheet(f"color: {acc_color}; font-size: 20px; font-weight: bold;")
        self.status_info_label.setStyleSheet(f"color: {acc_color}; padding-left: 10px;")

        # Dynamiczny hover przycisku (ciemny dla jasnego tła, jasny dla ciemnego)
        h_color = "rgba(255, 255, 255, 0.15)" if is_dark else "rgba(0, 0, 0, 0.1)"
        self.theme_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; font-size: 14px; border-radius: 3px; }}
            QPushButton:hover {{ background-color: {h_color}; }}
        """)

    def toggle_theme(self):
        new_theme = 'light' if self.settings_manager.get_theme() == 'dark' else 'dark'
        self.settings_manager.set_theme(new_theme)

        # 1. CSS
        self.ApplyTheme(new_theme)

        # 2. Sidebar (efekty hover separatorów)
        self.sidebar.update_all_styles(active=False)

        # 3. Dynamiczne elementy okna (hover przycisku, logo)
        self.update_dynamic_styles()

        # 4. WYKRESY - musisz dodać metodę update_theme do swoich klas tabów
        for tab in self.tabs.values():
            if hasattr(tab, 'update_theme'):
                tab.update_theme(new_theme)

        # 5. Komunikat
        self.status_info_label.setText(f"Status: Zmieniono motyw na {new_theme.upper()}")
        QTimer.singleShot(3000, lambda: self.status_info_label.setText("Status: Gotowy"))

    def ApplyTheme(self, theme_type="dark"):
        self.setStyleSheet(get_stylesheet(theme_type))