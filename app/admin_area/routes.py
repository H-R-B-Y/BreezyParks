from .. import schema, app, db
from . import admin_area
from flask import jsonify, request, Response, render_template
from flask_login import login_required, current_user

@admin_area.route("/")
def admin_area_home():
	return render_template("admin_area/home.html.jinja")


# Right now we just need to worry about post authoring 

@admin_area.route("/new_post", methods=["GET", "POST"])
def admin_area_new_post():
	if request.method == "POST":
		title = request.form.get("title")
		content = request.form.get("body")
		status = request.form.get("status")
		if not title or not content:
			return jsonify({"status":"error", "message":"Title and content are required"}), 400
		post = schema.BlogPost(title=title, status=status, body=content)
		schema.db.session.add(post)
		schema.db.session.commit()
		return jsonify({"status":"success", "message":"Post created", "id":post.id}), 201
	return render_template("admin_area/posts/new_post.html.jinja")

@admin_area.route("/edit_post/<int:id>", methods=["GET", "POST"])
def admin_area_edit_post(id : int):
	if request.method == "POST":
		post = schema.BlogPost.query.get(id)
		if not post:
			return jsonify({"status":"error", "message":"Post not found"}), 404
		print(request.form.get("status"))
		if request.form.get("title") == "" or request.form.get("body") == "" or request.form.get("status").lower() not in ["published", "draft"]:
			return jsonify({"status":"error", "message":"Malformed post!"}), 400 
		post.title = request.form.get("title")
		post.body = request.form.get("body")
		post.status = request.form.get("status").lower()
		db.session.commit()
		return jsonify({"status":"success", "message":"Post updated"}), 200
	post = schema.BlogPost.query.get(id)
	if not post:
		return jsonify({"status":"error", "message":"Post not found"}), 404
	return render_template("admin_area/posts/new_post.html.jinja", post=post)

@admin_area.route("/delete_post/<int:id>", methods=["POST"])
def admin_area_delete_post(id : int):
	post = schema.BlogPost.query.get(id)
	if not post:
		return jsonify({"status":"error", "message":"Post not found"}), 404
	db.session.delete(post)
	db.session.commit()
	return jsonify({"status":"success", "message":"Post deleted"}), 200

@admin_area.route("/post_view")
def admin_area_post_view():
	posts = schema.BlogPost.query.all()
	return render_template("admin_area/posts/view_posts.html.jinja", posts=posts)