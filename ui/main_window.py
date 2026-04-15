# ui/main_window.py
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QLabel, QPushButton, QComboBox, QStatusBar, QStyleFactory, QStackedWidget,
                             QTabBar, QFrame)
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtCore import Qt

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
        self.setWindowTitle(config.MainProgramConfig.WINDOW_TITLE)
        self.resize(*config.MainProgramConfig.WINDOW_SIZE)
        self.SetUpGUI()
        self.ApplyTheme('dark')

    def SetUpGUI(self):
        self.settings_manager = SettingsManager()
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.mainLayout = QVBoxLayout(self.centralWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)  # Usuwamy marginesy zewnętrzne
        self.mainLayout.setSpacing(0)

        # 1. Nav Bar (Góra)
        self.nav_bar = QHBoxLayout()
        self.nav_bar.setContentsMargins(15, 5, 15, 5)
        self.logo_label = QLabel("<3 ECG Monitor")
        self.logo_label.setStyleSheet(f"color: {config.Colors.DARK_ACCENT}; font-size: 20px; font-weight: bold;")
        self.logo_label.setFixedWidth(200)
        self.tab_bar = QTabBar()
        self.tab_bar.addTab("Rejestracja")
        self.tab_bar.addTab("Analiza sygnału")
        self.tab_bar.addTab("Wczytaj plik")
        self.tab_bar.addTab("Deep Learning")
        self.tab_bar.addTab("Ustawienia")
        self.nav_bar.addWidget(self.logo_label)
        self.nav_bar.addWidget(self.tab_bar)
        self.mainLayout.addLayout(self.nav_bar)
        self.nav_bar.addStretch()

        self.nav_bar.setSpacing(5)
        # 2. Body Area (Sidebar + StackedWidget) - NOWOŚĆ!
        self.contentLayout = QHBoxLayout()
        self.contentLayout.setSpacing(0)

        self.sidebar = Sidebar(self.settings_manager)
        self.contentLayout.addWidget(self.sidebar)

        self.stacked_widget = QStackedWidget()
        self.tab_livemonitoring = LiveSignalsTab(self.settings_manager)
        self.tab_analysis = AnalysisTab(self.settings_manager)
        self.tab_files = FilesViewerTab(self.settings_manager)
        self.tab_deeplearning = DeepLearningTab(self.settings_manager)
        self.tab_settings = SettingsTab(self.settings_manager)

        self.stacked_widget.addWidget(self.tab_livemonitoring)
        self.stacked_widget.addWidget(self.tab_analysis)
        self.stacked_widget.addWidget(self.tab_files)
        self.stacked_widget.addWidget(self.tab_deeplearning)
        self.stacked_widget.addWidget(self.tab_settings)

        self.contentLayout.addWidget(self.stacked_widget)
        self.mainLayout.addLayout(self.contentLayout)

        # 3. Status Bar (Dół)
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Bottom Bar - Status: Ready")
        self.statusBar.setStyleSheet(f"color: {config.Colors.DARK_ACCENT}; font-size: {config.FontsConfig.BOTTOM_BAR_FONT_SIZE}pt;")
        # Sygnały
        self.tab_bar.currentChanged.connect(self.stacked_widget.setCurrentIndex)

    def ApplyTheme(self, type="dark"):
        self.setStyleSheet(get_stylesheet(type))
    def add_separator(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setStyleSheet(f"background-color:{config.Colors.DARK_BACKGROUND}; min-height: 1px;  margin: 5px 0px;")
        layout.addWidget(line)