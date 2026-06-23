from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QComboBox, QSpinBox, QCheckBox, QDialogButtonBox
from PyQt6.QtGui import QFont

class CustomizeDialog(QDialog):
    def __init__(self, current_font: str, current_size: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Customize Formatting")
        self.setMinimumWidth(350)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.font_combo = QComboBox()
        safe_fonts = [
            "Times New Roman",
            "Arial",
            "Calibri",
            "Georgia",
            "Verdana",
            "Segoe UI",
            "Tahoma",
            "Consolas",
            "Courier New"
        ]
        self.font_combo.addItems(safe_fonts)
        
        if current_font in safe_fonts:
            self.font_combo.setCurrentText(current_font)
        else:
            self.font_combo.setCurrentText("Times New Roman")
            
        form_layout.addRow("Main Font:", self.font_combo)
        
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 24)
        self.size_spin.setValue(current_size)
        form_layout.addRow("Font Size (pt):", self.size_spin)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_values(self) -> tuple[str, int]:
        return self.font_combo.currentText(), self.size_spin.value()

class DefaultSettingsDialog(QDialog):
    def __init__(self, current_font: str, current_size: int, current_mode: str, current_toc: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings by Default")
        self.setMinimumWidth(380)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.font_combo = QComboBox()
        safe_fonts = [
            "Times New Roman",
            "Arial",
            "Calibri",
            "Georgia",
            "Verdana",
            "Segoe UI",
            "Tahoma",
            "Consolas",
            "Courier New"
        ]
        self.font_combo.addItems(safe_fonts)
        if current_font in safe_fonts:
            self.font_combo.setCurrentText(current_font)
        else:
            self.font_combo.setCurrentText("Times New Roman")
        form_layout.addRow("Default Font:", self.font_combo)
        
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 24)
        self.size_spin.setValue(current_size)
        form_layout.addRow("Default Size (pt):", self.size_spin)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Obsidian MD", "Raw MD"])
        self.mode_combo.setCurrentText(current_mode)
        form_layout.addRow("Default Mode:", self.mode_combo)
        
        self.toc_chk = QCheckBox()
        self.toc_chk.setChecked(current_toc)
        form_layout.addRow("Default TOC:", self.toc_chk)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_values(self) -> tuple[str, int, str, bool]:
        return (
            self.font_combo.currentText(),
            self.size_spin.value(),
            self.mode_combo.currentText(),
            self.toc_chk.isChecked()
        )