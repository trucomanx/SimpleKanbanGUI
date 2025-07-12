import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLineEdit, QLabel, QScrollArea, QAction, QToolBar, QMessageBox,
    QFrame, QInputDialog
)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag


class NoteWidget(QFrame):
    def __init__(self, title="", content="", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(1)
        self.setStyleSheet("background-color: white;")

        self.title = QLineEdit(title)
        self.content = QTextEdit(content)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.content)
        self.setLayout(layout)

        self.setAcceptDrops(False)
        self.setMinimumWidth(200)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText("note")  # Just a placeholder
            drag.setMimeData(mime)
            drag.setHotSpot(event.pos())
            drag.exec_(Qt.MoveAction)


class KanbanColumn(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

        self.title_label = QLabel(f"<b>{title}</b>")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.title_label)
        self.setLayout(self.layout)

        self.title = title

    def add_note(self, note):
        self.layout.addWidget(note)

    def remove_note(self, note):
        self.layout.removeWidget(note)
        note.setParent(None)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        note = event.source()
        if note and isinstance(note, NoteWidget):
            self.add_note(note)
            event.acceptProposedAction()


class KanbanBoard(QWidget):
    def __init__(self):
        super().__init__()
        self.columns = []

        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)

        # Add default columns
        for title in ["Ideias", "Em elaboração", "Submetidos", "Aprovados"]:
            self.add_column(title)

    def add_column(self, title):
        column = KanbanColumn(title)
        self.columns.append(column)
        self.main_layout.addWidget(column)

    def remove_last_column(self):
        if self.columns:
            col = self.columns.pop()
            self.main_layout.removeWidget(col)
            col.setParent(None)

    def add_note_to_column(self, column_title, note):
        for col in self.columns:
            if col.title == column_title:
                col.add_note(note)
                break


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kanban Local - Organizador de Ideias")
        self.setMinimumSize(900, 500)

        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)

        add_col_action = QAction("➕ Adicionar Quadro", self)
        add_col_action.triggered.connect(self.add_column)
        self.toolbar.addAction(add_col_action)

        rem_col_action = QAction("🗑️ Remover Último Quadro", self)
        rem_col_action.triggered.connect(self.remove_column)
        self.toolbar.addAction(rem_col_action)

        add_note_action = QAction("📝 Nova Nota", self)
        add_note_action.triggered.connect(self.add_note)
        self.toolbar.addAction(add_note_action)

        self.board = KanbanBoard()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.board)
        self.setCentralWidget(scroll)

    def add_column(self):
        title, ok = QInputDialog.getText(self, "Novo Quadro", "Título do quadro:")
        if ok and title:
            self.board.add_column(title)

    def remove_column(self):
        confirm = QMessageBox.question(
            self,
            "Remover Quadro",
            "Tem certeza que deseja remover o último quadro?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.board.remove_last_column()

    def add_note(self):
        if not self.board.columns:
            QMessageBox.warning(self, "Aviso", "Adicione pelo menos um quadro antes de criar uma nota.")
            return
        title, ok = QInputDialog.getText(self, "Novo Título", "Título da nota:")
        if ok:
            note = NoteWidget(title, "Digite aqui o conteúdo em Markdown...")
            self.board.columns[0].add_note(note)  # adiciona na primeira coluna por padrão


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

