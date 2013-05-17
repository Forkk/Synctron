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

from ws4py.websocket import WebSocket

import json
import time

# Calculating Video Time in Rooms:
# Calculating the current time on a video in rooms is done using two values: start_time and current_pos.
# start_time tracks the last time play was clicked.
# current_pos tracks what the current time was the last time the video was paused.

rooms = {
	
}


class UserWebSocket(WebSocket):
	def opened(self):
		# Just set up the actions dict.
		self.room = None
		self.actions = {
			"init": self.action_init,
			"sync": self.action_sync,
			"play": self.action_play,
			"pause": self.action_pause,
			"changevideo": self.action_changevideo,
		}

	def received_message(self, message):
		data = None
		action = None

		if not message.is_text:
			self.close(1008, "All messages must be valid JSON.")
			return

		try:
			data = json.loads(message.data)
			action = data["action"]
		except ValueError:
			self.close(1008, "All messages must be valid JSON.")
			return

		# Try find an action that matches the specified action.
		if not action in self.actions:
			sock.send(json.dumps({ "action": "error", "reason": "invalid_action", "reason_msg": "Invalid action" }))
		else:
			self.actions[action](data)

	def closed(self, code, reason=None):
		if self.room:
			self.room["users"].remove(self)



	####################
	# RECEIVED ACTIONS #
	####################

	def action_init(self, data):
		"""
		Action sent by the client when the user joins a room.
		This function expects the data to contain the following information: pass
		Responds with information about what's currently going on such as the currently playing video's ID, time, playlist info, etc.
		"""

		if "room_id" not in data:
			self.close(1008, "init action requires a room ID")
			return

		# If the room specified in data doesn't exist, we need to create it.
		self.room = None
		if data["room_id"] not in rooms:
			rooms[data["room_id"]] = {
				"room_id": data["room_id"],
				"users": [ self ],
				"video_id": "J5bhT4-9M0o",
				"video_service": "YouTube",
				"is_playing": False,
				"start_time": 0,
				"current_pos": 0,
			}
			self.room = rooms[data["room_id"]]

		else:
			self.room = rooms[data["room_id"]]
			self.room["users"].append(self)
		
		# Send setvideo to change the video to the correct video.
		self.send_setvideo()


	def action_sync(self, data):
		"""
		Action sent from the client to request that the server send the client a sync action.
		"""
		self.send_sync()


	def action_play(self, data):
		"""
		Plays the video. Duh...
		This also is used for seeking. When a seek is done, the client sends a play event and specifies the time that was seeked to.
		All this really does is update start_time, set current_pos to the given time, and set is_playing to True
		"""

		if self.room["is_playing"] and "time" not in data:
			# If room is already playing, sync the user who tried to play it.
			# Unless they're seeking.
			self.send_sync()
			return

		print "Playing room %s" % self.room["room_id"]

		stime = self.calc_video_time()
		if "time" in data:
			stime = int(data["time"])
		
		self.room["current_pos"] = stime
		self.room["start_time"] = int(time.time())
		self.room["is_playing"] = True
		__sync_all_clients__(self.room)


	def action_pause(self, data):
		"""
		Pauses the video. Duh...
		All this does is update current_pos and set is_playing to False
		"""

		if not self.room["is_playing"]:
			# If room is already paused, sync the user who tried to pause it.
			self.send_sync()
			return

		print "Pausing room %s" % self.room["room_id"]

		self.room["current_pos"] = self.calc_video_time()
		self.room["is_playing"] = False
		__sync_all_clients__(self.room)


	def action_changevideo(self, data):
		"""
		Changes the currently playing video.
		Expects the following information: video_id
		"""

		print "Changing video in room %s to %s" % (self.room["room_id"], data["video_id"])

		self.room["video_service"] = "YouTube" #data["video_service"]
		self.room["video_id"] = data["video_id"]
		self.room["current_pos"] = 0
		self.room["start_time"] = int(time.time())
		self.room["is_playing"] = False
		[sock.send_setvideo() for sock in self.room["users"]]



	###################
	# SENDING ACTIONS #
	###################

	def send_sync(self):
		"""Sends a sync action to the client."""
		video_time = 0
		# If start_time is 0, then we need to start the video by setting the time to the current system time.
		if self.room["start_time"] == 0:
			self.room["start_time"] = int(time.time())

		# Otherwise, we need to calculate what time the video is currently at.
		else:
			video_time = self.calc_video_time()

		# print "Sync. vtime: %i current time: %i start time: %i current position: %i" % \
		# 	(video_time, time.time(), self.room["start_time"], self.room["current_pos"])
		# Send the sync action to set the client's time.
		self.send(json.dumps({
			"action": "sync",
			"video_time": video_time, # The current time on the video in seconds since the beginning of the video.
			"is_playing": self.room["is_playing"],
		}))


	def send_setvideo(self):
		"""Sends a setvideo action to the client."""
		self.send(json.dumps({
			"action": "setvideo",
			# The service that the video is playing from. Only YouTube is supported currently.
			"video_service": self.room["video_service"], 
			# The ID of the video that's playing. Currently just a test.
			"video_id": self.room["video_id"],
		}))



	##################
	# MISC FUNCTIONS #
	##################

	def calc_video_time(self):
		if self.room["is_playing"]:
			# It's simply current time - start time + start position. <3
			return int(time.time()) - self.room["start_time"] + self.room["current_pos"]

		# Unless the room is paused. Then we just send the current position.
		else:
			return self.room["current_pos"]


def __sync_all_clients__(room):
	"""
	Sends a sync to all clients in the given room.
	"""
	[sock.send_sync() for sock in room["users"]]


if __name__ == "__main__":
	from gevent import monkey; monkey.patch_all()
	from ws4py.server.geventserver import WSGIServer
	from ws4py.server.wsgiutils import WebSocketWSGIApplication

	print("Running WebSocket server...")
	server = WSGIServer(('localhost', 8889), WebSocketWSGIApplication(handler_cls=UserWebSocket))
	server.serve_forever()
