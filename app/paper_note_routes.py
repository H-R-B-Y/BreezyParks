import base64
from functools import wraps
from datetime import datetime, timedelta
from app import app, db, require_token, require_admin, get_extra_data, write_to_extra
from app.schema import User, PaperNote
from flask import Flask, redirect, url_for, request, render_template, flash, jsonify
from sqlalchemy import desc, func
from authlib.integrations.flask_client import OAuth
from flask_login import login_required, current_user

def user_can_note(user : User):
	if True: return True # WARN: delete after test
	latest : PaperNote = PaperNote.query.filter_by(user_id = user.id).order_by(desc(PaperNote.created_date)).first()
	if not latest:
		return True
	if (datetime.utcnow() - latest.created_date) < timedelta(hours=24):
		return False
	return True

def require_able_to_post(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		if not user_can_note(current_user):
			flash("You are unable to send a note.")
			return redirect(url_for("index"))
		return func(*args, **kwargs)
	return wrapper

@app.route("/paper_index")
@login_required
@require_able_to_post
def paper_index():
	return render_template("things/paper_index.html.jinja")

@app.route("/post_note", methods=["POST"])
@login_required
@require_able_to_post
def post_note():
	if not user_can_note(current_user): return "Nope!", 400
	if (request.headers.get("Content-Type") == "application/json"):
		data = request.get_json()
		data_type = data.get("data_type", "").strip().lower()
		data_text = data.get("data_text", "").strip()
		data_raw = data.get("data_raw", "").strip()
		if data_type not in ["raw", "text"] or \
			(data_type == "raw" and data_raw == "") or \
			(data_type == "text" and data_text == ""):
			flash("Data type did not match data sent", "error")
			return "Nope!", 400
		if (data_type == "raw" and len(data_raw) != (212 * 104) / 4):
			flash("That didn't look quite right :(", "error")
			return "Nope!", 400
		new_note = PaperNote(user_id=current_user.id, type=(0 if data_type == "raw" else 1))
		if (data_type == "raw"): new_note.data = data_raw
		else: new_note.text = data_text
	elif (request.headers.get("Content-Type") == "application/octet-stream"):
		data = request.data
		new_note = PaperNote(user_id=current_user.id,type=0,data=data)
	db.session.add(new_note)
	db.session.commit()
	flash("Thanks for sending me a note!", "info")
	notes_sent = get_extra_data("notes_sent")
	write_to_extra("notes_sent", notes_sent + 1 if notes_sent else 1)
	return "OK", 200

@app.route("/get_note_admin", methods=["GET"])
@login_required
@require_admin
def get_paper_note_admin():
	# check if there are any notes to actually get
	if len(PaperNote.query.all()) == 0:
		return jsonify({"error": "There are no new notes"}), 404
	random_record : PaperNote = PaperNote.query.order_by(func.random()).first()
	if random_record == None:
		return jsonify({"error": "There are no new notes"}), 404
	return_data = {"data_type": random_record.type, "data_raw": random_record.data, "data_text": random_record.text, "from": User.query.filter_by(id=random_record.user_id).first().username}
	db.session.delete(random_record)
	db.session.commit()
	notes_read = get_extra_data("notes_read")
	write_to_extra("notes_read", notes_read + 1 if notes_read else 1)
	return jsonify(return_data), 200

@app.route("/get_note_token", methods=["GET"])
@require_token
def get_paper_note_token():
	# check if there are any notes to actually get
	if len(PaperNote.query.all()) == 0:
		return jsonify({"error": "There are no new notes"}), 404
	random_record : PaperNote = PaperNote.query.order_by(func.random()).first()
	if random_record == None:
		return jsonify({"error": "There are no new notes"}), 404
	return_data = {"data_type": random_record.type,
		"data_raw": base64.b64encode(random_record.data).decode("ascii"),
		"data_text": random_record.text,
		"from": User.query.filter_by(id=random_record.user_id).first().username,
		"created_date": random_record.created_date.timestamp()}
	#db.session.delete(random_record)
	#db.session.commit()
	notes_read = get_extra_data("notes_read")
	write_to_extra("notes_read", notes_read + 1 if notes_read else 1)
	return jsonify(return_data), 200
