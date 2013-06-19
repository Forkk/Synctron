PORT = 8000

# URI for the database to connect to.
SQLALCHEMY_DATABASE_URI = "mysql://sync@127.0.0.1/sync2"

# Flask's secret key. This should be changed in production deployments.
SECRET_KEY = "defaultsecretthatshouldbechangedwhenusedinproduction"

# This is necessary for the websocket stuff to work.
SESSION_COOKIE_HTTPONLY = False

# For Google analytics.
# GOOGLE_ANALYTICS_ID = ""

# Must be specified in some config.
# YT_API_KEY
