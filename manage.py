import os
import sys
import threading
import time
import requests
from django.core.management import execute_from_command_line
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets

# Global event to signal server to stop
stop_event = threading.Event()

class WebWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Django Project Output")
        
        # Get the system screen size
        screen = QtWidgets.QApplication.primaryScreen()
        screen_size = screen.size()

        # Set window size to match screen size
        self.setGeometry(0, 0, screen_size.width(), screen_size.height())

        # Create a QWebEngineView widget to display the web page
        self.browser = QtWebEngineWidgets.QWebEngineView(self)
        self.browser.setGeometry(0, 0, screen_size.width(), screen_size.height())

        # Load the Django server URL
        self.browser.load(QtCore.QUrl("http://127.0.0.1:8000/"))

    def closeEvent(self, event):
        # Signal the server to stop and close the window
        stop_event.set()
        event.accept()

def start_web_window():
    app = QtWidgets.QApplication(sys.argv)
    window = WebWindow()
    window.show()
    sys.exit(app.exec_())

def migrate_database():
    # Set the Django settings module environment variable
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_me.settings")
    
    # Run makemigrations
    sys.argv = ["manage.py", "makemigrations"]
    execute_from_command_line(sys.argv)
    
    # Run migrate
    sys.argv = ["manage.py", "migrate"]
    execute_from_command_line(sys.argv)

def start_django_server():

    # First, perform migrations
    migrate_database()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_me.settings")
    sys.argv = ["manage.py", "runserver", "--noreload"]
    while not stop_event.is_set():
        try:
            execute_from_command_line(sys.argv)
        except SystemExit:
            # Handle SystemExit if Django server exits (e.g., when stop_event is set)
            break

def wait_for_server():
    url = "http://127.0.0.1:8000/"
    timeout = 30  # Timeout in seconds
    start_time = time.time()

    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Django server is running.")
                break
        except requests.ConnectionError:
            pass
        
        if time.time() - start_time > timeout:
            print("Timeout waiting for Django server.")
            break
        
        time.sleep(1)

if __name__ == "__main__":
    # Start the Django server in a separate thread
    django_thread = threading.Thread(target=start_django_server)
    django_thread.daemon = True
    django_thread.start()

    # Wait for the Django server to start
    wait_for_server()

    # Start the PyQt5 window after the server starts
    start_web_window()
