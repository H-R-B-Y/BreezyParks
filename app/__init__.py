import os, json
from dotenv import load_dotenv, set_key
from flask import Flask, request, abort, jsonify, redirect, render_template, Response, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user, login_user, logout_user
from flask_socketio import SocketIO
from authlib.jose import JsonWebKey
from authlib.integrations.flask_client import OAuth
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__, template_folder="templates", static_folder="static")

load_dotenv()


app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["ENVIRONMENT_NAME"] = os.getenv("ENVIRONMENT_NAME")

if app.config["ENVIRONMENT_NAME"] == "development" or not app.config["ENVIRONMENT_NAME"]:
	app.config['SESSION_COOKIE_DOMAIN'] = None
	app.config['SESSION_COOKIE_SECURE'] = False  # Enforce HTTPS for cookies
if app.config["ENVIRONMENT_NAME"] == "production":
	app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
	app.config['SESSION_COOKIE_SECURE'] = True  # Enforce HTTPS for cookies
	app.config['PREFERRED_URL_SCHEME'] = 'https'
	app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
	app.config['SESSION_COOKIE_HTTPONLY'] = True


app.config["cfSiteKey"] = os.getenv("cfSiteKey")
app.config["cfSecretKey"] = os.getenv("cfSecretKey")
app.config["mailPassword"] = os.getenv("mailServerKey")
app.config["mailAddress"] = os.getenv("mailAddress")
app.config["loginAddress"] = os.getenv("loginAddress")
app.config["googleclientid"] = os.getenv("googleclientid")

app.config["spotify_client_id"] = os.getenv("spotifyAppId")
app.config["spotify_client_secret"] = os.getenv("spotifyAppSecret")

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DBADDR")
db = SQLAlchemy(app)

# Socket IO Stup
socketio = SocketIO(app)

loginman = LoginManager(app)

from app import schema

# Need to double check this later.
# deal with schema here: 
loginman.login_view = 'login' 
# Define the user loader function
@loginman.user_loader
def load_user(user_id):
	return schema.User.query.get(int(user_id))


@app.before_request
def enforce_single_domain():
	if app.config["ENVIRONMENT_NAME"] == "production":
		if request.url.startswith('http://'):
			# Redirect HTTP to HTTPS
			url = request.url.replace('http://', 'https://', 1)
			return redirect(url, code=301)

@app.before_request
def banned_user_wrapper():
	if current_user.is_authenticated and current_user.is_banned:
		flash("Your account has been banned. You have been logged out.", "error")
		logout_user()

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

@app.cli.command("create_db")
def create_db():
	if app.config["ENVIRONMENT_NAME"] == "development":
		db.create_all()
	else:
		print("Not in development mode, not creating database.")


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

def render_page_failsafe(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		try:
			res = func(*args, **kwargs)
			if isinstance(res, tuple):
				body, status_code = res
				if isinstance(body, dict) and body.get("status") == "error":
					return render_template("default_error.html.jinja", status_code = str(status_code), **body), status_code
				if isinstance(body, Response) and body.headers.get("Content-Type") == "application/json":
					jsondata = body.get_json()
					if jsondata.get("status") == "error":
						if jsondata.get("message"):
							return render_template("default_error.html.jinja", status_code = str(status_code), message = jsondata.get("message")), status_code
						return render_template("default_error.html.jinja", status_code = str(status_code), message = "No message provided"), status_code
				if isinstance(body, str) and status_code != 200:
					return render_template("default_error.html.jinja", status_code = str(status_code), message = body), status_code
			return res
		except Exception as e:
			return render_template("default_error.html.jinja", status_code = 500, message = e), 500
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

from app import api_v1

app.register_blueprint(api_v1.api_v1_bp, url_prefix="/api_v1")

from app import admin_area

app.register_blueprint(admin_area.admin_area, url_prefix=os.getenv("ADMIN_PATH"))

from app import spotify_stuff

app.register_blueprint(spotify_stuff.spotify_routes, url_prefix="/spotify")