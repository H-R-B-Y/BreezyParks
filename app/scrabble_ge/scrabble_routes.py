from flask import Blueprint, request, jsonify, make_response, render_template, flash
from . import scrabble_bp, zeta_word_game, word_dictionary_connection
from .. import schema, app, db, socketio
from flask_login import login_required, current_user

from functools import wraps
import sqlite3

zeta_word_game_namespace_instance = zeta_word_game("/zeta/distinct_word_game")
socketio.on_namespace(zeta_word_game_namespace_instance)
@scrabble_bp.route("/")
def scrabble_index():
	if (current_user.username in zeta_word_game_namespace_instance.hands.keys()):
		flash(str(zeta_word_game_namespace_instance.hands[current_user.username].score))
	return render_template("scrabble_ge/scrabble_ge.html.jinja")

@scrabble_bp.route("/validate/<string:word>")
@word_dictionary_connection
def scrabble_validate_word(word):
	conn : sqlite3.Connection = scrabble_validate_word.dictionary_connection
	curs : sqlite3.Cursor = scrabble_validate_word.dictionary_cursor
	output = curs.execute("SELECT id, word, definition FROM words WHERE word = ?;", (word,)).fetchone()
	if isinstance(output, tuple):
		return jsonify({"status":"success","message":"Word found","data":{n:d for n,d in zip(["id", "word","definition"], output)}}), 200
	else:
		return jsonify({"status":"error","message":"No word found",}), 404