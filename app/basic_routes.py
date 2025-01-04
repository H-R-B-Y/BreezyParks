import os
import json
from datetime import datetime, timedelta
from app import app, db, google, loginman, socketio, zetaSocketIO, require_admin, write_to_extra, schema
from app.jinja_template_addons import get_likes_for_x, user_liked_x
from app.schema import User, ThingPost, Comment, BlogPost, Like
from sqlalchemy import desc, asc
from flask import render_template, flash, redirect, url_for, request, jsonify
from authlib.integrations.flask_client import OAuth
from flask_login import login_required, current_user

socketio.on_namespace(zetaSocketIO.zeta("/zeta/"))
@app.route("/")
def index():
	return render_template("index.html.jinja")

@app.route("/wip/")
def workinprogress():
	return render_template("workinprogress.html.jinja")

@app.route("/secret_set/<string:key>/<string:value>")
@login_required
@require_admin
def secret_set(key : str, value : str):
	write_to_extra(key, value)
	return f"Set {key} to {value} successfully!"

@app.route("/flashme/<string:text>")
@app.route("/flashme/<string:text>/<string:flash_type>")
def flashme(text = "", flash_type = ""):
	flash(text, flash_type)
	return redirect(url_for("index"))

@app.route("/things")
def things_index():
	return render_template("things/index.html.jinja")

@app.route("/thing_pages")
def thing_pages():
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
def thing_id(id):
	thing = ThingPost.query.filter_by(id=id).first()
	if not thing:
		return "Thing not found", 404
	if thing.type == "url":
		return redirect(url_for(thing.url_for))
	elif thing.type == "template":
		return render_template(thing.template_path, thing_id=id, thing=thing)
	else:
		return "Something went wrong", 404
	
@app.route("/posts")
def posts_index():
	return render_template("posts/index.html.jinja")

@app.route("/post_pages")
def post_pages():
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
def post_id(id):
	thing = BlogPost.query.filter_by(id = id).first()
	if not thing:
		return "Thing not found", 404
	return render_template("posts/default.html.jinja", post=thing)

'''
Like something to be called by like buttons, like buttons must provide ID and Type
'''
@app.route("/like/<string:type>/<int:id>", methods=["POST"])
@login_required
def like_something(type, id):
	table = {"blog_post": schema.BlogPost,
		"comment": schema.Comment,
		"thing": schema.ThingPost,
		"profile": schema.User}
	if "profile" == type and id == current_user.id:
		return jsonify({"state":"unliked"}), 200
	if not type or id == None or type not in table.keys():
		return "Not found", 404
	table_ref = table.get(type, None)
	item_ref = table_ref.query.filter_by(id=id).first()
	if not item_ref:
		return "Not found", 404
	# check if a like record exists
	like = schema.Like.query.filter_by(user_id=current_user.id,target_type=type,target_id=id).first()
	if like:
		db.session.delete(like)
		db.session.commit()
		return jsonify({"state":"unliked", "count":get_likes_for_x(type, id)}), 200
	new_like = schema.Like(user_id=current_user.id, target_type=type, target_id=id)
	db.session.add(new_like)
	db.session.commit()
	return jsonify({"state":"liked", "count":get_likes_for_x(type, id)}), 200

@app.route("/post_comment", methods=["POST"])
@login_required 
def post_a_comment():
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
	page_to_load = int(request.args.get('page',1))
	page_type = request.args.get("page_type", None)
	comments_for = request.args.get("comment_on_type", None)
	comments_for_id = request.args.get("comment_on_id", None)
	if not page_type or page_to_load < 1 or not comments_for:
		return jsonify({"status":"error", "message":"Page doesn't exist"}), 404
	per_page = 5
	start = (page_to_load - 1) * per_page
	end = start + per_page
	things = Comment.query.filter_by(target_type=comments_for, target_id=comments_for_id).order_by(asc(Comment.created_date)).all()
	data = [{"id":x.id, "user": x.user_id, "username": User.query.filter_by(id=x.user_id).first().username, "body":x.body} for x in things[start:end]]
	return jsonify({
			"status":"ok",
			"data":data,
			"page":page_to_load,
			"last_page": True if end >= len(things) else False,})

@app.route("/get_user_by_id")
def get_user_by_id_route():
	userid = int(request.args.get('user_id', 1))
	user = User.query.filter(id = userid).first()
	if not user:
		return jsonify({"status":"error", "message":"User not found."}), 404
	return jsonify({"status":"ok", "user_id":user.id, "username":user.username}), 200

@app.route("/likes_for_x")
def likes_for_x():
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
	type_of = request.args.get('page_type', None)
	if_of = int(request.args.get('page_id', -1))
	if type_of not in ["comment","blog_post","thing"] or if_of < 0:
		return jsonify({"status":"error", "message":"Invalid request."}), 404
	likes = Comment.query.filter_by(target_type=type_of, target_id=if_of).count() or 0
	return jsonify({"status":"ok", "data":likes})