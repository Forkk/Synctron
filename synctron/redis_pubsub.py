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

from synctron import app, db, red
from synctron.room import Room, userset_update, user_info_dict, guest_info_dict
from synctron.user import User
from synctron.roomlistsocket import broadcast_room_user_list_update
import gevent
import json

ps = red.pubsub()


def synchronize_all(data, room, dbsession):
	"""Message sent to tell Synctron to sync all users in the given room."""
	room.emit_synchronize()

def video_changed(data, room, dbsession):
	"""Message sent to tell Synctron that the video in the given room changed."""
	room.emit_video_changed()

def playlist_change(data, room, dbsession):
	"""Message sent to tell Synctron that the playlist changed."""
	# TODO: Handle thrown errors.
	change_type = data["change_type"]
	if change_type == "update":
		room.emit_playlist_update()
	elif change_type == "add":
		room.emit_video_added(data["entry"], data["index"])
	elif change_type == "remove":
		room.emit_videos_removed(data["indices"])
	elif change_type == "move":
		room.emit_video_moved(data["old_index"], data["new_index"])
	else:
		raise ValueError("Invalid playlist change type detected.")

def userlist_update(data, room, dbsession):
	"""Message sent to tell Synctron that the user list changed."""
	userset_update()
	broadcast_room_user_list_update()

def chat_message(data, room, dbsession):
	"""Message sent to tell Synctron that a chat or status message was sent."""
	# TODO: Handle thrown errors.
	message_type = data["message_type"]
	if message_type == "chat":
		user = None
		if not data["user"].startswith("Guest "):
			user = dbsession.query(User).filter_by(name=data["user"]).first()

		room.emit_chat_message(data["message"], 
			user_info_dict(user, room) if user is not None else guest_info_dict(data["user"], room), 
			"action" in data and data["action"])
	elif message.type == "status":
		room.emit_status_message(data["message"], data["msgtype"])

def config_update(data, room, dbsession):
	"""Message sent to tell Synctron that the room's settings have changed."""
	room.emit_config_update()


def redis_message_loop():
	"""Loop for processing PubSub messages on Redis."""
	ps.subscribe("rooms")

	message = None
	while True:
		try:
			gevent.sleep(0.25 if message is None else 0)

			message = ps.get_message()

			if message is not None and message["type"] == "message":
				data = None
				try:
					data = json.loads(message["data"])
				except ValueError:
					app.logger.error("Received invalid redis event message (invalid JSON): %s" % message["data"])

				dbsession = db.Session(db.engine)
				try:
					room = None
					if "room" in data:
						room = dbsession.query(Room).filter_by(slug=data["room"]).first()

					if room is None:
						app.logger.error("Received invalid redis event message (given room not found): %s" % message["data"])
					elif "event" not in data or data["event"] not in room_handlers:
						app.logger.error("Received invalid redis event message (event field missing): %s" % message["data"])
					else:
						room_handlers[data["event"]](data, room, dbsession)
				finally:
					dbsession.close()
		except:
			app.logger.error("An error occurred in the redis message loop.", exc_info=True)

gevent.spawn(redis_message_loop)


room_handlers = {
	"sync": synchronize_all,
	"video_changed": video_changed,
	"playlist_change": playlist_change,
	"userlist_update": userlist_update,
	"chat_message": chat_message,
	"config_update": config_update,
}
