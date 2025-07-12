import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QScrollArea, QLineEdit, QFileDialog, QToolBar,
    QMainWindow, QAction, QMessageBox, QSizePolicy, QFrame
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QMimeData, QByteArray, QDataStream, QIODevice
from PyQt5 import QtGui

class NoteWidget(QWidget):
    def __init__(self, title="", content=""):
        super().__init__()
        self.setAcceptDrops(True)
        self.layout = QVBoxLayout(self)
        self.setStyleSheet("background-color: #ffffff; border: 1px solid #cccccc; border-radius: 5px;")
        
        self.title_edit = QLineEdit(title)
        self.content_edit = QTextEdit(content)
        self.content_edit.setVisible(False)

        self.toggle_btn = QPushButton()
        self.toggle_btn.setIcon(QIcon.fromTheme("pan-down"))
        self.toggle_btn.setToolTip("Expandir/Comprimir conteúdo")
        self.toggle_btn.clicked.connect(self.toggle_content)

        self.remove_btn = QPushButton()
        self.remove_btn.setIcon(QIcon.fromTheme("edit-delete"))
        self.remove_btn.setToolTip("Remover nota")
        self.remove_btn.clicked.connect(self.delete_self)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.toggle_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addStretch()

        self.layout.addWidget(self.title_edit)
        self.layout.addLayout(btn_layout)
        self.layout.addWidget(self.content_edit)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

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
    def __init__(self, title="Novo Quadro"):
        super().__init__()
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("background-color: #e0f5e0; border: 2px solid #66cc66; padding: 5px;")

        self.layout = QVBoxLayout(self)

        self.title_edit = QLineEdit(title)
        self.title_edit.setStyleSheet("font-weight: bold; background-color: #ccffcc;")

        self.add_btn = QPushButton()
        self.add_btn.setIcon(QIcon.fromTheme("list-add"))
        self.add_btn.setToolTip("Adicionar nova nota")
        self.add_btn.clicked.connect(lambda: self.add_note())

        self.remove_btn = QPushButton()
        self.remove_btn.setIcon(QIcon.fromTheme("edit-delete"))
        self.remove_btn.setToolTip("Remover quadro")
        self.remove_btn.clicked.connect(self.remove_self)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.title_edit)
        top_layout.addWidget(self.add_btn)
        top_layout.addWidget(self.remove_btn)

        self.notes_layout = QVBoxLayout()
        self.notes_layout.setSpacing(10)
        self.notes_layout.addStretch()

        self.layout.addLayout(top_layout)
        self.layout.addLayout(self.notes_layout)


    def add_note(self, note_title="Basico 1", note_content="Qualter texto"):
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
            'notes': notes
        }

    def set_data(self, data):
        self.title_edit.setText(data.get('title', ''))
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

        # Cria nova nota aqui
        self.add_note(note_data['title'], note_data['content'])

        # Remove a nota original do local de origem
        dragged_note = QApplication.instance().dragged_note
        if dragged_note:
            dragged_note.setParent(None)
            dragged_note.deleteLater()
            QApplication.instance().dragged_note = None  # Limpa referência

        event.acceptProposedAction()



class KanbanWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kanban Local - Artigos Científicos")
        self.resize(1000, 600)

        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)

        self.add_column_action = QAction(QIcon.fromTheme("list-add"), "Adicionar Quadro", self)
        self.add_column_action.setToolTip("Adicionar novo quadro")
        self.add_column_action.triggered.connect(lambda: self.add_column())

        self.save_action = QAction(QIcon.fromTheme("document-save"), "Salvar", self)
        self.save_action.setToolTip("Salvar para arquivo JSON")
        self.save_action.triggered.connect(self.save_to_file)

        self.load_action = QAction(QIcon.fromTheme("document-open"), "Carregar", self)
        self.load_action.setToolTip("Carregar de arquivo JSON")
        self.load_action.triggered.connect(self.load_from_file)

        self.toolbar.addAction(self.add_column_action)
        self.toolbar.addAction(self.save_action)
        self.toolbar.addAction(self.load_action)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.columns_widget = QWidget()
        self.columns_layout = QHBoxLayout(self.columns_widget)
        self.columns_layout.setSpacing(15)
        self.columns_layout.addStretch()

        self.scroll_area.setWidget(self.columns_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(self.scroll_area)

        # Quadros iniciais
        for title in ["Ideias", "Em elaboração", "Submetidos", "Aprovados"]:
            self.add_column(title)

    def add_column(self, title="Novo Quadro"):
        column = ColumnWidget(title)
        self.columns_layout.insertWidget(self.columns_layout.count() - 1, column)

    def save_to_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar como", "", "JSON (*.json)")
        if path:
            data = []
            for i in range(self.columns_layout.count() - 1):
                item = self.columns_layout.itemAt(i).widget()
                if isinstance(item, ColumnWidget):
                    data.append(item.get_data())
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Carregar", "", "JSON (*.json)")
        if path:
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception as e:
                    QMessageBox.critical(self, "Erro", f"Erro ao carregar: {e}")
                    return

            for i in reversed(range(self.columns_layout.count() - 1)):
                item = self.columns_layout.itemAt(i).widget()
                if item:
                    item.setParent(None)

            for col_data in data:
                col = ColumnWidget()
                col.set_data(col_data)
                self.columns_layout.insertWidget(self.columns_layout.count() - 1, col)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KanbanWindow()
    window.show()
    sys.exit(app.exec_())

