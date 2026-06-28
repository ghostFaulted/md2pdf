from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QWheelEvent

class SafePdfView(QPdfView):
    def resizeEvent(self, event):
        if self.width() <= 10 or self.height() <= 10:
            event.accept()
            return
        if self.window() and (self.window().isMinimized() or self.window().isHidden()):
            event.accept()
            return
        super().resizeEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            angle = event.angleDelta().y()
            zoom_step = 0.1 if angle > 0 else -0.1
            
            old_zoom = self.zoomFactor()
            new_zoom = max(0.5, min(3.0, old_zoom + zoom_step))
            
            if old_zoom == new_zoom:
                event.accept()
                return

            mouse_pos = event.position()
            
            hbar = self.horizontalScrollBar()
            vbar = self.verticalScrollBar()
            
            content_x = hbar.value() + mouse_pos.x()
            content_y = vbar.value() + mouse_pos.y()
            
            self.setZoomMode(QPdfView.ZoomMode.Custom)
            self.setZoomFactor(new_zoom)
            
            ratio = new_zoom / old_zoom
            new_content_x = content_x * ratio
            new_content_y = content_y * ratio
            
            new_h_val = int(new_content_x - mouse_pos.x())
            new_v_val = int(new_content_y - mouse_pos.y())
            
            hbar.setValue(new_h_val)
            vbar.setValue(new_v_val)
            
            event.accept()
        else:
            super().wheelEvent(event)