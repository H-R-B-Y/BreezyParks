from flask import Blueprint, request, jsonify, make_response, Response
from .. import schema
from flask_login import login_required, current_user
from functools import wraps

"""How to make an api request:

For admin user accounts:
	Just make the reuqest as normal, the user will be authenticated and the request will be processed.

For token holders:
	1. Set the api_version header to 1.
	2. Set the Authorization header to "Bearer <token>" where <token> is the token you have.

"""

api_v1_bp = Blueprint("api_v1", __name__)

def _add_api_version_header(response):
	"""
	Helper function to add the API-Version header to the response.
	"""
	if isinstance(response, tuple):
		# Unpack tuple
		body, *rest = response
		# Extract status code (default to 200)
		status_code = rest[0] if len(rest) > 0 and isinstance(rest[0], int) else 200
		# Extract headers (default to empty dict)
		headers = rest[1] if len(rest) > 1 and isinstance(rest[1], dict) else {}
		flask_response = make_response(body, status_code)
		flask_response.headers.update(headers)
	elif isinstance(response[0], Response):
		# If it's already a Response object, modify it directly
		flask_response = response[0]
	else:
		# If not a tuple or a Response, treat it as a raw response body
		flask_response = make_response(response[0])

	# Add the API-Version header
	flask_response.headers['API-Version'] = '1'
	return flask_response


def api_v1_validation(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		# Perform API version validation
		if not current_user.is_authenticated:
			if request.headers.get("API-Version") != "1":
				return _add_api_version_header(
					(jsonify({"status": "error", "message": "Invalid API version", "version": "1"}), 400)
				)
			auth_header = request.headers.get('Authorization')
			if not auth_header:
				return _add_api_version_header(
					(jsonify({"status": "error", "message": "Missing Authorization header", "version": "1"}), 401)
				)
			# Ensure the header starts with 'Bearer'
			parts = auth_header.split()
			if len(parts) != 2 or parts[0].lower() != "bearer":
				return _add_api_version_header(
					(jsonify({"status": "error", "message": "Invalid Authorization header format", "version": "1"}), 401)
				)
			# Validate the token
			token = parts[1]
			# Replace this with your actual token validation logic
			if schema.AccessToken.query.filter_by(token=token).first() is not None:
				return _add_api_version_header(func(*args, **kwargs))
			return _add_api_version_header(
				(jsonify({"status": "error", "message": "Invalid token", "version": "1"}), 403)
			)
		elif current_user.is_authenticated and current_user.is_admin:
			return _add_api_version_header(func(*args, **kwargs))
		# Add API version header by default
		return _add_api_version_header(func(*args, **kwargs))

	return wrapper

from . import routes
