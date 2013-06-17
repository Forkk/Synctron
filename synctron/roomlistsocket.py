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

from socketio.namespace import BaseNamespace

from synctron import app, db

from synctron.room import Room, rooms

_connections = []

class RoomListNamespace(BaseNamespace):
	"""
	Namespace for handling events having to do with room lists.
	"""

	def initialize(self):
		self.logger = app.logger
		_connections.append(self)

	def log(self, msg):
		self.logger.info("[{0}] {1}".format(self.socket.sessid, msg))

	def disconnect(self):
		_connections.remove(self)


	#################
	# SOCKET EVENTS #
	#################

	def on_list_update(self):
		"""Event sent by the client to request a list update."""
		# Send the users room list.
		self.send_room_user_list_update()

	def send_room_user_list_update(self, broadcast=False):
		"""Sends the client a list of rooms with the most users."""
		roomlist = [{ "name": name, "usercount": len(users) } for name, users in rooms.iteritems()]
		roomlist.sort(key=lambda room: room["usercount"], reverse=True)
		self.emit("room_list_users", roomlist[:10])

def broadcast_room_user_list_update():
	"""Calls send_room_user_list_update for all connections."""
	[connection.send_room_user_list_update() for connection in _connections]
