from resources import config


def get_stylesheet(theme='dark'):
    if theme == 'dark':
        return f"""
        /* ======================================================= */
        /* 1. USTAWIENIA GLOBALNE (Fundamenty)                     */
        /* ======================================================= */
        QWidget {{
            font-family: "{config.FontsConfig.FONT_FAMILY}";
            font-size: {config.FontsConfig.FONT_SIZE}pt;
            color: {config.Colors.DARK_TEXT_PRIMARY};
        }}
        QMainWindow {{
            background-color: {config.Colors.DARK_BACKGROUND};
        }}

        /* ======================================================= */
        /* 2. GŁÓWNE ELEMENTY STRUKTURALNE (Paski, Sidebary)       */
        /* ======================================================= */
        QFrame#Sidebar {{
            background-color: {config.Colors.DARK_PANEL_BG};
            border-right: 0px solid {config.Colors.DARK_BORDER};
            border-top: 1px solid {config.Colors.DARK_BORDER};
            border-bottom: 1px solid {config.Colors.DARK_BORDER};
            border-top-right-radius: 2px;
            border-bottom-right-radius: 2px;
        }}

        QTabBar::tab {{
            background: transparent;
            padding: 8px 15px;
            color: {config.Colors.DARK_TEXT_SECONDARY};
            border: none;     
        }}
        QTabBar::tab:hover {{
            color: {config.Colors.DARK_ACCENT};
            border-bottom: 2px solid {config.Colors.DARK_BORDER};
        }}
        QTabBar::tab:selected {{
            color: {config.Colors.DARK_ACCENT};
            border-bottom: 2px solid {config.Colors.DARK_ACCENT};
        }}

        /* ======================================================= */
        /* 3. KONTENERY I SEKCJE (Klasy dynamiczne)                */
        /* ======================================================= */
        QFrame[cssClass="panel"] {{
            background-color: {config.Colors.DARK_BACKGROUND};
            border: 1px solid {config.Colors.DARK_BORDER};
            border-radius: 2px;
            padding: 0px;
        }}
        QFrame[cssClass="card"] {{
            background-color: #0d0f1a; 
            border: 1px solid {config.Colors.DARK_BORDER};
            border-radius: 6px;
        }}
        QFrame[cssClass="conn-panel"] {{
            background-color: #0a0c14; 
            border-bottom: 1px solid {config.Colors.DARK_BORDER};
        }}
        QFrame[cssClass="toolbar"] {{
            background-color: {config.Colors.DARK_PANEL_BG};
            border-bottom: 1px solid {config.Colors.DARK_BORDER};
            border-top: 1px solid {config.Colors.DARK_BORDER};
        }}
        QFrame[cssClass="kanaly"] {{
            background-color: {config.Colors.DARK_BACKGROUND};
            border-right: 1px solid {config.Colors.DARK_BORDER};
        }}

        /* ======================================================= */
        /* 4. KONTROLKI WEJŚCIOWE (Przyciski, Listy, Pola wyboru)  */
        /* ======================================================= */

        /* --- PRZYCISKI (Zwykłe) --- */
        QPushButton {{
            background-color: transparent;
            color: {config.Colors.DARK_TEXT_SECONDARY};
            border: 1px solid {config.Colors.DARK_BORDER};
            border-radius: 5px;
            padding: 4px 10px;
            min-height: 20px;
        }}
        QPushButton:hover {{
            background-color: {config.Colors.DARK_PANEL_BG};
            color: {config.Colors.DARK_TEXT_PRIMARY};
        }}
        QPushButton:pressed {{
            background-color: {config.Colors.DARK_BORDER};
        }}

        /* --- PRZYCISKI (Warianty CSS) --- */
        QPushButton[cssClass="primary"] {{
            border-color: {config.Colors.POSITIVE_STATUS};
            color: {config.Colors.LIGHT_ACCENT};
        }}
        QPushButton[cssClass="primary"]:hover {{
            background-color: {config.Colors.DARK_PANEL_BG};
        }}
        QPushButton[cssClass="danger"] {{
            border-color: {config.Colors.HEART_COLOR};
            color: {config.Colors.HEART_COLOR};
        }}
        QPushButton[cssClass="danger-active"] {{
            background-color: #220a0d; 
            color: #ff4455;
            border-color: {config.Colors.HEART_COLOR};
        }}

        /* --- LISTY ROZWIJANE (QComboBox) --- */
        QComboBox {{
                    combobox-popup: 0;
                    border: 1px solid {config.Colors.DARK_BORDER};
                    border-radius: 5px;
                    padding: 4px 10px;
                    min-width: 200px;
                    min-height: 20px;
                    font-size: 16px;
                    background-color: {config.Colors.DARK_PANEL_BG};
                    color: {config.Colors.DARK_TEXT_PRIMARY};
                    margin: 0px; 
        }}
        QComboBox:hover {{
            border: 1px solid {config.Colors.DARK_ACCENT};
        }}
        
        /* 1. KONTENER STRZAŁKI (Usuwa artefakty i ma zaokrąglone prawe rogi) */
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 24px;
            border-left: 1px solid {config.Colors.DARK_BORDER}; /* Elegancki separator */
            border-top-right-radius: 5px; 
            border-bottom-right-radius: 5px;
            background-color: transparent;
        }}
        QComboBox::drop-down:hover {{
            background-color: {config.Colors.DARK_PANEL_BG};
        }}

        /* 2. RYSOWANIE STRZAŁKI KODEM (CSS Triangle Hack) */
        QComboBox::down-arrow {{
            width: 0px;
            height: 0px;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {config.Colors.DARK_TEXT_SECONDARY}; /* Kolor samej strzałki */
            margin-top: 2px;
        }}
        QComboBox::down-arrow:hover {{
            border-top: 5px solid {config.Colors.DARK_ACCENT}; /* Zielona po najechaniu! */
        }}

        /* 3. ROZWIJANA LISTA (Menu) */
        QComboBox QAbstractItemView {{
            background-color: {config.Colors.DARK_PANEL_BG};
            color: {config.Colors.DARK_TEXT_PRIMARY};
            border: 1px solid {config.Colors.DARK_BORDER};
            border-radius: 5px;
            selection-background-color: {config.Colors.DARK_ACCENT};
            selection-color: {config.Colors.DARK_BACKGROUND}; 
            outline: none; 
        }}
        
        /* --- ELEMENTY LISTY --- */
        
        QComboBox::item:selected, QComboBox::item:hover {{
            background-color: {config.Colors.DARK_ACCENT};
            color: {config.Colors.DARK_BACKGROUND};
        }}
        
        /* --- PTASZEK (Wskaźnik zaznaczenia) --- */
        QComboBox::indicator {{
            width: 14px;
            height: 14px;
            margin-left: 5px; /* Lekkie odsunięcie ptaszka od lewej krawędzi */
        }}

        /* --- CHECKBOXY --- */
        QCheckBox {{
            color: {config.Colors.DARK_TEXT_SECONDARY};
            spacing: 8px; 
        }}
        QCheckBox:hover {{
            color: {config.Colors.DARK_TEXT_PRIMARY};
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            background-color: {config.Colors.DARK_BACKGROUND};
            border: 1px solid {config.Colors.DARK_BORDER};
            border-radius: 4px;
        }}
        QCheckBox::indicator:hover {{
            border: 1px solid {config.Colors.DARK_ACCENT};
        }}
        QCheckBox::indicator:checked {{
            background-color: {config.Colors.DARK_ACCENT};
            border: 1px solid {config.Colors.DARK_ACCENT};
        }}

        /* --- RADIO BUTTONS (Sidebar) --- */
        QRadioButton {{
            color: {config.Colors.DARK_TEXT_SECONDARY};
            spacing: 8px;
        }}
        QRadioButton:hover {{
            color: {config.Colors.DARK_TEXT_PRIMARY};
        }}
        QRadioButton::indicator {{
                    width: 12px;
                    height: 12px;
                    background-color: transparent;
                    border: 1px solid {config.Colors.DARK_BORDER}; 
                    border-radius: 7px; 
                    margin: 2px; 
                }}
        QRadioButton::indicator:hover {{
            border: 1px solid {config.Colors.DARK_ACCENT};
        }}
        QRadioButton::indicator:checked {{
            background-color: {config.Colors.DARK_BACKGROUND};
            border: 2px solid {config.Colors.DARK_ACCENT}; 
        }}
        /* --- ODZNAKI STATUSU (Badges) --- */
        QLabel[cssClass="badge-ok"] {{
            background-color: {config.Colors.STATUS_OK_BG};
            color: {config.Colors.STATUS_OK_TEXT};
            padding: 4px 8px;
            border-radius: 10px;
        }}
        QLabel[cssClass="badge-err"] {{
            background-color: {config.Colors.STATUS_ERR_BG};
            color: {config.Colors.STATUS_ERR_TEXT};
            padding: 4px 8px;
            border-radius: 10px;
        }}
        QFrame#SidebarSeparator {{
            background-color: {config.Colors.DARK_BORDER};
            min-height: 1px;
            max-height: 1px;
            margin: 5px 0px;
        }}
        /* --- NAGŁÓWKI SEKCJI --- */
        QLabel[cssClass="section-title"] {{
                    color: {config.Colors.DARK_TEXT_MUTED}; 
                    font-size: 9pt; 
                    font-weight: bold; 
                    letter-spacing: 1px;
                    text-transform: uppercase;
                    padding: 0px;
                    margin-bottom: 5px;
        }}
        QLabel[cssClass="card-title"] {{
                    color: {config.Colors.DARK_TEXT_SECONDARY}; 
                    font-size: 10pt; 
                    font-weight: bold;
        }}
                        
        """

    elif theme == 'light':
        return f"""
                /* ======================================================= */
                /* MOTYW JASNY (LIGHT THEME)                               */
                /* ======================================================= */
                QWidget {{
                    font-family: "{config.FontsConfig.FONT_FAMILY}";
                    font-size: {config.FontsConfig.FONT_SIZE}pt;
                    color: {config.Colors.LIGHT_TEXT_PRIMARY};
                    
                }}
                QMainWindow {{
                    background-color: {config.Colors.LIGHT_BACKGROUND};
                }}

                QFrame#Sidebar {{
                    background-color: {config.Colors.LIGHT_PANEL_BG};
                    border-right: 1px solid {config.Colors.LIGHT_BORDER};
                    border-top: 1px solid {config.Colors.LIGHT_BORDER};
                    border-bottom: 1px solid {config.Colors.LIGHT_BORDER};
                }}

                QTabBar::tab {{
                    background: transparent;
                    padding: 8px 15px;
                    color: {config.Colors.LIGHT_TEXT_SECONDARY};
                    border: none;     
                }}
                QTabBar::tab:hover {{
                    color: {config.Colors.DARK_ACCENT};
                    border-bottom: 2px solid {config.Colors.LIGHT_BORDER};
                }}
                QTabBar::tab:selected {{
                    color: {config.Colors.DARK_ACCENT};
                    border-bottom: 2px solid {config.Colors.DARK_ACCENT};
                }}

                QFrame[cssClass="panel"] {{
                    background-color: {config.Colors.LIGHT_BACKGROUND};
                    border: 1px solid {config.Colors.LIGHT_BORDER};
                    border-radius: 2px;
                    padding: 0px;
                }}
                QFrame[cssClass="card"] {{
                    background-color: {config.Colors.LIGHT_CARD_BG}; 
                    border: 1px solid {config.Colors.LIGHT_BORDER};
                    border-radius: 6px;
                }}
                QFrame[cssClass="conn-panel"] {{
                    background-color: {config.Colors.LIGHT_CONN_BG}; 
                    border-bottom: 1px solid {config.Colors.LIGHT_BORDER};
                }}
                QFrame[cssClass="toolbar"] {{
                    background-color: {config.Colors.LIGHT_PANEL_BG};
                    border-bottom: 1px solid {config.Colors.LIGHT_BORDER};
                    border-top: 1px solid {config.Colors.LIGHT_BORDER};
                }}
                QFrame[cssClass="kanaly"] {{
                    background-color: {config.Colors.LIGHT_BACKGROUND};
                    border-right: 1px solid {config.Colors.LIGHT_BORDER};
                }}

                QPushButton {{
                    background-color: transparent;
                    color: {config.Colors.LIGHT_TEXT_SECONDARY};
                    border: 1px solid {config.Colors.LIGHT_BORDER};
                    border-radius: 5px;
                    padding: 4px 10px;
                    min-height: 20px;
                }}
                QPushButton:hover {{
                    background-color: {config.Colors.LIGHT_BACKGROUND};
                    color: {config.Colors.LIGHT_TEXT_PRIMARY};
                    border-color: {config.Colors.LIGHT_BORDER_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {config.Colors.LIGHT_BORDER};
                }}

                QPushButton[cssClass="primary"] {{
                    border-color: {config.Colors.DARK_ACCENT};
                    color: {config.Colors.DARK_ACCENT};
                }}
                QPushButton[cssClass="primary"]:hover {{
                    background-color: {config.Colors.LIGHT_BACKGROUND};
                }}
                QPushButton[cssClass="danger"] {{
                    border-color: {config.Colors.HEART_COLOR};
                    color: {config.Colors.HEART_COLOR};
                }}
                QPushButton[cssClass="danger-active"] {{
                    background-color: {config.Colors.LIGHT_STATUS_ERR_BG}; 
                    color: {config.Colors.HEART_COLOR};
                    border-color: {config.Colors.HEART_COLOR};
                }}

                QComboBox {{
                    combobox-popup: 0;
                    border: 1px solid {config.Colors.LIGHT_BORDER};
                    border-radius: 5px;
                    padding: 4px 10px;
                    min-width: 200px;
                    min-height: 20px;
                    font-size: 16px;
                    background-color: {config.Colors.LIGHT_PANEL_BG};
                    color: {config.Colors.LIGHT_TEXT_PRIMARY};
                    margin: 0px; 
                }}
                QComboBox:hover {{
                    border: 1px solid {config.Colors.DARK_ACCENT};
                }}

                QComboBox::drop-down {{
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 24px;
                    border-left: 1px solid {config.Colors.LIGHT_BORDER};
                    border-top-right-radius: 5px; 
                    border-bottom-right-radius: 5px;
                    background-color: transparent;
                }}
                QComboBox::drop-down:hover {{
                    background-color: {config.Colors.LIGHT_BACKGROUND};
                }}
                QComboBox::down-arrow {{
                    width: 0px;
                    height: 0px;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 5px solid {config.Colors.LIGHT_TEXT_SECONDARY};
                    margin-top: 2px;
                }}
                QComboBox::down-arrow:hover {{
                    border-top: 5px solid {config.Colors.DARK_ACCENT};
                }}

                QComboBox QAbstractItemView {{
                    background-color: {config.Colors.LIGHT_PANEL_BG};
                    color: {config.Colors.LIGHT_TEXT_PRIMARY};
                    border: 1px solid {config.Colors.LIGHT_BORDER};
                    selection-background-color: {config.Colors.DARK_ACCENT};
                    selection-color: {config.Colors.LIGHT_PANEL_BG}; 
                    outline: none;
                    border-radius: 5px; /* Usuwa zaokrąglenia na liście */
                    padding: 2px;
                    
                    }}
                
                QComboBox::item:selected, QComboBox::item:hover {{
                    background-color: {config.Colors.DARK_ACCENT};
                    color: {config.Colors.LIGHT_PANEL_BG};
                    
                }}
                QComboBox::indicator {{
                    width: 14px;
                    height: 14px;
                    margin-left: 5px;
                    
                }}
                

                QCheckBox {{
                    color: {config.Colors.LIGHT_TEXT_SECONDARY};
                    spacing: 8px; 
                }}
                QCheckBox:hover {{
                    color: {config.Colors.LIGHT_TEXT_PRIMARY};
                }}
                QRadioButton::indicator {{
                    width: 12px;
                    height: 12px;
                    background-color: transparent;
                    border: 1px solid {config.Colors.DARK_BORDER}; 
                    border-radius: 7px; 
                    margin: 2px; 
                }}
                QCheckBox::indicator:hover {{
                    border: 1px solid {config.Colors.DARK_ACCENT};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {config.Colors.DARK_ACCENT};
                    border: 1px solid {config.Colors.DARK_ACCENT};
                }}

                QRadioButton {{
                    color: {config.Colors.LIGHT_TEXT_SECONDARY};
                    spacing: 8px;
                }}
                QRadioButton:hover {{
                    color: {config.Colors.LIGHT_TEXT_PRIMARY};
                }}
                QRadioButton::indicator {{
                    width: 12px;
                    height: 12px;
                    background-color: {config.Colors.LIGHT_PANEL_BG};
                    border: 1px solid {config.Colors.LIGHT_BORDER};
                    border-radius: 7px; 
                }}
                QRadioButton::indicator:hover {{
                    border: 1px solid {config.Colors.DARK_ACCENT};
                }}
                QRadioButton::indicator:checked {{
                    background-color: {config.Colors.LIGHT_PANEL_BG};
                    border: 1px solid {config.Colors.DARK_ACCENT}; 
                }}
                /* --- ODZNAKI STATUSU (Badges) --- */
                QLabel[cssClass="badge-ok"] {{
                    background-color: {config.Colors.LIGHT_STATUS_OK_BG};
                    color: {config.Colors.LIGHT_STATUS_OK_TEXT};
                    padding: 4px 8px;
                    border-radius: 10px;
                }}
                QLabel[cssClass="badge-err"] {{
                    background-color: {config.Colors.LIGHT_STATUS_ERR_BG};
                    color: {config.Colors.LIGHT_STATUS_ERR_TEXT};
                    padding: 4px 8px;
                    border-radius: 10px;
                }}
                QFrame#SidebarSeparator {{
                    background-color: {config.Colors.LIGHT_ACCENT};
                    min-height: 1px;
                    max-height: 1px;
                    margin: 5px 0px;
                    }}
                /* --- NAGŁÓWKI SEKCJI --- */
                QLabel[cssClass="section-title"] {{
                    color: {config.Colors.LIGHT_TEXT_MUTED}; 
                    font-size: 9pt; 
                    font-weight: bold; 
                    letter-spacing: 1px;
                    text-transform: uppercase;
                    padding: 0px;
                    margin-bottom: 5px;
                }}
                QLabel[cssClass="card-title"] {{
                    color: {config.Colors.LIGHT_TEXT_SECONDARY}; 
                    font-size: 10pt; 
                    font-weight: bold;
                }}
                """