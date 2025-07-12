import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QToolBar,
    QAction, QFileDialog, QMessageBox, QScrollArea,
    QFrame, QInputDialog, QSizePolicy
)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag, QIcon


class NoteWidget(QWidget):
    def __init__(self, title="", content=""):
        super().__init__()
        self.title = title
        self.content = content
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setStyleSheet("background-color: white; border: 1px solid #ccc; padding: 5px;")
        self.setAcceptDrops(True)

        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("font-weight: bold;")

        self.content_edit = QTextEdit(self.content)
        self.content_edit.setPlaceholderText("Escreva aqui...")
        self.content_edit.setFixedHeight(80)

        self.toggle_button = QPushButton("⬇")
        self.toggle_button.setToolTip("Expandir/recolher")
        self.toggle_button.clicked.connect(self.toggle_content)

        self.remove_button = QPushButton("X")
        self.remove_button.setToolTip("Remover nota")
        self.remove_button.clicked.connect(self.remove_self)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.title_label)
        hlayout.addStretch()
        hlayout.addWidget(self.toggle_button)
        hlayout.addWidget(self.remove_button)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(2)

        self.layout.addLayout(hlayout)
        self.layout.addWidget(self.content_edit)

    def toggle_content(self):
        is_visible = self.content_edit.isVisible()
        self.content_edit.setVisible(not is_visible)
        self.toggle_button.setText("⬇" if not is_visible else "⬆")

    def remove_self(self):
        self.setParent(None)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.title_label.text() + "\n" + self.content_edit.toPlainText())
            drag.setMimeData(mime_data)
            drag.exec_(Qt.MoveAction)

    def get_data(self):
        return {
            "title": self.title_label.text(),
            "content": self.content_edit.toPlainText()
        }


class BoardWidget(QFrame):
    def __init__(self, title=""):
        super().__init__()
        self.title = title
        self.setStyleSheet("background-color: #d6f5d6; border: 2px solid #a2cfa2; border-radius: 6px;")
        self.setMinimumWidth(250)
        self.setAcceptDrops(True)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")

        self.add_note_button = QPushButton("+ Nota")
        self.add_note_button.setToolTip("Adicionar nova nota")
        self.add_note_button.clicked.connect(self.add_note)

        self.remove_board_button = QPushButton("🗑")
        self.remove_board_button.setToolTip("Remover quadro")
        self.remove_board_button.clicked.connect(self.remove_board)

        title_layout = QHBoxLayout()
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.add_note_button)
        title_layout.addWidget(self.remove_board_button)

        self.layout.addLayout(title_layout)

    def add_note(self, title="", content=""):
        if not title:
            title, ok = QInputDialog.getText(self, "Nova Nota", "Título da nota:")
            if not ok or not title:
                return
        note = NoteWidget(title, content)
        self.layout.addWidget(note)

    def remove_board(self):
        self.setParent(None)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        data = event.mimeData().text().split("\n", 1)
        title = data[0]
        content = data[1] if len(data) > 1 else ""
        self.add_note(title, content)
        event.acceptProposedAction()

    def get_data(self):
        notes = []
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if isinstance(widget, NoteWidget):
                notes.append(widget.get_data())
        return {
            "title": self.title_label.text(),
            "notes": notes
        }


class KanbanApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kanban Científico")
        self.resize(1000, 600)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Toolbar
        toolbar = QToolBar("Toolbar")
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)

        add_board_action = QAction(QIcon.fromTheme("list-add"), "Adicionar Quadro", self)
        add_board_action.setToolTip("Adicionar novo quadro")
        add_board_action.triggered.connect(self.add_board)
        toolbar.addAction(add_board_action)

        save_action = QAction(QIcon.fromTheme("document-save"), "Salvar JSON", self)
        save_action.setToolTip("Salvar estado atual")
        save_action.triggered.connect(self.save_to_json)
        toolbar.addAction(save_action)

        load_action = QAction(QIcon.fromTheme("document-open"), "Carregar JSON", self)
        load_action.setToolTip("Carregar de arquivo")
        load_action.triggered.connect(self.load_from_json)
        toolbar.addAction(load_action)

        main_layout.addWidget(toolbar)

        # Scroll area for boards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.boards_container = QWidget()
        self.boards_layout = QHBoxLayout()
        self.boards_layout.setAlignment(Qt.AlignLeft)
        self.boards_container.setLayout(self.boards_layout)
        self.scroll_area.setWidget(self.boards_container)
        main_layout.addWidget(self.scroll_area)

        # Adicionar quadros padrão
        for title in ["Ideias", "Em elaboração", "Submetidos", "Aprovados"]:
            self.add_board(title)

    def add_board(self, title=None):
        if not title:
            title, ok = QInputDialog.getText(self, "Novo Quadro", "Nome do quadro:")
            if not ok or not title:
                return
        board = BoardWidget(title)
        self.boards_layout.addWidget(board)

    def save_to_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar como", filter="JSON (*.json)")
        if not path:
            return

        data = []
        for i in range(self.boards_layout.count()):
            widget = self.boards_layout.itemAt(i).widget()
            if isinstance(widget, BoardWidget):
                data.append(widget.get_data())

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        QMessageBox.information(self, "Sucesso", "Dados salvos com sucesso.")

    def load_from_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Carregar", filter="JSON (*.json)")
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar o arquivo:\n{e}")
            return

        # Limpa tudo antes de carregar
        while self.boards_layout.count():
            item = self.boards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for board in data:
            b = BoardWidget(board.get("title", "Sem Título"))
            for note in board.get("notes", []):
                b.add_note(note.get("title", ""), note.get("content", ""))
            self.boards_layout.addWidget(b)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KanbanApp()
    window.show()
    sys.exit(app.exec_())

