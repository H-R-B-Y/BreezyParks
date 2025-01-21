from .. import schema
import random
from threading import Lock
from datetime import datetime
import uuid

class Tile():
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

	tiles_by_uuid = {}

	def __init__(self, identity, owner):
		assert identity in self.faces
		self.uuid = uuid.uuid4()
		self.id = str(self.uuid)
		self.owner = owner
		self.identity = identity
		self.score = self.scores[identity]
		self.is_vowel = identity in self.vowels

		self.is_placed = False
		self.position = None
		self.is_played = False
		self.played_word = None
		self.played_by = None
		self.played_score = self.score
		
		Tile.tiles_by_uuid[str(self.id)] = self
	
	def __str__(self):
		return self.identity
	
	def data(self):
		return {
			"id" : str(self.id),
			"identity" : self.identity,
			"score" : self.score,
			"pos" : self.position or 'hand',
			"is_placed" : self.is_placed,
			"is_played" : self.is_played,
			"played_by" : self.played_by,
			"played_score" : self.played_score,
			"played_word" : str(self.played_word.id) if self.played_word else None
		}
	
	@classmethod
	def get_by_uuid(cls, id):
		return cls.tiles_by_uuid.get(id, None)

class Hand():
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

class Word():
	words_by_uuid = {}
	def __init__(self, owner : str, tiles=[], unique_tiles = [], score = 0, axis = None):
		self.uuid = uuid.uuid4()
		self.id = str(self.uuid)
		self.tiles = unique_tiles
		self.word = ''.join([str(t) for t in tiles]) or ''
		self.score = 0
		self.owner = owner
		self.init_time = datetime.utcnow()
		self.extends = list(set([(tile.played_word.id if tile.played_word else self.id) for tile in tiles]))
		self.extends.remove(self.id)
		self.axis = axis
		Word.words_by_uuid[str(self.id)] = self
		for tile in tiles:
			tile.is_placed = True
			tile.is_played = True
			tile.played_by = self.owner
			tile.played_word = self

	def data(self):
		return {
			"id" : str(self.id),
			"word" : self.word,
			"tiles" : [t.data() for t in self.tiles],
			"score" : self.score,
			"owner" : self.owner if self.owner else None,
			"extends" : self.extends,
			"axis" : self.axis
		}
	
	@classmethod
	def validate_axis(cls, tiledata, axis):
		if not axis in ["h", "v"]:
			return False
		x = set()
		y = set()

		for t in tiledata:
			p = t["position"]
			x.add(p["x"])
			y.add(p["y"])
		
		if len(x) != 1 or len(y) != 1:
			return False
		
		is_horiz = True if len(y) == 1 else False

		if is_horiz and axis != "h":
			return False
		elif not is_horiz and axis != "v":
			return False
		
		return True


class Board():
	# need some way to remember what tiles are special tiles.
	def __init__(self, size=15):
		self.grid_lock = Lock()
		self.grid = [[None for _ in range(size)] for _ in range(size)] # I hate this approach but it works for now
		self.size = [size, size]
		self.words = set()
		self.special_tiles = self.init_special()
		self.tile_occurance = {t : 0 for t in Tile.faces}
		self.played_tiles = set()

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
		for t, base_freq in Tile.base_distribution.items():
			weights[t] = base_freq / (1 + self.tile_occurance[t])
		return weights

	def normailse_tile_weights(self, weights):
		total_weight = sum(weights.values())
		return {t : weight / total_weight for t, weight in weights.items()}

	def create_new_tile(self, owner = None):
		weigths = self.calculate_tile_weigths()
		prob = self.normailse_tile_weights(weights=weigths)
		t, probs = zip(*prob.items())
		identity = random.choices(t, probs)[0]
		self.tile_occurance[identity] += 1
		return Tile(identity=identity, owner=owner)
	
	def place_tiles(self, tiles):
		print(tiles)
		with self.grid_lock:
			for tile in tiles:
				x = tiles[tile].get("x")
				y = tiles[tile].get("y")
				if tile.id in self.played_tiles:
					return False
				# check there is not already a tile in position
				if self.grid[x][y] != None:
					return False
			for tile in tiles:
				self.grid[x][y] = tile
				self.played_tiles.add(tile.id)
			print(self.grid)
			return True
			
		

