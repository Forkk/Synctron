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

from sqlalchemy import Table, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import object_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.sql.expression import func

from synctron import app, db, connections
from synctron.vidinfo import get_video_info
from synctron.database import Base, admin_association_table, stars_association_table

import time
from copy import copy
from random import shuffle

def get_entry_info(entry):
	"""
	Returns a dict containing information about the given playlist entry.
	"""
	# Because get_video_info caches video information, and we're going to be adding data to the dict,
	# we need to make a copy of it first so that the data we add to the dict doesn't get added to the
	# data that get_video_info has cached.
	info = copy(get_video_info(entry.video_id))
	if info is None:
		return None
	info["added_by"] = entry.added_by
	return info


class Room(Base):
	"""
	Class that represents one of Synctron's rooms.
	"""
	__tablename__ = "rooms"

	# The room's ID number and primary key.
	id = Column(Integer, primary_key=True)

	# The room's title. This is what is displayed to the user.
	title = Column(String(40))

	# The room's slug. Used to identify the room in URLs and such.
	slug = Column(String(40), unique=True)

	# The room's topic. This is a description of sorts for the room.
	topic = Column(String(500))

	# The owner of the room.
	owner_id = Column(Integer, ForeignKey("users.id"))


	# Whether the video is currently playing or not.
	is_playing = Column(Boolean, default=False, nullable=False)

	# The time since epoch last time the video was started.
	start_timestamp = Column(Integer, default=0, nullable=False)

	# The position that playback was at (in seconds) last time the video was paused.
	last_position = Column(Integer, default=0, nullable=False)


	# The index of the currently playing video in the room's playlist. NULL if nothing is playing.
	playlist_position = Column(Integer, default=0, nullable=True)
	
	# Videos in the room's playlist.
	playlist = relationship("PlaylistEntry", order_by="PlaylistEntry.position",
							collection_class=ordering_list("position"))


	# List of users who are admins in this room.
	admins = relationship("User", secondary=admin_association_table)


	# List of users who starred this room.
	stars = relationship("User", secondary=stars_association_table)


	## Room Settings ##
	# A private room is one that doesn't show up on the home page or in searches.
	is_private =		Column(Boolean, default=0, nullable=False)

	users_can_pause =	Column(Boolean, default=1, nullable=False)
	users_can_skip =	Column(Boolean, default=1, nullable=False)
	users_can_add =		Column(Boolean, default=1, nullable=False)
	users_can_remove =	Column(Boolean, default=1, nullable=False)
	users_can_move =	Column(Boolean, default=1, nullable=False)


	def __init__(self, slug, title=None):
		"""
		Initializes the room.
		"""

		# The slug is the room's string identifier used in URLs and the like.
		self.slug = slug

		if title is None:
			self.title = slug
		else:
			self.title = title


	##############
	# PROPERTIES #
	##############
	# Various properties for calculating stuff such as the current time in the video.

	@property
	def current_position(self):
		"""Calculates what the current time in the video's playback should be."""
		if self.is_playing:
			# If the video is playing, the current position is the current time since epoch - start time + last position
			return int(time.time()) - int(self.start_timestamp) + self.last_position
		else:
			# If the video is paused, just return the last position.
			return self.last_position

	@property
	def users(self):
		"""Generator listing users in the room."""
		for user in connections:
			if "room" in user.session and user.session["room"] == self.slug:
				yield user

	@property
	def video_is_playing(self):
		"""Returns true if a video is currently playing (ie playlist_position refers to an actual video in the playlist)."""
		return self.playlist_position >= 0 and self.playlist_position < len(self.playlist)

	@property
	def current_video_id(self):
		"""Gets the video ID of the currently playing video. None if nothing is playing"""
		if not self.video_is_playing:
			return None
		else:
			return self.playlist[self.playlist_position].video_id

	@property
	def dbsession(self):
		"""Gets the database session that this room is attached to."""
		return object_session(self)

	##############
	# OPERATIONS #
	##############
	# Various operations that can be performed on the room.

	def save(self):
		"""Saves the room to the database."""
		self.dbsession.add(self)
		self.dbsession.commit()

	#### PLAYBACK OPERATIONS ####
	# Operations relating to playback of the current video.

	def play(self):
		"""
		Sets the room to play the video.
		"""

		# Update the start time and set playing to true.
		self.start_timestamp = time.time()
		self.is_playing = True
		self.save()
		self.emit_synchronize(self.current_position, self.is_playing)

	def pause(self):
		"""
		Sets the room to pause the video.
		"""
		current_position = self.current_position

		# Update last_position and set playing to false.
		self.last_position = current_position if current_position >= 0 else 0
		self.is_playing = False
		self.save()
		self.emit_synchronize(current_position, self.is_playing)

	def seek(self, seek_time):
		"""
		Seeks to a different time in the video.
		"""
		# Set last_position to the time we want to seek to and reset the start time.
		self.start_time = time.time()
		self.last_position = int(seek_time)
		self.save()
		self.emit_synchronize(self.current_position, self.is_playing)


	#### PLAYLIST OPERATIONS ####
	# Operations relating to the room's playlist.

	def add_video(self, video_id, index=None, added_by=None):
		"""
		Adds a video to the playlist.

		If index is None or greater than the playlist length, the video is added to the end of the list.
		Otherwise, it is added at the given index.

		Returns the new playlist entry.
		"""
		was_ended = not self.video_is_playing
		video_info = get_video_info(video_id)

		if video_info is None:
			# The video ID is not valid. Raise an error.
			raise Exception("The given video ID is not valid.")

		entry = PlaylistEntry(video_id, added_by)

		if index is None:
			self.playlist.append(entry)
		else:
			# If the index is invalid, error.
			if type(index) is not int:
				raise Exception("The given index (%s) isn't valid." % index)

			if index > len(self.playlist):
				self.playlist.append(entry)
			else:
				self.playlist.insert(index, entry)
				if index < self.playlist_position or (index == self.playlist_position and self.video_is_playing):
					self.playlist_position += 1

		# Add it to the database.
		self.dbsession.add(entry)
		self.save()

		self.emit_video_added(get_entry_info(entry), entry.position)

		# If the playlist had ended before we added the video, play the one we just added.
		if was_ended:
			self.change_video(len(self.playlist) - 1)

		return entry

	def remove_video(self, index):
		"""
		Removes the video at the given index from the playlist.
		"""
		before_current = False

		# Some logic to figure out what the currently playing index will be after the video is removed.
		if index < self.playlist_position:
			# If the video we're removing is before the currently playing one, we'll need to decrement playlist_position by one.
			before_current = True
		
		self.dbsession.delete(self.playlist[index])
		self.playlist.remove(self.playlist[index])
		self.save()

		self.emit_videos_removed([index])

		# If we're removing the currently playing video, call change video to change to the new currently playing video.
		if not before_current and index == self.playlist_position:
			self.change_video(self.playlist_position)

	def shuffle_playlist(self):
		"""
		Shuffles the playlist. Very complicated.
		"""
		current = None
		if self.video_is_playing:
			current = self.playlist[self.playlist_position]
		shuffle(self.playlist)
		self.playlist_position = self.playlist.index(current)
		self.save()
		self.emit_playlist_update([get_entry_info(entry) for entry in self.playlist])
		self.emit_video_changed(self.playlist_position, self.current_video_id)

	def change_video(self, index, time_padding=3):
		"""
		Changes the current position in the playlist to the given index.
		time_padding specifies how many seconds of "padding" should be added (defaults to 3 seconds).
		Time padding here is meant to prevent the case where the client syncs a few seconds after the
		server starts "playing" the video, causing the video to start a few seconds after the actual
		beginning of the video. This is prevented by setting the server's last_position to 
		-time_padding when the video starts.
		"""
		
		self.playlist_position = index

		self.last_position = -time_padding
		self.start_timestamp = time.time()
		self.is_playing = True
		self.save()
		self.emit_video_changed(self.playlist_position, self.current_video_id)

	def check_video_ended(self):
		"""
		Called every few seconds if the video in the room is playing.
		Checks if the video has ended and calls video_ended if so.
		"""
		if self.current_video_id is None:
			return
			
		current_video = get_video_info(self.current_video_id)
		if current_video is None:
			return

		# Get the duration of the currently playing video.
		# We add 2 to this to give an extra couple seconds of "padding" to make sure videos
		# don't seem to end early.
		duration = current_video["duration"] + 2

		# If the current position is greater than or equal to the duration of the video, the video has ended.
		if self.current_position >= duration:
			self.video_ended()

	def video_ended(self):
		"""
		Callback for when the currently playing video has ended.
		"""
		# Increment playlist position
		self.change_video(self.playlist_position + 1)


	#### USER OPERATIONS ####
	# Operations having to do with the users in the room.

	def userlist_update(self):
		"""
		Gets a list of dicts containing info about users in the room and passes it to emit_userlist_update.
		"""
		dbsession = db.Session(db.engine)
		userlist = []
		try:
			userlist = [u.info_dict(dbsession=dbsession) for u in self.users]
		finally:
			dbsession.close()
		self.emit_userlist_update(userlist)

	def add_user(self, user):
		"""
		Adds a user to the room and sends it events to initialize the client.
		"""
		user.playlist_update([get_entry_info(entry) for entry in self.playlist])
		user.video_changed(self.playlist_position, self.current_video_id)
		self.userlist_update()

	def remove_user(self, user):
		"""
		Removes a user from the room and emits a userlist update.
		"""
		self.userlist_update()


	#### CHAT OPERATIONS ####
	# Operations having to do with chat.

	def chat_message(self, message, user, force_post=False):
		"""
		Posts the given message in chat from the given user.
		Does nothing if message is empty, unless force_post is set to true True.
		"""
		if len(message) > 0 or force_post:
			self.emit_chat_message(message, user)


	##########
	# EVENTS #
	##########
	# Code relating to the room's events that are passed to the connected users.

	def emit_synchronize(self, video_time, is_playing):
		[user.synchronize(video_time, is_playing) for user in self.users]

	def emit_video_changed(self, playlist_position, video_id):
		[user.video_changed(playlist_position, video_id) for user in self.users]

	def emit_playlist_update(self, entries):
		[user.playlist_update(entries) for user in self.users]

	def emit_video_added(self, entry, index):
		[user.video_added(entry, index) for user in self.users]

	def emit_videos_removed(self, indices):
		[user.videos_removed(indices) for user in self.users]

	def emit_video_moved(self, old_index, new_index):
		[user.video_moved(old_index, new_index) for user in self.users]

	def emit_userlist_update(self, userlist):
		dbsession = db.Session(db.engine)
		[user.userlist_update(userlist, dbsession=dbsession) for user in self.users]

	def emit_chat_message(self, message, from_user):
		[user.chat_message(message, from_user) for user in self.users]


class PlaylistEntry(Base):
	"""
	Class representing an entry in a room's playlist.
	"""
	__tablename__ = "playlist_entries"

	# Entry ID number.
	id = Column(Integer, primary_key=True)

	# The video's YouTube video ID.
	video_id =	Column(String(15))

	# The position of the video in the room's playlist.
	position =	Column(Integer)

	# The username of the user who added the video.
	added_by =	Column(String(80))

	# The ID of the room this entry belongs to.
	room_id =	Column(Integer, ForeignKey("rooms.id"))

	def __init__(self, vid, by=None):
		self.video_id = vid
		self.added_by = by
