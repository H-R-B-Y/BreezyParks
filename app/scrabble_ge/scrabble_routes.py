from flask import Blueprint, request, jsonify, make_response, render_template, flash
from . import scrabble_bp, zeta_word_game, word_dictionary_connection, model
from .. import schema, app, db, socketio, require_admin, require_token
from flask_login import login_required, current_user
from datetime import datetime
from functools import wraps
from threading import Thread
import sqlite3

zeta_word_game_namespace_instance = zeta_word_game("/zeta/word_game")
socketio.on_namespace(zeta_word_game_namespace_instance)
@scrabble_bp.route("/")
def scrabble_index():
	return render_template("scrabble_ge/scrabble_ge.html.jinja")

@scrabble_bp.route("/state_check")
def scrabble_state_check():
	ns = zeta_word_game_namespace_instance
	state = "ok" if ns.err is None else "error"
	resetting = ns.resetting
	data = {"status": "success",
		"message": "Game State",}
	if current_user.is_authenticated and current_user.is_admin:
		data = {**data, "err": str(ns.err)}
	data = {**data, "state": state, "resetting": resetting}
	return jsonify(data), 200

@scrabble_bp.route("/force_reset")
@login_required
@require_admin
def scrabble_reset():
	ns = zeta_word_game_namespace_instance
	err = None
	try:
		ns.reset_game()
	except Exception as e:
		err = e
	finally:
		pass
	data = {
		"status" : "success" if None == (err or ns.err) else "error", # or will take any value or none if both is none
		"message" : "Server reset"
	}
	if err:
		data["server_err"] = str(err)
	if ns.err:
		data["ns_err"] = str(err)
	return jsonify(data), 200

@scrabble_bp.route("/reset")
@require_token
def scrabble_reset_with_token():
	ns = zeta_word_game_namespace_instance
	err = None
	try:
		ns.reset_game()
	except Exception as e:
		err = e
	finally:
		pass
	data = {
		"status" : "success" if None == (err or ns.err) else "error", # or will take any value or none if both is none
		"message" : "Server reset"
	}
	if err:
		data["server_err"] = str(err)
	if ns.err:
		data["ns_err"] = str(err)
	return jsonify(data), 200

@scrabble_bp.route("/validate/<string:word>")
@word_dictionary_connection
@login_required
def scrabble_validate_word(word):
	ns = zeta_word_game_namespace_instance
	if not (current_user.username in ns.totalPlayers):
		return jsonify({"status":"error","message":"You are not in a game"}), 200 # need a user error code here
	conn : sqlite3.Connection = scrabble_validate_word.dictionary_connection
	curs : sqlite3.Cursor = scrabble_validate_word.dictionary_cursor
	output = curs.execute("SELECT id, word, definition FROM words WHERE word = ?;", (word,)).fetchone()
	if isinstance(output, tuple):
		return jsonify({"status":"success","message":"Word found","data":{n:d for n,d in zip(["id", "word","definition"], output)}}), 200
	else:
		return jsonify({"status":"error","message":"No word found",}), 404

# NOTE: Please move the following to an apporpriate file!
# region defintions
def get_endpoint(word):
	return f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.lower().strip()}"

def get_definitions(response_data):
	meanings = []
	try:
		data = response_data.json()
		for meaning in data[0]["meanings"]:
			if len(meaning["definitions"]) > 3:
				meaning["definitions"] = meaning["definitions"][0:3]
			for definition in meaning["definitions"]:
				meanings.append(definition["definition"])
	except Exception as e:
		print(f"error {e}")
		return None
	return "\n".join(meanings)

def add_definition(cursor, word_id, word, defintion):
	add_query = """
	UPDATE words
	SET definition = ?
	WHERE id = ? AND word = ?
	"""
	cursor.execute(add_query, (defintion, word_id, word))

def attempt_to_get_definition(word_id, word):
	from requests import get
	connection = sqlite3.connect(app.config["word_dictionary_path"])
	cursor = connection.cursor()
	try:
		resp = get(get_endpoint(word))
		if resp.status_code == 200:
			defintion = get_definitions(resp)
			if defintion:
				add_definition(cursor=cursor, word_id=word_id, word=word, defintion=defintion)
	finally:
		connection.commit()
		connection.close()
	return 
# endregion
	
@scrabble_bp.route("/played_word", methods=["POST"])
@word_dictionary_connection
@login_required
def scrabble_played_word():
	ns = zeta_word_game_namespace_instance
	curs : sqlite3.Cursor = scrabble_played_word.dictionary_cursor
	data = request.get_json()
	# print(data)
	try:
		words = [ns.WordProto(w) for w in data]
	except AssertionError as e:
		return jsonify({"status": "error", "message": "Assertion error (tiles or axis invalid)", "details": str(e)})
	primary = None
	for word in words:
		if word.is_parent and not primary:
			primary = word
		elif primary and word.is_parent:
			return jsonify({"status": "error", "message": "Multiple primary words.", "word":f"{primary} and {word}"})
		for tile in word.all_tiles:
			if not tile.is_played:
				if tile.owner != current_user.username or not tile in ns.hands[current_user.username].tiles:
					return jsonify({"status":"error", "message":"Played tiles are not thy own", "word":str(word)})
			else:
				if tile.id not in ns.board.played_tiles:
					return jsonify({"status":"error", "message":"One or more external tile is not played", "word":str(word)})
		
		output = curs.execute("SELECT id, word, definition FROM words WHERE word = ?", (word.word,)).fetchone()
		if not isinstance(output, tuple):
			return jsonify({"status":"error", "message":"Word not in dictionary", "word":str(word)})
		if output[2] == None:
			Thread(target=attempt_to_get_definition, args=(output[0], output[1])).start()

	if not ns.board.place_tiles({t : primary.new_tile_positions[t.id] for t in primary.new_tiles}):
		return jsonify({"status":"error", "message":"Board contains tiles in this position", "word":str(primary)})

	x_all = set()
	y_all = set()

	for tile in primary.new_tiles:
		ns.hands[current_user.username].tiles.remove(tile)
		x_all.add(tile.position["x"])
		y_all.add(tile.position["y"])

	all_min = min(min(x_all), min(y_all))
	all_max = max(max(x_all), max(y_all))
	true_min = min(abs(all_max - (ns.board.size - 1)), all_min)
	true_words = []
	for word in words:
		# print(word)
		this_word = model.Word(current_user.username, tiles = word.all_tiles, unique_tiles=word.new_tiles)
		this_word.axis = word.axis 
		ns.board.words.add(this_word)
		true_words.append(this_word)
		if word == primary:
			# print(word)
			primary = this_word
	ns.board.primaryWords.add(primary)
	ns.playerTiming[current_user.username] = datetime.utcnow().timestamp()
		
	# print(f"true min {true_min}")
	if true_min < 3:
		ns.resizeBoard(3 - true_min)
	
	ns.calculate_score(true_words)
	ns.emit("new_word", {"word" : primary.data()})

	return jsonify({"status": "success", "message": "Word played", "word":primary.data()})


@scrabble_bp.route("/get_state", methods=["GET"])
def scrabble_get_player_state():
	ns = zeta_word_game_namespace_instance
	playername = current_user.username
	state = ns.get_player_state(playername)
	return jsonify({"status": "success", "state": state}), 200


@scrabble_bp.route("/discard/<string:id>")
@login_required
def scrabble_discard_tile(id):
	ns = zeta_word_game_namespace_instance
	if not (current_user.username in ns.totalPlayers):
		return jsonify({"status":"error","message":"You are not in a game"})
	hand : model.Hand = ns.hands[current_user.username]
	tile : model.Tile = model.Tile.get_by_uuid(id)
	if tile == None or hand == None:
		return jsonify({"status":"error","message":"Tile or Hand does not exist"}), 404
	if not (tile in hand.tiles):
		return jsonify({"status":"error","message":"Tile is not part of your hand"})
	if not ns.player_allowed_discard(current_user.username):
		return jsonify({"status":"error","message":"All discards used"}), 200
	hand.tiles.remove(tile)	
	hand.discardsUsed += 1;
	return jsonify({"status":"success","message":"Discarded Tile"}), 200