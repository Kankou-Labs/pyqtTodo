from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt, pyqtSignal
import sys,os
from ui_files.anotherwindow_ui import Ui_MainWindow
from utils import resource_path


class DetailsWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    on_closed = pyqtSignal(object) #define a signal on detailWindow close
    def __init__(self, task_id, todo, date, description, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self.todo = todo
        self.date = date
        self.description = description
        # uic.loadUi(resource_path(os.path.join('ui_files', 'anotherwindow.ui')), self)
        self.setupUi(self)
        
    def show_details(self, todo, date, description):
        self.findChild(QtWidgets.QLabel, 'todo_field').setText(todo)
        self.findChild(QtWidgets.QLabel, 'date_field').setText(date)
        self.findChild(QtWidgets.QLabel, 'description_field').setText(description)
        self.show()

    def closeEvent(self, event): #called when detailWindow is closed through a signal
        print("closed window")
        self.on_closed.emit(self) #emit the on_closed signal
        super().closeEvent(event)  # Call the parent class closeEvent