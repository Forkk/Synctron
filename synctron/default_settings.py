# URL for the websocket API
WSAPI_URL = "ws://127.0.0.1:8889"

# URI for the database to connect to.
SQLALCHEMY_DATABASE_URI = "mysql://sync@127.0.0.1/sync"

# Flask's secret key. This should be changed in production deployments.
SECRET_KEY = "defaultsecretthatshouldbechangedwhenusedinproduction"

# This is necessary for the websocket stuff to work.
SESSION_COOKIE_HTTPONLY = False
