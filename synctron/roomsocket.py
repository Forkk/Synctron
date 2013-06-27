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

from socketio import socketio_manage
from socketio.namespace import BaseNamespace

from synctron import app, db, connections

from synctron.room import Room, get_entry_info
from synctron.user import User
from synctron.vidinfo import get_video_info

from roomlistsocket import broadcast_room_user_list_update

# Global variable for counting guests.
guest_ctr = 1

def socketevent(func):
	"""Decorator for Socket.IO event functions. Handles and logs exceptions."""
	def inner(self, *args, **kwargs):
		retval = None
		try:
			retval = func(self, *args, **kwargs)
		except Exception as e:
			self.logger.error("Uncaught exception in event handler %s. Closing connection." % func.__name__, exc_info=True)
			self.emit("server_error", "Uncaught exception in function %s" % func)
			self.disconnect()
		return retval
	return inner

def dbaccess(func):
	"""Decorator for functions that need access to the database."""
	def inner(self, *args, **kwargs):
		dbsession = kwargs.pop("dbsession", None)
		session_created = False
		retval = None
		if "dbsession" not in self.session or self.session["dbsession"] is None:
			if dbsession is None:
				dbsession = db.Session(db.engine)
				session_created = True
			self.session["dbsession"] = dbsession
		try:
			retval = func(self, *args, **kwargs)
		finally:
			if dbsession is not None and "dbsession" in self.session and self.session["dbsession"] is not None:
				if session_created:
					self.session["dbsession"].close()
				self.session["dbsession"] = None
		return retval
	return inner

class RoomNamespace(BaseNamespace):
	"""
	Namespace for handling events having to do with rooms and synchronizing videos in rooms.
	"""

	def initialize(self):
		self.logger = app.logger
		self.log("Socket.IO session started.")
		connections.append(self)

	def log(self, msg):
		self.logger.info("[{0}] {1}".format(self.socket.sessid, msg))

	def disconnect(self, *args, **kwargs):
		if self in connections:
			connections.remove(self)

		if "dbsession" in self.session and self.session["dbsession"] is not None:
			self.log("Closing leaked session")
			self.session["dbsession"].close()

		# Stupid hack to fix stupid Socket.IO bug.
		if "silent" in kwargs:
			del kwargs["silent"]

		if "room" in self.session:
			self.session["dbsession"] = dbsession = db.Session(db.engine)
			try:
				room = self.get_room()
				room.remove_user(self)
				broadcast_room_user_list_update()
			finally:
				dbsession.close()

		BaseNamespace.disconnect(self, *args, **kwargs)

	#################
	# SOCKET EVENTS #
	#################

	@socketevent
	@dbaccess
	def on_join(self, room_slug):
		"""
		Event called by the client when it initially joins a room.
		room_slug is the slug of the room that the client is joining.

		This function needs to do the following:
			- Check if the user is logged in and get their account from the database.
			- Try to find the room the user is joining in the database.
			- Add the user to the room.
		"""

		# Authenticate
		# The flask session is the second item in the tuple passed as socketio_manage's request arg.
		fsession = self.request[1]
		self.session["user_id"] = None
		user = None
		if "user" in fsession:
			user = self.dbsession.query(User).filter_by(id=fsession["user"]).first()

		# Assign a guest ID whether they're a guest or not.
		global guest_ctr
		self.session["guest_id"] = guest_ctr
		guest_ctr += 1

		if user is not None:
			# If the user is logged in, store their user ID in the socket's session dict.
			self.session["user_id"] = fsession["user"] # So much shit named session...

		# Get the room.
		room = self.dbsession.query(Room).filter_by(slug=room_slug).first()
		if room is None:
			# If the room doesn't exist, send room_not_found and close the socket.
			self.emit("room_not_found");
			self.disconnect();
			return

		self.session["room"] = room_slug
		self.config_update(room)
		room.add_user(self)
		broadcast_room_user_list_update()

	@socketevent
	@dbaccess
	def on_sync(self):
		"""
		Event called by the client to request a re-sync.
		"""
		room = self.get_room()
		self.synchronize(room.current_position, room.is_playing)

	@socketevent
	@dbaccess
	def on_play(self):
		"""
		Event called by the client to play the video.
		"""
		room = self.get_room()
		if room.is_playing or not self.can_pause:
			# If the room is already playing, re-sync whoever tried to play it.
			self.synchronize(room.current_position, room.is_playing)
		else:
			# Otherwise, play the video.
			room.play()

	@socketevent
	@dbaccess
	def on_pause(self):
		"""
		Event called by the client to pause the video.
		"""
		room = self.get_room()
		if not room.is_playing or not self.can_pause:
			# If the room is already paused, re-sync whoever tried to pause it.
			self.synchronize(room.current_position, room.is_playing)
		else:
			# Otherwise, pause the video.
			room.pause()

	@socketevent
	@dbaccess
	def on_seek(self, seek_time):
		"""
		Event called by the client to seek to a different point in the video.
		"""
		room = self.get_room()
		if not self.can_pause:
			self.synchronize(room.current_position, room.is_playing)
		else:
			room.seek(seek_time)


	@socketevent
	@dbaccess
	def on_change_video(self, index):
		"""
		Event called by the client to change the currently playing video to the given index.
		"""
		if self.can_skip:
			room = self.get_room()
			room.change_video(index)
		else:
			self.emit("error_occurred", "not_allowed", "You're not allowed to skip videos in this room.")

	@socketevent
	@dbaccess
	def on_add_video(self, video_id, index=None):
		"""
		Event called by the client to add a video to the playlist.
		"""
		if self.can_add:
			if get_video_info(video_id) is None:
				self.emit("error_occurred", "invalid_vid", "The given video ID is not valid.")
			else:
				room = self.get_room()
				room.add_video(video_id, index, self.name)
		else:
			self.emit("error_occurred", "not_allowed", "You're not allowed to add videos to this room.")

	@socketevent
	@dbaccess
	def on_remove_video(self, index):
		"""
		Event called by the client to remove a video from the playlist.
		"""
		if self.can_remove:
			room = self.get_room()
			room.remove_video(index)
		else:
			self.emit("error_occurred", "not_allowed", "You're not allowed to remove videos in this room.")

	@socketevent
	@dbaccess
	def on_reload_playlist(self):
		"""
		Event called by the client to reload the playlist.
		"""
		room = self.get_room()
		self.playlist_update([get_entry_info(entry) for entry in room.playlist])

	@socketevent
	@dbaccess
	def on_shuffle_playlist(self):
		"""
		Event called by the client to randomize the order of videos in the playlist.
		"""
		if self.can_move:
			room = self.get_room()
			room.shuffle_playlist()
		else:
			self.emit("error_occurred", "not_allowed", "You're not allowed to move videos in this room.")


	@socketevent
	@dbaccess
	def on_chat_message(self, message, action):
		"""
		Event called by the client to send a chat message to the room.
		"""
		message = message[:200]

		room = self.get_room()
		room.chat_message(message, self, action=action)

	@socketevent
	@dbaccess
	def on_kick_user(self, username, message):
		"""
		Event called by the client to kick a user.
		"""
		if not self.is_admin:
			self.status_message("Only admins and room owners can kick people from rooms.", "Error")
			return

		room = self.get_room()
		for user in room.users:
			if user.name == username:
				# Kick the user.
				room.pub_status_message("%s kicked %s from the room. Reason: %s" % (self.name, user.name, message), "Status")
				user.kick(self, message)
				return
		self.status_message("User not found: %s" % username, "Error")

	##############
	# PROPERTIES #
	##############

	@property
	def user_id(self):
		if "user_id" in self.session:
			return self.session["user_id"]
		else:
			return None

	@property
	@dbaccess
	def name(self):
		"""The user's name."""
		user = None
		if not self.is_guest:
			user = self.dbsession.query(User).filter_by(id=self.user_id).first()
		if user is None:
			return "Guest %i" % self.session["guest_id"]
		else:
			return user.name

	@property
	@dbaccess
	def is_owner(self):
		"""True if this user owns the room it's connected to."""
		if self.is_guest:
			return False
		else:
			room = self.get_room()
			if room.owner is None:
				return False
			else:
				return room.owner.id == self.user_id

	@property
	@dbaccess
	def is_admin(self):
		"""True if this user is an admin in the room it's connected to."""
		if self.is_guest:
			return False
		elif self.is_owner:
			return True
		else:
			room = self.get_room()
			for admin in room.admins:
				if admin.id == self.user_id:
					return True
			return False

	@property
	@dbaccess
	def is_guest(self):
		"""True if this user is a guest."""
		return self.user_id is None

	@dbaccess
	def info_dict(self):
		"""
		A dict containing some information about this user that is used by the user list.
		"""
		return {
			"username": self.name,
			"isguest": self.is_guest,
			"isadmin": self.is_admin,
			"isowner": self.is_owner,
		}

	@dbaccess
	def get_room(self):
		"""
		Gets the user's current room from the database.
		"""
		if "room" in self.session:
			return self.dbsession.query(Room).filter_by(slug=self.session["room"]).first()
		else:
			return None

	@property
	def dbsession(self):
		return self.session["dbsession"]


	## Permissions ##

	@property
	@dbaccess
	def can_pause(self):
		"""True if the user is allowed to play/pause the video in the room."""
		if self.is_admin:
			return True
		else:
			room = self.get_room()
			return room.users_can_pause

	@property
	@dbaccess
	def can_skip(self):
		"""True if the user is allowed to change the playing video in the room."""
		if self.is_admin:
			return True
		else:
			room = self.get_room()
			return room.users_can_skip

	@property
	@dbaccess
	def can_add(self):
		"""True if the user is allowed to add videos to the room."""
		if self.is_admin:
			return True
		else:
			room = self.get_room()
			return room.users_can_add

	@property
	@dbaccess
	def can_remove(self):
		"""True if the user is allowed to remove videos from the room."""
		if self.is_admin:
			return True
		else:
			room = self.get_room()
			return room.users_can_remove

	@property
	@dbaccess
	def can_move(self):
		"""True if the user can move videos in the playlist."""
		if self.is_admin:
			return True
		else:
			room = self.get_room()
			return room.users_can_move


	###############
	# ROOM EVENTS #
	###############

	def synchronize(self, video_time, is_playing):
		"""
		Sends a sync event to the client with the given information.
		"""
		self.emit("sync", video_time, is_playing)


	def video_changed(self, playlist_position, video_id):
		"""
		Sends a video changed event to the client with the given position.
		"""
		self.emit("video_changed", playlist_position, video_id)

	def playlist_update(self, entries):
		"""
		Event fired to send the user the entire playlist.
		entries is an array containing information about the videos.
		"""
		self.emit("playlist_update", entries)

	def video_added(self, entry, index):
		"""
		Event fired when videos are added to the playlist.
		entry is an array containing information about the video.
		index is the index of the added video.
		"""
		self.emit("video_added", entry, index)

	def videos_removed(self, indices):
		"""
		Event fired when a video is removed from the playlist.
		indices is an array of the indices of the videos that were removed.
		"""
		self.emit("videos_removed", indices)

	def video_moved(self, old_index, new_index):
		"""
		Event fired when a video is moved to a new index in the playlist.
		old_index is the video's old index.
		new_index is the video's new index.
		"""
		self.emit("video_moved", old_index, new_index)

	@dbaccess
	def userlist_update(self, userlist):
		"""
		Sends the userlist to the client.
		"""
		print "update userlist for " + self.name
		self.emit("userlist_update", 
			[dict(
				userinfo, 
				isyou=userinfo["username"] == self.name) 
			for userinfo in userlist])

	def chat_message(self, message, from_user, action=False):
		"""
		Event fired when a chat message is sent out.
		If action is True, the message will be an action (/me).
		"""
		self.emit("chat_message", message, from_user["username"], action)

	def status_message(self, message, msgtype):
		"""
		Event fired to send a "status message" to the client.
		This will be printed out in the client's chat.
		"""
		self.emit("status_message", message, msgtype)

	def config_update(self, room):
		"""
		Event fired when room settings change.
		"""
		self.emit("config_update", {
			"title": room.title,
			"topic": room.topic,
			"users_can_add": room.users_can_add,
			"users_can_remove": room.users_can_remove,
			"users_can_move": room.users_can_move,
			"users_can_pause": room.users_can_pause,
			"users_can_skip": room.users_can_skip,
		})

	def kick(self, by, message):
		"""
		Emits the kick event, kicking this user from the room and then disconnects the socket.
		"""
		self.emit("kicked", by.name, message)
		self.disconnect()
