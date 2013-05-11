# Copyright (C) 2013 Screaming Cats

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from bottle import route, run, static_file
from bottle.ext.websocket import GeventWebSocketServer
from bottle.ext.websocket import websocket

import json

import wsapi

# JINJA NINJAAAAAAA
from bottle import jinja2_view as view, jinja2_template as template


@route("/")
def home_page():
	return "Move along! Nothing to see here!"


@route("/room/<room_id>")
def room_page(room_id):
	return template("player.j2")


# For static files.
@route("/static/<path:path>")
def static(path):
	print path
	return static_file(path, root="./static")

if __name__ == "__main__":
	run(host="localhost", port = 8000, debug = True, server=GeventWebSocketServer)
