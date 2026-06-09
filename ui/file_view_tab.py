from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QPushButton, QWidget, QSplitter, QSlider, QListWidget, QListWidgetItem)
import pyqtgraph as pg
from resources import config

FORMAT_COLORS = {
    "edf": "#7c6af7",
    "wfdb": "#00a880",
    "csv": "#cc8800",
    "json": "#00d4aa"
}


class ClickableCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, title, subtitle, ext, format_id):
        super().__init__()
        self.format_id = format_id
        self.is_active = False
        self.is_dark_theme = True
        self.setProperty("cssClass", "card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        self.title_lbl = QLabel(title)
        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setWordWrap(True)

        ext_color = FORMAT_COLORS.get(format_id, config.Colors.DARK_ACCENT)
        self.ext_lbl = QLabel(ext)
        self.ext_lbl.setStyleSheet(f"color: {ext_color}; font-size: 9pt; border: none; background: transparent;")

        layout.addWidget(self.title_lbl)
        layout.addWidget(self.sub_lbl)
        layout.addWidget(self.ext_lbl)
        layout.addStretch()

    def mousePressEvent(self, event):
        self.clicked.emit(self.format_id)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.update_card_style(hover=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update_card_style(hover=False)
        super().leaveEvent(event)

    def set_active(self, active):
        self.is_active = active
        self.update_card_style()

    def update_theme(self, is_dark):
        self.is_dark_theme = is_dark
        text_prim = config.Colors.DARK_TEXT_PRIMARY if is_dark else config.Colors.LIGHT_TEXT_PRIMARY
        text_sec = config.Colors.DARK_TEXT_SECONDARY if is_dark else config.Colors.LIGHT_TEXT_SECONDARY
        base_style = "border: none; background: transparent;"

        self.title_lbl.setStyleSheet(f"color: {text_prim}; font-weight: bold; font-size: 11pt; {base_style}")
        self.sub_lbl.setStyleSheet(f"color: {text_sec}; font-size: 9pt; {base_style}")
        self.update_card_style()

    def update_card_style(self, hover=False):
        if self.is_active:
            bg = config.Colors.DARK_PANEL_BG if self.is_dark_theme else config.Colors.LIGHT_PANEL_BG
            self.setStyleSheet(
                f"background-color: {bg}; border: 1px solid {config.Colors.DARK_ACCENT}; border-radius: 6px;")
        elif hover:
            hover_bg = config.Colors.DARK_BORDER_HOVER if self.is_dark_theme else "#f0f2f5"
            border_color = config.Colors.DARK_BORDER if self.is_dark_theme else config.Colors.LIGHT_BORDER
            self.setStyleSheet(f"background-color: {hover_bg}; border: 1px solid {border_color}; border-radius: 6px;")
        else:
            self.setStyleSheet("")


class FilesViewerTab(QFrame):
    def __init__(self, settingsmanager):
        super().__init__()
        self.setProperty("cssClass", "panel")
        self.settingsmanager = settingsmanager
        self.active_format = "edf"
        self.format_cards = {}

        self.recent_items_widgets = []

        self.initUI()
        self.update_theme(self.settingsmanager.get_theme())

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background-color: transparent; height: 10px; }")
        splitter.setChildrenCollapsible(False)

        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(20, 20, 20, 10)
        top_layout.setSpacing(20)

        formats_container = QWidget()
        formats_layout = QVBoxLayout(formats_container)
        formats_layout.setContentsMargins(0, 0, 0, 0)

        lbl_format = QLabel("FORMAT PLIKU")
        lbl_format.setProperty("cssClass", "section-title")
        formats_layout.addWidget(lbl_format)

        grid_formats = QGridLayout()
        grid_formats.setSpacing(10)

        self.add_format_card(grid_formats, 0, 0, "EDF / EDF+", "Standard medyczny, naglowek z metadanymi", ".edf",
                             "edf")
        self.add_format_card(grid_formats, 0, 1, "WFDB / PhysioNet", "Bazy MIT-BIH, PhysioNet", ".hea + .dat", "wfdb")
        self.add_format_card(grid_formats, 1, 0, "CSV / TXT", "Kolumny: czas, napiecie, adnotacje", ".csv, .txt", "csv")
        self.add_format_card(grid_formats, 1, 1, "JSON", "Dane i metadane w jednym pliku", ".json", "json")

        formats_layout.addLayout(grid_formats)
        top_layout.addWidget(formats_container, stretch=2)

        drop_container = QWidget()
        drop_layout = QVBoxLayout(drop_container)
        drop_layout.setContentsMargins(0, 0, 0, 0)

        lbl_drop = QLabel("WCZYTAJ PLIK")
        lbl_drop.setProperty("cssClass", "section-title")
        drop_layout.addWidget(lbl_drop)

        self.btn_load_file = QPushButton("📁 Przeciagnij plik tutaj\n\nlub kliknij, aby przegladac")
        self.btn_load_file.setSizePolicy(self.btn_load_file.sizePolicy().Policy.Expanding,
                                         self.btn_load_file.sizePolicy().Policy.Expanding)
        drop_layout.addWidget(self.btn_load_file)
        top_layout.addWidget(drop_container, stretch=1)

        recent_container = QWidget()
        recent_layout = QVBoxLayout(recent_container)
        recent_layout.setContentsMargins(0, 0, 0, 0)

        lbl_recent = QLabel("OSTATNIO OTWARTE")
        lbl_recent.setProperty("cssClass", "section-title")
        recent_layout.addWidget(lbl_recent)

        self.recent_list = QListWidget()

        self.add_recent_file(".edf", "nagranie_2024-03-20.edf", "EDF · 5 min", "edf")
        self.add_recent_file(".hea", "mit-bih-arrhythmia/100.hea", "PhysioNet · 30 min", "wfdb")
        self.add_recent_file(".csv", "eksport_pacjent_01.csv", "CSV · 2 min", "csv")

        recent_layout.addWidget(self.recent_list)
        top_layout.addWidget(recent_container, stretch=1)

        bottom_panel = QFrame()
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)

        player_toolbar = QFrame()
        player_toolbar.setProperty("cssClass", "toolbar")
        player_layout = QHBoxLayout(player_toolbar)
        player_layout.setContentsMargins(15, 8, 15, 8)

        self.btn_play = QPushButton("▶ Odtwarzaj")
        self.btn_play.setProperty("cssClass", "primary")
        self.btn_stop = QPushButton("◼ Zatrzymaj")

        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setRange(0, 1000)
        self.time_slider.setCursor(Qt.CursorShape.PointingHandCursor)

        self.lbl_time = QLabel("00:00 / 05:00")

        player_layout.addWidget(self.btn_play)
        player_layout.addWidget(self.btn_stop)
        player_layout.addSpacing(15)
        player_layout.addWidget(self.time_slider)
        player_layout.addSpacing(15)
        player_layout.addWidget(self.lbl_time)

        self.graphs_widget = pg.GraphicsLayoutWidget()

        self.plot_ecg = self.graphs_widget.addPlot(title="EKG (Z pliku)")
        self.plot_ecg.setLabel('left', 'Amplituda', units='mV')
        self.graphs_widget.nextRow()
        self.plot_ppg = self.graphs_widget.addPlot(title="PPG (Z pliku)")
        self.plot_ppg.setLabel('left', 'Sygnal', units='ADC')
        self.plot_ppg.setXLink(self.plot_ecg)

        bottom_layout.addWidget(player_toolbar)
        bottom_layout.addWidget(self.graphs_widget, stretch=1)

        splitter.addWidget(top_panel)
        splitter.addWidget(bottom_panel)
        splitter.setSizes([250, 600])

        main_layout.addWidget(splitter)
        self.set_active_card("edf")

    def add_format_card(self, grid, row, col, title, sub, ext, fmt_id):
        card = ClickableCard(title, sub, ext, fmt_id)
        card.clicked.connect(self.set_active_card)
        self.format_cards[fmt_id] = card
        grid.addWidget(card, row, col)

    def set_active_card(self, fmt_id):
        self.active_format = fmt_id
        for key, card in self.format_cards.items():
            card.set_active(key == fmt_id)

    def add_recent_file(self, ext, filename, meta, fmt_id):
        item = QListWidgetItem(self.recent_list)

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 6, 10, 6)

        base_style = "border: none; background: transparent;"

        ext_color = FORMAT_COLORS.get(fmt_id, config.Colors.DARK_ACCENT)
        lbl_ext = QLabel(ext)
        lbl_ext.setStyleSheet(f"color: {ext_color}; font-size: 10pt; font-weight: bold; {base_style}")
        lbl_ext.setFixedWidth(40)

        lbl_name = QLabel(filename)
        lbl_meta = QLabel(meta)
        lbl_meta.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(lbl_ext)
        layout.addWidget(lbl_name, stretch=1)
        layout.addWidget(lbl_meta)

        self.recent_items_widgets.append((lbl_name, lbl_meta))

        item.setSizeHint(widget.sizeHint())
        self.recent_list.setItemWidget(item, widget)

    def update_theme(self, theme):
        is_dark = theme == 'dark'

        bg_color = config.Colors.DARK_BACKGROUND if is_dark else config.Colors.LIGHT_BACKGROUND
        panel_bg = config.Colors.DARK_PANEL_BG if is_dark else config.Colors.LIGHT_PANEL_BG
        card_bg = config.Colors.DARK_CARD_BG if is_dark else config.Colors.LIGHT_CARD_BG

        text_prim = config.Colors.DARK_TEXT_PRIMARY if is_dark else config.Colors.LIGHT_TEXT_PRIMARY
        text_sec = config.Colors.DARK_TEXT_SECONDARY if is_dark else config.Colors.LIGHT_TEXT_SECONDARY

        border = config.Colors.DARK_BORDER if is_dark else config.Colors.LIGHT_BORDER
        accent = config.Colors.DARK_ACCENT
        grid_alpha = 0.3 if is_dark else 0.2

        self.graphs_widget.setBackground(bg_color)
        for plot in [self.plot_ecg, self.plot_ppg]:
            plot.getAxis('left').setPen(text_sec)
            plot.getAxis('left').setTextPen(text_sec)
            plot.getAxis('bottom').setPen(text_sec)
            plot.getAxis('bottom').setTextPen(text_sec)
            plot.setTitle(plot.titleLabel.text, color=text_sec, size="10pt")
            plot.showGrid(x=True, y=True, alpha=grid_alpha)

        self.btn_load_file.setStyleSheet(f"""
            QPushButton {{
                background-color: {panel_bg};
                border: 1px dashed {text_sec};
                border-radius: 8px;
                color: {text_prim};
                font-size: 11pt;
            }}
            QPushButton:hover {{
                border: 1px dashed {accent};
                background-color: rgba(0, 212, 170, 0.05);
            }}
        """)

        recent_hover_bg = config.Colors.DARK_BORDER_HOVER if is_dark else "#f0f2f5"

        self.recent_list.setStyleSheet(f"""
            QListWidget {{ background: transparent; border: none; outline: none; }}
            QListWidget::item {{ background: {card_bg}; border-radius: 4px; margin-bottom: 4px; }}
            QListWidget::item:hover {{ background: {recent_hover_bg}; }}
            QListWidget::item:selected {{ background: {border}; border-left: 2px solid {accent}; }}
        """)

        base_style = "border: none; background: transparent;"
        for lbl_name, lbl_meta in self.recent_items_widgets:
            lbl_name.setStyleSheet(f"color: {text_prim}; font-size: 10pt; {base_style}")
            lbl_meta.setStyleSheet(f"color: {text_sec}; font-size: 9pt; {base_style}")

        for card in self.format_cards.values():
            card.update_theme(is_dark)

        self.lbl_time.setStyleSheet(
            f"color: {text_sec}; font-family: {config.FontsConfig.FONT_FAMILY}; font-size: 11pt;")