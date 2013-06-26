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

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from gevent import monkey, spawn as gevent_spawn

from synctron.sessioninterface import ItsdangerousSessionInterface

from redis import StrictRedis

import uuid

monkey.patch_all()

app = Flask(__name__)
app.config.from_object("synctron.default_settings")
app.config.from_envvar("SYNC_SETTINGS")

app.session_interface = ItsdangerousSessionInterface()

app.logger.info("Initializing SQLAlchemy...")
db = SQLAlchemy(app)

# A unique identifier for this worker/process.
# This is used to identify this process's user sets within redis.
app.logger.info("Generating worker UUID...")
workerid = uuid.uuid4()

app.logger.info("Loading redis...")
red = StrictRedis.from_url(app.config.get("REDIS_URL"))

# Stupid array for keeping track of connected users.
# It has to be in here to prevent stupid circular imports.
connections = []

import synctron.views

from synctron.room import userset_greenlet
app.logger.info("Starting userset polling...")
gevent_spawn(userset_greenlet)
