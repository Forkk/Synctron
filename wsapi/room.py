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

import time

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

		# The ID of the video that is currently playing.
		self.video_id = ""

		# The service that is playing the video. (YouTube is the only one right now)
		self.video_service = "YouTube"

		# Whether the video is playing or not.
		self.is_playing = False

		# The last time playback was started.
		self.start_time = 0

		# The position the video was at the last time playback was paused.
		self.last_position = 0


	##############
	# OPERATIONS #
	##############
	# Various operations that can be performed on the room.

	## PLAYBACK STUFF ##

	def synchronize(self):
		"""Synchronizes playback for all the users in the room."""
		[user.send_sync() for user in self.users]

	def play(self, sync=True):
		"""Plays the video in the room."""
		print("Playing room %s." % self.room_id)

		# Set the start time to the current time and set is_playing to true.
		self.start_time = int(time.time())
		self.is_playing = True
		if (sync): self.synchronize()

	def seek(self, seek_time, sync=True):
		"""Seeks the video in the room to the given time (in seconds)."""
		print("Seeking room %s to %i seconds." % (self.room_id, seek_time))

		# Set last position to the time we want to seek to and reset the start time.
		self.start_time = int(time.time())
		self.last_position = int(seek_time)
		if (sync): self.synchronize()

	def pause(self, sync=True):
		"""Pauses the video in the room."""
		print("Pausing room %s." % self.room_id)

		# Set last position to the current position and set is_playing to false.
		self.last_position = self.current_pos()
		self.is_playing = False
		if (sync): self.synchronize()

	def change_video(self, new_vid):
		"""Changes the video playing to the given video."""
		print("Changing video in room %s to %s." % (self.room_id, new_vid))

		self.video_id = new_vid
		self.last_position = 0
		self.start_time = int(time.time())
		self.is_playing = True
		[user.send_setvideo() for user in self.users]


	## USER STUFF ##

	def add_user(self, user):
		"""
		Adds the given user to the room.
		Called when the init action is received from the user.
		"""
		print("User '%s' joined room %s." % (user.username, self.room_id))

		# Add the user to the user list, and send them setvideo.
		self.users.append(user)
		user.send_setvideo()

	def remove_user(self, user):
		"""
		Removes the given user from the room.
		Called when a user's socket closes.
		Do *NOT* send anything to the user that left the room inside this function.
		"""
		print("User '%s' left room %s." % (user.username, self.room_id))
		self.users.remove(user)


	################
	# CALCULATIONS #
	################
	# Calculations such as the current video time.

	def current_pos(self):
		"""Calculates the current time in the video based on start_time and last_position"""
		# If the video is playing, the current position is the current time since epoch - start time + last position
		if self.is_playing:
			return int(time.time()) - self.start_time + self.last_position
		# If the video is paused, just return the last position.
		else:
			return self.last_position
