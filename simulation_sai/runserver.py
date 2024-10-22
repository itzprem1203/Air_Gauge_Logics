import os
import subprocess
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QComboBox, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QScreen
from threading import Thread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.server_process = None  # To keep track of the Django server process
        self.init_ui()

    def init_ui(self):
        # Create a dropdown box
        self.dropdown = QComboBox(self)
        self.python_executables = find_python_executables()
        self.dropdown.addItems(self.python_executables)

        # Create an OK button
        self.ok_button = QPushButton('OK', self)
        self.ok_button.clicked.connect(self.on_ok_clicked)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.dropdown)
        layout.addWidget(self.ok_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.setWindowTitle("Select Python Executable")

        # Get the size of the screen and set the window size
        screen = QScreen.availableGeometry(QApplication.primaryScreen())
        self.setGeometry(screen)  # Set window size to the full screen size

    def on_ok_clicked(self):
        selected_python = self.dropdown.currentText()
        if not selected_python:
            QMessageBox.warning(self, "No Selection", "No Python executable selected.")
            return

        # Disable the dropdown and button
        self.dropdown.setEnabled(False)
        self.ok_button.setEnabled(False)

        # Start Django server in a separate thread
        self.server_thread = Thread(target=self.run_django_server, args=(selected_python,))
        self.server_thread.daemon = True
        self.server_thread.start()

        # Wait for the server to start
        time.sleep(5)  # Adjust this if needed

        # Start the web view
        self.create_web_view()

    def run_django_server(self, python_executable):
        # Change working directory to the project folder
        project_dir = r'C:\Program Files\gauge_logic'
        os.chdir(project_dir)

        # Path for virtual environment within project_dir
        venv_path = os.path.join(project_dir, 'myenv')
        
        # Create virtual environment if it doesn't exist
        if not os.path.exists(venv_path):
            subprocess.run([python_executable, '-m', 'venv', venv_path], shell=True)

        # Activate the virtual environment
        venv_python = os.path.join(venv_path, 'Scripts', 'python.exe')

        # Install requirements in the virtual environment
        requirements_path = os.path.join(project_dir, 'requirements.txt')
        if os.path.exists(requirements_path):
            subprocess.run([venv_python, '-m', 'pip', 'install', '-r', requirements_path])

        # Run Django server using the virtual environment's Python
        self.server_process = subprocess.Popen([venv_python, 'manage.py', 'runserver'])

    def create_web_view(self):
        """Create and display the web view to show the Django server output."""
        # Create a web view widget
        self.web_view = QWebEngineView(self)
        
        # Set the URL using QUrl
        self.web_view.setUrl(QUrl("http://127.0.0.1:8000/"))

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.web_view)

        # Update the container with the new layout
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Update window title
        self.setWindowTitle("Django Server Output")

    def closeEvent(self, event):
        """Override the close event to terminate the server process."""
        if self.server_process:
            self.server_process.terminate()  # Terminate the server process
            self.server_process.wait()  # Wait for the process to terminate
        event.accept()

def find_python_executables():
    """Find Python executables in user directories."""
    possible_paths = [
        os.path.expanduser(r'~\AppData\Local\Programs\Python\Python312\python.exe'),
        os.path.expanduser(r'~\AppData\Local\Programs\Python\Python310\python.exe'),
        os.path.expanduser(r'~\AppData\Local\Programs\Python\Python39\python.exe'),
        # Add more possible paths if needed
    ]
    return [path for path in possible_paths if os.path.exists(path)]

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.showMaximized()  # Show the window maximized with window controls
    app.exec_()
