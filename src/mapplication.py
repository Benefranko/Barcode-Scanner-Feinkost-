from PySide2.QtCore import QEvent, Signal
from PySide2.QtWidgets import QApplication


class MApplication(QApplication):
    inputBuffer: str = ""
    newScan = Signal(str)

    def __init__(self, args):
        super(MApplication, self).__init__(args)

    def notify(self, receiver, event: QEvent):
        try:
            if event.type() == QEvent.KeyPress:

                if event.text() == "\r":
                    self.newScan.emit(self.inputBuffer)
                    self.inputBuffer = ""
                else:
                    self.inputBuffer += event.text()
                # QApplication.notify(self, receiver, QKeyEvent(QEvent.KeyPress,  42, Qt.NoModifier, 0, 0, 0, 'AHA',
                # False,  1 ) )
                return True
            else:
                return QApplication.notify(self, receiver, event)
        except Exception as exc:
            print('critical error occurred: {0}. Please save your data and restart application'.format(exc))
            return False
