import os
from datetime import datetime, timedelta
from app import app, db, google, loginman
from app.schema import User
from flask import Flask, redirect, url_for, session, request, render_template, flash, jsonify, Blueprint
from authlib.integrations.flask_client import OAuth, OAuthError
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user



# THIS NEEDS TO BE DONE BY BUTTONS ON THE LOGIN SCREEN
@app.route("/login")
def login():
	if current_user.is_authenticated:
		return redirect(url_for("profile"))
	session['nonce'] = "" # WARN: what is this lol
	return render_template("login_page.html.jinja", google_login_url=url_for("login_google_redirect"))

@app.route("/login_google_redirect")
def login_google_redirect():
	if current_user.is_authenticated:
		return redirect(url_for("profile"))
	return google.authorize_redirect(redirect_uri=url_for("google_auth", _external=True, _scheme=app.config['PREFERRED_URL_SCHEME']))

# @app.route("/login/github")
# def login_github():
#     return github.authorize_redirect(redirect_uri=url_for("auth_github", _external=True))

@app.route("/google_auth")
def google_auth():
	try:
		token = google.authorize_access_token()
	except OAuthError as e:
		flash("There was an issue logging in.", "error")
		#print(f"login issue {e}")
		return redirect(url_for("index"))
	user_info = google.parse_id_token(token, nonce="")
	# Create or retrieve the user
	user = User.query.filter_by(google_id=user_info["sub"]).first()
	if not user:
		user = User.query.filter_by(email=user_info["email"]).first()
		if not user:
			# print(user_info)
			user = User(username=user_info.get("given_name") or user_info.get("name") or user_info["email"].split('@')[0])
			user.email = user_info["email"]
			user.google_id = user_info["sub"]
	prev = user.last_login_date
	user.last_login_date = datetime.utcnow()
	db.session.add(user)
	db.session.commit()
	login_user(user)
	if prev:
		return redirect(url_for("profile"))
	else:
		flash("Update your username!")
		return redirect(url_for("update_profile"))

@app.route("/check-username", methods=["GET"])
def check_username():
	username = request.args.get('username').strip()
	if not username:
		return jsonify({'error': 'Username is required'}), 400
	# Query the database for the username
	user_exists = db.session.query(User).filter_by(username=username).first() is not None
	if user_exists:
		return jsonify({'available': False}), 200
	else:
		return jsonify({'available': True}), 200

@app.route("/profile")
@app.route("/<string:username>/profile")
def profile(username:str = None):
	if not username and current_user.is_authenticated:
		return render_template("profile.html.jinja")
	else:
		user = User.get_user_by_name(username)
		if not user: return "Not found", 404
		else: return render_template("profile.html.jinja", user=user)


@app.route("/profile/update", methods=["GET", "POST"])
@login_required
def update_profile():
	if request.method == "POST":
		new_username = request.form.get("username", "").strip()
		if not new_username:
			flash("Username cannot be empty.", "error")
			return render_template("edit_profile.html.jinja")

		if User.query.filter_by(username=new_username).count() > 0:
			flash("Username is currently in use, please choose another one.", "error")
			return render_template("edit_profile.html.jinja")

		if new_username == current_user.username:
			flash("New username must be different from the current one.", "warning")
			return render_template("edit_profile.html.jinja")
	
		if current_user.username_last_updated and (datetime.utcnow() - current_user.username_last_updated) < timedelta(hours=24):
			flash(f"Username was updated in the past 24hrs, please wait before trying again.", "error")
			return render_template("edit_profile.html.jinja")

		# Update username
		current_user.username = new_username
		current_user.username_last_updated = datetime.utcnow()
		db.session.commit()
		flash("Username updated successfully", "success")
		return redirect(url_for("profile"))  # Redirect only on success

	# Render the update form for GET requests
	return render_template("edit_profile.html.jinja")

# @app.route('/<string:username>/sprite', methods=["GET"])
# def get_user_sprite_username (username:str):
# 	user = User.get_user_by_name(username)
# 	if not user: return 'User not found', 404
# 	return jsonify({'username':user.username, 'sprite':user.image_token}), 200
	

# @app.route('/<int:userid>/sprite', methods=["GET"])
# def get_user_sprite_id (userID:int):
# 	user = User.get_user_by_id(userID)
# 	if not user: return 'User not found', 404
# 	return jsonify({'username':user.username, 'sprite':user.image_token}), 200


# @app.route("/auth/github")
# def auth_github():
# 	token = github.authorize_access_token()
# 	user_info = github.get("user").json()

# 	# Create or retrieve the user
# 	user = users.get(user_info['login'])
# 	if not user:
# 		user = User(id=user_info['login'], email=user_info['email'])
# 		users[user.id] = user

# 	login_user(user)
# 	return redirect(url_for("index"))

@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for("index"))
