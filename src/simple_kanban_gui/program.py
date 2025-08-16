import sys
import json
import os
import signal
import subprocess

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QScrollArea, QLineEdit, QFileDialog, QToolBar,
    QMainWindow, QAction, QMessageBox, QSizePolicy, QFrame
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QMimeData, QByteArray, QDataStream, QIODevice, QUrl
from PyQt5.QtGui import QFontMetrics, QDesktopServices
from PyQt5 import QtGui



import simple_kanban_gui.about as about
import simple_kanban_gui.modules.configure as configure 
from simple_kanban_gui.desktop import create_desktop_file, create_desktop_directory, create_desktop_menu
from simple_kanban_gui.modules.wabout  import show_about_window

# Path to config file
CONFIG_PATH = os.path.join(os.path.expanduser("~"),".config",about.__package__,"config.json")

DEFAULT_CONTENT={   "toolbar_new_kanban": "New kanban",
                    "toolbar_new_kanban_tooltip": "New kanban window",
                    "toolbar_add_column": "Add board",
                    "toolbar_add_column_tooltip": "Add new frame",
                    "toolbar_save": "Save",
                    "toolbar_save_tooltip": "Save data to JSON file",
                    "toolbar_save_as": "Save as",
                    "toolbar_save_as_tooltip": "Save data to JSON file",
                    "toolbar_load": "Load",
                    "toolbar_load_tooltip": "Load data from Json file",
                    "toolbar_configure": "Configure",
                    "toolbar_configure_tooltip": "Open the configure Json file",
                    "toolbar_about": "About",
                    "toolbar_about_tooltip": "About the program",
                    "toolbar_coffee": "Coffee",
                    "toolbar_coffee_tooltip": "Buy me a coffee (TrucomanX)",
                    "window_filename": "Filename:",
                    "window_path_problems": "Path problems!",
                    "window_error_loading": "Error when loading:",
                    "window_width": 1500,
                    "window_height": 800,
                    "kanban_title_label":"Title",
                    "kanban_title_default":"My title",
                    "kanban_description_label":"Description",
                    "kanban_description_default":"",
                    "board_startup_list": ["To do", "Doing", "Done"],
                    "board_style": {"frame":"background-color: #e0f5e0; border: 2px solid #66cc66; padding: 5px; border-radius: 5px;","title":"font-weight: bold; background-color: #ccffcc; color:#000000"},
                    "board_title": "New board",
                    "board_new_note": "Add a new note",
                    "board_delete": "Remove board",
                    "board_interchange_right": "Interchange board with the right",
                    "board_width": 350,
                    "note_style": {"frame":"background-color: #ffffff; border: 1px solid #cccccc; border-radius: 5px;"},
                    "note_title": "Initial title",
                    "note_content": "Hi",
                    "note_expand_compress": "Expand/Compress content",
                    "note_remove": "Remove note"
                }

configure.verify_default_config(CONFIG_PATH,default_content=DEFAULT_CONTENT)

CONFIG=configure.load_config(CONFIG_PATH)



class NoteWidget(QWidget):
    def __init__(self, title="", content=""):
        super().__init__()
        self.setAcceptDrops(True)
        self.layout = QVBoxLayout(self)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(CONFIG["note_style"]["frame"])

        
        self.title_edit = QLineEdit(title)
        self.title_edit.setCursorPosition(0)
        self.title_edit.setToolTip(title)
        self.title_edit.returnPressed.connect(self.on_title_enter)
        
        self.content_edit = QTextEdit()
        self.content_edit.setPlainText(content)
        self.content_edit.setVisible(False)

        self.toggle_btn = QPushButton()
        self.toggle_btn.setIcon(QIcon.fromTheme("insert-text"))
        self.toggle_btn.setToolTip(CONFIG["note_expand_compress"])
        self.toggle_btn.clicked.connect(self.toggle_content)

        self.remove_btn = QPushButton()
        self.remove_btn.setIcon(QIcon.fromTheme("edit-delete"))
        self.remove_btn.setToolTip(CONFIG["note_remove"])
        self.remove_btn.clicked.connect(self.delete_self)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.toggle_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addStretch()

        self.layout.addWidget(self.title_edit)
        self.layout.addLayout(btn_layout)
        self.layout.addWidget(self.content_edit)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

    def on_title_enter(self):
        new_title = self.title_edit.text()
        self.title_edit.setToolTip(new_title)
        self.title_edit.setCursorPosition(0)

    def toggle_content(self):
        self.content_edit.setVisible(not self.content_edit.isVisible())

    def delete_self(self):
        self.setParent(None)
        self.deleteLater()

    def get_data(self):
        return {
            'title': self.title_edit.text(),
            'content': self.content_edit.toPlainText()
        }

    def set_data(self, data):
        self.title_edit.setText(data.get('title', ''))
        self.title_edit.setCursorPosition(0)
        self.content_edit.setPlainText(data.get('content', ''))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Salva a referência ao widget arrastado na aplicação
            QApplication.instance().dragged_note = self

            mime = QMimeData()
            data = QByteArray()
            stream = QDataStream(data, QIODevice.WriteOnly)
            stream.writeQString(json.dumps(self.get_data()))
            mime.setData("application/x-kanban-note", data)

            drag = QtGui.QDrag(self)
            drag.setMimeData(mime)
            drag.exec_(Qt.MoveAction)
            QApplication.instance().dragged_note = None


class ColumnWidget(QFrame):
    def __init__(self, title=CONFIG["board_title"], style=CONFIG["board_style"]):
        super().__init__()
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(style["frame"])
        
        self.setFixedWidth(CONFIG["board_width"])
        
        self.style=style

        self.layout = QVBoxLayout(self)

        self.title_edit = QLineEdit(title)
        self.title_edit.setCursorPosition(0)
        self.title_edit.setToolTip(title)
        self.title_edit.setStyleSheet(style["title"])
        self.title_edit.returnPressed.connect(self.on_title_enter)

        self.add_btn = QPushButton()
        self.add_btn.setIcon(QIcon.fromTheme("list-add"))
        self.add_btn.setToolTip(CONFIG["board_new_note"])
        self.add_btn.clicked.connect(lambda: self.add_note())

        self.remove_btn = QPushButton()
        self.remove_btn.setIcon(QIcon.fromTheme("edit-delete"))
        self.remove_btn.setToolTip(CONFIG["board_delete"])
        self.remove_btn.clicked.connect(self.remove_self)
        
        self.interchange_right_btn = QPushButton()
        self.interchange_right_btn.setIcon(QIcon.fromTheme("go-next"))
        self.interchange_right_btn.setToolTip(CONFIG["board_interchange_right"])
        self.interchange_right_btn.clicked.connect(self.interchange_right)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.title_edit)
        top_layout.addWidget(self.add_btn)
        top_layout.addWidget(self.remove_btn)
        top_layout.addWidget(self.interchange_right_btn)

        self.notes_layout = QVBoxLayout()
        self.notes_layout.setSpacing(10)
        self.notes_layout.addStretch()

        self.layout.addLayout(top_layout)
        self.layout.addLayout(self.notes_layout)

    def interchange_right(self):
        # Encontrar o layout pai (KanbanWindow.columns_layout)
        parent_layout = self.parentWidget().layout()
        
        # Obter a lista de widgets = []
        widgets = []
        for i in range(parent_layout.count()):
            item = parent_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, ColumnWidget):
                widgets.append(widget)

        if len(widgets) <= 1:
            return

        # Encontrar índice da coluna atual
        try:
            idx = widgets.index(self)
        except ValueError:
            return

        # Cálculo cíclico do índice seguinte
        next_idx = (idx + 1) % len(widgets)

        # Trocar posições no layout
        # Remover todos os widgets e itens, inclusive stretch
        for i in reversed(range(parent_layout.count())):
            item = parent_layout.itemAt(i)
            widget = item.widget()
            if widget:
                parent_layout.removeWidget(widget)
            else:
                parent_layout.removeItem(item)  # remove o stretch

        # Reordenar
        widgets[idx], widgets[next_idx] = widgets[next_idx], widgets[idx]

        # Re-inserir os widgets na nova ordem
        for i, w in enumerate(widgets):
            parent_layout.insertWidget(i, w)

        # Certifique-se de manter o stretch sempre no fim
        parent_layout.addStretch()
        
    def on_title_enter(self):
        new_title = self.title_edit.text()
        self.title_edit.setCursorPosition(0)
        self.title_edit.setToolTip(new_title)

    def add_note(self, note_title=CONFIG["note_title"], note_content=CONFIG["note_content"]):
        note = NoteWidget(note_title, note_content)
        self.notes_layout.insertWidget(self.notes_layout.count() - 1, note)

    def remove_self(self):
        self.setParent(None)
        self.deleteLater()

    def get_data(self):
        notes = []
        for i in range(self.notes_layout.count() - 1):  # -1 to skip stretch
            item = self.notes_layout.itemAt(i).widget()
            if isinstance(item, NoteWidget):
                notes.append(item.get_data())
        return {
            'title': self.title_edit.text(),
            'notes': notes,
            'style': self.style
        }

    def set_data(self, data):
        self.style=data.get('style', CONFIG["board_style"])
        self.setStyleSheet(self.style["frame"])
        
        self.title_edit.setStyleSheet(self.style["title"])
        self.title_edit.setText(data.get('title', ''))
        self.title_edit.setToolTip(data.get('title', ''))

        for note in data.get('notes', []):
            self.add_note(note['title'], note['content'])

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-kanban-note"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        data = event.mimeData().data("application/x-kanban-note")
        stream = QDataStream(data, QIODevice.ReadOnly)
        note_json = stream.readQString()
        note_data = json.loads(note_json)

        dragged_note = QApplication.instance().dragged_note

        # Remove a nota original do local de origem
        if dragged_note:
            dragged_note.setParent(None)
            dragged_note.deleteLater()
            QApplication.instance().dragged_note = None  # Limpa referência

        # Calcula a posição ideal para inserção
        pos = event.pos()
        insert_at = self.notes_layout.count() - 1  # default = before stretch

        for i in range(self.notes_layout.count() - 1):  # -1 ignora o stretch
            item = self.notes_layout.itemAt(i)
            widget = item.widget()
            if widget and isinstance(widget, NoteWidget):
                widget_pos = widget.mapTo(self, widget.rect().center())
                if pos.y() < widget_pos.y():
                    insert_at = i
                    break

        new_note = NoteWidget(note_data['title'], note_data['content'])
        self.notes_layout.insertWidget(insert_at, new_note)

        event.acceptProposedAction()



class KanbanWindow(QMainWindow):
    def __init__(self, filepath):
        super().__init__()
        self.setWindowTitle(about.__program_name__)
        self.resize(CONFIG["window_width"], CONFIG["window_height"])

        ## Icon
        # Get base directory for icons
        base_dir_path = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = os.path.join(base_dir_path, 'icons', 'logo.png')
        self.setWindowIcon(QIcon(self.icon_path)) 

        self.toolbar = QToolBar()
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(self.toolbar)

        self.new_kanban_action = QAction(QIcon.fromTheme("document-new"), CONFIG["toolbar_new_kanban"], self)
        self.new_kanban_action.setToolTip(CONFIG["toolbar_new_kanban_tooltip"])
        self.new_kanban_action.triggered.connect(lambda: self.func_new_kanban())

        self.add_column_action = QAction(QIcon.fromTheme("list-add"), CONFIG["toolbar_add_column"], self)
        self.add_column_action.setToolTip(CONFIG["toolbar_add_column_tooltip"])
        self.add_column_action.triggered.connect(lambda: self.add_column())

        self.save_action = QAction(QIcon.fromTheme("document-save"), CONFIG["toolbar_save"], self)
        self.save_action.setToolTip(CONFIG["toolbar_save_tooltip"])
        self.save_action.triggered.connect(self.save_to_file)
        
        self.save_as_action = QAction(QIcon.fromTheme("document-save-as"), CONFIG["toolbar_save_as"], self)
        self.save_as_action.setToolTip(CONFIG["toolbar_save_as_tooltip"])
        self.save_as_action.triggered.connect(self.save_as_to_file)

        self.load_action = QAction(QIcon.fromTheme("document-open"), CONFIG["toolbar_load"], self)
        self.load_action.setToolTip(CONFIG["toolbar_load_tooltip"])
        self.load_action.triggered.connect(lambda: self.load_from_file(""))

        # Adicionar o espaçador
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        #
        self.configure_action = QAction(QIcon.fromTheme("document-properties"), CONFIG["toolbar_configure"], self)
        self.configure_action.setToolTip(CONFIG["toolbar_configure_tooltip"])
        self.configure_action.triggered.connect(self.open_configure_editor)
        
        #
        self.about_action = QAction(QIcon.fromTheme("help-about"), CONFIG["toolbar_about"], self)
        self.about_action.setToolTip(CONFIG["toolbar_about_tooltip"])
        self.about_action.triggered.connect(self.open_about)
        
        # Coffee
        self.coffee_action = QAction(QIcon.fromTheme("emblem-favorite"), CONFIG["toolbar_coffee"], self)
        self.coffee_action.setToolTip(CONFIG["toolbar_coffee_tooltip"])
        self.coffee_action.triggered.connect(self.on_coffee_action_click)


        self.toolbar.addAction(self.new_kanban_action)
        self.toolbar.addAction(self.add_column_action)
        self.toolbar.addAction(self.save_action)
        self.toolbar.addAction(self.save_as_action)
        self.toolbar.addAction(self.load_action)
        self.toolbar.addWidget(spacer)
        self.toolbar.addAction(self.configure_action)
        self.toolbar.addAction(self.about_action)
        self.toolbar.addAction(self.coffee_action)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.columns_widget = QWidget()
        self.columns_layout = QHBoxLayout(self.columns_widget)
        self.columns_layout.setSpacing(10)
        self.columns_layout.addStretch()

        self.scroll_area.setWidget(self.columns_widget)

        main_layout = QVBoxLayout(central_widget)
        
        # Cria o widget de topo e seu layout
        self.top_line_widget = QWidget()
        self.top_line_layout = QHBoxLayout(self.top_line_widget)
        self.top_label = QLabel(CONFIG["window_filename"])
        self.top_input = QLineEdit("")
        self.top_input.setReadOnly(True)
        self.top_line_layout.addWidget(self.top_label)
        self.top_line_layout.addWidget(self.top_input)

        # Title layout
        self.top_title_line_widget = QWidget()
        #self.top_title_line_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.top_title_layout = QHBoxLayout(self.top_title_line_widget)
        self.top_title_label = QLabel(CONFIG["kanban_title_label"])
        self.top_title_input = QLineEdit(CONFIG["kanban_title_default"])
        self.top_description_label = QLabel(CONFIG["kanban_description_label"])
        self.top_description_input = QLineEdit(CONFIG["kanban_description_default"])
        self.top_title_layout.addWidget(self.top_title_label)
        self.top_title_layout.addWidget(self.top_title_input)
        self.top_title_layout.addWidget(self.top_description_label)
        self.top_title_layout.addWidget(self.top_description_input)

        # Adiciona ao layout principal
        main_layout.addWidget(self.top_line_widget)
        main_layout.addWidget(self.top_title_line_widget)
        main_layout.addWidget(self.scroll_area)

        # Quadros iniciais
        for title in CONFIG["board_startup_list"]:
            self.add_column(title)
            
        self.top_line_widget.setVisible(False)
        
        if len(filepath)>0:
            self.load_from_file(filepath)

    def on_coffee_action_click(self):
        QDesktopServices.openUrl(QUrl("https://ko-fi.com/trucomanx"))
        
    def func_new_kanban(self):
        subprocess.Popen([sys.executable, __file__])

    def open_configure_editor(self):
        if os.name == 'nt':  # Windows
            os.startfile(CONFIG_PATH)
        elif os.name == 'posix':  # Linux/macOS
            subprocess.run(['xdg-open', CONFIG_PATH])

    def add_column(self, title=CONFIG["board_title"],style=CONFIG["board_style"]):
        column = ColumnWidget(title,style)
        self.columns_layout.insertWidget(self.columns_layout.count() - 1, column)

    def save_as_to_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save as", "", "JSON (*.kanban.json)")
        if not path.endswith(".kanban.json"):
            path += ".kanban.json"
        self.top_input.setText(path)
        self.save_to_file()
        
    def save_to_file(self):
        path=self.top_input.text()
        
        if path=='':
            self.save_as_to_file()
            return
        else:
            boards = []
            for i in range(self.columns_layout.count() - 1):
                item = self.columns_layout.itemAt(i).widget()
                if isinstance(item, ColumnWidget):
                    boards.append(item.get_data())
                    
            data={  "title":self.top_title_input.text(),
                    "description":self.top_description_input.text(),
                    "boards":boards}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.top_line_widget.setVisible(True)

    def load_from_file(self, path=""):
        
        if (len(path)==0) or not os.path.exists(path):
            path, _ = QFileDialog.getOpenFileName(self, "Load", "", "JSON (*.kanban.json)")
            
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"{CONFIG['window_error_loading']}\n{e}")
                    return
            
            self.top_line_widget.setVisible(True)
            self.top_input.setText(path)
            
            self.top_title_input.setText(data["title"])
            self.top_description_input.setText(data["description"])

            for i in reversed(range(self.columns_layout.count() - 1)):
                item = self.columns_layout.itemAt(i).widget()
                if item:
                    item.setParent(None)

            for col_data in data["boards"]:
                col = ColumnWidget()
                col.set_data(col_data)
                self.columns_layout.insertWidget(self.columns_layout.count() - 1, col)
        else:
            QMessageBox.warning(self, CONFIG["window_path_problems"], f"{CONFIG['window_error_loading']}\n{path}")  

    def open_about(self):
        data={
            "version": about.__version__,
            "package": about.__package__,
            "program_name": about.__program_name__,
            "author": about.__author__,
            "email": about.__email__,
            "description": about.__description__,
            "url_source": about.__url_source__,
            "url_doc": about.__url_doc__,
            "url_funding": about.__url_funding__,
            "url_bugs": about.__url_bugs__
        }
        show_about_window(data,self.icon_path)

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    create_desktop_directory()    
    create_desktop_menu()
    create_desktop_file('~/.local/share/applications')
    
    filepath = ""
    if(len(sys.argv)==2):
        if sys.argv[1] == "--autostart":
            create_desktop_directory(overwrite = True)
            create_desktop_menu(overwrite = True)
            create_desktop_file('~/.config/autostart', overwrite=True)
            return
            
        if sys.argv[1] == "--applications":
            create_desktop_directory(overwrite = True)
            create_desktop_menu(overwrite = True)
            create_desktop_file('~/.local/share/applications', overwrite=True)
            return

        if os.path.exists(sys.argv[1]):
            filepath = sys.argv[1]
    else:
        for n in range(len(sys.argv)):
            if sys.argv[n] == "--autostart":
                create_desktop_directory(overwrite = True)
                create_desktop_menu(overwrite = True)
                create_desktop_file('~/.config/autostart', overwrite=True)
                return
            if sys.argv[n] == "--applications":
                create_desktop_directory(overwrite = True)
                create_desktop_menu(overwrite = True)
                create_desktop_file('~/.local/share/applications', overwrite=True)
                return

    app = QApplication(sys.argv)
    app.setApplicationName(about.__package__) 
    
    window = KanbanWindow(filepath)
    window.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()

