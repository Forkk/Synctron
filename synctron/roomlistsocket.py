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

from synctron import app, db, connections as roomsocket_connections

from synctron.room import Room

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

	def disconnect(self, *args, **kwargs):
		if "silent" in kwargs:
			del kwargs["silent"]

		if self in _connections:
			_connections.remove(self)
		BaseNamespace.disconnect(self, *args, **kwargs)


	#################
	# SOCKET EVENTS #
	#################

	def on_list_update(self):
		"""Event sent by the client to request a list update."""
		# Send the users room list.
		self.send_room_user_list_update()

	def send_room_user_list_update(self, broadcast=False):
		"""Sends the client a list of rooms with the most users."""
		room_dict = {}
		for connection in roomsocket_connections:
			if "room" in connection.session:
				if connection.session["room"] in room_dict:
					room_dict[connection.session["room"]] += 1
				else:
					room_dict[connection.session["room"]] = 1

		room_list = []
		dbsession = db.Session(db.engine)
		try:
			for slug, usercount in room_dict.iteritems():
				room = dbsession.query(Room).filter_by(slug=slug).first()
				if room is None or room.is_private:
					continue

				room_data = {
					"slug": slug,
					"title": room.title,
					"usercount": usercount,
				}
				room_list.append(room_data)
		finally:
			dbsession.close()

		room_list.sort(key=lambda room: room["usercount"], reverse=True)
		self.emit("room_list_users", room_list[:10])

def broadcast_room_user_list_update():
	"""Calls send_room_user_list_update for all connections."""
	[connection.send_room_user_list_update() for connection in _connections]
