from PySide2.QtCore import QThread, Slot, QObject
import git
from enum import Enum


class Updater(QThread):
    # Enum mit Objektzuständen
    class STATES(Enum):
        UNKNOWN = 0
        WAIT_FOR_CHECK = 1
        UPDATING = 2
        UPDATE_FINISHED = 3

    state = STATES.WAIT_FOR_CHECK
    repo: git.Repo = None

    def __init__(self, parent: QObject, path: str):
        # super(QThread, self).__init__(parent)
        self.repo = git.Repo(path, search_parent_directories=True)
        print(self.repo.git.status())
        self.get_most_recent_git_tag()


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

    def get_most_recent_git_tag(self):
        tags = sorted(self.repo.tags, key=lambda t: t.commit.committed_datetime)
        print("tags:", tags)
        for ver in reversed(tags):
            print(ver)
            if not ver.startsWith("v") or ver.count(".") != 3:
                continue
            latest_tag = tags[-1]


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

    @Slot()
    def updateThreadStarted(self):
        # change status
        return

    @Slot()
    def updateThreadFinished(self):
        # change status
        return
