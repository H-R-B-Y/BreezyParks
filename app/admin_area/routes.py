from .. import schema, app, db
from . import admin_area
from flask import jsonify, request, Response, render_template
from flask_login import login_required, current_user

@admin_area.route("/")
def admin_area_home():
	return render_template("admin_area/home.html.jinja")

# Right now we just need to worry about post authoring 
# region EDIT POST
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

# endregion

# region EDIT THING

"""
	formData.append("title", thing_title);
	formData.append("status", thing_status);
	formData.append("type", thing_type);
	formData.append("url_path", thing_url);
	formData.append("template_path", thing_template);
"""


@admin_area.route("/new_thing", methods=["GET", "POST"])
def admin_area_new_thing():
	if request.method == "POST":
		title = request.form.get("title")
		status = request.form.get("status")

		thing_type = request.form.get("type");
		thing_url = request.form.get("url_path");
		thing_template = request.form.get("template_path");

		if not title or not thing_type:
			return jsonify({"status":"error", "message":"Title and type are required"}), 400

		if thing_type not in ["url", "template"]:
			return jsonify({"status":"error", "message":"Type is not valid"}), 400
		
		if (thing_type == "url" and not thing_url) or (thing_type == "template" and not thing_template):
			return jsonify({"status":"error", "message":"Provided content is not valid"}), 400
			
		thing = schema.ThingPost(
			title = title,
			type = thing_type,
			url_for = thing_url,
			template_path = thing_template,
			status = status
		)

		schema.db.session.add(thing)
		schema.db.session.commit()
		return jsonify({"status":"success", "message":"Thing created", "id":None}), 201
	return render_template("admin_area/things/new_thing.html.jinja")

@admin_area.route("/edit_thing/<int:id>", methods=["GET", "POST"])
def admin_area_edit_thing(id : int):
	if request.method == "POST":
		thing = schema.ThingPost.query.get(id)
		if not thing:
			return jsonify({"status":"error", "message":f"Thing with id {id} doesnt exist"}), 400
		
		title = request.form.get("title")
		status = request.form.get("status")

		thing_type = request.form.get("type");
		thing_url = request.form.get("url_path");
		thing_template = request.form.get("template_path");

		if not title or not thing_type:
			return jsonify({"status":"error", "message":"Title and type are required"}), 400

		if thing_type not in ["url", "template"]:
			return jsonify({"status":"error", "message":"Type is not valid"}), 400
		
		if (thing_type == "url" and not thing_url) or (thing_type == "template" and not thing_template):
			return jsonify({"status":"error", "message":"Provided content is not valid"}), 400
		
		thing.title = title
		thing.status = status
		thing.type = thing_type
		thing.url_for = thing_url
		thing.template_path = thing_template

		schema.db.session.commit()
		return jsonify({"status":"success", "message":"Thing updated"}), 200
	thing = schema.ThingPost.query.get(id)
	if not thing:
		return jsonify({"status":"error", "message":"Thing not found"}), 404
	return render_template("admin_area/things/new_thing.html.jinja", thing=thing)

@admin_area.route("/delete_thing/<int:id>", methods=["POST"])
def admin_area_delete_thing(id : int):
	thing = schema.ThingPost.query.get(id)
	if not thing:
		return jsonify({"status":"error", "message":"thing not found"}), 404
	db.session.delete(thing)
	db.session.commit()
	return jsonify({"status":"success", "message":"thing deleted"}), 200

@admin_area.route("/thing_view")
def admin_area_thing_view():
	things = schema.ThingPost.query.all()
	return render_template("admin_area/things/view_things.html.jinja", things=things)

# endregion



@admin_area.route("/user_view")
def admin_area_user_view():
	return render_template("admin_area/users/view_users.html.jinja")

@admin_area.route("/user_details/<int:id>")
def admin_area_user_details(id):
	return render_template("admin_area/users/user_details.html.jinja", user=schema.User.query.get(id))