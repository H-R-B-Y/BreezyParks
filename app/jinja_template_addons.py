from app import app, db, get_extra_data, schema
from app.schema import User, Like, Comment
from flask import request
from sqlalchemy import desc
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
		target_id = id).order_by(desc(Comment.created_date)).all()

app.jinja_env.globals.update(getComments = get_comments)

def user_liked_x(user_id : int , type : str, id : int):
	if user_id is None or type is None or id is None:
		return False
	else:
		table = {"blog_post": schema.BlogPost,
		"comment": schema.Comment,
		"thing": schema.ThingPost,
		"profile": schema.User}
		if type not in table.keys():
			return False
		like = Like.query.filter_by(
			target_type = type,
			target_id = id,
			user_id = user_id
		).first()
		if like:
			return True
	return False

app.jinja_env.globals.update(UserLikedThis = user_liked_x)

def comment_has_replies(comment_id : int):
	if comment_id is None:
		return False
	count = Comment.query.filter_by(
		target_type = "comment",
		is_reply = 1,
		target_id = comment_id).count()
	return True if count > 0 else False

app.jinja_env.globals.update(CommentHasReplies = comment_has_replies)

# def get_replies_to_comment(comment_id : int):
# 	if comment_id is None:
# 		return []
# 	replies = Comment.query.filter_by(
# 		target_type = "comment",
# 		is_reply = 1,
# 		target_id = comment_id).all()
# 	return replies or []

# app.jinja_env.globals.update(GetRepliesToComment = get_replies_to_comment)