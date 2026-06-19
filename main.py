import sys
from PyQt6.QtWidgets import QApplication, QMessageBox

from core.system_check import check_dependencies
from gui.window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    is_ready, _, error_msg = check_dependencies()
    
    if not is_ready:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("md2pdf - System Dependency Error")
        msg_box.setText("Missing required external tools.")
        msg_box.setInformativeText(error_msg)
        msg_box.exec()
        sys.exit(1)

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()