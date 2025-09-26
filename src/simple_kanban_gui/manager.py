#!/usr/bin/python3

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kanban Card Browser (Qt5)

Um "gestor de ficheros" em cards que navega por pastas e mostra APENAS arquivos
com extensão *.kanban.json. Para cada arquivo, exibe as chaves primárias
"title" e "description" como um card. Pastas aparecem como ícones clicáveis.

Requisitos:
  - PyQt5

Execução:
  python3 kanban_card_browser_qt5.py [diretorio_inicial]

Notas de design:
  - Pastas e arquivos são renderizados como "tiles" num grid responsivo.
  - Apenas diretórios e arquivos *.kanban.json são listados.
  - Duplo clique: entra em pastas. Clique simples no card não abre nada (apenas seleciona).
  - Menu de contexto nos cards: "Open in the default editor" e "Open in the file manager".
"""

import json
import os
import sys
import pathlib
import subprocess
import signal

from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtWidgets import (QApplication, QMainWindow, QFrame, QGridLayout, QFormLayout, QVBoxLayout, QLabel, QStyle, QSizePolicy, QToolButton, QHBoxLayout, QWidget, QMainWindow, QAction, QLineEdit, QInputDialog, QMessageBox, QDialog, QPushButton, QPlainTextEdit, QDialogButtonBox)
from PyQt5.QtGui     import (QPalette, QColor, QMouseEvent, QContextMenuEvent, QIcon, QDesktopServices)
from PyQt5.QtCore    import (Qt, QUrl)

import simple_kanban_gui.about as about
import simple_kanban_gui.modules.configure as configure 
from simple_kanban_gui.desktop import create_desktop_file, create_desktop_directory, create_desktop_menu
from simple_kanban_gui.modules.wabout  import show_about_window

KANBAN_SUFFIX = ".kanban.json"

# Info path
INFO_PATH = os.path.join(os.path.expanduser("~"),".config",about.__package__,"info_path.json")

DEFAULT_INFO_CONTENT =  {   "last_path": os.path.expanduser("~"),
                            "kanban_path": os.path.expanduser("~")
                        }

configure.verify_default_config(INFO_PATH,default_content=DEFAULT_INFO_CONTENT)

INFO=configure.load_config(INFO_PATH)



# Path to config file
CONFIG_PATH = os.path.join(os.path.expanduser("~"),".config",about.__package__,"config_manager.json")

DEFAULT_CONTENT={   "toolbar_home": "Home",
                    "toolbar_home_tooltip": "Go to home directory",
                    "toolbar_up": "Up",
                    "toolbar_up_tooltip": "Go to a directory higher than the current directory",
                    "toolbar_refresh": "Refresh",
                    "toolbar_refresh_tooltip": "Refresh the view the current directory",
                    "toolbar_new_folder": "New folder",
                    "toolbar_new_folder_tooltip": "Create a new folder in the current directory",
                    "toolbar_new_card": "New card",
                    "toolbar_new_card_tooltip": "Create a new card in the current directory",
                    "toolbar_set_kanban": "Set kanban",
                    "toolbar_set_kanban_tooltip": "Set the kanban directory",
                    "toolbar_go_kanban": "Go to kanban",
                    "toolbar_go_kanban_tooltip": "Go to kanban directory",
                    "toolbar_configure": "Configure",
                    "toolbar_configure_tooltip": "Open the configure Json file",
                    "toolbar_about": "About",
                    "toolbar_about_tooltip": "About the program",
                    "toolbar_coffee": "Coffee",
                    "toolbar_coffee_tooltip": "Buy me a coffee (TrucomanX)",
                    "window_width": 1500,
                    "window_height": 800,
                    "window_margin": 4,
                    "window_spacing": 4,
                    "window_current_path": "Current path:",
                    "folder_style": "#FolderTile {border:1px solid rgba(0,0,0,0.08); border-radius:16px; background:white;}",
                    "folder_label_style": "font-weight:600;",
                    "context_menu_style": """
QMenu::item {
    background-color: transparent;
    font-size:14px;
    text-align: left;
    color: #000000;
    padding-left: 12px;
    padding-right: 12px;
}
QMenu::item:selected {
    background-color: transparent;
    font-size:14px;
    text-align: left;
    font-weight: bold;
    color: #000000;
    padding-left: 12px;
    padding-right: 12px;
}
QMenu::item:disabled {
    color: #999;  
    text-decoration: line-through; 
}
                    """,
                    "card_style": """
#KanbanCard {border:1px solid rgba(0,0,0,0.08); border-radius:16px; background:#e0f5e0;}
#KanbanCard QLabel.icon     {background:#e0f5e0;}
#KanbanCard QLabel.filename {background:#e0f5e0; font-size:12px; color:#444;}
#KanbanCard QLabel.title    {background:#e0f5e0; font-size:14px; font-weight:700;}
#KanbanCard QLabel.subtitle {background:#e0f5e0; font-size:14px; color:#444;}
                    """,
                    "folder_margin": 12,
                    "card_margin": 12,
                    "folder_spacing": 6,
                    "card_spacing": 6,
                    "folder_icon_size": 64,
                    "card_icon_size": 24,
                    "open_in_file_manager": "Open in file manager",
                    "edit_title_description": "Edit title/description",
                    "error_reading": "Error reading:",
                    "open_in_default_editor": "Open in the default editor",
                    "reading_permission_denied": "Reading permission denied",
                    "invalid_path": "Invalid path",
                    "error": "Error",
                    "warning": "Warning",
                    "invalid_path": "Current path is not valid:",
                    "directory_name": "Enter directory name:",
                    "folder_exist": "Directory already exists:",
                    "not_create_directory": "Could not create directory:",
                    "filename_empty": "Filename cannot be empty!",
                    "directory_not_exist": "The directory does not exist:",
                    "not_saving_card": "It was not possible to save the card:",
                    "new_card_filename_label":"Filename:",
                    "new_card_filename_default":"Filename (sem extensão)",
                    "new_card_title_label":"Title:",
                    "new_card_title_default":"My title",
                    "new_card_description_label":"Description:",
                    "new_card_description_default":"",
                    "new_card_board": ["To do", "Doing", "Done"],
                    "new_card_board_style": {   "frame":"background-color: #e0f5e0; border: 2px solid #66cc66; padding: 5px; border-radius: 5px;",
                                                "title":"font-weight: bold; background-color: #ccffcc; color:#000000"
                                            },
                    "ok": "OK",
                    "cancel": "Cancel"
                }

configure.verify_default_config(CONFIG_PATH,default_content=DEFAULT_CONTENT)

CONFIG=configure.load_config(CONFIG_PATH)

# ------------------------- Utilidades de Plataforma ------------------------- #

def open_with_default_app(path: str):
    """Abre o arquivo/pasta com o aplicativo padrão do sistema operacional."""
    
    if os.path.isdir(path):
        if sys.platform.startswith("darwin"):
            subprocess.Popen(["open", path])
        elif os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", path])
        return
    else:
        if path.lower().endswith(KANBAN_SUFFIX):
            process = subprocess.Popen(["simple-kanban-gui", path])
            return
# ------------------------------- Widgets UI -------------------------------- #

class FolderTile(QFrame):
    activated = QtCore.pyqtSignal(str)  # caminho

    def __init__(self, path: str, name: str, parent=None):
        super().__init__(parent)
        self.path = path
        self.name = name
        self.setObjectName("FolderTile")

        self.setCursor(Qt.PointingHandCursor)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet(CONFIG["folder_style"])

        lay = QVBoxLayout(self)
        lay.setContentsMargins( CONFIG["folder_margin"],
                                CONFIG["folder_margin"],
                                CONFIG["folder_margin"], 
                                CONFIG["folder_margin"])
        lay.setSpacing(CONFIG["folder_spacing"])

        icon_label = QLabel()
        icon = self.style().standardIcon(QStyle.SP_DirIcon)
        pix = icon.pixmap(CONFIG["folder_icon_size"], CONFIG["folder_icon_size"])
        icon_label.setPixmap(pix)
        icon_label.setAlignment(Qt.AlignCenter)

        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet(CONFIG["folder_label_style"])
        name_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        lay.addWidget(icon_label)
        lay.addWidget(name_label)

    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
        self.activated.emit(self.path)
        super().mouseDoubleClickEvent(e)

    def contextMenuEvent(self, e: QContextMenuEvent) -> None:
        menu = QtWidgets.QMenu(self)
        #menu.setStyleSheet(CONFIG["context_menu_style"])
    
        act_open = menu.addAction(CONFIG["open_in_file_manager"])
        action = menu.exec_(e.globalPos())
        if action == act_open:
            open_with_default_app(self.path)


class KanbanCard(QFrame):
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setObjectName("KanbanCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(CONFIG["card_style"])

        title, description = self._read_title_description(file_path)

        lay = QVBoxLayout(self)
        lay.setContentsMargins( CONFIG["card_margin"], 
                                CONFIG["card_margin"], 
                                CONFIG["card_margin"], 
                                CONFIG["card_margin"])
        lay.setSpacing(CONFIG["card_spacing"])

        # Ícone de arquivo (genérico) + nome base pequeno
        header = QHBoxLayout()
        header.setSpacing(CONFIG["card_spacing"])
        
        #
        icon_label = QLabel()
        icon_label.setObjectName("icon")
        icon_label.setProperty("class", "icon")
        icon = self.style().standardIcon(QStyle.SP_FileIcon)
        pix = icon.pixmap(CONFIG["folder_icon_size"], CONFIG["folder_icon_size"])
        icon_label.setPixmap(pix)
        header.addWidget(icon_label)

        #
        base_name = pathlib.Path(file_path).name
        
        #
        base_lbl = QLabel(base_name)
        base_lbl.setObjectName("filename")
        base_lbl.setProperty("class", "filename")
        base_lbl.setToolTip(file_path)
        base_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        header.addWidget(base_lbl, 1)
        header.addStretch(1)
        lay.addLayout(header)

        #
        title_lbl = QLabel(title)
        title_lbl.setObjectName("title")
        title_lbl.setProperty("class", "title")
        title_lbl.setWordWrap(True)
        title_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)

        #
        desc_lbl = QLabel(description)
        desc_lbl.setObjectName("subtitle")
        desc_lbl.setProperty("class", "subtitle")
        desc_lbl.setWordWrap(True)
        desc_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)

        #
        lay.addWidget(title_lbl)
        lay.addWidget(desc_lbl)
        lay.addStretch(1)

        # Instalar event filter nos labels para repassar double click
        for lbl in [title_lbl, desc_lbl, base_lbl]:
            lbl.installEventFilter(self)

    # --- fora do __init__ ---
    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.MouseButtonDblClick:
            if source in [self.findChild(QLabel, "title"),
                          self.findChild(QLabel, "subtitle"),
                          self.findChild(QLabel, "filename")]:
                open_with_default_app(self.file_path)
                return True  # evento tratado
        return super().eventFilter(source, event)
        
    @staticmethod
    def _read_title_description(file_path: str):
        title = "(sem título)"
        description = ""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                title = str(data.get("title", title))
                description = str(data.get("description", description))
        except Exception as e:
            title = CONFIG["error_reading"]+f" {pathlib.Path(file_path).name}"
            description = str(e)
        return title, description

    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
        # Open in the default editor ao dar duplo clique no card
        open_with_default_app(self.file_path)
        super().mouseDoubleClickEvent(e)

    def contextMenuEvent(self, e: QContextMenuEvent) -> None:
        menu = QtWidgets.QMenu(self)
        #menu.setStyleSheet(CONFIG["context_menu_style"])
        
        act_open = menu.addAction(CONFIG["open_in_default_editor"])
        act_reveal = menu.addAction(CONFIG["open_in_file_manager"])
        act_edit = menu.addAction(CONFIG["edit_title_description"])
        
        action = menu.exec_(e.globalPos())
        if action == act_open:
            open_with_default_app(self.file_path)
        elif action == act_reveal:
            open_with_default_app(str(pathlib.Path(self.file_path).parent))
        elif action == act_edit:
            self.edit_title_description()

    def edit_title_description(self):
        title, description = self._read_title_description(self.file_path)

        dialog = QDialog(self)
        dialog.setWindowTitle(CONFIG["edit_title_description"])
        layout = QGridLayout(dialog)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        # Labels e campos em duas colunas
        layout.addWidget(QLabel(CONFIG["new_card_title_label"]), 0, 0)
        title_edit = QLineEdit(title)
        layout.addWidget(title_edit, 0, 1)

        layout.addWidget(QLabel(CONFIG["new_card_description_label"]), 1, 0)
        desc_edit = QPlainTextEdit(description)
        layout.addWidget(desc_edit, 1, 1)

        # Botões OK/Cancel
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box, 2, 0, 1, 2)

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        if dialog.exec_() == QDialog.Accepted:
            # Salvar no JSON
            try:
                data = {}
                if os.path.exists(self.file_path):
                    with open(self.file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                    data["title"] = title_edit.text().strip()
                    data["description"] = desc_edit.toPlainText().strip()
                    with open(self.file_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                
                # atualizar labels
                self.findChild(QLabel, "title").setText(data["title"])
                self.findChild(QLabel, "subtitle").setText(data["description"])
            except Exception as ex:
                QMessageBox.critical(self, "Error", f"Failed to save: {ex}")

# ------------------------------- Navegador --------------------------------- #

class GridView(QtWidgets.QScrollArea):
    """ScrollArea que organiza child widgets em um grid responsivo.

    Use setItems(widgets) para (re)popular. Relayout automático no resize.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.viewport().setStyleSheet("background:white;")

        container = QWidget()
        self._grid = QtWidgets.QGridLayout(container)
        self._grid.setContentsMargins(12, 12, 12, 12)
        self._grid.setHorizontalSpacing(12)
        self._grid.setVerticalSpacing(12)
        self.setWidget(container)

        self._items = []  # type: list[QWidget]
        self._preferred_tile_width = 280  # px

    def setItems(self, widgets: list[QWidget]):
        # Limpar
        self._items = widgets
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        # Ajustar altura igual
        max_height = 0
        for w in widgets:
            w.setMinimumHeight(0)
            w.setMaximumHeight(16777215)
            max_height = max(max_height, w.sizeHint().height())
        for w in widgets:
            w.setFixedHeight(max_height)
        self._relayout()

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        super().resizeEvent(e)
        self._relayout()

    def _relayout(self):
        if not self._items:
            return
        area_w = self.viewport().width() - self._grid.contentsMargins().left() - self._grid.contentsMargins().right()
        cols = max(1, area_w // (self._preferred_tile_width + self._grid.horizontalSpacing()))
        # Reposicionar
        row = 0
        col = 0
        for w in self._items:
            self._grid.addWidget(w, row, col)
            w.setMinimumWidth(self._preferred_tile_width)
            w.setMaximumWidth(self._preferred_tile_width)
            col += 1
            if col >= cols:
                col = 0
                row += 1

class NewCardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New card")
        self.resize(400, 200)

        layout = QVBoxLayout(self)

        # Campos
        form_layout = QFormLayout()

        self.filename_edit = QLineEdit(self)
        self.filename_edit.setPlaceholderText(CONFIG["new_card_filename_default"])
        form_layout.addRow(QLabel(CONFIG["new_card_filename_label"]), self.filename_edit)

        self.title_edit = QLineEdit(self)
        self.title_edit.setPlaceholderText(CONFIG["new_card_title_default"])
        form_layout.addRow(QLabel(CONFIG["new_card_title_label"]), self.title_edit)

        self.desc_edit = QPlainTextEdit(self)
        self.desc_edit.setPlaceholderText(CONFIG["new_card_description_default"])
        form_layout.addRow(QLabel(CONFIG["new_card_description_label"]), self.desc_edit)

        layout.addLayout(form_layout)

        # Botões
        self.ok_btn = QPushButton(CONFIG["ok"], self)
        self.ok_btn.clicked.connect(self.accept)
        layout.addWidget(self.ok_btn)

        self.cancel_btn = QPushButton(CONFIG["cancel"], self)
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn)

    def get_data(self):
        return (
            self.filename_edit.text().strip(),
            self.title_edit.text().strip(),
            self.desc_edit.toPlainText().strip()
        )

class MainWindow(QMainWindow):
    def __init__(self, start_dir: str):
        super().__init__()
        self.setWindowTitle(about.__manager_name__)
        self.resize(CONFIG["window_width"], CONFIG["window_height"])
        self._current_dir = pathlib.Path(start_dir).resolve()

        ## Icon
        # Get base directory for icons
        base_dir_path = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = os.path.join(base_dir_path, 'icons', 'logo.png')
        self.setWindowIcon(QIcon(self.icon_path)) 

        # ---------------- Toolbar (apenas ações) ---------------- #
        self.create_toolbar()
        
        # ---------------- Widget central ---------------- #
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins( CONFIG["window_margin"], 
                                        CONFIG["window_margin"], 
                                        CONFIG["window_margin"], 
                                        CONFIG["window_margin"])
        main_layout.setSpacing(CONFIG["window_spacing"])

        # ---------------- Path Layout ---------------- #
        path_layout = QHBoxLayout()
        path_layout.setSpacing(CONFIG["window_spacing"])
        path_layout.addWidget(QtWidgets.QLabel(CONFIG["window_current_path"]))

        self.path_edit = QLineEdit()
        self.path_edit.returnPressed.connect(self._emit_path)
        path_layout.addWidget(self.path_edit, 1)  # ocupa espaço restante
        main_layout.addLayout(path_layout)

        # ---------------- Grid ---------------- #
        self.grid = GridView()
        main_layout.addWidget(self.grid, 1)

        # ---------------- Inicializa ---------------- #
        self.navigate_to(str(self._current_dir))

    def create_toolbar(self):

        self.toolbar = QtWidgets.QToolBar("Principal")
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(self.toolbar)

        # Go kanban
        act_gokanban = QAction(QIcon(self.icon_path), CONFIG["toolbar_go_kanban"], self)
        act_gokanban.setToolTip(CONFIG["toolbar_go_kanban_tooltip"])
        act_gokanban.triggered.connect(self.go_kanban_path)
        self.toolbar.addAction(act_gokanban)
        
        # Home
        act_home = QAction(QIcon.fromTheme("go-home"), CONFIG["toolbar_home"], self)
        act_home.setToolTip(CONFIG["toolbar_home_tooltip"])
        act_home.triggered.connect(self.goto_home)
        self.toolbar.addAction(act_home)

        # Up
        act_up = QAction(QIcon.fromTheme("go-up"), CONFIG["toolbar_up"], self)
        act_up.setToolTip(CONFIG["toolbar_up_tooltip"])
        act_up.triggered.connect(self.go_up)
        self.toolbar.addAction(act_up)

        # Refresh
        act_refresh = QAction(QIcon.fromTheme("view-refresh"), CONFIG["toolbar_refresh"], self)
        act_refresh.setToolTip(CONFIG["toolbar_refresh_tooltip"])
        act_refresh.triggered.connect(self.refresh)
        self.toolbar.addAction(act_refresh)

        # Criar diretório
        act_newdir = QAction(QIcon.fromTheme("folder-new"), CONFIG["toolbar_new_folder"], self)
        act_newdir.setToolTip(CONFIG["toolbar_new_folder_tooltip"])
        act_newdir.triggered.connect(self.create_new_dir)
        self.toolbar.addAction(act_newdir)

        # Criar card
        act_newcard = QAction(QIcon.fromTheme("document-new"), CONFIG["toolbar_new_card"], self)
        act_newcard.setToolTip(CONFIG["toolbar_new_card_tooltip"])
        act_newcard.triggered.connect(self.create_new_card)
        self.toolbar.addAction(act_newcard)

        # Adicionar o espaçador
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar.addWidget(spacer)
        
        # Set kanban
        act_setkanban = QAction(QIcon.fromTheme("go-jump"), CONFIG["toolbar_set_kanban"], self)
        act_setkanban.setToolTip(CONFIG["toolbar_set_kanban_tooltip"])
        act_setkanban.triggered.connect(self.set_kanban_path)
        self.toolbar.addAction(act_setkanban)
        
        #
        self.configure_action = QAction(QIcon.fromTheme("document-properties"), CONFIG["toolbar_configure"], self)
        self.configure_action.setToolTip(CONFIG["toolbar_configure_tooltip"])
        self.configure_action.triggered.connect(self.open_configure_editor)
        self.toolbar.addAction(self.configure_action)
        
        #
        self.coffee_action = QAction(CONFIG["toolbar_coffee"], self)
        self.coffee_action.setIcon(QIcon.fromTheme("emblem-favorite"))
        self.coffee_action.setToolTip(CONFIG["toolbar_coffee_tooltip"])
        self.coffee_action.triggered.connect(self.on_coffee_action_click)
        self.toolbar.addAction(self.coffee_action)
        
        #
        self.about_action = QAction(QIcon.fromTheme('help-about'), CONFIG["toolbar_about"], self)
        self.about_action.triggered.connect(self.open_about)
        self.about_action.setToolTip(CONFIG["toolbar_about_tooltip"])
        self.toolbar.addAction(self.about_action)

    def set_kanban_path(self):
        INFO["kanban_path"] = str(self._current_dir)
        configure.save_config(INFO_PATH,INFO)
    
    def go_kanban_path(self):
        self.navigate_to(str(INFO["kanban_path"]))
    
    def create_new_card(self):
        dialog = NewCardDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            filename, title, description = dialog.get_data()

            if not filename:
                QMessageBox.warning(self, CONFIG["error"], CONFIG["filename_empty"])
                return

            dir_path = self.path_edit.text().strip()
            if not os.path.isdir(dir_path):
                QMessageBox.warning(self, CONFIG["error"], CONFIG["directory_not_exist"]+f"\n{dir_path}")
                return

            if filename.endswith(KANBAN_SUFFIX):
                filepath = os.path.join(dir_path, filename)
            else:
                filepath = os.path.join(dir_path, filename + KANBAN_SUFFIX)

            Boards=[]
            for board_name in CONFIG["new_card_board"]:
                Boards.append(  { "title": board_name,
                                  "notes": [],
                                  "style": CONFIG["new_card_board_style"] })

            data = {
                "title": title,
                "description": description,
                "boards": Boards
            }

            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                self.refresh()
                #QMessageBox.information(self, "Sucesso", f"Card salvo em:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, CONFIG["error"], CONFIG["not_saving_card"]+f"\n{e}")

    def open_configure_editor(self):
        if os.name == 'nt':  # Windows
            os.startfile(CONFIG_PATH)
        elif os.name == 'posix':  # Linux/macOS
            subprocess.run(['xdg-open', CONFIG_PATH])
            
    def create_new_dir(self):
        base_path = self.path_edit.text().strip()
        if not os.path.isdir(base_path):
            QMessageBox.warning(self, CONFIG["error"], CONFIG["invalid_path"] + f"\n{base_path}")
            return

        dir_name, ok = QInputDialog.getText(self, CONFIG["toolbar_new_folder"], CONFIG["directory_name"])
        if ok and dir_name.strip():
            new_path = os.path.join(base_path, dir_name.strip())
            if os.path.exists(new_path):
                QMessageBox.warning(self, CONFIG["warning"], CONFIG["folder_exist"] + f"\n{new_path}")
            else:
                try:
                    os.makedirs(new_path)
                    #QMessageBox.information(self, "Success", f"Directory created:\n{new_path}")
                    self.refresh()  # atualiza a visão, se houver
                except Exception as e:
                    QMessageBox.critical(self, CONFIG["error"], CONFIG["not_create_directory"] + f"\n{e}")


    def on_coffee_action_click(self):
        QDesktopServices.openUrl(QUrl("https://ko-fi.com/trucomanx"))

    def open_about(self):
        data={
            "version": about.__version__,
            "package": about.__package__,
            "program_name": about.__manager_name__,
            "author": about.__author__,
            "email": about.__email__,
            "description": about.__description__,
            "url_source": about.__url_source__,
            "url_doc": about.__url_doc__,
            "url_funding": about.__url_funding__,
            "url_bugs": about.__url_bugs__
        }
        show_about_window(data,self.icon_path)

    def _emit_path(self):
        current_path = self.path_edit.text().strip()
        self.navigate_to(current_path)


    def goto_home(self):
        self.navigate_to(str(pathlib.Path.home()))

    # ---------------- Navegação ---------------- #
    def go_up(self):
        parent = self._current_dir.parent
        self.navigate_to(str(parent))

    def refresh(self):
        self.navigate_to(str(self._current_dir))

    def navigate_to(self, path: str):
        p = pathlib.Path(path).expanduser()
        if not p.exists() or not p.is_dir():
            QtWidgets.QMessageBox.warning(self, CONFIG["invalid_path"], f"{p}")
            return
        self._current_dir = p.resolve()
        self.path_edit.setText(str(self._current_dir))
        self._populate()
        
        INFO["last_path"] = str(self._current_dir)
        configure.save_config(INFO_PATH,INFO)

    # ----------------------------- Listagem --------------------------------- #
    def _populate(self):
        folders: list[FolderTile] = []
        cards: list[KanbanCard] = []

        try:
            ## Inclui arquivos ocultos
            #entries = list(os.scandir(self._current_dir))
            entries = [e for e in os.scandir(self._current_dir) if not e.name.startswith(".")]

        except PermissionError:
            QtWidgets.QMessageBox.critical(self, CONFIG["reading_permission_denied"], f"{self._current_dir}")
            return

        # Diretórios primeiro, nome ordenado
        for e in sorted([x for x in entries if x.is_dir()], key=lambda d: d.name.lower()):
            tile = FolderTile(e.path, e.name)
            tile.activated.connect(self.navigate_to)
            folders.append(tile)

        # Arquivos *.kanban.json
        files = [x for x in entries if x.is_file() and x.name.lower().endswith(KANBAN_SUFFIX)]

        # Pré-carregar títulos para ordenar pelos títulos caso disponíveis
        def read_title(fp: str) -> str:
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return str(data.get("title", ""))
            except Exception:
                pass
            return ""

        files_sorted = sorted(files, key=lambda f: (read_title(f.path).lower(), f.name.lower()))
        for f in files_sorted:
            cards.append(KanbanCard(f.path))

        self.grid.setItems(folders + cards)


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    create_desktop_directory()    
    create_desktop_menu()
    create_desktop_file(os.path.join("~",".local","share","applications"), 
                        program_name=about.__manager_name__)
    
    filepath = os.getcwd()
    if(len(sys.argv)==2):
        if sys.argv[1] == "--autostart":
            create_desktop_directory(overwrite = True)
            create_desktop_menu(overwrite = True)
            create_desktop_file(os.path.join("~",".config","autostart"), 
                                overwrite=True, 
                                program_name=about.__manager_name__)
            return
            
        if sys.argv[1] == "--applications":
            create_desktop_directory(overwrite = True)
            create_desktop_menu(overwrite = True)
            create_desktop_file(os.path.join("~",".local","share","applications"), 
                                overwrite=True, 
                                program_name=about.__manager_name__)
            return
        
        if sys.argv[1] == "--last-path":
            filepath = INFO["last_path"]

        if os.path.exists(sys.argv[1]):
            filepath = sys.argv[1]
    else:
        for n in range(len(sys.argv)):
            if sys.argv[n] == "--autostart":
                create_desktop_directory(overwrite = True,program_name=about.__manager_name__)
                create_desktop_menu(overwrite = True)
                create_desktop_file(os.path.join("~",".config","autostart"), overwrite=True)
                return
            if sys.argv[n] == "--applications":
                create_desktop_directory(overwrite = True,program_name=about.__manager_name__)
                create_desktop_menu(overwrite = True)
                create_desktop_file(os.path.join("~",".local","share","applications"), overwrite=True)
                return

            if sys.argv[n] == "--last-path":
                filepath = INFO["last_path"]
    
    app = QApplication(sys.argv)
    app.setStyleSheet(CONFIG["context_menu_style"])
    app.setApplicationName(about.__manager_name__) 
    
    # Aparência sutil
    #app.setStyle("Imagine") # "Fusion"
    #palette = app.palette()
    #palette.setColor(QPalette.Window, QColor("#f7f7f8"))
    #palette.setColor(QPalette.Base, QColor("#ffffff"))
    #app.setPalette(palette)

    w = MainWindow(filepath)
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

