from flask import Blueprint, request, jsonify, make_response, render_template
from .. import schema, app, zetaSocketIO
from threading import Lock
from flask_login import login_required, current_user
from flask_socketio import Namespace, emit
from functools import wraps
from . import model
from requests import get
from datetime import datetime 
import uuid
import sqlite3
import os

scrabble_bp = Blueprint("scrabble_ge", __name__)
app.config["word_dictionary_path"] = os.getenv("WORD_DICTIONARY_PATH")

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




class zeta_word_game(zetaSocketIO.zeta):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# parent has active users which contains current players
		# but we also need to keep track of all players in the game
		self.totalPlayers = set() 


		self.board = model.Board()
		self.hands = {} # in form {user : hand}

	def on_connect(self):
		'''
		On connect store the sid, the username, and create a lookup value for this sid.
		Active users and active sids are sets so don't need to worry about duplicates
		'''
		# Let users know about ALL USERS IN THE GAME
		# we then need to send a message stating which are online currently
		for uName in self.totalPlayers:
			emit("joined", {"username":uName, "active": uName in self.activeUsers}, to=request.sid, broadcast=False)

		self.activeSids.add(request.sid)
		# Broadcast that new user has joined here.
		# Add user details to the class (Done after broadcast such that no actions are dispatched
		# for uninitialised users)
		if current_user.is_authenticated:
			# NOTE: This emit IS SENT TO THE USER AS WELL,
			# this is the key that allows the user to request the board
			emit("joined", {"username":current_user.username, "x":0, "y":0}, include_self=True, broadcast=True)
			self.activeUsers.add(current_user.username)
			self.sidLookup[request.sid] = current_user.username
			self.totalPlayers.add(current_user.username)
			if current_user.username not in self.hands.keys():
				self.hands[current_user.username] = model.Hand(current_user)
				#self.words[current_user.username] = []
		
	def on_disconnect(self):
		'''
		On Disconnect we need to remove the sid
		We then need to remove the sids lookup value
		We also need to remove the utser from the active users
			IF and ONLY IF they have no other active session in his namespace.
		'''
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
	
	def on_request_game_state(self, data):
		print("recieved game state request")
		timestamp = None
		if data.get("timestamp", None):
			timestamp = data["timestamp"]
		words = self.board.words_after_timestamp(timestamp)
		print("sending game state")
		emit("board_state", {"board_size":self.board.size, "words_played":[w.data() for w in list(words)], "timestamp":datetime.utcnow().timestamp()}, to=request.sid, broadcast=False)
		emit("player_state", {"username":current_user.username, **self.hands[current_user.username].data()}, to=request.sid, broadcast=False)

	def on_request_hand(self, data = None):
		# if player doesn't have 7 tiles create new tiles
		hand = self.hands[current_user.username]
		while len(hand.tiles)  < 7:
			hand.tiles.append(self.board.create_new_tile(owner=current_user.username))
		emit("player_state", {"username":current_user.username, **self.hands[current_user.username].data()}, to=request.sid, broadcast=False)

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
		
	@word_dictionary_connection
	def on_played_word(self, data = None):
		print(data)
		curs : sqlite3.Cursor = self.on_played_word.dictionary_cursor
		# words are sent as an array of form:
		# {
		#	is_parent_word : true / false
		#	word : string
		#	new_tiles : array of UUIDs
		#	all_tiles : array of UUIDs
		#	axis : 'h' / 'v'
		# }
		try:
			words = [self.WordProto(dat) for dat in data.get("words")]
		except AssertionError as e:
			emit("played_word_response", {"status":"error", "message":"Assertion error (tiles or axis invalid)", "details":str(e)}, to=request.sid, broadcast=False)
			return

		primary = None

		for word in words:
			if word.is_parent and not primary:
				primary = word
			elif primary and word.is_parent:
				emit("played_word_response", {"status":"error", "message":"Multiple primary words", "word":str(word)}, to=request.sid, broadcast=False)
				return
			# Checks that all new tiles placed are part of the users hand.
			for tile in word.all_tiles:
				if not tile.is_played:
					if tile.owner != current_user.username or not tile in self.hands[current_user.username].tiles:
						emit("played_word_response", {"status":"error", "message":"Played tiles are not thy own", "word":str(word)}, to=request.sid, broadcast=False)
						return
				else:
					if tile.id not in self.board.played_tiles:
						emit("played_word_response", {"status":"error", "message":"One or more external tile is not played", "word":str(word)}, to=request.sid, broadcast=False)
						return
			output = curs.execute("SELECT id, word FROM words WHERE word = ?", (word.word,)).fetchone()
			if not isinstance(output, tuple):
				emit("played_word_response", {"status":"error", "message":"Word not in dictionary", "word":str(word)}, to=request.sid, broadcast=False)
				return
			
		if not self.board.place_tiles({t : primary.new_tile_positions[t.id] for t in primary.new_tiles}):
			emit("played_word_response", {"status":"error", "message":"Board contains tiles in this position", "word":str(primary)}, to=request.sid, broadcast=False)
			return
		
		for tile in primary.new_tiles:
			tile.position = primary.new_tile_positions[tile.id]
		
		this_word = model.Word(current_user.username, tiles=primary.all_tiles, unique_tiles=primary.new_tiles)
		this_word.axis = primary.axis
		for tile in primary.new_tiles:
			self.hands[current_user.username].tiles.remove(tile)
		
		self.board.words.add(this_word)

		print(this_word)
		print(self.hands[current_user.username].tiles)
		emit("played_word_response", {"status":"success", "message":"Word played", "word":str(primary)}, to=request.sid, broadcast=False)
		emit("new_word", {"word" : this_word.data()})
		return

"""	@word_dictionary_connection
	def on_played_word(self, data = None):
		# need the tiles that were played.
		# need the words that were created?? 
		print(data)
		curs : sqlite3.Cursor = self.on_played_word.dictionary_cursor
		output = curs.execute("SELECT id, word FROM words WHERE word = ?", (data["word"],)).fetchone()
		if not isinstance(output, tuple):
			emit("played_word_response", {"status":"error", "message":"Word not in dictionary", "word":data["word"]}, to=request.sid, broadcast=False)
			return
		# validate that all played tiles are users
		tiles = [model.Tile.get_by_uuid(x.get("uuid")) for x in data.get("tiles")]
		if not all([tile.owner == current_user.username for tile in tiles]) \
				or not all([tile in self.hands[current_user.username].tiles for tile in tiles]):
			
		# validate tiles are part of word

		model.Word.validate_axis(data.get("tiles"), data.get("axis"))

		for t in tiles:
			if t.identity not in data.get("word"):
				emit("played_word_response", {"status":"error", "message":"Played tiles are not part of word", "word":data["word"]}, to=request.sid, broadcast=False)
				return
			
		if not self.board.place_tiles(data.get("tiles")):
			print("failed to find place on board.")
			emit("played_word_response", {"status":"error", "message":"Board contains tiles in this position", "word":data["word"]}, to=request.sid, broadcast=False)
			return
		
		this_word = model.Word(current_user.username, tiles)

		for uid in data.get("buildsOn"):
			if uid not in self.board.played_tiles:
				emit("played_word_response", {"status":"error", "message":"Building on tiles that are not in play", "word":data["word"]}, to=request.sid, broadcast=False)
				return 

		for tData in data.get("tiles"):
			x = tData["position"]["x"]
			y = tData["position"]["y"]
			t = model.Tile.get_by_uuid(tData["uuid"])
			t.position = [x,y]

		if self.words.get(current_user.username, None):
			self.words[current_user.username].append(this_word)
		else:
			self.words[current_user.username] = [this_word]
		for tile in tiles:
			self.hands[current_user.username].tiles.remove(tile)
		self.board.words.add(this_word)
		print(self.hands)
		print(self.words)
		emit("played_word_response", {"status":"success", "message":"Word played", "word":data["word"]}, to=request.sid, broadcast=False)
		emit("new_word", {"word" : this_word.data()})"""
		

		
		
		
		

from . import scrabble_routes
