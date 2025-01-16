from flask import Blueprint, request, jsonify, make_response, render_template
from .. import schema, app, zetaSocketIO
from threading import Lock
from flask_login import login_required, current_user
from flask_socketio import Namespace, emit
from functools import wraps
from . import model
from requests import get
from datetime import datetime 

scrabble_bp = Blueprint("scrabble_ge", __name__)


class zeta_word_game(zetaSocketIO.zeta):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# parent has active users which contains current players
		# but we also need to keep track of all players in the game
		self.totalPlayers = set() 


		self.board = model.board()
		self.hands = {} # in form {user : hand}
		self.words = {} # in form {user : [words]}

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
				self.hands[current_user.username] = model.hand(current_user)
				self.words[current_user.username] = []
		
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
		emit("board_state", {"board_size":self.board.size, "words_played":list(words), "timestamp":datetime.utcnow().timestamp()}, to=request.sid, broadcast=False)
		emit("player_state", {"username":current_user.username, **self.hands[current_user.username].data()}, to=request.sid, broadcast=False)

	def on_request_hand(self, data = None):
		# if player doesn't have 7 tiles create new tiles
		hand = self.hands[current_user.username]
		while len(hand.tiles)  < 7:
			hand.tiles.append(self.board.create_new_tile())
		emit("player_state", {"username":current_user.username, **self.hands[current_user.username].data()}, to=request.sid, broadcast=False)
			
		
		

from . import scrabble_routes
