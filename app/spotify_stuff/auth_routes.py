import random, base64, requests
from datetime import datetime, timedelta
from .. import schema, app, db
from . import spotify_routes, enforce_check_wilt_enabled
from flask import jsonify, request, Response, render_template, url_for, session, flash, redirect
from flask_login import login_required, current_user


def get_auth_route ():
	""" Get the auth route for Spotify
	"""
	state_val = str(random.randint(0, 1000000000))
	query_params = {
		"response_type": "code",
		"client_id": app.config["spotify_client_id"],
		"scope" : 'user-read-private user-read-currently-playing user-read-email',
		"redirect_uri": url_for("spotify_routes.spotify_callback", _external=True),
		"state": state_val
	}
	base_url = "https://accounts.spotify.com/authorize?"
	session["state"] = state_val
	return base_url + "&".join([f"{key}={value}" for key, value in query_params.items()])


@spotify_routes.route("/register")
@login_required
@enforce_check_wilt_enabled
def spotify_register():
	""" Register a user with Spotify
	"""
	if current_user.spotify_token \
		and current_user.spotify_token.refresh_token \
		and current_user.spotify_token.expired == False:
		flash("Spotify account already linked", "info")
		return redirect(url_for("profile"))
	return render_template("spotify_stuff/spotify_stuff.html.jinja", auth_url=get_auth_route())

@spotify_routes.route("/callback")
@login_required
@enforce_check_wilt_enabled
def spotify_callback():
	if "error" in request.args.keys():
		return render_template("default_error.html.jinja", status_code = 403, message = f"Unauthorized: {request.args.get('error')}"), 403#
	if request.args.get("state") != session.get("state"):
		return render_template("default_error.html.jinja", status_code = 403, message = "Unauthorized: State value mismatch"), 403
	code = request.args.get("code")
	# Get the token
	# check if user already has a spotify token record:
	token = schema.SpotifyToken.query.filter_by(user_id=current_user.id).first()
	if not token:
		token = schema.SpotifyToken(user_id = current_user.id)
	
	body = {
		"grant_type": "authorization_code",
		"code": code,
		"redirect_uri": url_for("spotify_routes.spotify_callback", _external=True),
	}

	credentails = app.config["spotify_client_id"] + ":" + app.config["spotify_client_secret"]
	headers = {
		"Authorization": "Basic " + base64.b64encode(credentails.encode()).decode(),
		"Content-Type": "application/x-www-form-urlencoded"
	}

	url = "https://accounts.spotify.com/api/token"
	response = requests.post(url, headers=headers, data=body)
	if response.status_code != 200:
		return render_template("default_error.html.jinja", status_code = 403, message = "Unauthorized"), 403
	
	access_token = response.json().get("access_token")
	refresh_token = response.json().get("refresh_token")
	expires_in = response.json().get("expires_in")
	if refresh_token is None or access_token is None or expires_in is None:
		return render_template("default_error.html.jinja", status_code = 403, message = "Unauthorized"), 403
	
	token.access_token = access_token
	token.refresh_token = refresh_token
	token.access_expires = datetime.utcnow() + timedelta(seconds=expires_in)
	token.updated_at = datetime.utcnow()
	db.session.add(token)
	db.session.commit()
	flash("Spotify account linked successfully", "info")
	return redirect(url_for("profile"))
