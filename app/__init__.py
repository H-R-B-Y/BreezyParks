import os, json
from dotenv import load_dotenv, set_key
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_socketio import SocketIO
from authlib.jose import JsonWebKey
from authlib.integrations.flask_client import OAuth
from functools import wraps



app = Flask(__name__, template_folder="templates", static_folder="static")

load_dotenv()
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DBADDR")
db = SQLAlchemy(app)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["cfSiteKey"] = os.getenv("cfSiteKey")
app.config["cfSecretKey"] = os.getenv("cfSecretKey")
app.config["mailPassword"] = os.getenv("mailServerKey")
app.config["mailAddress"] = os.getenv("mailAddress")
app.config["loginAddress"] = os.getenv("loginAddress")
app.config["googleclientid"] = os.getenv("googleclientid")
# print(app.config["googleclientid"])
# print(os.getenv("googleclientsecret"))

# Socket IO Stup
socketio = SocketIO(app)

loginman = LoginManager(app)

# Need to double check this later.
# deal with schema here: 
loginman.login_view = 'login' 
# Define the user loader function
@loginman.user_loader
def load_user(user_id):
	return schema.User.get_user_by_id(user_id)

# OAuth setup
oauth = OAuth(app)
google = oauth.register(
	name="google",
	client_id=app.config["googleclientid"],
	client_secret=os.getenv("googleclientsecret"),
	authorize_url="https://accounts.google.com/o/oauth2/auth",
	authorize_params=None,
	access_token_url="https://accounts.google.com/o/oauth2/token",
	access_token_params=None,
	refresh_token_url=None,
	client_kwargs={"scope": "openid profile email"},
	jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
)

from app import schema

# should probably move this stuff into its own file but whatever
def require_admin(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		if not current_user or not current_user.is_authenticated:
			return abort(403)
		if not current_user.is_admin:
			return {"error": "Unauthorized"}, 401
		return (func(*args, **kwargs))
	return wrapper

# Example wrapper for later token use
def require_token(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		print(request.headers)
		auth_header = request.headers.get('Authorization')
		if not auth_header:
			return jsonify({"error": "Missing Authorization header"}), 401
		# Ensure the header starts with 'Bearer'
		parts = auth_header.split()
		if len(parts) != 2 or parts[0].lower() != "bearer":
			return jsonify({"error": "Invalid Authorization header format"}), 401
		# Validate the token
		token = parts[1]
		# valid something like:
		if schema.AccessToken.query.filter_by(token=token).first() != None:
			return func(*args, **kwargs)
		return jsonify({"error": "Invalid token"}), 403
	return wrapper

def write_to_extra(key : str, value : str):
	file_path = "extra_data.json"
	if not os.path.exists(file_path):
		with open(file_path, "w") as f:
			json.dump({}, f)
	with open(file_path, "r") as f:
		try:
			data = json.load(f)
		except json.JSONDecodeError:
			data = {}
	data[key] = value
	with open(file_path, "w") as f:
		json.dump(data, f, indent=1)
	return True

def get_extra_data(key : str):
	file_path = "extra_data.json"
	if not os.path.exists(file_path):
		return None
	with open(file_path, "r") as f:
		try:
			data = json.load(f)
		except json.JSONDecodeError:
			data = {}
	if key in data.keys():
		return data[key]
	else: return None

from app import basic_routes
from app import jinja_template_addons
from app import login_auth_routes
from app import paper_note_routes


# # Delete this later.
# @app.cli.command("create-db")
# def create_db():
# 	db.create_all()

# github = oauth.register(
# 	name="github",
# 	client_id=os.environ.get("GITHUB_CLIENT_ID"),
# 	client_secret=os.environ.get("GITHUB_CLIENT_SECRET"),
# 	authorize_url="https://github.com/login/oauth/authorize",
# 	access_token_url="https://github.com/login/oauth/access_token",
# 	client_kwargs={"scope": "read:user user:email"},
# )

# example usage:
# @app.route("/login")
# def login():
#     return google.authorize_redirect(redirect_uri=url_for("auth", _external=True))

# @app.route("/auth")
# def auth():
#     token = google.authorize_access_token()
#     user_info = google.parse_id_token(token)
    
#     # Create or retrieve the user
#     user = users.get(user_info['email'])
#     if not user:
#         user = User(id=user_info['email'], email=user_info['email'])
#         users[user.id] = user
    
#     login_user(user)
#     return redirect(url_for("index"))

# @app.route("/login/github")
# def login_github():
#     return github.authorize_redirect(redirect_uri=url_for("auth_github", _external=True))

# @app.route("/auth/github")
# def auth_github():
#     token = github.authorize_access_token()
#     user_info = github.get("user").json()

#     # Create or retrieve the user
#     user = users.get(user_info['login'])
#     if not user:
#         user = User(id=user_info['login'], email=user_info['email'])
#         users[user.id] = user

#     login_user(user)
#     return redirect(url_for("index"))

# @app.route("/logout")
# @login_required
# def logout():
#     logout_user()
#     return redirect(url_for("index")

# reference:
# Load the Google Platform Library
# You must include the Google Platform Library on your web pages that integrate Google Sign-In.
# <script src="https://apis.google.com/js/platform.js" async defer></script>
# Specify your app's client ID
# Specify the client ID you created for your app in the Google Developers Console with the google-signin-client_id meta element.
# <meta name="google-signin-client_id" content="YOUR_CLIENT_ID.apps.googleusercontent.com">