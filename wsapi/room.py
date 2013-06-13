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

import requests

import time
from threading import Timer

from common.db import RoomData, PlaylistEntry

from wsapi import Session

# Calculating Video Time in Rooms:
# Calculating the current time on a video in rooms is done using two values: start_time and current_pos.
# start_time tracks the last time play was clicked.
# last_position tracks what the current time was the last time the video was paused.

class Room(object):
	"""
	# A class that represents a room.
	Contains a list of user websockets, data about the room, and functions for performing various operations.
	"""

	def __init__(self, room_id, session=None):
		"""
		Initializes a new room with the given ID.
		"""

		# Set the room ID.
		self.room_id = room_id

		# Check if this room is in the database.
		close_session = False
		if session is None:
			session = Session()
			close_session = True
		room_data = session.query(RoomData).filter_by(name=self.room_id).first()
		if room_data is None:
			# Add it if it isn't.
			room_data = RoomData(self.room_id)
			session.add(room_data)
			session.commit()

		# List of users in the room.
		self.users = []

		# The service that is playing the video. (YouTube is the only one right now)
		self.video_service = "YouTube"

		# Whether the video is playing or not.
		self.is_playing = False

		# The last time playback was started.
		self.start_time = 0

		# The position the video was at the last time playback was paused.
		self.last_position = 0

		# Timer for when the video ends.
		# This is used to figure out when we should go to the next video in the playlist.
		self.video_timer = None

		if close_session: session.close()


	##############
	# OPERATIONS #
	##############
	# Various operations that can be performed on the room.

	#### PLAYBACK STUFF ####

	def synchronize(self):
		"""Synchronizes playback for all the users in the room."""
		[user.send_sync() for user in self.users]

	def play(self, sync=True, user=None):
		"""Plays the video in the room."""
		session = Session()
		room_data = self.get_room_data(session)

		if user is not None:
			user_data = user.get_user_data(session)
			if not room_data.users_can_pause and not user.is_admin(room_data, user_data):
				user.send_sync()
				session.close()
				return


		print("%s played video in room %s." % (user, self.room_id))

		self.update_video_timer(room_data=room_data)

		# Set the start time to the current time and set is_playing to true.
		self.start_time = int(time.time())
		self.is_playing = True
		if (sync): self.synchronize()
		session.close()

	def seek(self, seek_time, sync=True, user=None):
		"""Seeks the video in the room to the given time (in seconds)."""
		session = Session()
		room_data = self.get_room_data(session)

		if user is not None:
			user_data = user.get_user_data(session)
			if not room_data.users_can_pause and not user.is_admin(room_data, user_data):
				user.send_sync()
				session.close()
				return

		print("%s seeked to %i seconds in room %s." % (user, seek_time, self.room_id))

		self.update_video_timer(room_data=room_data)

		# Set last position to the time we want to seek to and reset the start time.
		self.start_time = int(time.time())
		self.last_position = int(seek_time)
		if (sync): self.synchronize()
		session.close()

	def pause(self, sync=True, user=None):
		"""Pauses the video in the room."""
		session = Session()
		room_data = self.get_room_data(session)

		if user is not None:
			user_data = user.get_user_data(session)
			if not room_data.users_can_pause and not user.is_admin(room_data, user_data):
				user.send_sync()
				session.close()
				return

		print("%s paused room %s." % (user, self.room_id))

		new_current_pos = self.current_pos - 1 # Go back 1 second on pause.

		# Cancel the video timer.
		if self.video_timer is not None:
			self.video_timer.cancel()
			self.video_timer = None

		# Set last position to the current position and set is_playing to false.
		self.last_position = new_current_pos if new_current_pos >= 0 else 0
		self.is_playing = False
		if (sync): self.synchronize()
		session.close()


	#### PLAYLIST STUFF ####

	def playlist_update(self, room_data=None):
		"""Called when the playlist changes. Sends playlistupdate to all users."""
		[user.send_playlistupdate(room_data) for user in self.users]

	def add_video(self, new_vid, index=None, user=None):
		"""
		Adds a video to the playlist.

		If index is None, the video is added to the end of the list.
		Otherwise, it is added at the given index.
		"""
		session = Session()
		room_data = self.get_room_data(session)

		if user is not None:
			user_data = user.get_user_data(session)
			if not room_data.users_can_add and not user.is_admin(room_data, user_data):
				user.send_error("access_denied", "You're not allowed to add videos to this room.")
				session.close()
				return

		print("%s added video ID %s to playlist in room %s." % (user, new_vid, self.room_id))

		was_ended = self.get_playlist_ended(room_data)

		new_vid_info = get_video_info(new_vid)

		if not new_vid_info:
			if user:
				user.send_error("invalid_vid", "The given video ID (%s) is not valid or video info could not be loaded." % new_vid)
			else:
				print("Attempt to add invalid video ID: %s" % new_vid)
			session.close()
			return

		list_entry = PlaylistEntry(new_vid)

		if index is None:
			room_data.playlist.append(list_entry)
		else:
			# If the index is invalid, error.
			if type(index) is not int:
				if user: user.send_error("invalid_index", "The given index (%s) isn't valid." % index)
				else: print("Tried to add a video at an invalid index (%s)." % index)
				session.close()
				return

			if index > len(room_data.playlist):
				room_data.playlist.append(list_entry)
			else:
				room_data.playlist.insert(index, list_entry)
				if index < room_data.playlist_pos or (index == room_data.playlist_pos and not self.get_playlist_ended(room_data)):
					room_data.playlist_pos += 1

		session.add(list_entry)
		session.commit()

		self.playlist_update(room_data)

		# If the playlist was over before the video was added, change to the video we added.
		if was_ended:
			self.change_video(len(room_data.playlist) - 1, session=session, room_data=room_data)

		session.close()

	def remove_video(self, index, user=None):
		"""
		Removes the given video from the playlist.
		"""
		session = Session()
		room_data = self.get_room_data(session)

		if user is not None:
			user_data = user.get_user_data(session)
			if not room_data.users_can_remove and not user.is_admin(room_data, user_data):
				user.send_error("access_denied", "You're not allowed to remove videos from this room.")
				session.close()
				return

		print("%s removed video number %i from playlist in room %s." % (user, index, self.room_id))

		before_current = False

		# We'll need to do some logic to determine what the current playing index will be changed to.
		if index < room_data.playlist_pos:
			# If we're removing a video that's before the one that's currently playing, decrement the current_pos by one.
			room_data.playlist_pos -= 1
			before_current = True

		session.delete(room_data.playlist[index])
		del room_data.playlist[index]
		session.commit()

		self.playlist_update(room_data)

		if not before_current and index == room_data.playlist_pos:
			# If we're removing the video that's currently playing, the playlist position stays the same,
			# but we need to set the playing video to the one at the new current position.
			self.change_video(room_data.playlist_pos, session=session, room_data=room_data);
		session.close()

	def change_video(self, index, user=None, time_padding=3, session=None, room_data=None):
		"""
		Changes the current position in the playlist to the given index.
		time_padding specifies how many seconds of "padding" should be added (defaults to 3 seconds).
		Time padding here is meant to prevent the case where the client syncs a few seconds after the
		server starts "playing" the video, causing the video to start a few seconds after the actual
		beginning of the video. This is prevented by setting the server's last_position to 
		-time_padding when the video starts.
		"""
		close_session = False
		if session is None: 
			session = Session()
			close_session = True
		if room_data is None: room_data = self.get_room_data(session)

		if user is not None:
			user_data = user.get_user_data(session)
			if not room_data.users_can_skip and not user.is_admin(room_data, user_data):
				user.send_error("access_denied", "You're not allowed to skip videos in this room.")
				return

		print("%s changed playlist position in room %s to %i." % (user, self.room_id, index))

		room_data.playlist_pos = index
		session.commit()

		self.update_video_timer(0, room_data=room_data)

		self.last_position = -time_padding
		self.start_time = int(time.time())
		self.is_playing = True
		[user.send_setvideo(room_data) for user in self.users]
		if close_session == True: session.close()

	def video_ended(self):
		"""Callback for the video timer used to figure out when the video ends."""
		session = Session()
		room_data = self.get_room_data(session)

		print("Video in room %s ended." % self.room_id)

		# Increment playlist position.
		self.change_video(room_data.playlist_pos + 1)
		session.close()

	def update_video_timer(self, elapsed_time=None, time_padding=5, room_data=None):
		"""
		Cancels the existing video timer and resets it to go off at the end of the video.
		If elapsed_time is not none, the value of elapsed_time will be used instead of the current_pos property.
		time_padding is how many seconds of "padding" should be added (defaults to 5 seconds).
		The timer will be set to the time remaining in the video plus time_padding. This is done to help 
		prevent the video from being switched to the next video before the video ends. Often, the server will
		think the video has ended before it has ended for everyone else. Time padding helps prevent this.
		"""
		if room_data is None: room_data = self.get_room_data()

		# Set the video timer to the duration of the video.
		if self.video_timer is not None:
			# Cancel the timer if it's already running.
			self.video_timer.cancel()
			self.video_timer = None

		current_video = None

		if not self.get_playlist_ended(room_data):
			current_video = get_video_info(room_data.playlist[room_data.playlist_pos].video_id)

		# If no video is playing, don't set the timer.
		if current_video is None:
			return

		# If duration is 0, don't set the timer.
		if current_video["duration"] <= 0:
			return

		# Set the timer to go off when the video ends.
		time_remaining = current_video["duration"] - (self.current_pos if elapsed_time is None else elapsed_time) + 5
		print("Setting video timer for %i seconds." % time_remaining)
		self.video_timer = Timer(time_remaining, self.video_ended)
		self.video_timer.start()


	#### USER STUFF ####

	def user_list_update(self, session):
		"""Called when the user list changes. Sends userlistupdate to all users."""
		[user.send_userlistupdate(session) for user in self.users]

	def add_user(self, user, session, room_data=None):
		"""
		Adds the given user to the room.
		Called when the init action is received from the user.
		"""
		if room_data is None: room_data = self.get_room_data(session)

		print("%s joined room %s." % (user, self.room_id))

		# Add the user to the user list, and send them setvideo.
		self.users.append(user)
		user.send_setvideo(room_data)
		user.send_playlistupdate(room_data)
		self.user_list_update(session)

	def remove_user(self, user):
		"""
		Removes the given user from the room.
		Called when a user's socket closes.
		Do *NOT* send anything to the user that left the room inside this function.
		"""
		print("%s left room %s." % (user, self.room_id))
		self.users.remove(user)

		# This can't be done anymore because the owner must be in the database.
		# If the user was the room owner and he was a guest, pick a new owner.
		# if user.is_owner and user.is_guest:
		# 	if len(self.users) > 0:
		# 		# Pick the first non-guest in the room.
		# 		owner_candidates = [user for user in self.users if not user.is_guest]
		# 		if len(owner_candidates) <= 0:
		# 			# If no non-guests can be found in the room, pick the first guest.
		# 			owner_candidates = self.users
		# 		self.set_room_owner(owner_candidates[0])
		# 	else:
		# 		# If no new owner candidates can be found, set the owner to None.
		# 		# A new owner will be assigned when someone joins.
		# 		self.owner = None

		session = Session()
		self.user_list_update(session)
		session.close()

	def set_room_owner(self, user, session=None, user_data=None):
		"""
		Sets the given user as the room owner.
		The room owner has all permissions in the room.
		"""
		if not user.is_guest():
			print("%s is now the owner in room %s." % (user, self.room_id))
			close_session = False
			if session is None:
				session = Session()
				close_session = True
			if user_data is None: user_data = user.get_user_data(session)
			room_data = self.get_room_data(session)
			room_data.owner = user_data
			session.commit()
			if close_session: session.close()

	def get_room_owner(self, session):
		return self.get_room_data(session).owner


	#### CHAT STUFF ####

	def post_chat_message(self, message, user, force_post=False):
		"""
		Posts the given message in chat from the given user.
		Does nothing if message is empty, unless force_post is set to true True.
		"""
		if len(message) > 0 or force_post:
			[sendto.send_chatmsg(user, message) for sendto in self.users]


	################
	# CALCULATIONS #
	################
	# Calculations such as the current video time and the current video ID.

	@property
	def current_pos(self):
		"""Calculates the current time in the video based on start_time and last_position"""
		# If the video is playing, the current position is the current time since epoch - start time + last position
		if self.is_playing:
			return int(time.time()) - self.start_time + self.last_position
		# If the video is paused, just return the last position.
		else:
			return self.last_position

	# @property
	# def current_video(self, session=None):
	# 	"""Returns a dict containing info about the current video."""
	# 	if session is None:
	# 		session = Session()

	# 	if self.playlist_ended:
	# 		# If the playlist position is past the end of the playlist, return None.
	# 		return None
	# 	else:
	# 		# Otherwise, set the video ID to the ID at the current position in the playlist.
	# 		return self.playlist[self.playlist_position]

	def get_playlist_ended(self, room_data=None):
		"""True if the playlist has ended."""
		if room_data is None: room_data = self.get_room_data()
		return room_data.playlist_pos >= len(room_data.playlist)


	####################
	# OTHER PROPERTIES #
	####################

	@property
	def room_data(self):
		"""
		Quick property function that just loads room data from the database.
		"""
		return self.get_room_data()

	def get_room_data(self, session):
		"""
		Uses the given session to get the room data for this room from the database and returns it.
		If session is None, a session will be created automatically.
		"""
		return session.query(RoomData).filter_by(name=self.room_id).first()

	def get_playlist(self, room_data):
		"""Returns an array of the video IDs in the room's playlist."""
		return room_data.playlist

	def get_playlist_info(self, room_data):
		"""Returns an array containing video info for each item in the room's playlist."""
		return [get_video_info(item.video_id) for item in self.get_playlist(room_data)]

	def get_current_video(self, room_data=None):
		"""
		Gets the currently playing video from the given room_data object.
		If room_data is None, it will be loaded from the database automatically.
		"""
		if room_data is None: room_data = self.get_room_data()
		if self.get_playlist_ended(room_data):
			return None
		else:
			return room_data.playlist[room_data.playlist_pos]

	###################
	# OTHER FUNCTIONS #
	###################

	# Move along, nothing to see here.


# Cache of video info. Dictionary maps video info to video ID.
video_info_cache = {}

def get_video_info(vid):
	"""
	Does a YouTube API request and returns a dict containing information about the video.
	If the given video ID is not a valid YouTube video ID, returns None.
	"""

	if vid in video_info_cache:
		return video_info_cache[vid]

	req = requests.get("http://gdata.youtube.com/feeds/api/videos/%s?v=2&alt=json" % vid)

	try:
		response = req.json()
	except ValueError:
		# If it's not valid JSON, this isn't a valid video ID.
		return None

	author = None
	if len(response["entry"]["author"]) > 0:
		author = response["entry"]["author"][0]["name"]["$t"]

	video_info_cache[vid] = {
		"video_id": vid,
		"title": response["entry"]["title"]["$t"],
		"author": author,
		"duration": int(response["entry"]["media$group"]["yt$duration"]["seconds"]),
	}
	
	return video_info_cache[vid]
