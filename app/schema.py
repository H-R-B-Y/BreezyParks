import bcrypt
import json
import base64
import requests
from datetime import datetime, timedelta
from sqlalchemy import (
	BLOB, Column, Integer, String, Boolean, Text, ForeignKey,
	DateTime, UniqueConstraint, CheckConstraint, desc
)
from app import db, app
from flask import url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, current_user
from functools import wraps

# so autocomplete works
db : SQLAlchemy = db

class User(UserMixin, db.Model):
	__tablename__ = 'users'

	id = db.Column(Integer, primary_key=True, autoincrement=True)
	username = db.Column(String(255), nullable=False, unique=True)
	password_hash = db.Column(Text)
	is_admin = db.Column(Boolean, default=False)
	created_date = db.Column(DateTime, default=datetime.utcnow())
	last_login_date = db.Column(DateTime)
	email = db.Column(Text, nullable=False, unique=True)
	google_id = db.Column(String(255), unique=True)
	github_id = db.Column(String(255), unique=True)
	username_last_updated = db.Column(DateTime)

	can_comment = db.Column(Boolean, default=True)
	wilt_enabled = db.Column(Boolean, default=False)

	likes = db.relationship("Like", back_populates="user", cascade="all, delete-orphan")
	comments = db.relationship("Comment", back_populates="user", cascade="all, delete-orphan")
	spotify_token = db.relationship("SpotifyToken",  uselist=False, back_populates="user", cascade="all, delete-orphan")

	@classmethod
	def get_user_by_name(cls, name):
		""" Gets a user from a given username
		
		Keyword arguments:
		name -- username
		Return: schema.user if found else None
		"""
		user = User.query.filter_by(username=name).first()
		if user:
			return user
		else: return None

	@classmethod
	def get_user_by_id(cls, user_id):
		return cls.query.get(user_id)


class BlogPost(db.Model):
	__tablename__ = 'blog_posts'

	id = db.Column(Integer, primary_key=True, autoincrement=True)
	title = db.Column(Text, nullable=False)
	body = db.Column(Text)
	path_to_body = db.Column(Text)
	created_date = db.Column(DateTime, default=datetime.utcnow())
	modified_date = db.Column(DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow())
	status = db.Column(Text, CheckConstraint("status IN ('draft', 'published', 'deleted')"), default='draft')

	CheckConstraint("body IS NOT NULL OR path_to_body IS NOT NULL", name="check_body_or_path")

	@property
	def likes(self):
		return Like.likes_for(self)


class ThingPost(db.Model):
	__tablename__ = 'thing_posts'

	id = Column(Integer, primary_key=True, autoincrement=True)
	title = Column(Text, nullable=False)
	template_path = Column(Text)
	type = Column(Text)
	url_for = Column(Text)
	created_date = Column(DateTime, nullable=False, default=datetime.utcnow())

	@property
	def likes(self):
		return Like.likes_for(self)


class Comment(db.Model):
	class comment_proto:
		proto = True
		user_id = "${userid}"
		username = "${username}"
		body = "${comment_body}"
		isreply = "${isreply}"
		id = "${id}"
	
	__tablename__ = 'comments'

	id = db.Column(Integer, primary_key=True, autoincrement=True)
	user_id = db.Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
	target_type = db.Column(Text, CheckConstraint("target_type IN ('blog_post','comment','thing')"), nullable=False)
	target_id = db.Column(Integer, nullable=False)
	is_reply = db.Column(Boolean, default=False)
	body = db.Column(Text, nullable=False)
	created_date = db.Column(DateTime, default=datetime.utcnow())

	user = db.relationship("User", back_populates="comments")
	UniqueConstraint('user_id', 'target_type', 'target_id')

	@classmethod
	def comments_for(cls, target = None):
		if (target == None or not type(target) in [BlogPost, Comment, ThingPost]):
			return None
		target_type = ['blog_post', 'comment', 'thing'][[BlogPost, Comment, ThingPost].index(type(target))]
		likes = cls.query.filter_by(target_type=target_type, target_id=target.id).order_by(desc(cls.created_date)).all()
		return (likes)

	def get_replies(self):
		my_replies = Comment.query.filter_by(target_type="comment", target_id=self.id)\
			.order_by(desc(Comment.created_date)).all()
		return my_replies
	
	@property
	def likes(self):
		return Like.likes_for(self)
	
	@property
	def username(self):
		return self.user.username


class Like(db.Model):
	__tablename__ = 'likes'

	id = Column(Integer, primary_key=True, autoincrement=True)
	user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
	target_type = Column(String(128), nullable=False)
	target_id = Column(Integer, nullable=False)
	created_date = Column(DateTime, default=datetime.utcnow())

	user = db.relationship("User", back_populates="likes")
	UniqueConstraint('user_id','target_type','target_id', name='unique_case')

	@classmethod
	def likes_for(cls, target = None):
		if (target == None or not type(target) in [BlogPost, Comment, ThingPost, User]):
			return None
		target_type = ['blog_post', 'comment', 'thing', 'profile'][[BlogPost, Comment, ThingPost, User].index(type(target))]
		likes = cls.query.filter_by(target_type=target_type, target_id=target.id).order_by(desc(cls.created_date)).all()
		return (likes)


class PaperNote(db.Model):
	__tablename__ = 'paper_notes'

	id = Column(Integer, primary_key=True, autoincrement=True)
	user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
	data = Column(BLOB, nullable=True)
	text = Column(Text, nullable=True)
	created_date = Column(DateTime, default=datetime.utcnow())
	status = Column(Text, CheckConstraint("status IN ('pending', 'completed', 'deleted')"), default='pending')
	type = Column(Integer, CheckConstraint('type IN (0, 1)'), nullable=False)


class AccessToken(db.Model):
	__tablename__ = 'access_tokens'

	id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
	token = Column(Text, nullable=False)
	token_name = Column(Text, nullable=True)


class SpotifyToken(db.Model):
	__tablename__ = 'spotify_tokens'

	id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
	access_token = Column(Text, nullable=False)
	refresh_token = Column(Text, nullable=False)
	access_expires = Column(DateTime, nullable=False)
	user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
	updated_at = Column(DateTime, default=datetime.utcnow())

	user = db.relationship("User", back_populates="spotify_token")

	def make_spotify_request(self, url, method="GET", body=None, headers=None):
		if headers is None:
			headers = {}
		if body is None:
			body = {}
		if self.access_expires < datetime.utcnow():
			if not self.refresh_my_token():
				return {"error": "Unauthorized"}, 401
		headers["Authorization"] = "Bearer " + self.access_token
		if method == "GET":
			response = requests.get(url, headers=headers)
		elif method == "POST":
			response = requests.post(url, headers=headers, data=body)
		elif method == "PUT":
			response = requests.put(url, headers=headers, data=body)
		elif method == "DELETE":
			response = requests.delete(url, headers=headers)
		else:
			return {"error": "Invalid method"}, 400
		if response.status_code != 200:
			return {"error": "Failed to make request"}, 500
		json = response.json()
		if json.get("error"):
			return {"error": json.get("error")}, 400
		if json.get("refresh_token"):
			self.refresh_token = json.get("refresh_token")
			db.session.add(self)
			db.session.commit()
		return json

	@property
	def expired(self):
		return self.access_expires < datetime.utcnow()
	
	@property
	def current_track_info(self):
		if self.expired:
			if not self.refresh_token():
				return None
		url = "https://api.spotify.com/v1/me/player/currently-playing"
		data = self.make_spotify_request(url)
		return data

	def refresh_my_token(self):
		if self.refresh_token is None:
			if current_user:
				flash(f" It appears we cannot authenticate your spotify account. Please re-link spotify here {url_for('spotify_routes.spotify_register')}", "error")
			return False
		credentails = app.config["spotify_client_id"] + ":" + app.config["spotify_client_secret"]
		headers = {
			"Authorization": "Basic " + base64.b64encode(credentails.encode()).decode(),
			"Content-Type": "application/x-www-form-urlencoded"
		}
		body = {
			"grant_type": "refresh_token",
			"refresh_token": self.refresh_token
		}
		url = "https://accounts.spotify.com/api/token"
		response = requests.post(url, headers=headers, data=body)
		if response.status_code != 200:
			print("Failed to refresh token")
			return False
		self.access_token = response.json().get("access_token")
		refresh_token = response.json().get("refresh_token")
		self.refresh_token = refresh_token if refresh_token else self.refresh_token
		self.access_expires = datetime.utcnow() + timedelta(seconds=response.json().get("expires_in"))
		self.updated_at = datetime.utcnow()
		db.session.add(self)
		db.session.commit()
		return True

	@staticmethod
	def validate_access(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			if not current_user.is_authenticated or not current_user.wilt_enabled:
				return {"error": "Unauthorized"}, 401
			if not current_user.spotify_token:
				return url_for("spotify_routes.spotify_register")
			if current_user.spotify_token.access_expires < datetime.utcnow():
				if not current_user.spotify_token.refresh_my_token():
					return {"error": "Unauthorized"}, 401
			return func(*args, **kwargs)
		return wrapper
	
	def __repr__(self):
		return f"<SpotifyToken {self.id}>"


"""
def set_password (self, password) -> None :  
	Sets the passowrd for the current instance
	
	Keyword arguments:
	password -- the unencrypted password.
	Return: None
	
	self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(self, password) -> bool:
	Checks an unhashed password against the hashed password stored on user
	
	Keyword arguments:
	password - the unhashed password you would like to check.
	Return: bool
	
	return bcrypt.checkpw(password.encode('utf-8'), self.password_hash)

"""
