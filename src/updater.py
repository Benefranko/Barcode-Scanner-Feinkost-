from PySide2.QtCore import QThread, Slot, QObject
import git
from enum import Enum
import subprocess
import sys
from subprocess import Popen, PIPE, STDOUT

import signal

class Updater(QThread):
    # Enum mit Objektzuständen
    class STATES(Enum):
        UNKNOWN = 0
        WAITING = 1
        CHECKING_FOR_UPDATE = 2
        CHECKING_FINISHED = 3
        UPDATING = 4
        UPDATE_FINISHED = 5

    state: STATES = STATES.WAITING
    exit_state: int = 0
    repo: git.Repo = None

    status: str = ""

    update_available: bool = False
    newest_version: str = ""

    def __init__(self, parent, path: str):
        # super(QThread, self).__init__(parent)
        self.repo = git.Repo(path, search_parent_directories=True)
        print(self.repo.git.status())
        print(self.getCurrentVersion())
        print(self.getCurrentCommit())
        self.updateAvailable()
        self.startUpdate()

    def updateAvailable(self):
        return self.update_available

    def checkForNewVersion(self):
        # pull to branch
        # check newest TAg
        # compare to own one
        # return (bool updateAvailable, own version, new version)
        return

    def eventHandler(self, event: str, value: str):

        if self.state == self.STATES.UNKNOWN:
            pass

        elif self.state == self.STATES.WAITING:
            if event == "START_UPDATE":
                self.startUpdate()

        elif self.state == self.STATES.UPDATING:
            if event == "GET_STATUS":
                return "Updating..."
            pass

        elif self.state == self.STATES.UPDATE_FINISHED:
            if event == "GET_STATUS":
                self.state = self.STATES.WAITING
                return self.status
            pass

        elif self.state == self.STATES.CHECKING_FOR_UPDATE:
            pass

        elif self.state == self.STATES.CHECKING_FINISHED:
            if event == "GET_STATUS":
                self.state = self.STATES.WAITING
                return self.status
            pass

        else:
            pass

    def startUpdate(self):
        self.state = self.STATES.UPDATING
        self.exit_state = 0
        old_version = self.getCurrentVersion()

        try:
            self.repo.remotes.origin.pull()
#            print("TEST", [sys.executable, sys.argv[0]])
#            p = Popen([sys.executable, sys.argv[0], '--help', '-platform off-screen'], stdout=PIPE, stdin=PIPE)
#
            # stdout_data = p.communicate(input='quit'.encode(), timeout=1)[0]
#            print("p:", p.stdout.read(10))

#            p.stdin.write("quit".encode())#
#            p.send_signal(signal.SIGTERM)

#           print("poll:", p.wait())

        except Exception as e:
            self.exit_state = -1
            print("ERROR: ", e)
            # Restore current Version
            pass
        if self.exit_state !=0:
            self.restoreOldVersion(old_version)


        self.state = self.STATES.UPDATE_FINISHED

    def restoreOldVersion(self, hash):
        try:
            pass
        except Exception as e:
            return 1
        return 0

    def killThread(self):
        if self.isRunning():
            self.requestInterruption()
            if self.wait(100):
                self.quit()
                if self.wait(100):
                    print("quit failed")
                    self.terminate()
                    self.wait(100)

    def getCurrentCommit(self):
        return self.repo.head.object.hexsha

    def getCurrentVersion(self):
        tags: [] = sorted(self.repo.tags, key=lambda t: t.commit.committed_datetime)
        for ver in reversed(tags):
            if not ver.name.startswith("v") or ver.name.count(".") != 2:
                continue
            return ver.name[1:]
        return "-1"

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
