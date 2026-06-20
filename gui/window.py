import os
import tempfile
import traceback
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFileDialog, QLabel, QCheckBox, 
    QTextEdit, QMessageBox, QGroupBox, QSplitter,
    QSizePolicy
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView
from core.compiler import MarkdownCompiler

class SafePdfView(QPdfView):
    def resizeEvent(self, event):
        if self.width() <= 10 or self.height() <= 10:
            event.accept()
            return
        if self.window() and (self.window().isMinimized() or self.window().isHidden()):
            event.accept()
            return
        super().resizeEvent(event)

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("md2pdf - Markdown to PDF Converter")
        self.setMinimumSize(1100, 700)
        
        self.input_file = ""
        self.output_file = ""
        self.preview_temp_pdf_path = os.path.join(tempfile.gettempdir(), "md2pdf_preview_cache.pdf")
        
        self._build_ui()

    def _build_ui(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)

        file_group = QGroupBox("File Paths")
        file_layout = QVBoxLayout()
        
        row_in = QHBoxLayout()
        self.lbl_input = QLabel("Input: Not selected")
        self.lbl_input.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        
        self.btn_in = QPushButton("Browse .md")
        self.btn_in.clicked.connect(self._select_input)
        row_in.addWidget(self.lbl_input)
        row_in.addWidget(self.btn_in)
        
        row_out = QHBoxLayout()
        self.lbl_output = QLabel("Output: Not selected")
        self.lbl_output.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        
        self.btn_out = QPushButton("Save As .pdf")
        self.btn_out.clicked.connect(self._select_output)
        row_out.addWidget(self.lbl_output)
        row_out.addWidget(self.btn_out)

        file_layout.addLayout(row_in)
        file_layout.addLayout(row_out)
        file_group.setLayout(file_layout)
        left_layout.addWidget(file_group)

        opt_group = QGroupBox("Options")
        opt_layout = QHBoxLayout()
        self.chk_toc = QCheckBox("Generate Table of Contents")
        opt_layout.addWidget(self.chk_toc)
        opt_group.setLayout(opt_layout)
        left_layout.addWidget(opt_group)

        btn_layout = QHBoxLayout()
        
        self.btn_preview = QPushButton("PREVIEW")
        self.btn_preview.setMinimumHeight(45)
        self.btn_preview.setStyleSheet("font-weight: bold;")
        self.btn_preview.clicked.connect(self._start_preview_compilation)
        
        self.btn_convert = QPushButton("COMPILE TO PDF")
        self.btn_convert.setMinimumHeight(45)
        self.btn_convert.setStyleSheet("font-weight: bold; background-color: #0d6efd; color: white;")
        self.btn_convert.clicked.connect(self._start_final_compilation)
        
        btn_layout.addWidget(self.btn_preview)
        btn_layout.addWidget(self.btn_convert)
        left_layout.addLayout(btn_layout)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("font-family: Consolas, monospace; background-color: #1e1e1e; color: #d4d4d4;")
        left_layout.addWidget(self.console)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)

        preview_group = QGroupBox("PDF Live Preview")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(2, 2, 2, 2)

        self.pdf_view = SafePdfView(self)
        self.pdf_document = QPdfDocument(self)
        self.pdf_view.setDocument(self.pdf_document)
        
        preview_layout.addWidget(self.pdf_view)
        right_layout.addWidget(preview_group)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)

        main_layout.addWidget(splitter)
        self.setCentralWidget(central_widget)

    def _set_elided_path(self, label: QLabel, prefix: str, full_path: str):
        path_obj = Path(full_path)
        if len(path_obj.parts) > 2:
            display_text = f"{prefix}: .../{path_obj.parent.name}/{path_obj.name}"
        else:
            display_text = f"{prefix}: {full_path}"
        
        label.setText(display_text)
        label.setToolTip(full_path)

    def _select_input(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Markdown File", "", "Markdown Files (*.md)")
        if path:
            self.input_file = path
            self._set_elided_path(self.lbl_input, "Input", path)
            
            in_p = Path(path)
            auto_out = in_p.with_suffix('.pdf')
            self.output_file = str(auto_out)
            self._set_elided_path(self.lbl_output, "Output", self.output_file)

    def _select_output(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF As", self.output_file, "PDF Files (*.pdf)")
        if path:
            self.output_file = path
            self._set_elided_path(self.lbl_output, "Output", path)

    def _start_preview_compilation(self):
        self._start_compilation(is_preview=True)

    def _start_final_compilation(self):
        self._start_compilation(is_preview=False)

    def _start_compilation(self, is_preview: bool):
        try:
            if not self.input_file:
                QMessageBox.warning(self, "Missing File", "Please select an input markdown file first.")
                return
            
            if not is_preview and not self.output_file:
                QMessageBox.warning(self, "Missing Destination", "Please specify where to save the final PDF.")
                return

            self.console.clear()
            self.pdf_document.close()

            options = {
                "toc": self.chk_toc.isChecked()
            }

            target_output = self.preview_temp_pdf_path if is_preview else self.output_file

            self.worker = CompilerWorker(self.input_file, target_output, options, is_preview, parent=self)
            self.worker.log_signal.connect(self._append_log)
            self.worker.finished_signal.connect(self._on_compilation_finished)
            self.worker.start()

        except Exception as e:
            error_details = traceback.format_exc()
            QMessageBox.critical(self, "Critical Error", f"Failed to start compilation:\n{error_details}")

    def _append_log(self, text: str):
        self.console.append(text)

    def _on_compilation_finished(self, success: bool, log: str, is_preview: bool):
        self._append_log(log)
        
        if success:
            self._append_log("\n>>> COMPILATION SUCCESSFUL <<<")
            try:
                active_pdf = self.preview_temp_pdf_path if is_preview else self.output_file
                self.pdf_document.load(active_pdf)
                self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
                self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
            except Exception as e:
                self._append_log(f"\nFailed to load preview: {str(e)}")
                
            if not is_preview:
                QMessageBox.information(self, "Success", "PDF exported and saved successfully.")
        else:
            self._append_log("\n>>> COMPILATION FAILED <<<")
            QMessageBox.critical(self, "Error", "Compilation failed. Check the logs for details.")

    def closeEvent(self, event):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            
        if hasattr(self, 'preview_temp_pdf_path') and os.path.exists(self.preview_temp_pdf_path):
            try:
                os.remove(self.preview_temp_pdf_path)
            except Exception:
                pass
                
        event.accept()