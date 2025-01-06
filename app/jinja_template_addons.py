from app import app, db, get_extra_data, schema
from app.schema import User, Like, Comment
from app.paper_note_routes import user_can_note
from flask import request
from sqlalchemy import desc, asc
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

def get_username(currentUser : User):
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

def get_likes_for_x(type : str, id : int):
	table = {"blog_post": schema.BlogPost,
		"comment": schema.Comment,
		"thing": schema.ThingPost,
		"profile": schema.User}
	if type not in table.keys():
		return None
	return Like.query.filter_by(
		target_type = type,
		target_id = id).count()

app.jinja_env.globals.update(getLikesForX = get_likes_for_x)

def get_comments(type : str, id : int, page : int = 1):
	table = {"blog_post": schema.BlogPost,
		"comment": schema.Comment,
		"thing": schema.ThingPost}
	if type not in table.keys():
		return []
	table = table[type]
	if table.query.filter_by(id=id).first() is None:
		return []
	per_page = 5
	start = (page - 1) * per_page
	end = start + per_page
	comment = schema.Comment.query.filter_by(
		target_type=type,
		target_id = id).order_by(asc(Comment.created_date)).all()[start : end]
	return comment

app.jinja_env.globals.update(getComments = get_comments)

def user_liked_x(user_id : int , type : str, id : int):
	# print(f"{user_id} {type} {id}")
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

app.jinja_env.globals.update(UserCanNote = user_can_note)

def get_comment_proto():
	return Comment.comment_proto()

app.jinja_env.globals.update(GetCommentProto = get_comment_proto)


def get_current_playing_track(user : schema.User):
	if not user or not user.is_authenticated:
		return None
	if not user.spotify_token or not user.wilt_enabled:
		return None
	if user.spotify_token.expired:
		if not user.spotify_token.refresh_my_token():
			return None
	track = user.spotify_token.current_track_info
	if not track or isinstance(track, dict) == False:
		return None
	return track

app.jinja_env.globals.update(GetCurrentPlayingTrack = get_current_playing_track)

def get_current_playing_track_uri(user : schema.User):
	track = get_current_playing_track(user)
	if not track:
		return None
	device = track.get("device")
	if track.get("is_playing") == False:
		return None
	if device:
		if device.get("is_active") == False or device.get("is_private_session") == True:
			return None
	track_item = track.get("item")
	if not track_item:
		return None
	track_type = track.get("current_playing_type") or track_item.get("type")
	if not track_type:
		return None
	if track_type == "track":
		return track_item.get("uri")
	if track_type == "episode":
		return track_item.get("uri")
	return None

app.jinja_env.globals.update(GetCurrentPlayingTrackUri = get_current_playing_track_uri)


# def get_replies_to_comment(comment_id : int):
# 	if comment_id is None:
# 		return []
# 	replies = Comment.query.filter_by(
# 		target_type = "comment",
# 		is_reply = 1,
# 		target_id = comment_id).all()
# 	return replies or []

# app.jinja_env.globals.update(GetRepliesToComment = get_replies_to_comment)