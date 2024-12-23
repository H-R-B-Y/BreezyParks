from app import app, db, get_extra_data, schema
from app.schema import User, Like
from flask import request
import datetime
import random
import os, json

def rndid():
	return random.randint(1,1000)

app.jinja_env.globals.update(rndId = rndid)
app.jinja_env.globals.update(conf = app.config)
app.jinja_env.globals.update(getExtraData = get_extra_data)

# Need this for later.
# from app.schema import User
# # return username or none

def get_username (currentUser : User):
	if not currentUser or not currentUser.is_authenticated:
		return None
	return currentUser.username

app.jinja_env.globals.update(getUsername = get_username)

app.jinja_env.globals.update(Users = User)

def get_users_liked_count(username : str):
	if not username:
		return None
	user = User.query.filter_by(username=username).first()
	if not user:
		return None
	likes = Like.query.filter_by(user_id = user.id)
	return [likes.filter_by(target_type = "blog_post").count(), likes.filter_by(target_type = "comment").count()]

app.jinja_env.globals.update(getUserLikedCount = get_users_liked_count)

def get_comments(type : str, id : int):
	table = {"blog_post": schema.BlogPost,
		"comment": schema.Comment,
		"thing": schema.ThingPost}
	if type not in table.keys():
		return []
	table = table[type]
	if table.query.filter_by(id=id).first() is None:
		return []
	return schema.Comment.query.filter_by(
		target_type=type,
		target_id = id).all()

app.jinja_env.globals.update(getComments = get_comments)