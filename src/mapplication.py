from PySide2.QtCore import QEvent, Signal
from PySide2.QtWidgets import QApplication


import logging
from pathlib import Path
log = logging.getLogger(Path(__file__).name)


# Subclass QApplication, um eigene notify-Methode zu integrieren,
# um Sämtliche KeyPress Events vor allen anderen Objekten abzufangen.
# Es gibt zwar die Möglichkeit, das Fokussieren einzelner Objekte zu verhindern, aber um sicherzugehen, dass nicht
# irgendein Unterobjekt anvisiert wird, und so die keyPressEvent Methode nicht mehr aufgerufen wird, sollen hier alle
# Keypress Events abgefangen werden. Später vielleicht erweiterbar: Scanner Eingaben, von Tastatur trennen
# Ignoriere auch weitere Events, die es dem USer ermöglichen, aus dem Fenster zu gelangen, oder dieses zu schließen

class MApplication(QApplication):
    # Buffer für Eingabe
    inputBuffer: str = ""
    # Signal, verbunden mit NewScan() in MainWindow

    newScan: Signal = Signal(str)
    # don't block quit if try to exit
    want_exiting: bool = False

    def __init__(self, args):
        super(MApplication, self).__init__(args)

    def notify(self, receiver, event: QEvent):
        try:
            # Wenn das Event ein KeyPress ist:
            if event.type() == QEvent.KeyPress:
                # Wenn der Key ein Enter war, rufe die newScan Methode mit bisherigen Buffer auf und leere anschließend
                # diese. Der Barcode Scanner beendet nämlich jeden Scan mit einem r.
                if event.text() == "\r":
                    self.newScan.emit(self.inputBuffer)
                    self.inputBuffer = ""
                # Sonst füge die Taste dem Buffer hinzu
                else:
                    self.inputBuffer += event.text()

                event.accept()
                return True

            # Wenn das Fenster geschlossen werden soll, z.B. mit ALT F4, ignoriere das signal
            if not self.want_exiting and event.type() == QEvent.Close and self.inputBuffer != "quit":
                log.info("Prevent Window from closing (Type '[\\r] + \"quit\" + [ALT F4]' to close the Window)...")
                event.accept()
                return True

            # Wenn kein KeyPressEvent vorliegt, leite das Event an die Basisklasse weiter
            else:
                return QApplication.notify(self, receiver, event)
        except KeyboardInterrupt as exc:
            log.info("KeyboardInterruption in m_application::notify : {0}".format(exc))
            self.want_exiting = True
            QApplication.quit()
            return False
        except Exception as exc:
            log.critical("Exception in m_application::notify : {0}".format(exc))
            self.want_exiting = True
            QApplication.quit()
            return False
