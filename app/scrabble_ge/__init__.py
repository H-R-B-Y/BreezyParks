from flask import Blueprint, request, jsonify, make_response, render_template
from .. import schema, app, zetaSocketIO, exit_handlers, socketio, get_auth_token_from_header, check_auth_token

from threading import Lock
from flask_login import login_required, current_user
from flask_socketio import Namespace, emit, disconnect
from functools import wraps

from requests import get
from datetime import datetime, timedelta
import uuid
import sqlite3
import json
import os


scrabble_bp = Blueprint("scrabble_ge", __name__)
app.config["word_dictionary_path"] = os.getenv("WORD_DICTIONARY_PATH")


# @scrabble_bp.before_request
# def enforce_debug():
# 	auth_token = get_auth_token_from_header()
# 	if auth_token and check_auth_token(auth_token):
# 		return
# 	elif not current_user.is_authenticated or not current_user.is_debug:
# 		return render_template("default_error.html.jinja", status_code = 403, message = "Unauthorized"), 403

def word_dictionary_connection(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		dictionary_connection = None
		try:
			dictionary_connection = sqlite3.connect(app.config["word_dictionary_path"])
			dictionary_cursor = dictionary_connection.cursor()
			wrapper.dictionary_connection = dictionary_connection
			wrapper.dictionary_cursor = dictionary_cursor
			return func(*args, **kwargs)
		finally:
			if dictionary_connection and isinstance(dictionary_connection, sqlite3.Connection):
				dictionary_connection.close()
	return wrapper


from . import model

class zeta_word_game(zetaSocketIO.zeta):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.base_init()
		if state := self.check_if_import_possible():
			self.initialise_game_from_backup(state)
		

	def base_init(self):
		self.resetting = False
		self.err = None
		self.totalPlayers = set()
		self.board = model.Board()
		self.hands = {} # in form {user : hand}
		self.playerTiming = {}
		self.maxdiscards = 5

	def initialise_game_from_backup(self, state):
		self.resetting = True
		data = json.loads(state)
		try:
			# print("loading board: ")
			self.board = model.Board.init_from_data(data)

			# print("loading players")
			for player in data["players"]:
				self.totalPlayers.add(player)
				if player in data["timings"]:
					self.playerTiming[player] = data["timings"][player]
				self.hands[player] = model.Hand.init_from_data(player, data["hands"][player])
			# print("loading hands")
			# print(f"loaded game with id {data["id"]}")
		except json.JSONDecodeError as e:
			print(f"Error parsing game state: {e}")
			self.base_init()
		except KeyError as e:
			print(f"Error loading data from key: {e}")
			self.base_init()
		finally:
			self.resetting = False

	@word_dictionary_connection
	def check_if_import_possible(self):
		# Get today's date
		today = datetime.today()
		# Find the most recent Monday (start of the week)
		start_of_week = today - timedelta(days=today.weekday())
		# Convert to a timestamp for SQLite
		start_of_week_timestamp = start_of_week.strftime('%Y-%m-%d %H:%M:%S')
		conn : sqlite3.Connection = self.check_if_import_possible.dictionary_connection
		curs : sqlite3.Cursor = self.check_if_import_possible.dictionary_cursor
		# Fetch the latest game that started within this week
		curs.execute(
			"""
			SELECT id, state, started_at 
			FROM games 
			WHERE started_at >= ?
			ORDER BY started_at DESC 
			LIMIT 1
			""",
			(start_of_week_timestamp,)
		)
		game = curs.fetchone()
		if not game:
			return False
		else:
			return game[1]

	@word_dictionary_connection
	def save_game_state(self,):
		with self.board.grid_lock:
			conn : sqlite3.Connection = self.save_game_state.dictionary_connection
			curs : sqlite3.Cursor = self.save_game_state.dictionary_cursor
			# Save the game state and scores to DB?????
			if len(self.board.words) == 0:
				return
			state_data = json.dumps(
				self.board.data(
					players = list(self.totalPlayers),
					scores = {n:self.hands[n].score for n in self.hands.keys()},
					hands = {h:self.hands[h].data() for h in self.hands},
					timings = self.playerTiming,
				)
			)
			try:
				if state_data:
					curs.execute(
						"INSERT OR REPLACE INTO games (id, state, started_at, ended_at) VALUES (?, ?, ?, ?)",
						(self.board.gameid, state_data, datetime.fromtimestamp(self.board.starttime), datetime.utcnow(),)
					)
					conn.commit()
					conn.close()
			except Exception as e:
				print(f"error saving game {self.board.id}: {e}")

	def reset_game(self):
		part = 0
		try:
			self.emit("game_reset", {})
			self.resetting = True
			self.disconnect_all()
			self.reset_ns()
			part += 1
	
			self.save_game_state()
	
			del(self.totalPlayers)
			del(self.board)
			del(self.hands)
			del(self.playerTiming)
			part += 1
	
			self.base_init()
			part += 1
		except Exception as e:
			self.err = e
			print(f"Exception: {e} at part {['ns reset','state flush','state set','ERR'][part]}")
		finally:
			self.resetting = False

	def on_connect(self):
		'''
		On connect store the sid, the username, and create a lookup value for this sid.
		Active users and active sids are sets so don't need to worry about duplicates
		'''
		if self.resetting:
			disconnect()

		self.activeSids.add(request.sid)

		# Broadcast that new user has joined here.
		# Add user details to the class (Done after broadcast such that no actions are dispatched
		# for uninitialised users)
		if current_user.is_authenticated:
			if current_user.username not in self.hands.keys():
				self.hands[current_user.username] = model.Hand(current_user.username)
			self.activeUsers.add(current_user.username)
			self.sidLookup[request.sid] = current_user.username
			self.totalPlayers.add(current_user.username)
			emit("joined", {"username":current_user.username, "active": True, "score" : self.hands[current_user.username].score, "colour" : current_user.fav_colour}, include_self=False, broadcast=True)

		
	def on_disconnect(self):
		'''
		On Disconnect we need to remove the sid
		We then need to remove the sids lookup value
		We also need to remove the utser from the active users
			IF and ONLY IF they have no other active session in his namespace.
		'''
		if self.resetting:
			return
		# Code that needs to be executed regardless of whether user  still has active sessions or not:
		if request.sid in self.activeSids:
			self.activeSids.discard(request.sid)

		if not current_user.is_authenticated:
			return
		
		# Code that needs to be executed IF and ONLY IF the disconnecting session
		# is the last active session for the user.
		self.sidLookup.pop(request.sid, False)
		if(not any(map(lambda x: x==current_user.username, set(self.sidLookup.values())))):
			self.activeUsers.discard(current_user.username)
			emit("left", {"username":current_user.username}, include_self=False, broadcast=True)
	
	# This was part of the parent class but is no longer needed
	def on_moved(self, data):
		return 

	def player_allowed_discard(self, username):
		start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
		hand : model.Hand = self.hands[username]
		if datetime.fromtimestamp(hand.discardTimestamp) < start_of_day:
			hand.discardsUsed = 0
			hand.discardTimestamp = datetime.utcnow().timestamp();
		if hand.discardsUsed < self.maxdiscards:
			return True
		return False

	def player_allowed_turn(self, username):
		start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
		if self.playerTiming.get(current_user.username):
				if datetime.fromtimestamp(self.playerTiming[current_user.username]) > start_of_day:
					return False
		return True

	def get_player_hand(self, username):
		hand = self.hands[current_user.username]
		while len(hand.tiles) < 7:
			hand.tiles.append(self.board.create_new_tile(owner=current_user.username))
		return hand

	def get_player_state(self, username):
		return {
			"username" : username,
			**self.get_player_hand(username).data(),
			"allowed_turn" : self.player_allowed_turn(username),
			"discards_remaining" : self.maxdiscards - self.hands[username].discardsUsed,
			"allowed_discard" : self.player_allowed_discard(username),
		}

	def emit_player_state(self, username, sid):
		emit("player_state", self.get_player_state(username), to=sid, broadcast=False)

	def on_request_game_state(self, data):
		# print("recieved game state request")
		timestamp = None
		if data.get("timestamp", None):
			timestamp = data["timestamp"]
		words = self.board.words_after_timestamp(timestamp)
		# print("sending game state")
		emit("board_state", {
				"board_size":self.board.size,
				"special_tiles":list(self.board.special_tile_vector),
				"words_played":[w.data() for w in list(words)],
				"timestamp":datetime.utcnow().timestamp(),
				"score" : self.hands[current_user.username].score,
				"max_discards" : self.maxdiscards,
				"colour" : current_user.fav_colour,
			}, to=request.sid, broadcast=False)
		self.emit_player_state(current_user.username, request.sid)
		# Let users know about ALL USERS IN THE GAME
		# we then need to send a message stating which are online currently
		
	def on_request_hand(self, data = None):
		self.emit_player_state(username=current_user.username, sid=request.sid)

	class WordProto ():
		def __init__ (self, data):
			self.is_parent = data.get("is_parent_word")
			self.word = data.get("word")
			self.new_tile_positions = data.get("new_tile_positions")
			self.new_tiles = [model.Tile.get_by_uuid(x) for x in data["new_tiles"]] if data.get("new_tiles") else None
			assert None not in self.new_tiles
			self.all_tiles = [model.Tile.get_by_uuid(x) for x in data["all_tiles"]] if data.get("all_tiles") else None
			assert None not in self.all_tiles
			assert len(self.word) == len(self.all_tiles)
			self.axis = data.get("axis")
			self.validate_word()
			assert self.validate_axis()

		def validate_word(self):
			for i in range(len(self.word)):
				assert self.word[i] == self.all_tiles[i].identity

		def validate_axis(self):
			x = set()
			y = set()

			for tile in self.all_tiles:
				if tile in self.new_tiles:
					pos = self.new_tile_positions[tile.id]
					x.add(pos.get("x"))
					y.add(pos.get("y"))
				else:
					x.add(tile.position.get("x"))
					y.add(tile.position.get("y"))
			assert None not in x
			assert None not in y
			assert len(y) == 1 or len(x) == 1
			return self.axis == ("h" if len(y) == 1 else "v")
		
		def __str__(self):
			return self.word
		
	def on_request_players(self, data=[]):
		for uName in self.totalPlayers:
			if uName == current_user.username:
				continue
			emit("joined", {"username":uName,
	 				"active": uName in self.activeUsers,
					"score" : self.hands[uName].score,
					"colour" : schema.User.get_user_by_name(uName).fav_colour
				},
				to=request.sid,
				broadcast=False)

	def on_reset_turn (self, data):
		if (not current_user.is_authenticated) or (not current_user.is_admin):
			return
		if data.get("username"):
			self.playerTiming[data.get("username")] = None
			self.emit_player_state(username = data.get("username"), sid=self.all_sids_for_username(data.get("username")))
		else:
			self.playerTiming[current_user.username] = None
			self.emit_player_state(username = current_user.username, sid=request.sid)

	def on_debug_force_increment(self, data=[]):
		if current_user.is_authenticated and current_user.is_admin:
			self.resizeBoard(data.get("increment") or 1)
		return

	def resizeBoard(self, increment):
		#  Notify all clients that this may take a while and to block further action
		# Probably a good idea XD
		self.board.increment_size(increment=increment)
		self.emit("board_resized", {"size":self.board.size, "special_tiles":list(self.board.special_tile_vector)})

	def calculate_score(self, words):
		score = 0
		user = words[0].owner
		for word in words:
			word.calculate_score()
			score += word.score
		self.hands[user].score += score
		self.emit("score_updated", {"username" : user, "score" : self.hands[user].score})

	def on_admin_give_tile(self, data):
		if not current_user.is_admin:
			return
		else:
			tile = model.Tile("a", owner=data.get("username"))
			tile.identity = data.get("identity")
			tile.score = data.get("score") or tile.score
			if self.hands[data.get("username")]:
				self.hands[data.get("username")].tiles.append(tile)


zeta_word_game_namespace_instance = zeta_word_game("/zeta/word_game")
socketio.on_namespace(zeta_word_game_namespace_instance)
exit_handlers.append(
	(zeta_word_game_namespace_instance.save_game_state, ())
)

from . import scrabble_routes