import sys
import json
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from multiprocessing import Process, Queue

requiredSecrets = {
    "secretKey": "The site secret key.",
    "cfSiteKey": "The key or the sites turnstile",
    "cfSecretKey": "The secret for the sites turnstile",
    "mailServerKey": "Key/Password for mail server",
    "mailAddress": "Mail address to send from / login with",
    "loginAddress": "Address to login to smtp server"
}

app = Flask(__name__, template_folder="templates", static_folder="static")

# Configure the logging format
log_format = "[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s"
logging.basicConfig(level=logging.ERROR, format=log_format)

# DB config
# SQL_ALCHEMY_DATABASE_URL : the location of the database
# Here SQLite with no security is used but this can be secured if needed
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Socket IO Stup
socketio = SocketIO(app)

# Import the schema definition
from app import schema


# INIT flask login
loginMan = LoginManager(app)
loginMan.login_view = 'login'


# Define the user loader function
@loginMan.user_loader
def load_user(user_id):
    return schema.User.query.get(int(user_id))


# Secrets config
with open("app/secrets.json") as secretstxt:
    secrets = json.load(secretstxt)
    # Check for missing headers
    missingSecrets = list(map(lambda x: False if x in secrets.keys() else x,requiredSecrets.keys()))
    #print(missingSecrets)
    if any(missingSecrets):
        logging.critical(f"Missing required secrets:\n{', '.join(list(filter(lambda x: not x is False, missingSecrets)))}")
        sys.exit()

    # Secret key parsed from secrets.json, for unique secret key please run gensecretkey.py in the app folder
    app.config["SECRET_KEY"] = secrets["secretKey"]
    app.config["cfSiteKey"] = secrets["cfSiteKey"]
    app.config["cfSecretKey"] = secrets["cfSecretKey"]
    app.config["mailPassword"] = secrets["mailServerKey"]
    app.config["mailAddress"] = secrets["mailAddress"]
    app.config["loginAddress"] = secrets["loginAddress"]
    del(secrets)


# Routes Config
# import routes for main app
# blueprints can be imported here
from app import routes
from app import emailAuthRoutes

# custom Jinja addons
from app import jinjaTemplateAddons

# CLI command config
# initdb command, Only run this when the app is installed, this will generate the database using the imported schema above.
@app.cli.command()
def initdb():
    # create the tables defined in schema
    db.create_all()




# allow app to be run as-is (in dev mode)
if __name__ == '__main__':
    socketio.run(app)


