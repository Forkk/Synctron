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
import time

# Calculating Video Time in Rooms:
# Calculating the current time on a video in rooms is done using two values: start_time and current_pos.
# start_time tracks the last time play was clicked.
# current_pos tracks what the current time was the last time the video was paused.

rooms = {
	
}


def init(data, sock):
	"""
	Action sent by the client when the user joins a room.
	This function expects the data to contain the following information: pass
	Responds with information about what's currently going on such as the currently playing video's ID, time, playlist info, etc.
	"""

	# If the room specified in data doesn't exist, we need to create it.
	room = None
	if data["room_id"] not in rooms:
		room = {
			"users": [ sock ],
			"video_id": "J5bhT4-9M0o",
			"video_service": "YouTube",
			"is_playing": False,
			"start_time": 0,
			"current_pos": 0,
		}
		rooms[data["room_id"]] = room

	else:
		room = rooms[data["room_id"]]
		room["users"].append(sock)

	
	# Send setvideo to change the video to the correct video.
	sock.send(json.dumps({
		"action": "setvideo",
		"video_service": room["video_service"], # The service that the video is playing from. Only YouTube is supported currently.
		"video_id": room["video_id"], # The ID of the video that's playing. Currently just a test.
	}))


def __sync_all_clients__(room):
	"""
	Sends a sync to all clients in the given room.
	"""
	[__sync_client__(sock, room) for sock in room["users"]]


def __sync_client__(sock, room):
	"""
	Sends a sync action for the given room to the given socket.
	"""

	video_time = 0
	# If start_time is 0, then we need to start the video by setting the time to the current system time.
	if room["start_time"] == 0:
		room["start_time"] = int(time.time())

	# Otherwise, we need to calculate what time the video is currently at.
	elif room["is_playing"]:
		# It's simply current time - start time + start position. <3
		video_time = int(time.time()) - room["start_time"] + room["current_pos"]

	else:
		video_time = room["current_pos"]


	# Send the sync action to set the client's time.
	sock.send(json.dumps({
		"action": "sync",
		"video_time": video_time, # The current time on the video in seconds since the beginning of the video.
		"is_playing": room["is_playing"],
	}))


def sync(data, sock):
	"""
	Action sent by the server to tell the client what time the video is at.
	Sent under various conditions.
	"""

	room = None
	if data["room_id"] in rooms:
		room = rooms[data["room_id"]]
	else:
		sock.send(json.dumps({ "action": "error", "reason": "room_not_found", "reason_msg": "Can't sync video on an invalid room." }))

	__sync_client__(sock, room)


def play(data, sock):
	"""
	Plays the video. Duh...
	All this really does is update start_time and set is_playing to True
	"""

	room = None
	if data["room_id"] in rooms:
		room = rooms[data["room_id"]]
	else:
		sock.send(json.dumps({ "action": "error", "reason": "room_not_found", "reason_msg": "Can't play video on an invalid room." }))

	print "Playing room %s" % data["room_id"]

	room["is_playing"] = True
	room["start_time"] = int(time.time())
	__sync_all_clients__(room)


def pause(data, sock):
	"""
	Pauses the video. Duh...
	All this does is update current_pos and set is_playing to False
	"""

	room = None
	if data["room_id"] in rooms:
		room = rooms[data["room_id"]]
	else:
		sock.send(json.dumps({ "action": "error", "reason": "room_not_found", "reason_msg": "Can't pause video on an invalid room." }))

	print "Pausing room %s" % data["room_id"]

	if room["is_playing"]:
		room["current_pos"] = int(time.time()) - room["start_time"] + room["current_pos"]

	room["is_playing"] = False
	__sync_all_clients__(room)


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
		if msg == None:
			sock.close()

		data = None
		action = None
		try:
			data = json.loads(msg)
			action = data["action"]
		except ValueError:
			break # Kill the connection if the JSON isn't valid.

		if "room_id" not in data:
			break # We need a room ID.

		# Try find an action that matches the specified action.
		if not action in actions:
			sock.send(json.dumps({ "action": "error", "reason": "invalid_action", "reason_msg": "Invalid action" }))
		else:
			actions[action](data, sock)


actions = {
	"init": init,
	"sync": sync,
	"play": play,
	"pause": pause,
}
