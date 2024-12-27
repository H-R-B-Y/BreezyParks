import bcrypt
import json
from datetime import datetime
from sqlalchemy import (
	BLOB, Column, Integer, String, Boolean, Text, ForeignKey,
	DateTime, UniqueConstraint, CheckConstraint, desc
)
from app import db
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# so autocomplete works
db : SQLAlchemy = db

class User(UserMixin, db.Model):
	__tablename__ = 'users'

	id = db.Column(Integer, primary_key=True, autoincrement=True)
	username = db.Column(String, nullable=False, unique=True)
	password_hash = db.Column(String)
	is_admin = db.Column(Boolean, default=False)
	created_date = db.Column(DateTime, default=datetime.utcnow())
	last_login_date = db.Column(DateTime)
	email = db.Column(String, nullable=False, unique=True)
	google_id = db.Column(String, unique=True)
	github_id = db.Column(String, unique=True)
	username_last_updated = db.Column(DateTime)

	likes = db.relationship("Like", back_populates="user", cascade="all, delete-orphan")
	comments = db.relationship("Comment", back_populates="user", cascade="all, delete-orphan")

	# def set_password (self, password) -> None :  
	# 	""" Sets the passowrd for the current instance
		
	# 	Keyword arguments:
	# 	password -- the unencrypted password.
	# 	Return: None
	# 	"""
	# 	self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

	# def check_password(self, password) -> bool:
	# 	""" Checks an unhashed password against the hashed password stored on user
		
	# 	Keyword arguments:
	# 	password - the unhashed password you would like to check.
	# 	Return: bool
	# 	"""
	# 	return bcrypt.checkpw(password.encode('utf-8'), self.password_hash)

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

	CheckConstraint("body IS NOT NULL OR path_to_body IS NOT NULL", name="check_body_or_path")


class ThingPost(db.Model):
	__tablename__ = 'thing_posts'

	id = Column(Integer, primary_key=True, autoincrement=True)
	title = Column(Text, nullable=False)
	template_path = Column(Text)
	type = Column(Text)
	url_for = Column(Text)
	created_date = Column(DateTime, nullable=False, default=datetime.utcnow())


class Comment(db.Model):
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
		target_type = ['blog_post', 'comment', 'thing'][[BlogPost, Comment, ThingPost, User].index(type(target))]
		likes = cls.query.filter_by(target_type=target_type, target_id=target.id).order_by(desc(cls.created_date)).all()
		return (likes)

	def get_replies(self):
		my_replies = Comment.query.filter_by(target_type="comment", target_id=self.id)\
			.order_by(desc(Comment.created_date)).all()
		return my_replies


class Like(db.Model):
	__tablename__ = 'likes'

	id = Column(Integer, primary_key=True, autoincrement=True)
	user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
	target_type = Column(String, nullable=False)
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
	type = Column(Integer, CheckConstraint('type IN (0, 1)'), nullable=False)


class AccessToken(db.Model):
	__tablename__ = 'access_tokens'

	id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
	token = Column(Text, nullable=False)

