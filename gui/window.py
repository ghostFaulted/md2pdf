import traceback
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFileDialog, QLabel, QCheckBox, 
    QTextEdit, QMessageBox, QGroupBox
)
from PyQt6.QtCore import QThread, pyqtSignal
from core.compiler import MarkdownCompiler

class CompilerWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, input_path: str, output_path: str, options: dict, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.options = options
        self.compiler = MarkdownCompiler()

    def run(self):
        self.log_signal.emit("Starting compilation...\n")
        success, log = self.compiler.compile(self.input_path, self.output_path, self.options)
        self.finished_signal.emit(success, log)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Obsidian to PDF (LaTeX Engine)")
        self.setMinimumSize(700, 500)
        
        self.input_file = ""
        self.output_file = ""
        
        self._build_ui()

    def _build_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        file_group = QGroupBox("File Paths")
        file_layout = QVBoxLayout()

        row_in = QHBoxLayout()
        self.lbl_input = QLabel("Input: Not selected")
        btn_in = QPushButton("Browse .md")
        btn_in.clicked.connect(self._select_input)
        row_in.addWidget(self.lbl_input)
        row_in.addWidget(btn_in)
        
        row_out = QHBoxLayout()
        self.lbl_output = QLabel("Output: Not selected")
        btn_out = QPushButton("Save As .pdf")
        btn_out.clicked.connect(self._select_output)
        row_out.addWidget(self.lbl_output)
        row_out.addWidget(btn_out)

        file_layout.addLayout(row_in)
        file_layout.addLayout(row_out)
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)

        opt_group = QGroupBox("Options")
        opt_layout = QHBoxLayout()
        self.chk_toc = QCheckBox("Generate Table of Contents")
        opt_layout.addWidget(self.chk_toc)
        opt_group.setLayout(opt_layout)
        main_layout.addWidget(opt_group)

        self.btn_convert = QPushButton("COMPILE TO PDF")
        self.btn_convert.setMinimumHeight(40)
        self.btn_convert.setStyleSheet("font-weight: bold;")
        self.btn_convert.clicked.connect(self._start_compilation)
        main_layout.addWidget(self.btn_convert)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("font-family: Consolas, monospace; background-color: #1e1e1e; color: #d4d4d4;")
        main_layout.addWidget(self.console)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def _select_input(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Obsidian Markdown", "", "Markdown Files (*.md)")
        if path:
            self.input_file = path
            self.lbl_input.setText(f"Input: {path}")
            
            in_p = Path(path)
            auto_out = in_p.with_suffix('.pdf')
            self.output_file = str(auto_out)
            self.lbl_output.setText(f"Output: {self.output_file}")

    def _select_output(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF As", self.output_file, "PDF Files (*.pdf)")
        if path:
            self.output_file = path
            self.lbl_output.setText(f"Output: {path}")

    def _start_compilation(self):
        try:
            if not self.input_file or not self.output_file:
                QMessageBox.warning(self, "Missing Paths", "Please select both input and output files.")
                return

            self.btn_convert.setEnabled(False)
            self.console.clear()

            options = {
                "toc": self.chk_toc.isChecked()
            }

            self.worker = CompilerWorker(self.input_file, self.output_file, options, parent=self)
            self.worker.log_signal.connect(self._append_log)
            self.worker.finished_signal.connect(self._on_compilation_finished)
            self.worker.start()

        except Exception as e:
            error_details = traceback.format_exc()
            QMessageBox.critical(self, "Critical Error", f"Failed to start compilation:\n{error_details}")
            self.btn_convert.setEnabled(True)

    def _append_log(self, text: str):
        self.console.append(text)

    def _on_compilation_finished(self, success: bool, log: str):
        self._append_log(log)
        if success:
            self._append_log("\n>>> COMPILATION SUCCESSFUL <<<")
            QMessageBox.information(self, "Success", "PDF generated successfully.")
        else:
            self._append_log("\n>>> COMPILATION FAILED <<<")
            QMessageBox.critical(self, "Error", "Compilation failed. Check the logs for details.")
        
        self.btn_convert.setEnabled(True)