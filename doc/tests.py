
from PySide2.QtCore import QEvent, Signal, Slot
from PySide2.QtWidgets import QApplication


import logging
from pathlib import Path
log = logging.getLogger(Path(__file__).name)


class MApplication(QApplication):
    # Zwischenspeicher für Eingabe
    inputBuffer: str = ""
a = [...]
    def notify(self, receiver, event: QEvent):
        try:
            # Ist das Event 'event' ein Tastendruckevent, filtere es heraus
            if event.type() == QEvent.KeyPress:
                if event.text() == "\r":
                    self.newScan.emit(self.inputBuffer)
                    self.inputBuffer = ""
                else:
                    self.inputBuffer += event.text()
            # Wenn kein KeyPressEvent vorliegt, leite das Event an die Basisklasse 'QApplication' weiter
            else:
                return QApplication.notify(self, receiver, event)
a = [...]

