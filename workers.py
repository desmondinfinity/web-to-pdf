import threading
from PyQt6.QtCore import QThread, pyqtSignal
from converter import ConvertOptions, convert_to_pdf
from session import run_login_browser


class ConvertWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, options: ConvertOptions):
        super().__init__()
        self.options = options

    def run(self):
        try:
            convert_to_pdf(self.options, progress_callback=self.progress.emit)
            self.finished.emit(self.options.output_path)
        except Exception as e:
            self.error.emit(str(e))


class LoginWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()
        self._stop = threading.Event()

    def run(self):
        run_login_browser(self._stop, lambda ok, msg: self.finished.emit(ok, msg))

    def save_and_close(self):
        self._stop.set()
