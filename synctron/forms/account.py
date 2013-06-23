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
Module for forms pertaining to user accounts.
"""

from synctron import app, db
from synctron.user import User

from flask import render_template, redirect, abort, url_for, request, session
from flask.ext.wtf import Form, RecaptchaField
from wtforms import BooleanField, TextField, PasswordField, ValidationError, validators

from passlib.hash import sha512_crypt
from hashlib import sha384

from datetime import datetime

#################
## SIGNUP FORM ##
#################

class SignupForm(Form):
	"""
	Form for creating accounts.
	"""
	def username_not_taken(form, field):
		if db.session.query(User).filter_by(name=field.data).first() is not None:
			raise ValidationError("That username is already taken.")

	username = TextField("Username", [
		validators.Required(message="You must enter a username."),
		validators.Length(min=4, max=40, message="Usernames must be 4-40 characters long."),
		validators.Regexp(r"^[0-9A-Za-z \-\_]+$", message="Usernames can only contain alphanumerics, spaces, dashes, and underscores."),
		username_not_taken,
	])

	email = TextField("Email Address", [
		validators.Required(message="You must enter your email address."),
		validators.Email(message="That doesn't look like an email address."),
	])

	password = PasswordField("Password", [
		validators.Required(message="You must enter a password."),
		validators.Length(min=6, max=1024, message="Password must be 6-1024 characters long."),
		validators.EqualTo("confirm", message="Passwords must match."),
	])

	confirm = PasswordField("Repeat Password")

	# The most annoying necessary evil ever devised by mankind.
	captcha = RecaptchaField("Are you an evil robot?")

@app.route("/signup", methods=["GET", "POST"])
def signup():
	form = SignupForm()
	if form.validate_on_submit():
		passhash = sha512_crypt.encrypt(sha384(request.form["password"]).hexdigest())
		udata = User(request.form["username"], passhash, request.form["email"])
		db.session.add(udata)
		db.session.commit()
		return redirect(url_for("index"))
	return render_template("signup.j2", form=form)


################
## LOGIN FORM ##
################

class LoginForm(Form):
	"""
	Form for logging in.
	"""
	username = TextField("Username")
	password = PasswordField("Password")

@app.route("/login", methods=["GET", "POST"])
def login():
	form = LoginForm()
	login_failed = False
	if form.validate_on_submit():
		# Find the user.
		user = db.session.query(User).filter_by(name=request.form["username"]).first()

		# No user by that name.
		if user is None or not sha512_crypt.verify(sha384(request.form["password"]).hexdigest(), user.password):
			login_failed = True
		else:
			# Login succeeded. Set up the user's session.
			session["user"] = user.id
			session["username"] = user.name
			return redirect(url_for("index"))
	return render_template("login.j2", form=form, login_failed=login_failed)


@app.route("/logout", methods=["GET", "POST"])
def logout():
	session.pop("user", None)
	session.pop("username", None)
	return redirect(url_for("index"))


#######################
## USER PROFILE PAGE ##
#######################

@app.route("/user/<username>")
def user_profile(username):
	"""A user's profile page."""
	user = db.session.query(User).filter_by(name=username).first()

	# No user by that name.
	if user is None:
		return render_template("error/generic.j2", head="Who is that?", message="I don't know anyone by that name.")

	return render_template("user_profile.j2", user=user)
