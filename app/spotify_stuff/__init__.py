from flask import Blueprint, request, jsonify, make_response, render_template
from .. import schema, app
from flask_login import login_required, current_user
from functools import wraps

spotify_routes = Blueprint("spotify_routes", __name__)

def enforce_check_wilt_enabled(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		if not current_user.is_authenticated or not current_user.wilt_enabled:
			return render_template("default_error.html.jinja", status_code = 403, message = "Unauthorized"), 403
		return func(*args, **kwargs)
	return wrapper

from . import auth_routes