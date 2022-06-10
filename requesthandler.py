
from http.server import ThreadingHTTPServer, HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler


import main


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('content-type', 'text/html')
        self.end_headers()
        if main.widget != 0:
            self.wfile.write( ( "Anzahl an Elementen: " + str( main.widget.window.groupBox.layout().count()) + "\r\n   URL:/" ).encode() )
        self.wfile.write(self.path[1:].encode())
