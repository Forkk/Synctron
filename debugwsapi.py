from bottle import run
from bottle.ext.websocket import GeventWebSocketServer

import wsapi

if __name__ == "__main__":
	run(host="localhost", port = 8889, debug = True, server=GeventWebSocketServer, reloader=True)
