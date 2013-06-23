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

from sqlalchemy import Table, Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.orderinglist import ordering_list

from synctron import app, db
from synctron.room import Base, stars_association_table

from datetime import datetime

class User(Base):
	"""
	Class representing a user.
	"""
	__tablename__ = "users"

	# The user's ID number.
	id = Column(Integer, primary_key=True)

	# The user's name.
	name = Column(String(80), unique=True, nullable=False)

	# Hash of user's password.
	password = Column(String(160))

	# The user's email address.
	email = Column(String(320))


	# Rooms that this user owns.
	owned_rooms = relationship("Room", backref="owner")

	# Rooms that this user has starred.
	rooms_starred = relationship("Room", secondary=stars_association_table)

	# The date the account was created.
	account_created = Column(DateTime, nullable=False)

	# The last date the user was active.
	last_activity = Column(DateTime, nullable=True)

	# Profile settings.
	show_rooms_joined = Column(Boolean, nullable=False, default=True)
	show_rooms_owned = Column(Boolean, nullable=False, default=True)
	show_rooms_starred = Column(Boolean, nullable=False, default=True)

	def __init__(self, name, password, email):
		self.name = name
		self.password = password
		self.email = email
		self.account_created = datetime.now()
