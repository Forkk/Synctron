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

from base64 import urlsafe_b64decode
import json
import time

from common.db import UserData

from wsapi import Session, config, rooms, roomlist_listeners, get_room
from wsapi.room import Room
	
from common.sessioninterface import read_session_data


# Just a temporary thing for counting users.
# Used to generate names for users.
# This will probably go away when we come up with a real username system.

class UserWebSocket(WebSocket):
	usercount = 0

	#######################
	# WEBSOCKET FUNCTIONS #
	#######################

	def opened(self):
		# Set up the actions dict.
		self.room = None
		self.actions = {
			"init": self.action_init,
			"roomlist": self.action_roomlist,
			"sync": self.action_sync,
			"play": self.action_play,
			"pause": self.action_pause,
			"seek": self.action_seek,
			"changevideo": self.action_changevideo,
			"addvideo": self.action_addvideo,
			"removevideo": self.action_removevideo,
			"reloadplaylist": self.action_reloadplaylist,
			"chatmsg": self.action_chatmsg,
		}

		# Generate a username for the user.
		self.username = "Guest %i" % UserWebSocket.usercount
		self.user_id = None
		UserWebSocket.usercount += 1

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
			self.send_error("invalid_action", "An action was sent to the server that it did not understand.")
		else:
			self.actions[action](data)

	def closed(self, code, reason=None):
		if self.room and self in self.room.users:
			self.room.remove_user(self)
		if self in roomlist_listeners:
			roomlist_listeners.remove(self)


	####################
	# RECEIVED ACTIONS #
	####################

	def action_roomlist(self, data):
		"""
		Action sent by the client on the homepage, asking for a list of rooms with the most people in them.
		"""
		self.send_roomlist()
		if "listen" in data and data["listen"]:
			roomlist_listeners.append(self)

	def action_init(self, data):
		"""
		Action sent by the client when the user joins a room.
		This function expects the data to contain the following information: pass
		Responds with information about what's currently going on such as the currently playing video's ID, time, playlist info, etc.
		"""

		if "room_id" not in data:
			self.close(1008, "init action requires a room ID")
			return

		session = Session()
		if "session" in data:
			# If a session was given, attempt to read it and load user info from the database.
			user = None
			session_data = read_session_data(data["session"], config.get("SECRET_KEY"))

			if session_data is not None and "username" in session_data:
				user = session.query(UserData).filter_by(name=session_data["username"]).first()

			if user is not None:
				# User is authenticated.
				self.user_id = user.id
				self.username = user.name
			else:
				self.user_id = None

		# Set self.room to the room we're joining.
		self.room = get_room(data["room_id"])

		# If the room ID specified in data doesn't exist, we need to create/load it.
		if self.room is None:
			self.room = Room(data["room_id"], session)
			rooms.append(self.room)

			
		if len(self.room.users) <= 0 and self.room.get_room_owner(session) is None:
			self.room.set_room_owner(self, session)

		# Add the user to the room.
		self.room.add_user(self, session)
		session.close()

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

		if self.room.is_playing:
			# If room is already playing, sync the user who tried to play it.
			# Unless they're seeking.
			self.send_sync()
			return

		self.room.play(user=self)

	def action_seek(self, data):
		"""
		Seeks the video to the time specified in data.
		"""

		self.room.seek(data["time"], user=self)

	def action_pause(self, data):
		"""
		Pauses the video. Duh...
		All this does is update current_pos and set is_playing to False
		"""

		if not self.room.is_playing:
			# If room is already paused, sync the user who tried to pause it.
			self.send_sync()
			return

		self.room.pause(user=self)

	def action_changevideo(self, data):
		"""
		Changes the currently playing video.
		Expects the following information: index
		The index given specifies the index in the playlist of the video to play.
		"""

		self.room.change_video(data["index"], user=self)

	def action_addvideo(self, data):
		"""
		Adds a video to the playlist.
		Expects the following information: video_id
		Optionally, index can also be supplied. 
		If index is an integer, the video will be added at the specified index.
		"""

		# Index to add the video at. Add to the end of the list if unspecified.
		index = None
		if "index" in data and type(data["index"]) is int:
			index = data["index"]

		self.room.add_video(data["video_id"], index=index, user=self)

	def action_removevideo(self, data):
		"""
		Removes a video from the playlist.
		Expects the following information: index
		"""

		self.room.remove_video(data["index"], user=self)

	def action_reloadplaylist(self, data):
		"""
		Re-sends all the playlist information to the user.
		"""
		session = Session()
		self.send_playlistupdate_all(self.room.get_playlist_info(self.room.get_room_data(session)))
		session.close()

	def action_chatmsg(self, data):
		"""
		Posts a chat message from this user to the room.
		"""
		# There's no need to sanitize the message to make sure it doesn't have HTML here.
		# This is done client-side before the message is added to the chat box.
		self.room.post_chat_message(data["message"], self)

	# def action_changenick(self, data):
	# 	"""
	# 	Action for a user changing their nickname.
	# 	No longer used.
	# 	"""

	# 	print("User %s is changing their nick to %s." % (self.username, data["newnick"]))
	# 	self.username = data["newnick"]
	# 	self.room.user_list_update()


	###################
	# SENDING ACTIONS #
	###################

	def send_roomlist(self):
		"""Sends the client the roomlist"""
		popular = sorted(rooms, key=lambda room: len(room.users), reverse=True)
		self.send(json.dumps({
			"action": "roomlist",
			"rooms": [{
				"name": room.room_id,
				"usercount": len(room.users),
			} for room in popular[:10]],
		}))

	def send_sync(self):
		"""Sends a sync action to the client."""
		self.send(json.dumps({
			"action": "sync",
			"video_time": self.room.current_pos,
			"is_playing": self.room.is_playing,
		}))

	def send_setvideo(self, room_data=None):
		"""Sends a setvideo action to the client."""
		if room_data is None: room_data = self.room.get_room_data()

		current_video = self.room.get_current_video(room_data)

		self.send(json.dumps({
			"action": "setvideo",
			# The service that the video is playing from. Only YouTube is supported currently.
			"video_service": self.room.video_service, 
			# The ID of the video that's playing. Currently just a test.
			"video_id": "" if current_video is None else current_video.video_id,
			# The index of the currently playing video in the playlist.
			"playlist_pos": room_data.playlist_pos,
		}))


	def send_playlistupdate_all(self, playlist_info):
		"""
		Sends a playlistupdate action to the client specifying that the entire playlist
		changed.
		"""
		self.send(json.dumps({
			"action": "playlistupdate",
			"type": "all",
			"playlist": playlist_info,
		}))

	def send_playlistupdate_add(self, entries, first_index):
		"""
		Sends a playlistupdate action to the client specifying that videos were added to the playlist.
		"""
		self.send(json.dumps({
			"action": "playlistupdate",
			"type": "add",
			"entries": entries, 
			"first_index": first_index,
		}))

	def send_playlistupdate_remove(self, indices):
		"""
		Sends a playlistupdate action to the client specifying that videos were removed from the playlist.
		"""
		self.send(json.dumps({
			"action": "playlistupdate",
			"type": "remove",
			"indices": indices,
		}))

	def send_playlistupdate_move(self, old_index, new_index):
		"""
		Sends a playlistupdate action to the client specifying that a video in the playlist has been moved.
		"""
		self.send(json.dumps({
			"action": "playlistupdate",
			"type": "move",
			"old_index": old_index,
			"new_index": new_index,
		}))


	def send_userlistupdate(self, session, room_data=None):
		"""Sends a userlistupdate action to the client."""
		if room_data is None: room_data = self.room.get_room_data(session)

		def uinfo_dict(user):
			user_data = user.get_user_data(session)
			return {
				"username": user.username,
				"isyou": user is self,
				"isguest": user.is_guest(),
				"isadmin": user.is_admin(room_data, user_data),
				"isowner": user.is_owner(room_data, user_data),
			}

		self.send(json.dumps({
			"action": "userlistupdate",
			"userlist": [uinfo_dict(user) for user in self.room.users],
		}))

	def send_nickupdate(self, newname=None):
		"""
		Sends a namechanged action to the client.
		This action tells the client that their name has been changed.
		"""
		self.send(json.dumps({
			"action": "namechanged",
			"name": self.username if newname is not None else newname,
		}))

	def send_error(self, reason_id, reason_msg=None):
		"""
		Sends an error action to the client.
		reason_id should be a unique reason ID string.
		reason_msg should be a human readable error message. If not specified, will be the same as reason_id.
		"""
		self.send(json.dumps({
			"action": "error",
			"reason": reason_id,
			"reason_msg": reason_msg if reason_msg else reason_id,
		}))

	def send_chatmsg(self, sender, message):
		self.send(json.dumps({
			"action": "chatmsg",
			"sender": sender.username,
			"message": message,
		}))


	###############
	# OTHER STUFF #
	###############

	def is_owner(self, room_data, user_data):
		"""Returns true if the user is the owner of the room it's in."""
		if self.is_guest():
			return False
		return room_data.owner_id == self.user_id

	def is_admin(self, room_data, user_data):
		"""Returns true if the user is an admin in the room it's in."""
		if self.is_guest():
			return False
		if self.is_owner(room_data, user_data):
			return True
		for admin in room_data.admins:
			if admin.id == self.user_id:
				return True
		return False

	def is_guest(self):
		"""Returns true if the user is a guest."""
		return self.user_id is None

	def get_user_data(self, session):
		"""
		Uses the given session to get the user data for this user from the database and returns it.
		If session is None, a session will be created automatically.
		"""
		if self.user_id is None: return None
		return session.query(UserData).filter_by(id=self.user_id).first()

	def __str__(self):
		return "%s (%s)" % (self.username, self.peer_address[0])
