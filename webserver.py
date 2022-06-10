
from http.server import ThreadingHTTPServer, HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler

import requesthandler
from requesthandler import *


class WebServer(HTTPServer):
    def __int__(self, addr, port):
        super(WebServer, self).__int__((addr, port), RequestHandler)
