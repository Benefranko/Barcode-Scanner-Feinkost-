import os
from pathlib import Path
from PySide2.QtCore import QFile, QTimerEvent
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QPushButton, QLayout, QLabel, QLayoutItem
from PySide2.QtCore import QObject, Signal, Slot
from enum import Enum



class MainWindow(QMainWindow):
    window = None
    showTime = 50

    class STATES(Enum):
        UNKNOWN = 0
        SHOW_PRODUCT_DESCRIPTION = 1
        WAIT_FOR_SCAN = 2
    state = STATES.SHOW_PRODUCT_DESCRIPTION

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.load_ui()
        self.state = self.STATES.WAIT_FOR_SCAN
        self.window.stackedWidget.setCurrentIndex(0)

        # own changes
        self.setWindowTitle("My App")
        # connect
        self.window.pushButton.clicked.connect(self.button1clicked)
        self.window.pushButton_2.clicked.connect(self.button2clicked)

    def load_ui(self):
        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent / "form.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.window = loader.load(ui_file, self)
        ui_file.close()

    def timerEvent(self, event: QTimerEvent) -> None:
        self.showTime = self.showTime - 1
        if self.showTime <= 0:
            self.killTimer(event.timerId())
            self.switch_state("TIMER_TIMEOUT")

    def switch_state(self, action, value = None):
        match self.state:
            case self.STATES.SHOW_PRODUCT_DESCRIPTION:
                if action == "TIMER_TIMEOUT":
                    self.window.stackedWidget.setCurrentIndex(0)
                    self.state = self.STATES.WAIT_FOR_SCAN
                    return

            case self.STATES.WAIT_FOR_SCAN:
                if action == "NEW_LABEL":
                    layout = self.window.groupBox.layout()
                    layout.addWidget(QLabel(value))
                    return

                if action == "NEW_SCAN":
                    self.window.p_name.setText(value)
                    self.window.i1.setText(value)
                    self.window.w1.setText("value")

                    self.window.stackedWidget.setCurrentIndex(1)
                    self.state = self.STATES.SHOW_PRODUCT_DESCRIPTION

                    self.startTimer(100)

                    return
            case _:
                print("ERROR...")
        print("ERROR: UNHANDLED ACTION:" + action)

    def button1clicked(self):
        self.switch_state("NEW_LABEL", "value")

    def button2clicked(self):
        print("clicked -> 2")
        layout = self.window.groupBox.layout
        for i in reversed(range(layout().count())):
            self.window.groupBox.layout().itemAt(i).widget().deleteLater()

    @Slot(str)
    def new_scan(self, value):
        self.switch_state("NEW_SCAN", value)
