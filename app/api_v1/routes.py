from .. import schema, require_admin
from . import api_v1_bp, api_v1_validation, _add_api_version_header

from flask import jsonify, request, Response, url_for
from flask_login import login_required, current_user


@api_v1_bp.route("/paper_note_count", methods=["GET"])
@api_v1_validation
def api_v1_paper_note_count():
	status = request.args.get("status", None)
	filter = {}
	if status in ["pending", "completed", "deleted"]:
		status = request.args.get("status")
		filter["status"] = status
	count = schema.PaperNote.query.filter_by(**filter).count()
	return jsonify({"status":"ok", "count":count, "version":1}), 200

@api_v1_bp.route("/paper_notes_page", methods=["POST"])
@api_v1_validation
def api_v1_paper_note_page():
	page = int(request.json.get("page",1))
	per_page = int(request.json.get("per_page", 6))
	filter = {}
	status = request.json.get("status", None)
	if status in ["pending", "completed", "deleted"]:
		filter["status"] = status
	if (page < 1 or per_page < 1):
		return jsonify({"status":"error", "message":"Page doesn't exist", "version":1}), 404
	start = (page - 1) * per_page
	end = start + per_page
	notes = schema.PaperNote.query.filter_by(**filter).order_by(schema.PaperNote.created_date).all()
	data = [{"id":x.id, "title": x.title, "status":x.status, "path":url_for("api_v1.api_v1_paper_note_id", id=x.id)} for x in notes[start:end]]
	return jsonify({
			"status":"ok",
			"data":data,
			"page":page,
			"last_page": True if end >= len(notes) else False,
			"filter": filter,
			"version":1}), 200

@api_v1_bp.route("/paper_note/<int:id>", methods=["GET"])
@api_v1_validation
def api_v1_paper_note_id(id):
	paper_note = schema.PaperNote.query.filter_by(id = id).first()
	if not paper_note:
		return jsonify({"status":"error", "message":"Note not found", "version":1}), 404
	if paper_note.type == 0:
		res = Response(paper_note.data, content_type = "application/octet-stream")
	else:
		res = jsonify({"data": paper_note.text}), 200
	return res, 200

@api_v1_bp.route("/paper_note/<int:id>/delete", methods=["POST"])
@require_admin
def api_v1_paper_note_delete(id):
	paper_note = schema.PaperNote.query.filter_by(id = id).first()
	if not paper_note:
		return jsonify({"status":"error", "message":"Note not found", "version":1}), 404
	schema.db.session.delete(paper_note)
	schema.db.session.commit()
	return _add_api_version_header(jsonify({"status":"ok", "message":"Note deleted", "version":1}), 200)

"""
Following for comments and for likes
"""

@api_v1_bp.route("/comment_count", methods=["GET"])
@api_v1_validation
def api_v1_get_comment_count():
	requested_type = request.args.get("type", None)
	requested_id = request.args.get("id", None)
	requested_user = request.args.get("user_id", None)
	if requested_type and requested_type not in ['blog_post', 'comment', 'thing']:
		return jsonify({"status":"error", "message":"Invalid type", "version":1}), 400
	filter = {}
	if requested_type and requested_type in ['blog_post', 'comment', 'thing']:
		filter["target_type"] = requested_type
	if requested_id and requested_id.isnumeric():
		filter["target_id"] = requested_id
	if requested_user and requested_user.isnumeric():
		filter["user_id"] = requested_user
	count = schema.Comment.query.filter_by(**filter).count()
	return jsonify({"status":"ok", "count":count, "version":1}), 200

@api_v1_bp.route("/comment_page", methods=["POST"])
@api_v1_validation
def api_v1_comment_page():
	page = int(request.json.get("page",1))
	per_page = int(request.json.get("per_page", 6))
	if (page < 1 or per_page < 1):
		return jsonify({"status":"error", "message":"Page doesn't exist", "version":1}), 404
	
	filter = {}
	requested_type = request.json.get("type", None)
	requested_id = request.json.get("id", None)
	requested_user = request.json.get("user_id", None)
	if requested_type and requested_type not in ['blog_post', 'comment', 'thing']:
		return jsonify({"status":"error", "message":"Invalid type", "version":1}), 400
	if requested_type and requested_type in ['blog_post', 'comment', 'thing']:
		filter["target_type"] = requested_type
	if requested_id and requested_id.isnumeric():
		filter["target_id"] = requested_id
	if requested_user and requested_user.isnumeric():
		filter["user_id"] = requested_user
	start = (page - 1) * per_page
	end = start + per_page
	comments = schema.Comment.query.filter_by(**filter).order_by(schema.Comment.created_date).all()
	data = [{"id":x.id, "username":x.user.username, "body": x.body, "path":"api_v1/comment/"+str(x.id)} for x in comments[start:end]]
	return jsonify({
			"status":"ok",
			"data":data,
			"page":page,
			"last_page": True if end >= len(comments) else False,
			"version":1}), 200

@api_v1_bp.route("/comment/<int:id>", methods=["GET"])
@api_v1_validation
def api_v1_comment_id(id):
	comment = schema.Comment.query.filter_by(id = id).first()
	if not comment:
		return jsonify({"status":"error", "message":"Comment not found", "version":1}), 404
	return jsonify({
			"status":"ok",
			"username":comment.user.username,
			"body":comment.body,
			"created_date":comment.created_date.timestamp(),
			"version":1}), 200


@api_v1_bp.route("/like_count", methods=["GET"])
@api_v1_validation
def api_v1_get_like_count():
	requested_type = request.args.get("type", None)
	requested_id = request.args.get("id", None)
	requested_user = request.args.get("user_id", None)
	if requested_type and requested_type not in ['blog_post', 'comment', 'thing', 'profile']:
		return jsonify({"status":"error", "message":"Invalid type", "version":1}), 400
	filter = {}
	if requested_type and requested_type in ['blog_post', 'comment', 'thing', 'profile']:
		filter["target_type"] = requested_type
	if requested_id and requested_id.isnumeric():
		filter["target_id"] = requested_id
	if requested_user and requested_user.isnumeric():
		filter["user_id"] = requested_user
	count = schema.Like.query.filter_by(**filter).count()
	return jsonify({"status":"ok", "count":count, "version":1}), 200

"""
Following for users
"""

@api_v1_bp.route("/user_count", methods=["GET"])
@api_v1_validation
def api_v1_get_user_count():
	count = schema.User.query.count()
	return jsonify({"status":"ok", "count":count, "version":1}), 200

@api_v1_bp.route("/user_page", methods=["POST"])
@api_v1_validation
def api_v1_user_page():
	page = int(request.json.get("page",1))
	per_page = int(request.json.get("per_page", 6))
	if (page < 1 or per_page < 1):
		return jsonify({"status":"error", "message":"Page doesn't exist", "version":1}), 404
	start = (page - 1) * per_page
	end = start + per_page
	users = schema.User.query.order_by(schema.User.username).all()
	data = [{"id":x.id, "username": x.username, "path":"api_v1/user/"+str(x.id)} for x in users[start:end]]
	return jsonify({
			"status":"ok",
			"data":data,
			"page":page,
			"last_page": True if end >= len(users) else False,
			"version":1}), 200

@api_v1_bp.route("/user/<int:id>", methods=["GET"])
@api_v1_validation
def api_v1_user_id(id):
	user = schema.User.query.filter_by(id = id).first()
	if not user:
		return jsonify({"status":"error", "message":"User not found", "version":1}), 404
	data = {
		"status":"ok",
		"username":user.username,
		"created_date":user.created_date.timestamp(),
		"version":1}
	if current_user.is_authenticated and current_user.is_admin: # when tokens have permissions update this
		data["is_admin"] = user.is_admin
		data["email"] = user.email
		data["username_last_updated"] = user.username_last_updated.timestamp()
		data["comment_banned"] = not user.can_comment
		data["google_id"] = user.google_id
		data["last_login_date"] = user.last_login_date.timestamp()
	return jsonify(data), 200

@api_v1_bp.route("/user/<int:id>/ban_comment", methods=["POST"])
@require_admin
def api_v1_user_ban_comment(id):
	user = schema.User.query.filter_by(id = id).first()
	if not user:
		return jsonify({"status":"error", "message":"User not found", "version":1}), 404
	user.can_comment = not user.can_comment
	schema.db.session.commit()
	return _add_api_version_header(jsonify({"status":"success", "message":"Comment ban toggled", "banned": True if not user.can_comment else False, "version":1}), 200)

@api_v1_bp.route("/user/<int:id>/toggle_wilt", methods=["POST"])
@require_admin
def api_v1_user_toggle_wilt(id):
	user = schema.User.query.filter_by(id = id).first()
	if not user:
		return jsonify({"status":"error", "message":"User not found", "version":1}), 404
	user.wilt_enabled = not user.wilt_enabled
	schema.db.session.commit()
	return _add_api_version_header(jsonify({"status":"success", "message":"Wilt toggled", "wilt_enabled": True if user.wilt_enabled else False, "version":1}), 200)