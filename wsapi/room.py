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

# Calculating Video Time in Rooms:
# Calculating the current time on a video in rooms is done using two values: start_time and current_pos.
# start_time tracks the last time play was clicked.
# last_position tracks what the current time was the last time the video was paused.

class Room:
	"""
	A class that represents a room.
	Contains a list of user websockets, data about the room, and functions for performing various operations.
	"""

	def __init__(self, room_id):
		"""Initializes a new room with the given ID."""
		# The room's ID
		self.room_id = room_id

		# List of users in the room.
		self.users = []

		# List of video IDs to play after the current video ends.
		self.playlist = []

		# The current position in the playlist.
		self.playlist_position = 0

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
		print("%s played video in room %s." % (user, self.room_id))

		self.update_video_timer()

		# Set the start time to the current time and set is_playing to true.
		self.start_time = int(time.time())
		self.is_playing = True
		if (sync): self.synchronize()

	def seek(self, seek_time, sync=True, user=None):
		"""Seeks the video in the room to the given time (in seconds)."""
		print("%s seeked to %i seconds in room %s." % (user, seek_time, self.room_id))

		self.update_video_timer()

		# Set last position to the time we want to seek to and reset the start time.
		self.start_time = int(time.time())
		self.last_position = int(seek_time)
		if (sync): self.synchronize()

	def pause(self, sync=True, user=None):
		"""Pauses the video in the room."""
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


	#### PLAYLIST STUFF ####

	def playlist_update(self):
		"""Called when the playlist changes. Sends playlistupdate to all users."""
		[user.send_playlistupdate() for user in self.users]

	def add_video(self, new_vid, index=None, user=None):
		"""
		Adds a video to the playlist.

		If index is None, the video is added to the end of the list.
		Otherwise, it is added at the given index.
		"""

		print("%s added video ID %s to playlist in room %s." % (user, new_vid, self.room_id))

		was_ended = self.playlist_ended

		new_vid_info = self.get_video_info(new_vid, user)

		if not new_vid_info:
			if user:
				user.send_error("invalid_vid", "The given video ID (%s) is not valid or video info could not be loaded." % new_vid)
			else:
				print("Attempt to add invalid video ID: %s" % new_vid)
			return

		if index is None:
			self.playlist.append(new_vid_info)
		else:
			# If the index is invalid, error.
			if type(index) is not int:
				if user: user.send_error("invalid_index", "The given index (%s) isn't valid." % index)
				else: print("Tried to add a video at an invalid index (%s)." % index)
				return

			if index > len(self.playlist):
				self.playlist.append(new_vid_info)
			else:
				self.playlist.insert(index, new_vid_info)
				if index < self.playlist_position or (index == self.playlist_position and not self.playlist_ended):
					self.playlist_position += 1

		self.playlist_update()

		# If the playlist was over before the video was added, change to the video we added.
		if was_ended:
			self.change_video(len(self.playlist) - 1)

	def remove_video(self, index, user=None):
		"""
		Removes the given video from the playlist.
		"""

		print("%s removed video number %i from playlist in room %s." % (user, index, self.room_id))

		before_current = False

		# We'll need to do some logic to determine what the current playing index will be changed to.
		if index < self.playlist_position:
			# If we're removing a video that's before the one that's currently playing, decrement the current_pos by one.
			self.playlist_position -= 1
			before_current = True

		del self.playlist[index]
		self.playlist_update()

		if not before_current and index == self.playlist_position:
			# If we're removing the video that's currently playing, the playlist position stays the same,
			# but we need to set the playing video to the one at the new current position.
			self.change_video(self.playlist_position);

	def change_video(self, index, user=None):
		"""
		Changes the current position in the playlist to the given index.
		"""

		print("%s changed playlist position in room %s to %i." % (user, self.room_id, index))

		self.playlist_position = index

		self.update_video_timer(0)

		self.last_position = 0
		self.start_time = int(time.time())
		self.is_playing = True
		[user.send_setvideo() for user in self.users]

	def video_ended(self):
		"""Callback for the video timer used to figure out when the video ends."""
		print("Video in room %s ended." % self.room_id)

		# Increment playlist position.
		self.change_video(self.playlist_position + 1)

	def update_video_timer(self, elapsed_time=None):
		"""
		Cancels the existing video timer and resets it to go off at the end of the video.
		If elapsed_time is not none, the value of elapsed_time will be used instead of the current_pos property.
		"""
		# Set the video timer to the duration of the video.
		if self.video_timer is not None:
			# Cancel the timer if it's already running.
			self.video_timer.cancel()
			self.video_timer = None

		# If no video is playing, don't set the timer.
		if not self.current_video:
			return

		# If duration is 0, don't set the timer.
		if self.current_video["duration"] <= 0:
			return

		# Set the timer to go off when the video ends.
		time_remaining = self.current_video["duration"] - (self.current_pos if elapsed_time is None else elapsed_time)
		print("Setting video timer for %i seconds." % time_remaining)
		self.video_timer = Timer(time_remaining, self.video_ended)
		self.video_timer.start()


	#### USER STUFF ####

	def user_list_update(self):
		"""Called when the user list changes. Sends userlistupdate to all users."""
		[user.send_userlistupdate() for user in self.users]

	def add_user(self, user):
		"""
		Adds the given user to the room.
		Called when the init action is received from the user.
		"""
		print("%s joined room %s." % (user, self.room_id))

		# Add the user to the user list, and send them setvideo.
		self.users.append(user)
		user.send_setvideo()
		user.send_playlistupdate()
		self.user_list_update()

	def remove_user(self, user):
		"""
		Removes the given user from the room.
		Called when a user's socket closes.
		Do *NOT* send anything to the user that left the room inside this function.
		"""
		print("%s left room %s." % (user, self.room_id))
		self.users.remove(user)
		self.user_list_update()


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

	@property
	def current_video(self):
		"""Returns a dict containing info about the current video."""
		if self.playlist_ended:
			# If the playlist position is past the end of the playlist, return None.
			return None
		else:
			# Otherwise, set the video ID to the ID at the current position in the playlist.
			return self.playlist[self.playlist_position]

	@property
	def playlist_ended(self):
		"""True if the playlist has ended."""
		return self.playlist_position >= len(self.playlist)

	def get_video_info(self, vid, user=None):
		"""
		Does a YouTube API request and returns a dict containing information about the video.
		If the given video ID is not a valid YouTube video ID, returns None.
		"""
		req = requests.get("http://gdata.youtube.com/feeds/api/videos/%s?v=2&alt=json" % vid)

		try:
			response = req.json()
		except ValueError:
			# If it's not valid JSON, this isn't a valid video ID.
			return None

		author = None
		if len(response["entry"]["author"]) > 0:
			author = response["entry"]["author"][0]["name"]["$t"]

		return {
			"video_id": vid,
			"title": response["entry"]["title"]["$t"],
			"author": author,
			"duration": int(response["entry"]["media$group"]["yt$duration"]["seconds"]),
			"added_by": user,
		}
