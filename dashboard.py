import sys,os
from PyQt6 import QtWidgets, uic, QtCore
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtCore import Qt
import sqlite3
from details_window import DetailsWindow
from ui_files.mainwindow_ui import Ui_MainWindow
from utils import resource_path


basedir = os.path.dirname(__file__)

class Dashboard(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        # uic.loadUi(resource_path(os.path.join('ui_files', 'mainwindow.ui')), self)
        self.setupUi(self)
        self.conn, self.cursor = self.init_db()
        
        self.centralwidget = self.findChild(QtWidgets.QWidget, 'centralwidget')
        self.date_input = self.findChild(QtWidgets.QDateEdit, 'dateEdit')
        self.todo_input = self.findChild(QtWidgets.QLineEdit, 'lineEdit')
        self.description_input = self.findChild(QtWidgets.QPlainTextEdit, 'plainTextEdit')
        self.add_button = self.findChild(QtWidgets.QPushButton, 'pushButton')
        self.list_view = self.findChild(QtWidgets.QListWidget, 'listWidget')
        self.remove_button = self.findChild(QtWidgets.QPushButton, 'pushButton_2')
        self.logo_label = self.findChild(QtWidgets.QLabel, 'logoLabel')
        self.title = self.findChild(QtWidgets.QLabel, 'label')
        
        # Set up connections
        self.date_input.setDate(QtCore.QDate.currentDate())
        self.load_todos()
        self.add_button.clicked.connect(self.add_todo)
        self.remove_button.clicked.connect(self.remove_todo)
        self.list_view.itemDoubleClicked.connect(self.show_details)
        
        # Array to track details windows
        self.details_window = []

        # Shortcut to add todo on pressing Enter
        shortcut = QShortcut(QKeySequence("Return"), self)
        shortcut.activated.connect(self.handle_enter_pressed)

        # Shift + Enter to insert newline in description field
        self.description_input.installEventFilter(self)
    
    # event of Shfit + Enter to new line in the description field
    def eventFilter(self, obj, event):
        if obj == self.description_input and event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # press Enter to add todo
                self.handle_enter_pressed()
                return True
            elif event.key() == Qt.Key.Key_Return and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # press Shift + Enter to new line in the description field
                cursor = self.description_input.textCursor()
                cursor.insertText("\n")
                return True
        return super().eventFilter(obj, event)

    # event of Enter key to add todo
    def handle_enter_pressed(self):
        if self.todo_input.text():
            self.add_todo()
        
    def init_db(self):
        db_path = resource_path('todo.db')
        if not os.path.exists(db_path):
            print("Database does not exist. It will be created.")
        else:
            print("Database found at:", db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the todos table has the correct schema
        cursor.execute("PRAGMA table_info(todos)")
        columns = cursor.fetchall()
        if len(columns) != 4 or columns[0][1] != 'id':
            print("Recreating 'todos' table with 'id' column.")
            cursor.execute("DROP TABLE IF EXISTS todos")
            cursor.execute("""
                CREATE TABLE todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE,
                    todo TEXT,
                    description TEXT
                )
            """)
        else:
            print("'todos' table already exists with the correct schema.")
        return conn, cursor
    
    def load_todos(self):
        self.cursor.execute("SELECT id, date, todo FROM todos")
        self.rows = self.cursor.fetchall()
        self.list_view.clear()
        for row in self.rows:
            self.list_view.addItem(f"{row[1]} - {row[2]}")  # Display date and todo in the list view

    def add_todo(self):
        if self.todo_input.text() == "":
            return

        date = self.date_input.date().toString()
        todo = self.todo_input.text()
        description = self.description_input.toPlainText()
        self.cursor.execute("INSERT INTO todos (date, todo, description) VALUES (?, ?, ?)", (date, todo, description))
        self.conn.commit()
        
        # Clear input fields after adding
        self.date_input.setDate(QtCore.QDate.currentDate())
        self.todo_input.clear()
        self.description_input.clear()

        # Refresh the list of todos
        self.refresh_rows()

    def remove_todo(self):
        current_row = self.list_view.currentRow()
        if current_row != -1 and current_row < len(self.rows):
            task_id = self.rows[current_row][0]  # Use id to delete the selected item
            
            # Close the window associated with the deleted task, if it exists
            window_to_close = self.get_existing_window(task_id)
            if window_to_close:
                window_to_close.close()  # Close the window            
            # Delete the item from the database and the list view
            self.cursor.execute("DELETE FROM todos WHERE id = ?", (task_id,))
            self.conn.commit()
            self.list_view.takeItem(current_row)
            self.refresh_rows()

        
    def refresh_rows(self):
        self.cursor.execute("SELECT id, date, todo FROM todos")
        self.rows = self.cursor.fetchall()
        self.list_view.clear()
        for row in self.rows:
            self.list_view.addItem(f"{row[1]} - {row[2]}")  # Display date and todo in the list view
    
    def show_details(self):
        current_row = self.list_view.currentRow()
        if current_row == -1:
            return  # Exit if no row is selected

        task_id = self.rows[current_row][0]  # Retrieve id from the selected row
        self.cursor.execute("SELECT todo, date, description FROM todos WHERE id = ?", (task_id,))
        row = self.cursor.fetchone()

        if not row:
            return  # Exit if no data is found

        todo, date, description = row

        # Check if a details window for this item is already open
        existing_window = self.get_existing_window(task_id)
        if existing_window:
            existing_window.activateWindow()
            existing_window.raise_()
            return

        # Create a new details window with the unique id
        d_window = DetailsWindow(task_id, todo, date, description)
        d_window.show_details(todo, date, description)
        d_window.on_closed.connect(self.closed_detail_window)
        self.details_window.append(d_window)

    def get_existing_window(self, task_id):
        """Return an already open window if one exists for the given task_id"""
        for window in self.details_window:
            if window.task_id == task_id:
                return window
        return None

    def closeEvent(self, event):
        self.conn.close()
        event.accept()

    def closed_detail_window(self, window):
        if window in self.details_window:
            self.details_window.remove(window)