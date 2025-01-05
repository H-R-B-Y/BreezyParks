import os
import json
from datetime import datetime, timedelta
from app import app, db, google, loginman, socketio, zetaSocketIO, require_admin, write_to_extra, schema, render_page_failsafe
from app.jinja_template_addons import get_likes_for_x, user_liked_x
from app.schema import User, ThingPost, Comment, BlogPost, Like
from sqlalchemy import desc, asc
from flask import render_template, flash, redirect, url_for, request, jsonify
from authlib.integrations.flask_client import OAuth
from flask_login import login_required, current_user

socketio.on_namespace(zetaSocketIO.zeta("/zeta/"))
@app.route("/")
def index():
	"""
	Index page.
	"""
	return render_template("index.html.jinja")

@app.route("/wip/")
def workinprogress():
	"""
	Work in progress page.
	"""
	return render_template("workinprogress.html.jinja")

@app.route("/secret_set/<string:key>/<string:value>")
@login_required
@require_admin
def secret_set(key : str, value : str):
	"""
	Set extra data.
	"""
	write_to_extra(key, value)
	flash(f"Set {key} to {value} successfully!")
	return redirect(url_for("index")), 200

@app.route("/flashme/<string:text>")
@app.route("/flashme/<string:text>/<string:flash_type>")
def flashme(text = "", flash_type = ""):
	"""
	DEBUG: Flash a message.
	"""
	flash(text, flash_type)
	return redirect(url_for("index"))

@app.route("/things")
def things_index():
	"""
	Display the things index.
	"""
	return render_template("things/index.html.jinja")

@app.route("/thing_pages")
def thing_pages():
	"""
	Get a list of thing posts.
	returns:
		- status: ok/error
		- data: list of posts
		- page: page number
		- last_page: true/false
	"""
	page = int(request.args.get('page',1))
	if (page < 1):
		return jsonify({"status":"error", "message":"Page doesn't exist"}), 404
	per_page = 6
	start = (page - 1) * per_page
	end = start + per_page
	things = ThingPost.query.order_by(desc(ThingPost.created_date)).all()
	data = [{"id":x.id, "title": x.title, "path":"/thing/"+str(x.id)} for x in things[start:end]]
	return jsonify({
			"status":"ok",
			"data":data,
			"page":page,
			"last_page": True if end >= len(things) else False,})

@app.route("/thing/<int:id>")
@render_page_failsafe
def thing_id(id):
	"""
	Display a thing.
	returns:
		- redirect: if the thing is a URL
		- render_template: if the thing is a template
		- 404: if the thing is not found
	"""
	thing = ThingPost.query.filter_by(id=id).first()
	if not thing:
		return jsonify({"status":"error", "message":"That page doesn't exist"}), 404
	if thing.type == "url":
		return redirect(url_for(thing.url_for))
	elif thing.type == "template":
		return render_template(thing.template_path, thing_id=id, thing=thing)
	else:
		return jsonify({"status":"error","status":"Internal error"}), 500
	
@app.route("/posts")
def posts_index():
	"""
	Display the blog posts index.
	"""
	return render_template("posts/index.html.jinja")

@app.route("/post_pages")
def post_pages():
	"""
	Get a page of blog posts.
	returns:
		- status: ok/error
		- data: list of posts
		- page: page number
		- last_page: true/false
	"""
	page = int(request.args.get('page',1))
	if (page < 1):
		return jsonify({"status":"error", "message":"Page doesn't exist"}), 404
	per_page = 6
	start = (page - 1) * per_page
	end = start + per_page
	things = BlogPost.query.order_by(desc(BlogPost.created_date)).all()
	data = [{"id":x.id, "title": x.title, "path":"/thing/"+str(x.id)} for x in things[start:end]]
	return jsonify({
			"status":"ok",
			"data":data,
			"page":page,
			"last_page": True if end >= len(things) else False,})


@app.route("/post/<int:id>")
@render_page_failsafe
def post_id(id):
	"""
	Display a blog post.
	"""
	thing = BlogPost.query.filter_by(id = id).first()
	if not thing:
		return jsonify({"status":"error","message":"That post doesn't exist"}), 404
	return render_template("posts/default.html.jinja", post=thing)


@app.route("/like/<string:type>/<int:id>", methods=["POST"])
@login_required
def like_something(type, id):
	"""
	Like something.
	returns:
		- status: ok/error
		- state: liked/unliked
		- count: count of likes
	"""
	table = {"blog_post": schema.BlogPost,
		"comment": schema.Comment,
		"thing": schema.ThingPost,
		"profile": schema.User}
	if "profile" == type and id == current_user.id:
		return jsonify({"status":"ok", "state":"unliked"}), 200
	if not type or id == None or type not in table.keys():
		return jsonify({"status":"error", "message":"insufficient information"}), 400
	table_ref = table.get(type, None)
	item_ref = table_ref.query.get(id)
	if not item_ref:
		return jsonify({"status":"error", "message":"refrenced item does not exist"}), 404
	# check if a like record exists
	like = schema.Like.query.filter_by(user_id=current_user.id,target_type=type,target_id=id).first()
	if like:
		db.session.delete(like)
		db.session.commit()
		return jsonify({"status":"ok", "state":"unliked", "count":get_likes_for_x(type, id)}), 200
	new_like = schema.Like(user_id=current_user.id, target_type=type, target_id=id)
	db.session.add(new_like)
	db.session.commit()
	return jsonify({"status":"ok", "state":"liked", "count":get_likes_for_x(type, id)}), 200

@app.route("/post_comment", methods=["POST"])
@login_required 
def post_a_comment():
	"""
	Post a comment to something.
	returns:
		- status: ok/error
		- message: message if error
	"""
	if current_user.can_comment is False:
		return jsonify({"status":"error", "message":"You are banned from commenting."}), 200
	if Comment.query.filter_by(user_id = current_user.id).filter(Comment.created_date >= (datetime.utcnow() - timedelta(minutes = 10))).count() > 10:
		return jsonify({"status":"error", "message":"Too many recent comments."}), 200
	if Comment.query.filter_by(user_id = current_user.id).filter(Comment.created_date >= (datetime.utcnow() - timedelta(days = 1))).count() > 1000:
		current_user.can_comment = False
		db.session.commit()
		return jsonify({"status":"error", "message":"You have been comment banned (rate limit exceeded)."}), 200
	comment_body = request.form.get('comment_body')
	comment_on_type = request.form.get('comment_on_type')
	comment_on_id = request.form.get('comment_on_id')
	# Validate the form data
	if not comment_body or not comment_on_type or not comment_on_id or comment_on_type not in ('blog_post','comment','thing'):
		return jsonify({'status': 'error', 'message': 'Missing required fields'}), 200
	new_comment = Comment(user_id = current_user.id,
						target_type = comment_on_type,
						target_id = comment_on_id,
						body = comment_body,
						is_reply = False if comment_on_type != "comment" else True)
	db.session.add(new_comment)
	db.session.commit()
	return jsonify({'status': 'ok'})

@app.route("/get_comments")
def load_more_comments():
	"""
	Load more comments for a page or comment.
	returns:
		- status: ok/error
		- data: list of comments
		- page: page number
		- last_page: true/false
	"""
	page_to_load = int(request.args.get('page',1))
	page_type = request.args.get("page_type", None)
	comments_for = request.args.get("comment_on_type", None)
	comments_for_id = request.args.get("comment_on_id", None)
	if not page_type or page_to_load < 1 or not comments_for:
		return jsonify({"status":"error", "message":"Page doesn't exist"}), 404
	per_page = 6
	start = (page_to_load - 1) * per_page
	end = start + per_page
	comments = Comment.query.filter_by(target_type=comments_for, target_id=comments_for_id).order_by(asc(Comment.created_date)).all()
	data = [{"id":x.id, "user": x.user_id, "username": x.user.username, "body":x.body} for x in comments[start:end]]
	return jsonify({
			"status":"ok",
			"data":data,
			"page":page_to_load,
			"last_page": True if end >= len(comments) else False,})

@app.route("/get_user_by_id")
def get_user_by_id_route():
	"""
	Get a user by their ID.
	returns:
		- status: ok/error
		- user_id: id of the user
		- username: username
	"""
	userid = int(request.args.get('user_id', 1))
	user = User.query.filter(id = userid).first()
	if not user:
		return jsonify({"status":"error", "message":"User not found."}), 404
	return jsonify({"status":"ok", "user_id":user.id, "username":user.username}), 200

@app.route("/likes_for_x")
def likes_for_x():
	"""
	Get the likes for something.
	returns:
		- status: ok/error
		- data: count of likes
		- liked_by_you: true/false
	"""
	
	type_of = request.args.get('page_type', None)
	if_of = int(request.args.get('page_id', -1))
	if type_of not in ["comment","blog_post","thing","profile"] or if_of < 0:
		return jsonify({"status":"error", "message":"Invalid request."}), 404
	likes = get_likes_for_x(type_of, if_of) or 0
	user_liked_this = False
	if current_user.is_authenticated:
		user_liked_this = user_liked_x(current_user.id, "comment", if_of)
	return jsonify({"status":"ok", "data":likes, "liked_by_you":user_liked_this})

@app.route("/x_has_replies")
def x_has_replies():
	"""
	Checks if a comment has replies.
	returns:
		- status: ok/error
		- data: count of likes
	"""
	type_of = request.args.get('page_type', None)
	if_of = int(request.args.get('page_id', -1))
	if type_of not in ["comment","blog_post","thing"] or if_of < 0:
		return jsonify({"status":"error", "message":"Invalid request."}), 404
	likes = Comment.query.filter_by(target_type=type_of, target_id=if_of).count() or 0
	return jsonify({"status":"ok", "data":likes})