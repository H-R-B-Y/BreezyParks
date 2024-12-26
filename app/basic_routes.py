import os
import json
from datetime import datetime
from app import app, db, google, loginman, socketio, zetaSocketIO, require_admin, write_to_extra, schema
from app.schema import User, ThingPost, Comment
from sqlalchemy import desc
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

# This needs to be revamed;
@app.route("/thing_pages")
def things_pages():
	page = int(request.args.get('page', 1))
	per_page = int(request.args.get('per_page', 10))
	if per_page == 0:
		return jsonify({})
	start = (page - 1) * per_page
	end = start + per_page
	things = ThingPost.query.order_by(desc(ThingPost.created_date)).all()
	data = [{"title": x.title, "path":url_for(x.url_for)} for x in things[start:end]]
	total_pages = (len(things) + per_page - 1) / per_page
	return jsonify({
			"data":data,
			"page":page,
			"total_pages":total_pages
		})

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
	if not type or not id or type not in table.keys():
		return "Not found", 404
	table_ref = table.get(type, None)
	if not table_ref:
		return "Not found", 404
	item_ref = table_ref.query.filter_by(id=id).first()
	if not item_ref:
		return "Not found", 404
	# check if a like record exists
	like = schema.Like.query.filter_by(user_id=current_user.id,target_type=type,target_id=id).first()
	if like:
		db.session.delete(like)
		db.session.commit()
		return jsonify({"state":"unliked"}), 200
	new_like = schema.Like(user_id=current_user.id, target_type=type, target_id=id)
	db.session.add(new_like)
	db.session.commit()
	return jsonify({"state":"liked"}), 200

@app.route("/post_comment", methods=["POST"])
@login_required 
def post_a_comment():
	comment_body = request.form.get('comment_body')
	comment_on_type = request.form.get('comment_on_type')
	comment_on_id = request.form.get('comment_on_id')
	# Validate the form data
	if not comment_body or not comment_on_type or not comment_on_id or comment_on_type not in ('blog_post','comment','thing'):
		return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
	new_comment = Comment(user_id = current_user.id, target_type = comment_on_type, target_id = comment_on_id, body = comment_body)
	db.session.add(new_comment)
	db.session.commit()
	return jsonify({'status': 'ok'})