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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.orderinglist import ordering_list

Base = declarative_base()


admin_association_table = Table("admins", Base.metadata,
	Column("user_id",	Integer,	ForeignKey("users.id")), # The user who is the admin.
	Column("room_id",	Integer,	ForeignKey("rooms.id"))  # The room that the user is an admin in.
)

stars_table = Table("stars", Base.metadata,
	Column("user_id",	Integer,	ForeignKey("users.id")), # The user that starred the room.
	Column("room_id",	Integer,	ForeignKey("rooms.id"))  # The room that the user starred.
)

class UserData(Base):
	"""
	Class representing information about a user as it is stored in the database.
	"""
	__tablename__ = "users"

	id = Column(Integer, primary_key=True) # User ID
	name = Column(String(80), unique=True, nullable=False) # Username
	password = Column(String(160)) # Hash of user's password
	email = Column(String(320)) # User's email address

	# Rooms this user owns.
	owned_rooms = relationship("RoomData", backref="owner")

	# Rooms this user has starred.
	rooms_starred = relationship("RoomData", secondary=stars_table)

	def __init__(self, name, password, email):
		self.name = name
		self.password = password
		self.email = email

class RoomData(Base):
	"""
	Class representing information about a room as it is stored in the database.
	"""
	__tablename__ = "rooms"

	id = Column(Integer, primary_key=True) # Room ID number.
	name = Column(String(20), unique=True) # Room name. This is a unique string with no spaces.

	owner_id = Column(Integer, ForeignKey("users.id")) # The owner of the room.

	playlist = relationship("PlaylistEntry", order_by="PlaylistEntry.position",  # Videos in this room's playlist.
							collection_class=ordering_list("position"))
	playlist_pos = Column(Integer) # The currently playing video in the playlist.

	# List of users who are admins in this room.
	admins = relationship("UserData", secondary=admin_association_table)

	# List of users who starred this room.
	stars = relationship("UserData", secondary=stars_table)


	## Room Settings ##
	users_can_pause =	Column(Boolean, default=1, nullable=False)
	users_can_skip =	Column(Boolean, default=1, nullable=False)
	users_can_add =		Column(Boolean, default=1, nullable=False)
	users_can_remove =	Column(Boolean, default=1, nullable=False)

	def __init__(self, name):
		self.name = name
		self.playlist_pos = 0

class PlaylistEntry(Base):
	"""
	Class representing an entry in a room's playlist.
	"""
	__tablename__ = "playlist_entries"

	id = Column(Integer, primary_key=True) # Entry ID number.
	video_id =	Column(String(15)) # The video's YouTube video ID.
	position =	Column(Integer) # The position of the video in the playlist.
	added_by =	Column(String(80)) # The username of the user who added the video.

	room_id =	Column(Integer, ForeignKey("rooms.id")) # The ID of the room this entry belongs to.

	def __init__(self, vid, by=None):
		self.video_id = vid
		self.added_by = by
