from PySide2.QtCore import QThread, Slot, QObject
from enum import Enum
import constants
import subprocess
import timeit
import logging

# später mit success check and restore old version erweiterbar
from pathlib import Path
log = logging.getLogger(Path(__file__).name)


class Updater(QThread):
    # Enum mit Objektzuständen
    class STATES(Enum):
        UNKNOWN = 0
        NONE = 1
        UPDATING = 4
        UPDATE_FINISHED = 5

    state: STATES = STATES.NONE
    repo_path: str = ""

    status: str = ""
    exit_state: int = 0

    last_check: float = 0.0

    update_available: bool = False
    newest_version: str = "-1"
    current_version: str = "-1"

    def __init__(self):
        super().__init__()

    def setPath(self, path):
        self.repo_path = path

    def exec_git(self, args: []) -> (int, str):
        if self.repo_path and self.repo_path == "" or not self.repo_path:
            log.error("exec_git failed: args:{0}: REPO DIR NOT INITIALIZED".format(str(["git.exe"] + args)))
            return -1, ""

        try:
            # log.debug("exec_git: {0}".format(str(["git.exe"] + args)))
            with subprocess.Popen([constants.git_programm_path] + args, cwd=self.repo_path, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT) as proc:
                proc.wait(timeout=300)
                out = str(proc.stdout.read().decode())
                return proc.returncode, out
        except Exception as e:
            log.error("exec_git failed: {0} args:{1}".format(e, ["git.exe"] + args))
            return -1, str(e.args)

    def isUpdateAvailable(self) -> bool:
        n = self.getNewestVersion().split(".")
        o = self.getCurrentVersion().split(".")
        if len(n) != 3 or len(o) != 3:
            log.warning("GOT INVALID VERSION FOR CHECK! {0}, {1}".format(str(n), str(o)))
            return False
        for i in range(0, 3):
            if n[i].isdigit() and o[i].isdigit():
                if int(n[i]) > int(o[i]):
                    return True
        return False

    def getNewestVersion(self):
        # check if last check was longer than 5min ago
        # if true check
        # else return old
        if timeit.default_timer() - self.last_check > 300:
            self.last_check = timeit.default_timer()
            ret_v, rets = self.exec_git(["-c", "versionsort.suffix=-", "ls-remote", "--tags", "--sort=-v:refname", "origin"])
            if ret_v == 0:
                tags: [] = str(rets).split("\n")
                for ver in tags:
                    if "refs/tags/v" in ver:
                        ver = ver[ver.index("refs/tags/v") + 10:]
                    if not ver.startswith("v") or ver.count(".") != 2:
                        continue
                    self.newest_version = ver[1:]
                    return ver[1:]
                return "-1"
            else:
                log.warning("getNewestVersion failed: {0}".format(rets))
                return "-1"
        else:
            return self.newest_version

    def eventHandler(self, event: str, value: str = ""):

        if self.state == self.STATES.UNKNOWN:
            pass

        elif self.state == self.STATES.NONE:
            if event == "START_UPDATE":
                self.state = self.STATES.UPDATING
                self.start()
            elif event == "GET_STATUS":
                return ""
            pass

        elif self.state == self.STATES.UPDATING:
            if event == "GET_STATUS":
                if not self.isRunning():
                    self.state = self.STATES.UPDATE_FINISHED
                    return "Unknown Error! (" + self.status + ")"
                return "Updating... ( Laden sie die Seite 1 mal neu für neuere Infos )"
            pass

        elif self.state == self.STATES.UPDATE_FINISHED:
            if event == "GET_STATUS":
                # self.state = self.STATES.NONE
                # tmp = self.status
                # self.status = ""
                return self.status + "\nBitte starten sie das Programm neu!"
            pass

        else:
            log.error(" UPDATER: UNKNOWN STATE: {0}".format(self.state))

    def startUpdate(self):
        return self.eventHandler("START_UPDATE")

    def killThread(self):
        if self.isRunning():
            self.requestInterruption()
            if self.wait(100):
                self.quit()
                if self.wait(100):
                    print("quit failed")
                    self.terminate()
                    self.wait(100)

    def getCurrentVersion(self):
        if self.current_version == "-1":
            ret, tgs = self.exec_git(["tag", "-l", "--sort=-v:refname"])
            tags: [] = str(tgs).split("\n")
            for ver in tags:
                if not ver.startswith("v") or ver.count(".") != 2:
                    continue
                self.current_version = ver[1:]
                return self.current_version
            return "-1"
        return self.current_version

    # Für Internet seite: wenn update gestartet → entweder nichts oder Updating... oder Success oder failed... anzeigen
    def getStatus(self):
        return self.eventHandler("GET_STATUS")

    def run(self) -> None:

        if constants.reset_before_update:
            ret_v, rets = self.exec_git(["reset", "--hard", "origin/main"])
            log.debug("     [GIT RETURN]:\n {0} -> Exitcode: ({1})".format(rets, ret_v))
            if ret_v != 0:
                self.status = "Update fehlgeschlagen! Reset failed: " + rets
                log.error("Update fehlgeschlagen! Reset failed: {0}".format(rets))
                self.exit_state = ret_v
                self.state = self.STATES.UPDATE_FINISHED
                self.current_version = "-1"  # generate new next time
                return

        ret_v, rets = self.exec_git(["pull", "-f"])
        log.debug("     [GIT RETURN]:\n {0} -> Exitcode: ({1})".format(rets, ret_v))
        if ret_v != 0:
            self.status = "Update fehlgeschlagen! Pull failed: " + rets
            log.error("Update fehlgeschlagen! Pull failed: {0}".format(rets))
            self.exit_state = ret_v
        else:
            self.status = "Erfolgreich Update ausgeführt!"
            # reset to exact version has????
        self.state = self.STATES.UPDATE_FINISHED
        self.current_version = "-1"  # generate new next time
        return
