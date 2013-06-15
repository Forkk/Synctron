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

# Some regexes...

# Usernames must match this regex.
username_regex = re.compile(r"^[0-9A-Za-z \-\_]+$")


# Home page.

@app.route("/")
def index():
	popular_rooms = db.session.query(Room, func.count(stars_association_table.c.room_id).label("star_count")).join(stars_association_table).group_by(Room.id).order_by("star_count DESC").all()
	return render_template("home.j2", popular_rooms=
		[{ "name": room.Room.name, "stars": room.star_count } for room in popular_rooms])


###########
## LOGIN ##
###########

@app.route("/login")
def login_page():
	return render_template("login.j2")

@app.route("/login/ajax", methods=["POST"])
def login_submit():
	# Make sure the request is valid.
	if ("username" not in request.form or
		"password" not in request.form):
		abort(400) # Bad request.

	# Find the given user.
	user = db.session.query(UserData).filter_by(name=request.form["username"]).first()

	if user is None:
		# If there's no user by that name, bad login.
		return json.dumps({ "success": False, "error_id": "bad_login", "error_msg": "Wrong username or password." })
	else:
		# Otherwise, verify the password.
		if sha512_crypt.verify(request.form["password"], user.password):
			# Login succeeded. Set up the user's session.
			session["user"] = user.id
			session["username"] = user.name
			return json.dumps({ "success": True })
		else:
			# Bad login.
			return json.dumps({ "success": False, "error_id": "bad_login", "error_msg": "Wrong username or password." })

@app.route("/logout", methods=["GET", "POST"])
def logout_page():
	session.pop("user", None)
	session.pop("username", None)
	return redirect(url_for("index"))


############
## SIGNUP ##
############

@app.route("/signup")
def signup_page():
	return render_template("signup.j2")

@app.route("/signup/ajax", methods=["POST"])
def signup_submit():
	# Make sure the request is valid.
	if ("username" not in request.form or
		"password" not in request.form or
		"email"    not in request.form):
		abort(400) # Bad request.

	if not username_regex.match(request.form["username"]):
		return json.dumps({ 
			"success": False, "error_id": "invalid_name", 
			"error_msg": "That's not a valid username. Usernames can contain only alphanumerics, spaces, dashes, and underscores."
		})
	
	# Check if there's already a user with this username.
	if db.session.query(UserData).filter_by(name=request.form["username"]).first() is not None:
		# The username is taken.
		return json.dumps({ "success": False, "error_id": "name_taken", "error_msg": "That username is already taken." })

	# Hash the password.
	passhash = sha512_crypt.encrypt(request.form["password"])

	# Create the user,
	udata = UserData(request.form["username"], passhash, request.form["email"])
	db.session.add(udata)
	db.session.commit()

	return json.dumps({ "success": True, })


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
		user = db.session.query(UserData).filter_by(id=session["user"]).first()

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
		socketio_manage(request.environ, {
			"/room": RoomNamespace,
		}, request)
	except:
		app.logger.error("Exception while handling Socket.IO connection", exc_info=True)
	return Response()
