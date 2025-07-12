import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QLineEdit,
    QScrollArea, QToolBar, QAction, QFileDialog, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, QMimeData, QByteArray
from PyQt5.QtGui import QDrag, QIcon


class NoteWidget(QFrame):
    def __init__(self, title="", content=""):
        super().__init__()
        self.title = QLineEdit(title)
        self.content = QTextEdit(content)
        self.content.setFixedHeight(100)

        self.remove_button = QPushButton("🗑️")
        self.remove_button.setFixedSize(30, 30)

        self.layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Título:"))
        top_layout.addWidget(self.title)
        top_layout.addWidget(self.remove_button)
        self.layout.addLayout(top_layout)
        self.layout.addWidget(QLabel("Conteúdo (Markdown):"))
        self.layout.addWidget(self.content)
        self.setLayout(self.layout)

        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.setAcceptDrops(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText("note")  # marker
            drag.setMimeData(mime)
            drag.exec_(Qt.MoveAction)

    def to_dict(self):
        return {
            "title": self.title.text(),
            "content": self.content.toPlainText()
        }


class BoardColumn(QWidget):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.setAcceptDrops(True)
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel(f"<b>{name}</b>"))

        self.add_note_button = QPushButton("+ Nova Nota")
        self.add_note_button.setIcon(QIcon.fromTheme("document-new"))
        self.layout.addWidget(self.add_note_button)

        self.notes_container = QVBoxLayout()
        self.layout.addLayout(self.notes_container)
        self.layout.addStretch()
        self.setLayout(self.layout)
        self.setStyleSheet("background-color: #ddffdd; padding: 5px; border: 1px solid #ccc;")

    def add_note(self, note: NoteWidget):
        self.notes_container.insertWidget(0, note)
        note.remove_button.clicked.connect(lambda: self.remove_note(note))

    def remove_note(self, note):
        note.setParent(None)

    def dropEvent(self, event):
        note = event.source()
        if isinstance(note, NoteWidget):
            note.setParent(None)
            self.add_note(note)
            event.setDropAction(Qt.MoveAction)
            event.accept()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text() == "note":
            event.acceptProposedAction()

    def to_dict(self):
        return {
            "name": self.name,
            "notes": [note.to_dict() for note in self.notes()]
        }

    def notes(self):
        return [
            self.notes_container.itemAt(i).widget()
            for i in range(self.notes_container.count())
            if isinstance(self.notes_container.itemAt(i).widget(), NoteWidget)
        ]


class KanbanApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kanban para Artigos Científicos")
        self.resize(1000, 600)
        self.boards = []

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.toolbar = QToolBar("Toolbar")
        self.setup_toolbar()
        self.main_layout.addWidget(self.toolbar)

        self.boards_layout = QHBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_area_widget = QWidget()
        self.scroll_area_widget.setLayout(self.boards_layout)
        self.scroll_area.setWidget(self.scroll_area_widget)
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)

        for default_name in ["Ideias", "Em elaboração", "Submetidos", "Aprovados"]:
            self.add_board(default_name)

    def setup_toolbar(self):
        add_col_action = QAction(QIcon.fromTheme("list-add"), "Adicionar Quadro", self)
        add_col_action.triggered.connect(self.create_new_board)
        self.toolbar.addAction(add_col_action)

        rem_col_action = QAction(QIcon.fromTheme("list-remove"), "Remover Último Quadro", self)
        rem_col_action.triggered.connect(self.remove_last_board)
        self.toolbar.addAction(rem_col_action)

        save_action = QAction(QIcon.fromTheme("document-save"), "Salvar em JSON", self)
        save_action.triggered.connect(self.save_to_json)
        self.toolbar.addAction(save_action)

    def create_new_board(self):
        name, ok = QFileDialog.getSaveFileName(self, "Nome do novo quadro", "", "")
        if ok and name.strip():
            self.add_board(name.strip())

    def add_board(self, name):
        board = BoardColumn(name)
        board.add_note_button.clicked.connect(lambda: self.add_note_to_board(board))
        self.boards_layout.addWidget(board)
        self.boards.append(board)

    def remove_last_board(self):
        if self.boards:
            board = self.boards.pop()
            board.setParent(None)

    def add_note_to_board(self, board):
        note = NoteWidget("Novo Título", "")
        board.add_note(note)

    def save_to_json(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Salvar como JSON", "kanban.json", "JSON Files (*.json)")
        if filename:
            data = [board.to_dict() for board in self.boards]
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "Sucesso", f"Dados salvos em {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao salvar JSON: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KanbanApp()
    window.show()
    sys.exit(app.exec_())

