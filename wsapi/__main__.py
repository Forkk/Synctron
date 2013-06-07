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

from wsapi.user import UserWebSocket, Session

import sys
import argparse

def main(argv):
	parser = argparse.ArgumentParser("wsapi", description="WebSocket server for TubeSync.")

	parser.add_argument("-l", "--host", action="store", default="localhost", 
		help="the hostname to listen on (default: %(default)s)", metavar="HOST")
	parser.add_argument("-p", "--port", action="store", default=8889, type=int,
		help="the port to listen on (default: %(default)s)", metavar="PORT")

	parser.add_argument("-d", "--dburi", action="store", default="mysql://sync@127.0.0.1/sync",
		help="the SQLAlchemy database URI to connect to (default: %(default)s)", metavar="DB")
	parser.add_argument("-k", "--key", action="store", default="defaultsecretthatshouldbechangedwhenusedinproduction",
		help="the secret key that will be used to deserialize session info", metavar="KEY")

	args = parser.parse_args(argv[1:])

	from gevent import monkey; monkey.patch_all()
	from ws4py.server.geventserver import WSGIServer
	from ws4py.server.wsgiutils import WebSocketWSGIApplication

	from sqlalchemy import create_engine

	engine = create_engine(args.dburi)
	Session.configure(bind=engine)

	UserWebSocket.secret_key = args.key

	print("Running WebSocket server on %s:%i..." % (args.host, args.port))
	server = WSGIServer((args.host, args.port), WebSocketWSGIApplication(handler_cls=UserWebSocket))
	server.serve_forever()


# Main code for testing.
if __name__ == "__main__":
	main(sys.argv)
