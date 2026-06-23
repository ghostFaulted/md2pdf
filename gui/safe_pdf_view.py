from PyQt6.QtPdfWidgets import QPdfView

class SafePdfView(QPdfView):
    def resizeEvent(self, event):
        if self.width() <= 10 or self.height() <= 10:
            event.accept()
            return
        if self.window() and (self.window().isMinimized() or self.window().isHidden()):
            event.accept()
            return
        super().resizeEvent(event)