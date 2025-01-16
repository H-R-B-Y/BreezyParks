from flask import Blueprint, request, jsonify, make_response, render_template, flash
from . import scrabble_bp, zeta_word_game
from .. import schema, app, db, socketio
from flask_login import login_required, current_user

from functools import wraps

zeta_word_game_namespace_instance = zeta_word_game("/zeta/distinct_word_game")
socketio.on_namespace(zeta_word_game_namespace_instance)
@scrabble_bp.route("/")
def scrabble_index():
	if (current_user.username in zeta_word_game_namespace_instance.hands.keys()):
		flash(str(zeta_word_game_namespace_instance.hands[current_user.username].score))
	return render_template("scrabble_ge/scrabble_ge.html.jinja")