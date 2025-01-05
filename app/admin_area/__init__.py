from flask import Blueprint, request, jsonify, make_response, render_template
from .. import schema
from flask_login import login_required, current_user
from functools import wraps


admin_area = Blueprint("admin_area", __name__)

@admin_area.before_request
def enforce_check_is_admin():
	if not current_user.is_authenticated or not current_user.is_admin:
		return render_template("default_error.html.jinja", status_code = 403, message = "Unauthorized"), 403

from . import routes