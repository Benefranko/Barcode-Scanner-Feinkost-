import os
from pathlib import Path
from PySide2.QtCore import QFile, QTimerEvent
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QPushButton, QLayout, QLabel, QLayoutItem
from PySide2.QtCore import QObject, Signal, Slot
from PySide2.QtGui import QImage

from enum import Enum

from databasemanager import DataBaseManager


class MainWindow(QMainWindow):
    window = None
    SHOW_TIME = 10
    CHANGE_ADVERTISE_TIME = 2

    showTimeTimer = SHOW_TIME
    changeAdvertiseTimer = CHANGE_ADVERTISE_TIME
    timerID = -1
    databasemanager = None

    testCounter = 1

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
        self.showFullScreen()

        # own changes
        self.setWindowTitle("My App")
        self.window.b1.setStyleSheet("background-image: url(\"C:/Users/Markus/Desktop/Schulzeug/Q11/Englisch Converstation/whiskyy-klein_42261_480x576.jpg\"); color: blue;")
        self.window.b1.setFixedSize(QImage("C:/Users/Markus/Desktop/Schulzeug/Q11/Englisch Converstation/whiskyy-klein_42261_480x576.jpg").size())
        self.window.frame.setStyleSheet("background-image: url(\"C:/Users/Markus/Downloads/47271122-es-tut-uns-leid-symbol-internet-taste-auf-weißem-hintergrund-.jpg\"); color: blue;")
        self.window.frame.setFixedSize(QImage("C:/Users/Markus/Downloads/47271122-es-tut-uns-leid-symbol-internet-taste-auf-weißem-hintergrund-.jpg").size())

        # connect
        self.window.pushButton.clicked.connect(self.button1clicked)
        self.window.pushButton_2.clicked.connect(self.button2clicked)

        # connect to database
        self.databasemanager = DataBaseManager()
        self.databasemanager.connect()

        # start Timer
        self.timerID = self.startTimer(1000)

    def __exit__(self, exc_type, exc_value, traceback):
        self.killTimer(self.timerID)

    def load_ui(self):
        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent / "form.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.window = loader.load(ui_file, self)
        ui_file.close()

    def timerEvent(self, event: QTimerEvent) -> None:
        self.event_handler("TIMER")

    def new_advertise(self):
        self.event_handler("NEW_LABEL", "C:/Users/Markus/Desktop/Schulzeug/Q11/Englisch Converstation/img_5807-1_40950_362x480.jpg")
        return

    def newScanHandling(self, value):
        self.showTimeTimer = self.SHOW_TIME
        self.state = self.STATES.SHOW_PRODUCT_DESCRIPTION
        # self.databasemanager.p_all()

        data = self.databasemanager.get_data_by_ean(int(value))
        if data is None:
            # switch page to Nothing found
            self.window.stackedWidget.setCurrentIndex(2)
        else:
            self.window.p_name.setText(value)
            self.window.i1.setText(value)
            self.window.w1.setText("value")
            self.window.i2.setText(data.cursor_description[0][0])
            self.window.w2.setText(str(data[0]))
            self.window.i2.setText(data.cursor_description[77][0])
            self.window.w2.setText(data[77])
            self.window.i3.setText(data.cursor_description[79][0])
            self.window.w3.setPlainText(data[79])

            # switch page
            self.window.stackedWidget.setCurrentIndex(1)
        return

    def event_handler(self, action, value = None):
        handled: bool = False;

        # GLOBAL ACTION HANDLING
        if action == "NEW_LABEL":
            layout = self.window.groupBox.layout()
            label = None

            if value.startswith("C:/"):
                label = QPushButton(self)
                label.setStyleSheet("background-image: url(\"" + value + "\")")
                label.setFixedSize(QImage(value).size())

            else:
                label = QLabel(self)
                label.setText(value)

            layout.addWidget(label, self.testCounter / 20, self.testCounter % 20 )
            self.testCounter = self.testCounter + 1
            return

        # STATE specific ACTION HANDLING
        match self.state:
            case self.STATES.SHOW_PRODUCT_DESCRIPTION:
                if action == "EXIT_SHOW_DESCRIPTION":
                    self.window.stackedWidget.setCurrentIndex(0)
                    self.state = self.STATES.WAIT_FOR_SCAN
                    return

                if action == "TIMER":
                    handled = True
                    if self.showTimeTimer > 1:
                        self.showTimeTimer = self.showTimeTimer - 1
                    else:
                        self.showTimeTimer = self.SHOW_TIME
                        self.event_handler("EXIT_SHOW_DESCRIPTION")

                if action == "NEW_SCAN":
                    self.newScanHandling(value)
                    return

            case self.STATES.WAIT_FOR_SCAN:
                if action == "NEW_SCAN":
                    self.newScanHandling(value)
                    return

                if action == "CHANGE_ADVERTISE":
                    self.new_advertise()
                    return

                if action == "TIMER":
                    handled = True
                    if self.changeAdvertiseTimer > 1:
                        self.changeAdvertiseTimer = self.changeAdvertiseTimer - 1
                    else:
                        self.changeAdvertiseTimer = self.CHANGE_ADVERTISE_TIME
                        self.event_handler("CHANGE_ADVERTISE")

            case _:
                print("ERROR...")

        if not handled:
            print("ERROR: UNHANDLED ACTION:" + action)

    def button1clicked(self):
        cols = self.databasemanager.get_header_list()
        for i in cols:
            self.event_handler("NEW_LABEL", i)

    def button2clicked(self):
        layout = self.window.groupBox.layout
        for i in reversed(range(layout().count())):
            self.window.groupBox.layout().itemAt(i).widget().deleteLater()


    @Slot(str)
    def new_scan(self, value):
        self.event_handler("NEW_SCAN", value)
