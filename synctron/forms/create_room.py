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

from synctron import app, db
from synctron.user import User
from synctron.room import Room

from flask import render_template, redirect, abort, url_for, request, session
from flask.ext.wtf import Form, RecaptchaField
from wtforms import BooleanField, TextField, PasswordField, ValidationError, validators

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

	captcha = RecaptchaField()

@app.route("/create_room", methods=["GET", "POST"])
def create_room():
	# Verify that the user is logged in.
	user = None
	if "user" in session:
		user = db.session.query(User).filter_by(id=session["user"]).first()
	if user is None:
		return render_template("account_required.j2", message="You need an account to create a room.")

	else:
		form = CreateRoomForm()
		if form.validate_on_submit():
			room = Room(request.form["slug"], request.form["title"])
			room.is_private = "is-private" in request.form and request.form["is-private"] == "on"
			db.session.add(room)
			db.session.commit()
			return redirect(url_for("room_page", room_slug=slug))
	return render_template("create_room.j2", form=form)
