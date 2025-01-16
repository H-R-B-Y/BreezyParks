from .. import schema
import random
from threading import Lock
from datetime import datetime

class tile():
	faces = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
	scores = {
		'a': 1,
		'b': 3,
		'c': 3,
		'd': 2,
		'e': 1,
		'f': 4,
		'g': 2,
		'h': 4,
		'i': 1,
		'j': 8,
		'k': 5,
		'l': 1,
		'm': 3,
		'n': 1,
		'o': 1,
		'p': 3,
		'q': 10,
		'r': 1,
		's': 1,
		't': 1,
		'u': 1,
		'v': 4,
		'w': 4,
		'x': 8,
		'y': 4,
		'z': 10
	}

	base_distribution = {'a': 9, 'b': 2, 'c': 2, 'd': 4, 'e': 12, 'f': 2,
    'g': 3, 'h': 2, 'i': 9, 'j': 1, 'k': 1, 'l': 4,
    'm': 2, 'n': 6, 'o': 8, 'p': 2, 'q': 1, 'r': 6,
    's': 4, 't': 6, 'u': 4, 'v': 2, 'w': 2, 'x': 1,
    'y': 2, 'z': 1,
	}

	vowels = set(["a","e","i","o","u"])
	def __init__(self, identity):
		assert identity in self.faces
		self.identity = identity
		self.score = self.scores[identity]
		self.is_vowel = identity in self.vowels

		self.is_placed = False
		self.position = None
		self.is_played = False
		self.played_by = None
		self.played_score = self.score
	
	def __str__(self):
		return self.identity
	
	def data(self):
		return {
			"identity" : self.identity,
			"score" : self.score,
			"pos" : self.position or 'hand',
			"is_placed" : self.is_placed,
			"is_played" : self.is_played,
			"played_by" : self.played_by,
			"played_score" : self.played_score
		}

class hand():
	def __init__(self, owner : schema.User):
		self.tiles = []
		self.score = 0
		self.owner = owner

	def data(self):
		return {
			"tiles" : [t.data() for t in self.tiles],
			"score" : self.score,
			"username" : self.owner.username
		}

class word():
	def __init__(self, owner : schema.User, tiles=[], start=[0,0], end = [0,0], score = 0):
		self.tiles = tiles
		self.word = [str(t) for t in tiles] or ''
		self.score = 0
		self.owner = owner
		self.init_time = datetime.utcnow()

class board():
	# need some way to remember what tiles are special tiles.
	def __init__(self, size=15):
		self.grid_lock = Lock()
		self.grid = [[None for _ in range(size)] for _ in range(size)] # I hate this approach but it works for now
		self.size = [size, size]
		self.words = set()
		self.special_tiles = self.init_special()
		self.tile_occurance = {t : 0 for t in tile.faces}

	def init_special(self):
		return []
	
	def words_after_timestamp(self, timestamp):
		if timestamp:
			time = datetime.fromtimestamp(timestamp)
			if time > datetime.utcnow():
				return None
			return {w for w in self.words if w.init_time > time}
		else:
			return self.words
		
	def calculate_tile_weigths(self):
		weights = {}
		for t, base_freq in tile.base_distribution.items():
			weights[t] = base_freq / (1 + self.tile_occurance[t])
		return weights

	def normailse_tile_weights(self, weights):
		total_weight = sum(weights.values())
		return {t : weight / total_weight for t, weight in weights.items()}

	def create_new_tile(self):
		weigths = self.calculate_tile_weigths()
		prob = self.normailse_tile_weights(weights=weigths)
		t, probs = zip(*prob.items())
		identity = random.choices(t, probs)[0]
		self.tile_occurance[identity] += 1
		return tile(identity=identity)
		

