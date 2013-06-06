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

from flask import render_template, request, abort

from passlib.hash import sha256_crypt

from tubesync import app, db

import json

from common.db import UserData


@app.route("/")
def home_page():
	return "Move along! Nothing to see here!"


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
	
	# Check if there's already a user with this username.
	if db.session.query(UserData).filter_by(name=request.form["username"]).first() is not None:
		# The username is taken.
		return json.dumps({ "success": False, "error_id": "name_taken", "error_msg": "That username is already taken." })

	# Hash the password.
	passhash = sha256_crypt.encrypt(request.form["password"])

	# Create the user,
	udata = UserData(request.form["username"], passhash, request.form["email"])
	db.session.add(udata)
	db.session.commit()

	return json.dumps({ "success": True, })


@app.route("/room/<room_id>")
def room_page(room_id):
	return render_template("player.j2", 
		room_id = room_id, 
		wsapi_url = app.config.get("WSAPI_URL"))
