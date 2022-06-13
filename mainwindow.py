import os
from pathlib import Path
from PySide2.QtCore import QFile, QTimerEvent, Qt
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QPushButton, QLayout, QLabel, QLayoutItem, QFrame
from PySide2.QtCore import QObject, Signal, Slot
from PySide2.QtGui import QImage, QPixmap, QFontMetrics, QResizeEvent, QFont

from enum import Enum

from databasemanager import DataBaseManager


class MainWindow(QMainWindow):
    # Constants
    SHOW_TIME = 15
    CHANGE_ADVERTISE_TIME = 5
    SPECIAL_PRICE_RED_LINE_HEIGHT = 5
    SPACE_BETWEEN_PRICE_AND_SPECIAL_PRICE = 10
    SPECIAL_PRICE_FONT_SIZE = 18

    # Attributes
    showTimeTimer = SHOW_TIME
    changeAdvertiseTimer = CHANGE_ADVERTISE_TIME
    timerID = -1

    # Objects
    databasemanager = None
    window = None
    special_price_red_line = None
    special_price_label = None

    # Tests
    testCounter = 1
    t2 = 0

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

        # fullscreen
        # self.showFullScreen()
        self.setFixedSize(800, 400)
        self.setWindowFlags(Qt.CustomizeWindowHint | Qt.FramelessWindowHint)

        # init line...
        self.special_price_red_line = QFrame(self.window.groupBox_infos)
        self.special_price_red_line.setFrameShape(QFrame.HLine)
        # self.special_price_red_line.setFixedHeight(20)
        self.special_price_red_line.setLineWidth(6)
        self.special_price_red_line.setStyleSheet("color: rgba(255, 0, 0, 150)")
        self.special_price_red_line.hide()

        # special price label
        self.special_price_label = QLabel(self.window.groupBox_infos)
        self.special_price_label.setStyleSheet("color: rgba(255, 0, 0, 255)")
        self.special_price_label.setFont(QFont("Segoe UI", self.SPECIAL_PRICE_FONT_SIZE, QFont.Bold))
        self.special_price_label.hide()

        # own changes
        self.setWindowTitle("Feinkostscanner")

        pix = QPixmap("C:/Users/Markus/Downloads/47271122-es-tut-uns-leid-symbol-internet-taste-auf-weißem-hintergrund-.jpg")
        self.window.frame.setPixmap(pix.scaled(pix.toImage().size() / 2))

        pix = QPixmap("E:\Schulzeug\P-Seminar\git\Barcode-Scanner-Feinkost-/sunmi_scan.png")
        self.window.img1.setPixmap(pix.scaled( pix.toImage().size() / 5))

        pix = QPixmap("E:\Schulzeug\P-Seminar\git\Barcode-Scanner-Feinkost-/logo.jpg")
        self.window.logo.setPixmap(pix.scaled(pix.toImage().size() / 4))

        self.event_handler("NEW_LABEL", "C:/Users/Markus/Desktop/Schulzeug/Q11/Englisch Converstation/img_5807-1_40950_362x480.jpg")

        # ...
        #self.window.img.setMinimumWidth(600)
        #self.window.img.setMinimumHeight(800)

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
        self.window.stackedWidget_2.setCurrentIndex(self.t2)
        if self.t2 >= 1:
            self.t2 = 0
        else:
            self.t2 = self.t2 + 1
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
            # switch site for layout update & update of geometries of labels
            self.window.stackedWidget.setCurrentIndex(0)

            img = QImage()
            content = self.databasemanager.get_first_image(data.kArtikel)
            if content is not None:
                assert img.loadFromData(content)
                self.window.img.setPixmap(QPixmap.fromImage(img).scaled(200,200 , Qt.KeepAspectRatio))
            else:
                self.window.img.setPixmap(QPixmap("E:\Schulzeug\P-Seminar\git\Barcode-Scanner-Feinkost-/kein-bild-vorhanden.webp").scaled(200, 200, Qt.KeepAspectRatio))


            self.window.p_name.setText(data.Artikelname)
            self.window.preis.setText(str(float(int(data[28] * 100)) / 100) + " €")

            self.window.inhalt.setText("value")
            self.window.p_num.setText(str(data.Artikelnummer))
            self.window.ean.setText(str(data.EAN))

            descript = self.databasemanager.get_artcle_description(data.kArtikel)
            if descript is not None:
                self.window.description.setHtml(descript.cBeschreibung)
                print(descript.cBeschreibung)
            self.window.hersteller.setText(data.Hersteller)

            # switch site for layout update & update of geometries of labels
            self.window.stackedWidget.setCurrentIndex(1)
            special_price = self.databasemanager.get_special_price(data.kArtikel)

            if special_price is not None:
                # show them for update of positions
                self.special_price_label.show()
                self.special_price_red_line.show()
                # self.window.price_w.show()

                # self.special_price_label.setStyleSheet("background-color: rgba(0,100,0,100)")
                self.special_price_label.setStyleSheet("color: rgba(255,0,0,255)")
                self.special_price_label.setText(str(float(int(special_price.fNettoPreis*100)/100)) + " €")

                br_price = QFontMetrics(self.window.preis.font()).boundingRect(self.window.preis.text())
                br_special_price = QFontMetrics(self.special_price_label.font()).boundingRect(self.special_price_label.text())

                self.special_price_red_line.setGeometry(self.window.preis.x(),
                                                        self.window.preis.y() + self.window.preis.height() / 2,
                                                        br_price.width(),
                                                        self.SPECIAL_PRICE_RED_LINE_HEIGHT)

                print(br_special_price.height())
                print(br_price.height())
                print(((   br_price.height() - br_special_price.height() ) / 2)- br_price.height() / 2)

                self.special_price_label.setGeometry(self.window.preis.x() + br_price.width()
                                                     + self.SPACE_BETWEEN_PRICE_AND_SPECIAL_PRICE,
                                                     self.window.preis.y() - (  (  br_special_price.height() - br_price.height() ) / 2) ,
                                                     br_special_price.width() + 2,
                                                     br_special_price.height())

            else:
                self.special_price_label.hide()
                self.special_price_red_line.hide()

            # switch page
            # self.window.stackedWidget.setCurrentIndex(1)
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
                label.setFixedSize(QImage(value).size() * 2)

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
