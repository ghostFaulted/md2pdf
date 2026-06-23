import os
import tempfile
import traceback
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFileDialog, QLabel, QCheckBox, 
    QTextEdit, QMessageBox, QGroupBox, QSplitter,
    QSizePolicy, QComboBox, QDialog
)
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtCore import Qt, QByteArray, QBuffer, QIODevice, QSettings
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView

from .safe_pdf_view import SafePdfView
from .dialogs import CustomizeDialog, DefaultSettingsDialog
from .worker import CompilerWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("md2pdf - Markdown to PDF Converter")
        self.setMinimumSize(1100, 700)
        self.setAcceptDrops(True)
        
        self.input_file = ""
        self.output_file = ""
        self.preview_temp_pdf_path = os.path.join(tempfile.gettempdir(), "md2pdf_preview_cache.pdf")
        
        self.settings = QSettings("md2pdf", "md2pdf_app")
        
        self.selected_font = self.settings.value("default_font", "Times New Roman")
        self.selected_fontsize = int(self.settings.value("default_fontsize", 11))
        
        self._build_ui()

    def _build_ui(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = QWidget()
        left_widget.setMinimumWidth(350)
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
        
        btn_out = QPushButton("Save As .pdf")
        btn_out.clicked.connect(self._select_output)
        row_out.addWidget(self.lbl_output)
        row_out.addWidget(btn_out)

        file_layout.addLayout(row_in)
        file_layout.addLayout(row_out)
        file_group.setLayout(file_layout)
        left_layout.addWidget(file_group)

        opt_group = QGroupBox("Options")
        opt_layout = QVBoxLayout()
        
        row_settings = QHBoxLayout()
        self.chk_toc = QCheckBox("Generate Table of Contents")
        default_toc = self.settings.value("default_toc", "false") == "true"
        self.chk_toc.setChecked(default_toc)
        
        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["Obsidian MD", "Raw MD"])
        default_mode = self.settings.value("default_mode", "Obsidian MD")
        self.cmb_mode.setCurrentText(default_mode)
        
        row_settings.addWidget(self.chk_toc)
        row_settings.addWidget(self.cmb_mode)
        opt_layout.addLayout(row_settings)
        
        row_buttons = QHBoxLayout()
        self.btn_customize = QPushButton("Customize...")
        self.btn_customize.clicked.connect(self._open_customize_dialog)
        
        self.btn_default_settings = QPushButton("Default Settings...")
        self.btn_default_settings.clicked.connect(self._open_default_settings_dialog)
        
        row_buttons.addWidget(self.btn_customize)
        row_buttons.addWidget(self.btn_default_settings)
        opt_layout.addLayout(row_buttons)
        
        opt_group.setLayout(opt_layout)
        left_layout.addWidget(opt_group)

        btn_layout = QHBoxLayout()
        
        self.btn_preview = QPushButton("PREVIEW")
        self.btn_preview.setMinimumHeight(45)
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
        right_widget.setMinimumWidth(300)
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
        
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)

        main_layout.addWidget(splitter)
        self.setCentralWidget(central_widget)
        
        self._update_preview_button_state()

    def _update_preview_button_state(self):
        if self.input_file:
            self.btn_preview.setStyleSheet("font-weight: bold; background-color: #198754; color: white;")
        else:
            self.btn_preview.setStyleSheet("font-weight: bold; background-color: #333333; color: #888888; border: 1px solid #555555;")

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
            self._update_preview_button_state()

    def _select_output(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF As", self.output_file, "PDF Files (*.pdf)")
        if path:
            self.output_file = path
            self._set_elided_path(self.lbl_output, "Output", path)

    def _open_customize_dialog(self):
        dialog = CustomizeDialog(self.selected_font, self.selected_fontsize, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_font, self.selected_fontsize = dialog.get_values()

    def _open_default_settings_dialog(self):
        current_font = self.settings.value("default_font", "Times New Roman")
        current_size = int(self.settings.value("default_fontsize", 11))
        current_mode = self.settings.value("default_mode", "Obsidian MD")
        current_toc = self.settings.value("default_toc", "false") == "true"
        
        dialog = DefaultSettingsDialog(current_font, current_size, current_mode, current_toc, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            font, size, mode, toc = dialog.get_values()
            self.settings.setValue("default_font", font)
            self.settings.setValue("default_fontsize", size)
            self.settings.setValue("default_mode", mode)
            self.settings.setValue("default_toc", "true" if toc else "false")
            
            self.selected_font = font
            self.selected_fontsize = size
            self.cmb_mode.setCurrentText(mode)
            self.chk_toc.setChecked(toc)

    def _start_preview_compilation(self):
        self._start_compilation(is_preview=True)

    def _start_final_compilation(self):
        self._start_compilation(is_preview=False)

    def _clear_pdf_buffers(self):
        self.pdf_document.close()
        if hasattr(self, 'active_pdf_buffer'):
            self.active_pdf_buffer.close()
            del self.active_pdf_buffer
        if hasattr(self, 'active_pdf_data'):
            del self.active_pdf_data

    def _start_compilation(self, is_preview: bool):
        try:
            if not self.input_file:
                QMessageBox.warning(self, "Missing File", "Please select an input markdown file first.")
                return
            
            if not is_preview and not self.output_file:
                QMessageBox.warning(self, "Missing Destination", "Please specify where to save the final PDF.")
                return

            self.console.clear()
            self._clear_pdf_buffers()

            options = {
                "toc": self.chk_toc.isChecked(),
                "obsidian_mode": self.cmb_mode.currentText() == "Obsidian MD",
                "mainfont": self.selected_font,
                "fontsize": f"{self.selected_fontsize}pt"
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
                self._clear_pdf_buffers()
                
                with open(active_pdf, 'rb') as f:
                    pdf_bytes_data = f.read()
                
                self.active_pdf_data = QByteArray(pdf_bytes_data)
                self.active_pdf_buffer = QBuffer(self.active_pdf_data)
                self.active_pdf_buffer.open(QIODevice.OpenModeFlag.ReadOnly)
                
                self.pdf_document.load(self.active_pdf_buffer)
                self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
                self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
            except Exception as e:
                self._append_log(f"\nFailed to load preview: {str(e)}")
                
            if not is_preview:
                QMessageBox.information(self, "Success", "PDF exported and saved successfully.")
        else:
            self._append_log("\n>>> COMPILATION FAILED <<<")
            QMessageBox.critical(self, "Error", "Compilation failed. Check the logs for details.")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile() and url.toLocalFile().endswith(".md"):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile() and url.toLocalFile().endswith(".md"):
                    path = url.toLocalFile()
                    self.input_file = path
                    self._set_elided_path(self.lbl_input, "Input", path)
                    
                    in_p = Path(path)
                    auto_out = in_p.with_suffix('.pdf')
                    self.output_file = str(auto_out)
                    self._set_elided_path(self.lbl_output, "Output", self.output_file)
                    self._update_preview_button_state()
                    event.acceptProposedAction()
                    return

    def closeEvent(self, event):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            
        self._clear_pdf_buffers()
            
        if hasattr(self, 'preview_temp_pdf_path') and os.path.exists(self.preview_temp_pdf_path):
            try:
                os.remove(self.preview_temp_pdf_path)
            except Exception:
                pass
                
        event.accept()