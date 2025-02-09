from .. import schema
import random
from threading import Lock
from datetime import datetime
import uuid
import copy

class Tile():
	faces = [
	"a","b","c","d","e","f",
	"g","h","i","j","k","l",
	"m","n","o","p","q","r",
	"s","t","u","v","w","x",
	"y","z"
	]

	scores = {
	'a': 1, 'b': 3, 'c': 3, 'd': 2, 'e': 1, 'f': 4,
	'g': 2, 'h': 4, 'i': 1, 'j': 8, 'k': 5, 'l': 1,
	'm': 3, 'n': 1, 'o': 1, 'p': 3, 'q': 10, 'r': 1,
	's': 1, 't': 1, 'u': 1, 'v': 4, 'w': 4, 'x': 8,
	'y': 4, 'z': 10
	}

	base_distribution = {
	'a': 9, 'b': 2, 'c': 2, 'd': 4, 'e': 12, 'f': 2,
	'g': 3, 'h': 2, 'i': 9, 'j': 1, 'k': 1, 'l': 4,
	'm': 2, 'n': 6, 'o': 8, 'p': 2, 'q': 1, 'r': 6,
	's': 4, 't': 6, 'u': 4, 'v': 2, 'w': 2, 'x': 1,
	'y': 2, 'z': 1,
	}

	vowels = set(["a","e","i","o","u"])

	tiles_by_uuid = {}

	def __init__(self, identity, owner):
		assert identity in self.faces
		self.uuid = str(uuid.uuid4())
		self.id = str(self.uuid)
		self.owner = owner
		self.identity = identity
		self.score = self.scores[identity]
		self.is_vowel = identity in self.vowels

		self.position = None
		self.is_played = False
		self.played_word = None
		self.played_by = None
		self.played_score = self.score
		self.tile_mult = 1
		self.word_mult = 1
		
		Tile.tiles_by_uuid[str(self.id)] = self
	
	def __str__(self):
		return self.identity
	
	def data(self):
		return {
			"id" : str(self.id),
			"identity" : self.identity,
			"score" : self.score,
			"pos" : self.position or 'hand',
			"is_played" : self.is_played,
			"played_by" : self.played_by,
			"played_score" : self.played_score,
			"played_word" : self.played_word if self.played_word else None
		}
	
	@classmethod
	def init_from_data(cls, owner, data):
		tile = Tile("a", owner)
		del Tile.tiles_by_uuid[tile.uuid]
		tile.id = data["id"]
		Tile.tiles_by_uuid[tile.id] = tile
		tile.identity = data["identity"]
		tile.score = data["score"]
		# print(data)
		tile.position = data["pos"]
		tile.is_played = data["is_played"]
		tile.played_by = data["played_by"]
		tile.played_score = data["played_score"]
		tile.played_word = data["played_word"]
		return tile

	@classmethod
	def get_by_uuid(cls, id):
		return cls.tiles_by_uuid.get(id, None)

class Hand():
	def __init__(self, owner):
		self.tiles = []
		self.score = 0
		self.owner = owner
		self.discardsUsed = 0
		self.discardTimestamp = datetime.utcnow().timestamp()

	def data(self):
		# print(self.score)
		return {
			"tiles" : [t.data() for t in self.tiles],
			"score" : self.score,
			"username" : self.owner,
			"discardsUsed" : self.discardsUsed,
			"discardTimestamp" : self.discardTimestamp,
		}
	
	@classmethod
	def init_from_data(cls, owner, data):
		hand = Hand(owner=owner)
		hand.score = data.get("score", 0)
		hand.tiles = [Tile.init_from_data(owner, t) for t in data.get("tiles", [])]
		hand.discardsUsed = int(data.get("discardsUsed", 0))
		hand.discardTimestamp = data.get("discardTimestamp", datetime.utcnow().timestamp())
		return hand

class Word():
	words_by_uuid = {}
	def __init__(self, owner : str, tiles=[], unique_tiles = [], score = 0, axis = None):
		self.uuid = uuid.uuid4()
		self.id = str(self.uuid)
		self.tiles = unique_tiles
		self.all_tiles = tiles
		self.word = ''.join([str(t) for t in tiles]) or ''
		self.score = 0
		self.score_mult = 1
		self.owner = owner
		self.init_time = datetime.utcnow()
		self.extends = list(set([(tile.played_word if tile.played_word else self.id) for tile in tiles]))
		self.is_primary = False
		self.parent_primary = None
		if self.id in self.extends:
			self.extends.remove(self.id)
		self.axis = axis
		Word.words_by_uuid[str(self.id)] = self
		for tile in unique_tiles:
			tile.is_placed = True
			tile.is_played = True
			tile.played_by = self.owner
			tile.played_word = self.id
		for tile in self.tiles:
			self.score_mult *= tile.word_mult
		# print(f"word created with score_mult: {self.score_mult}")

	def data(self):
		return {
			"id" : str(self.id),
			"word" : self.word,
			"tiles" : [t.data() for t in self.tiles],
			"all_tiles": 
				[
					(t.data() if isinstance(t, Tile) else Tile.get_by_uuid(t).data() if isinstance(t, str) else Tile.get_by_uuid(t.get("id")).data() if isinstance(t, dict) else None) \
						for t in \
							(self.all_tiles if self.all_tiles else self.tiles)],
			"score" : self.score,
			"owner" : self.owner if self.owner else None,
			"extends" : self.extends,
			"axis" : self.axis,
			"is_primary" : self.is_primary,
			"parent_primary" : self.parent_primary,
		}
	
	@classmethod
	def init_from_data(cls, owner, data, tiles):
		# my_tiles = [Tile.init_from_data(t["played_by"], t) for t in data["tiles"]]
		if tiles:
			my_tiles = []
			for tile_data in data["tiles"]:
				if not tile_data["id"] in tiles.keys():
					print("Error, tile duplicated between two primaries!")
					my_tiles.append(Tile.get_by_uuid(tile_data["id"]))
					continue
				my_tiles.append(tiles[tile_data["id"]])
				del tiles[tile_data["id"]]
		else:
			my_tiles = [Tile.get_by_uuid(t["id"]) for t in data["tiles"]]
		word = Word(owner=owner, score=data["score"], axis=data["axis"])
		del Word.words_by_uuid[word.id]
		word.id = data["id"]
		word.word = data["word"]
		Word.words_by_uuid[data["id"]] = word
		word.tiles = my_tiles
		word.all_tiles = [Tile.get_by_uuid(x["id"]) for x in data.get("all_tiles")]
		word.score = data["score"]
		word.extends = data["extends"]
		word.is_primary = data["is_primary"]
		return word
	
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
	
	def calculate_score (self):
		score = 0
		tile : Tile
		for tile in self.tiles:
			tile.played_score = tile.score * tile.tile_mult * self.score_mult
		for tile in self.all_tiles:
			if tile in self.tiles:
				score += tile.played_score
			else:
				score += tile.played_score * self.score_mult
				tile.played_score *= self.score_mult
		# score *= self.score_mult
		self.score = score

	def __repr__ (self):
		return self.word
	
	def __str__ (self):
		return self.word


class Board():
	# need some way to remember what tiles are special tiles.
	def __init__(self, size=15):
		self.gameid = str(uuid.uuid4())
		self.starttime = datetime.utcnow().timestamp()
		self.grid_lock = Lock()
		self._size = size
		self.grid = [[None for _ in range(size)] for _ in range(size)] # I hate this approach but it works for now
		self.special_grid = [[None for _ in range(size)] for _ in range(size)]
		self.special_tile_vector = []

		[self.create_tile_special_squares(1, size // 2, 3) for _ in range(28)]
		[self.create_word_special_squares(1, size //2, 3) for _ in range(24)]
		
		self.words = set()
		self.primaryWords = set()

		self.tile_occurance = {t : 0 for t in Tile.faces}
		self.played_tiles = set()

	def print_words(self):
		words = '\n'.join(str(x) for x in self.words)
		# print(words)

	def create_tile_special_squares(self, range_min, range_max, max_mult):
		axis = random.choice(['n','e','s','w'])
		dist = random.randint(max(1, range_min), min(range_max, self._size // 2))
		x = ((self._size // 2) + (dist * (-1 if axis == 'w' else 1))) if axis in ['e','w'] else random.randint(0, self._size - 1)
		y = ((self._size // 2) + (dist * (-1 if axis == 'n' else 1))) if axis in ['n','s'] else random.randint(0, self._size - 1)
		if self.special_grid[x][y] != None:
			return False
		if max_mult > 2:
			mult = random.randint(2, max_mult)
		else:
			mult = 2
		self.special_grid[x][y] = ["t", mult]
		self.special_tile_vector.append([x,y,"t",mult])
		return True

	def create_word_special_squares(self, range_min, range_max, max_mult):
		axis = random.choice(['n','e','s','w'])
		dist = random.randint(max(1, range_min), min(range_max, self._size // 2))
		x = ((self._size // 2) + (dist * (-1 if axis == 'w' else 1))) if axis in ['e','w'] else random.randint(0, self._size - 1)
		y = ((self._size // 2) + (dist * (-1 if axis == 'n' else 1))) if axis in ['n','s'] else random.randint(0, self._size - 1)
		if self.special_grid[x][y] != None:
			return False
		if max_mult > 2:
			mult = random.randint(2, max_mult)
		else:
			mult = 2
		self.special_grid[x][y] = ["w", mult]
		self.special_tile_vector.append([x,y,"w",mult])
		return True
		
	@property
	def size(self):
		with self.grid_lock:
			return self._size

	def words_after_timestamp(self, timestamp):
		# print(self.primaryWords)
		if timestamp:
			time = datetime.fromtimestamp(timestamp)
			if time > datetime.utcnow():
				return None
			return {w for w in self.primaryWords if w.init_time > time}
		else:
			return self.primaryWords
		
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
	
	def print_board_state(self):
		for row in self.grid:
			for square in row:
				print("  " if square is None else square.identity + " ", end="")
			print("")

	def place_tiles(self, tiles):
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
				x = tiles[tile].get("x")
				y = tiles[tile].get("y")
				tile.position = tiles[tile]
				self.grid[x][y] = tile
				# print(f"checking x{x} y{y} for special: {self.special_grid[x][y]} for {tile.identity}")
				if self.special_grid[x][y] != None:
					sp = self.special_grid[x][y]
					# print(sp)
					if sp[0] == "t":
						tile.tile_mult = sp[1]
					elif sp[0] == "w":
						tile.word_mult = sp[1]
				self.played_tiles.add(tile.id)
		return True
			
	def increment_size(self, increment = 1):
		"""
		Please note 1 is 1 on all sides, resulting in a new side length of +2
		New board is always i * 2 + size
		"""
		# print(f"incrementing board by {increment}")
		new_inc = increment * 2
		new_size = new_inc + self.size
		new_board = [[None for _ in range(new_size)] for _ in range(new_size)]
		new_special = [[None for _ in range(new_size)] for _ in range(new_size)]
		# self.print_board_state()
		print()
		with self.grid_lock:
			current_board_state = self.grid
			for x in range(len(current_board_state)):
				for y in range(len(current_board_state[0])):
					if self.special_grid[x][y] != None:
						new_special[increment + x][increment + y] = self.special_grid[x][y]
					if current_board_state[x][y] != None:
						new_board[increment + x][increment + y] = current_board_state[x][y]
						print(f"{current_board_state[x][y]} at new position: {increment + x} {increment + y}")
						current_board_state[x][y].position["x"] = increment + x
						current_board_state[x][y].position["y"] = increment + y
						print(f"{current_board_state[x][y]} at new position: {increment + x} {increment + y}")
			self.grid = new_board
			self.special_grid = new_special
			old_size = self._size
			self._size = new_size
		for st in self.special_tile_vector:
			st[0] += increment
			st[1] += increment
		[self.create_tile_special_squares((old_size // 2) + 1, new_size // 2, int(3 + self._size / 6)) for i in range(10)]
		[self.create_word_special_squares((old_size // 2) + 1, new_size // 2, int(3 + self._size / 6)) for i in range(6)]
		# self.print_board_state()
		return True
	
	def data(self, *args, **kwargs):
		# print(self.played_tiles)
		# print(Tile.tiles_by_uuid)
		return {
			"id" : self.gameid,
			"started_at" : self.starttime,
			"board_size" : self._size,
			"primary_words" : [w.data() for w in self.primaryWords],
			"all_words" : [w.data() for w in self.words],
			"letter_mult_array" : self.special_tile_vector,
			"all_tiles" : [Tile.get_by_uuid(t).data() for t in self.played_tiles],
			"data" : list(args),
			**kwargs,
		}
	
	
	def add_played_word_from_data(self, data, tiles):
		word = Word.init_from_data(data["owner"], data, tiles)
		# add tiles to grid
		for tile in word.tiles:
			# print(tile.id)
			self.grid[tile.position["x"]][tile.position["y"]] = tile
			self.played_tiles.add(tile.id)
		# add word to played words / primary words
		self.words.add(word)
		self.primaryWords.add(word)
		# dont bother with score just load from data 

	@classmethod
	def init_from_data(cls, data):
		board = Board(data["board_size"])
		board.special_grid =[[None for _ in range(data["board_size"])] for _ in range(data["board_size"])]
		for x, y, t, m in data["letter_mult_array"]:
			board.special_grid[x][y] = [t, m]
		board.special_tile_vector = data["letter_mult_array"]
		# What happens when a word is played? 
		tiles = {}
		for tile in data["all_tiles"]:
			if tile["id"] in tiles.keys():
				print(f"Duplicate tile found in dataset! {tile} and {tiles[tile['id']]}")
			else:
				tiles[tile["id"]] = Tile.init_from_data(tile["played_by"], tile)
		primary_ids = []
		for word in data["primary_words"]:
			board.add_played_word_from_data(word, tiles)
			primary_ids.append(word["id"])
		for word in data["all_words"]:
			if word["id"] not in primary_ids:
				board.words.add(Word.init_from_data(word["owner"], word, tiles=None))
		board.gameid = data["id"]
		return board




