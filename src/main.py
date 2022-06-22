import sys
import mapplication
import mainwindow
import webserver


local_db_path: str = "./sqlLiteDB.db"
ms_sql_server_ip: str = "home.obermui.de"
ms_sql_server_port: int = 18769

local_http_server_ip: str = '127.0.0.1'
local_http_server_port: int = 8888


if __name__ == "__main__":
    w_server = webserver.Server(local_http_server_ip, local_http_server_port)
    w_server.start_listen()

    m_app = mapplication.MApplication(sys.argv)
    m_win = mainwindow.MainWindow(local_db_path, ms_sql_server_ip, ms_sql_server_port)

    # connect MApplication ( EventFilter ) with MainWindow( handle_EVENT )
    m_app.newScan.connect(m_win.new_scan)

    m_win.show()
    ret = m_app.exec_()

    w_server.stop_listen()
    sys.exit(ret)
