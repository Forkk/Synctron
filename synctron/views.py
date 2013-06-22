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

from flask import Response, render_template, request, session, url_for, abort, redirect

from sqlalchemy import func

from passlib.hash import sha512_crypt

from synctron import app, db
from synctron.room import Room
from synctron.user import User
from synctron.database import admin_association_table, stars_association_table

db.create_all()

import json
import uuid
import re


# Import Socket.IO stuff.
from socketio import socketio_manage
from roomsocket import RoomNamespace
from roomlistsocket import RoomListNamespace

# Import gevent stuff for our hacky little update rooms loop.
from gevent import spawn, sleep as gevent_sleep

# Some regexes...
username_regex = re.compile(r"^[0-9A-Za-z \-\_]+$")
roomslug_regex = re.compile(r"^[0-9A-Za-z\-\_]+$")


# Some other modules containing other pages.
import synctron.forms.account
import synctron.forms.room


# Home page.

@app.route("/")
def index():
	popular_rooms = db.session.query(Room, func.count(stars_association_table.c.room_id).label("star_count")).join(stars_association_table).group_by(Room.id).order_by("star_count DESC").all()
	return render_template("home.j2", popular_rooms=
		[{ "title": room.Room.title, "slug": room.Room.slug, "stars": room.star_count } 
			for room in popular_rooms
			if not room.Room.is_private])


###########
## ROOMS ##
###########

@app.route("/room/<room_slug>")
def room_page(room_slug):
	return render_template("player.j2", room_slug = room_slug)

@app.route("/room/<room_slug>/star", methods=["GET", "POST"])
def star_room(room_slug):
	"""
	Page that the client makes AJAX requests to in order to check whether or not they've starred the given room.
	"""
	# First, we try and find the room the user is trying to star.
	room = db.session.query(Room).filter_by(slug=room_slug).first()

	# If the room doesn't exist, return an error.
	if room is None:
		return json.dumps({ 
			"error": "room_not_found", 
			"error_msg": "Can't star a room that doesn't exist.", 
			"starred": False,
		})

	# Next, we find the user's account.
	user = None
	if "user" in session:
		user = db.session.query(User).filter_by(id=session["user"]).first()

	# If they're not logged in, return an error.
	if user is None:
		return json.dumps({ 
			"error": "not_logged_in", 
			"error_msg": "You must be logged in to star a room.", 
			"starred": False,
		})

	if "action" in request.args:
		# If 'action' is 'star', we set the user's star.
		if request.args["action"] == "star":
			# Check if the user has already starred the room.
			star_row = db.session.execute(stars_association_table.select().
				where(stars_association_table.c.user_id==user.id).where(stars_association_table.c.room_id==room.id)).first()
			# If the user hasn't already starred the room, add a star.
			if star_row is None:
				db.session.execute(stars_association_table.insert().values(user_id=user.id, room_id=room.id))
				db.session.commit()
			return json.dumps({ "starred": True })

		# If the user is unstarring the room, remove the star.
		elif request.args["action"] == "unstar":
			db.session.execute(stars_association_table.delete().where(stars_association_table.c.user_id==user.id).where(stars_association_table.c.room_id==room.id))
			db.session.commit()
			return json.dumps({ "starred": False })

	# If action is unspecified or anything other than "star" or "unstar", check if the user has starred the room.
	star_row = db.session.execute(stars_association_table.select().
		where(stars_association_table.c.user_id==user.id).where(stars_association_table.c.room_id==room.id)).first()
	return json.dumps({ "starred": star_row is not None }) # If the row exists, they've starred the room.


#############
## SOCKETS ##
#############

@app.route("/socket.io/<path:remaining>")
def socketio(remaining):
	try:
		session_dict = { }
		if "user" in session:
			session_dict["user"] = session["user"]

		socketio_manage(request.environ, {
			"/room": RoomNamespace,
			"/roomlist": RoomListNamespace,
		}, (request, session_dict))
	except:
		app.logger.error("Exception while handling Socket.IO connection", exc_info=True)
	return Response()


############################
## SILLY ROOM UPDATE LOOP ##
############################

def room_update_loop():
	"""Greenlet that calls check_video_ended on all the rooms every few seconds."""
	while True:
		gevent_sleep(2)
		try:
			dbsession = db.Session(db.engine)
			# Find all rooms whose videos are playing.
			rooms = dbsession.query(Room).filter_by(is_playing=True).all()
			for room in rooms:
				try:
					room.check_video_ended()
				except:
					app.logger.error("Exception updating room %s." % room.slug, exc_info=True)
				gevent_sleep(0)
			dbsession.close()
		except:
			app.logger.error("Exception in room update loop.", exc_info=True)

spawn(room_update_loop)
