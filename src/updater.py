from PySide2.QtCore import QThread, Signal, Slot
from git import Repo


class Updater(QThread):

    def __int__(self, parent):
        super(QThread, self).__init__(parent)

    def killThread(self):
        if self.isRunning():
            self.requestInterruption()
            if self.wait(100):
                self.quit()
                if self.wait(100):
                    print("quit failed")
                    self.terminate()
                    self.wait(100)

    # Bei Programmstart ausgeben
    # bei Internet seite anzeigen... z.b Neuste Version/ Updates vorhanden
    @staticmethod
    def getVersionStatus() -> str:
        return "git status"

    # Für Internet seite: wenn update gestartet → entweder nichts oder Updating... oder Success oder failed... anzeigen
    @staticmethod
    def getStatus():
        print("No Update done")
        print("Update failed:")
        print("Update successful")

    # Für Internet seite und start → aus db
    @staticmethod
    def getLastUpdate():
        print("date: (z.b. from loc db)")
        return

    # Aufgerufen von HTTP Thread → wichtig: wenn läuft 1. update button auf seite weg, wenn nicht immer hin
    def startUpdate(self):
        if self.isRunning():
            # Error
            return
        else:
            self.start()
        return

    def run(self) -> None:
        # save current version
        # git pull
        # if git pull fails -> reset to old version
        return

    @Slot
    def updateThreadStarted(self):
        # change status
        return

    @Slot
    def updateThreadFinished(self):
        # change status
        return
