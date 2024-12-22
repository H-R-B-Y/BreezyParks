import os
import json
from datetime import datetime
from app import app, db, google, loginman, socketio, zetaSocketIO, require_admin, write_to_extra
from app.schema import User, ThingPost
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
	pass