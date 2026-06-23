from PyQt6.QtCore import QThread, pyqtSignal
from core.compiler import MarkdownCompiler

class CompilerWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, bool)

    def __init__(self, input_path: str, output_path: str, options: dict, is_preview: bool, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.options = options
        self.is_preview = is_preview
        self.compiler = MarkdownCompiler()

    def run(self):
        msg = "Starting preview compilation...\n" if self.is_preview else "Starting final compilation...\n"
        self.log_signal.emit(msg)
        success, log = self.compiler.compile(self.input_path, self.output_path, self.options)
        self.finished_signal.emit(success, log, self.is_preview)