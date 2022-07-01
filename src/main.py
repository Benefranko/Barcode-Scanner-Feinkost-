import sys
import mapplication
import mainwindow
import webserver

# Einstellungen
# Pfad zu lokaler Datenbank, die zum Speichern der Statistiken der Nutzung, sowie der Bewertung dient
local_db_path: str = "./sqlLiteDB.db"
# MS SQL Server mit Daten zu Produkten
ms_sql_server_ip: str = "home.obermui.de"
# MS SQL Server Port
ms_sql_server_port: int = 18769

# Lokaler HTTP SERVER LISTEN IP
local_http_server_ip: str = '127.0.0.1'
# Lokaler HTTP SERVER LISTEN Port
local_http_server_port: int = 8888

# Pfad zu Qt-Designer Formulardatei: Die Grafik wurde nämlich mithilfe des Qt Creators erstellt.
ui_file_path: str = "../src/form_ALT.ui"

item_count_on_web_server_list: int = 50


if __name__ == "__main__":
    # MApplication
    m_app = None
    # Lokalen Statistiken Server
    w_server = None
    # Rückgabewert QApplication
    ret = None

    try:
        # Starte Lokalen Statistiken Server
        w_server = webserver.Server(local_http_server_ip, local_http_server_port)
        w_server.start_listen()

        # Erstelle Key Press Event Handler und Ui - MainWindow
        m_app = mapplication.MApplication(sys.argv)
        m_win = mainwindow.MainWindow(local_db_path, ms_sql_server_ip, ms_sql_server_port, ui_file_path)

        # connect MApplication ( EventFilter ) with MainWindow( handle_EVENT )
        m_app.newScan.connect(m_win.new_scan)

        # Mache das Fenster sichtbar
        m_win.show()

        # Warte auf exit signal
        ret = m_app.exec_()

    except Exception as exc:
        print(exc)

    # Stoppe lokalen Server und beende das Programm
    w_server.stop_listen()
    sys.exit(ret)
