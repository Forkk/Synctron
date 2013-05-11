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

from bottle import route

from bottle.ext.websocket import GeventWebSocketServer
from bottle.ext.websocket import websocket

import json


def init(data):
	"""
	Action sent by the client when the user joins a room.
	This function expects the data to contain the following information: pass
	Responds with information about what's currently going on such as the currently playing video's ID, time, playlist info, etc.
	"""
	
	return {
		"action": "init",

		"video_service": "YouTube", # The service that the video is playing from. Only YouTube is supported currently.
		"video_id": "J5bhT4-9M0o", # The ID of the video that's playing. Currently just a test. Awesome song BTW.
		"video_time": 0 # The current time on the video in seconds since the beginning of the video.
	}


@route("/wsapi", apply=[websocket])
def websocket_api(sock):
	"""
	The main handler for the websocket API.

	This receives messages from websockets and parses them as JSON. It then checks the "action" field in the JSON and looks for a corresponding field in the "actions" dict. When it finds one, it will call the function associated with it.

	If the message received is not valid JSON or if it doesn't contain an action field, the connection will be terminated.
	If the action specified in the received message is not a valid action, an error will be returned.

	When an action is called, whatever it returns will be passed to json.dumps() and sent to the client unless it is None.
	"""
	while True:
		msg = sock.receive()
		data = None
		action = None
		try:
			data = json.loads(msg)
			action = data["action"]
		except ValueError:
			break # Kill the connection if the JSON isn't valid.

		# Try find an action that matches the specified action.
		if not action in actions:
			sock.send(json.dumps({ "action": "error", "reason": "invalid_action", "reason_msg": "Invalid action" }))
		else:
			retdata = actions[action](data)
			if retdata is not None:
				sock.send(json.dumps(retdata))


actions = {
	"init": init,

}
