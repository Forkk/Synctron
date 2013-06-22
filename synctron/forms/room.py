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

"""
Forms related to creating and managing rooms.
"""

from synctron import app, db
from synctron.user import User
from synctron.room import Room

from flask import render_template, redirect, abort, url_for, request, session
from flask.ext.wtf import Form, RecaptchaField
from wtforms import BooleanField, TextField, PasswordField, ValidationError, validators

#################
## CREATE ROOM ##
#################

class CreateRoomForm(Form):
	"""
	Form for creating rooms.
	"""
	def room_slug_not_taken(form, field):
		if db.session.query(Room).filter_by(slug=field.data).first() is not None:
			raise ValidationError("That room slug is already taken.")

	title = TextField("Room Title", [
		validators.Required(message="You must specify a room title."),
		validators.Length(min=2, max=40, message="Title must be 2-40 characters long."),
	])

	slug = TextField("Room Slug", [
		validators.Required(message="You must specify a room slug."),
		validators.Length(min=2, max=20, message="Slug must be 2-20 characters long."),
		validators.Regexp(r"^[0-9A-Za-z\-\_]+$", message="Slug must contain only alphanumerics, dashes, and underscores."),
		room_slug_not_taken,
	])

	is_private = BooleanField("Make room private?")

	captcha = RecaptchaField("Are you an evil robot?")

@app.route("/create_room", methods=["GET", "POST"])
def create_room():
	# Verify that the user is logged in.
	user = None
	if "user" in session:
		user = db.session.query(User).filter_by(id=session["user"]).first()
	if user is None:
		return render_template("error/account_required.j2", message="You need to be logged in to create a room.")

	else:
		form = CreateRoomForm()
		if form.validate_on_submit():
			room = Room(request.form["slug"], request.form["title"])
			room.is_private = "is-private" in request.form and request.form["is-private"] == "on"
			room.owner = user
			db.session.add(room)
			db.session.commit()
			return redirect(url_for("room_page", room_slug=request.form["slug"]))
	return render_template("create_room.j2", form=form)


###################
## ROOM SETTINGS ##
###################

class RoomSettingsForm(Form):
	"""
	Form for changing a room's settings.
	"""
	title = TextField("Room Title", [
		validators.Required(message="You must specify a room title."),
		validators.Length(min=2, max=40, message="Title must be 2-40 characters long."),
	])
	topic = TextField("Room Topic")
	is_private = BooleanField("Private")

	users_can_add = BooleanField("Users can add videos")
	users_can_remove = BooleanField("Users can remove videos")
	users_can_move = BooleanField("Users can reorder the playlist")
	users_can_pause = BooleanField("Users can pause")
	users_can_skip = BooleanField("Users can skip to a different video in the playlist.")


@app.route("/room/<slug>/settings", methods=["GET", "POST"])
def room_settings(slug):
	# Get the room.
	room = db.session.query(Room).filter_by(slug=slug).first()

	# Error if the room doesn't exist.
	if room is None:
		return render_template("error/generic.j2", message="That room doesn't exist.")

	# Get the user.
	user = None
	if "user" in session:
		user = db.session.query(User).filter_by(id=session["user"]).first()

	# Error if the user isn't logged in.
	if user is None:
		return render_template("error/account_required.j2", message="You need to be logged in to change room settings.")

	# Error if the user doesn't own the room.
	if room.owner != user:
		return render_template("error/generic.j2", head="I'm sorry %s, I'm afraid I can't do that." % user.name, 
			message="You can't change settings on a room you don't own.")

	form = RoomSettingsForm(obj=room)
	message = None
	msg_type = "info"
	msg_timeout = None
	if form.validate_on_submit():
		# Set fields in the room and commit to the database.
		form.populate_obj(room)
		db.session.commit()
		message = "Room settings saved successfully."
		msg_type = "success"
		msg_timeout = 3000
		room.emit_config_update()
	return render_template("room_settings.j2", form=form, alert_msg=message, alert_type=msg_type, alert_timeout=msg_timeout)
