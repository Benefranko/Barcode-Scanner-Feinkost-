import sys
import mapplication
import mainwindow
import webserver

if __name__ == "__main__":
    w_server = webserver.Server()
    w_server.start_listen()

    m_app = mapplication.MApplication(sys.argv)
    m_win = mainwindow.MainWindow("./sqlLiteDB.db")

    # connect MApplication ( EventFilter ) with MainWindow( handle_EVENT )
    m_app.newScan.connect(m_win.new_scan)

    m_win.show()
    ret = m_app.exec_()

    w_server.stop_listen()
    sys.exit(ret)
