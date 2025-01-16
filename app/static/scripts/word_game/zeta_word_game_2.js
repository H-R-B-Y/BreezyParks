class Player {
	constructor(username){
		this.username = username;
		this.sprite = null;
		this.usernameText = null;
		this.ready = null;
	}

	loadSprite (drawContainer){
		this.usernameText = new PIXI.Text({text:this.username, style:{fill:"#fff"}});
		this.usernameText.anchor.set(0.5,1);
		
		fetch('/'+this.username+'/sprite').then(response => {
			if (!response.ok){throw new Error("Not OK")};
			return response.json();
		}).then(async data => {
			var texture = await PIXI.Assets.load(data.sprite);
			this.sprite = PIXI.Sprite.from(data.sprite);
		}).catch(async error => {
			console.log(error);
			var texture = await PIXI.Assets.load("/static/images/generichamster.png");
			this.sprite = PIXI.Sprite.from("/static/images/generichamster.png");
		}).then(() => {
			this.sprite.width = 64;
			this.sprite.height = 64;
			this.sprite.anchor.set(0.5,0.5);
			this.setPosition(parseInt(window.innerWidth/2), parseInt(window.innerHeight/2));
			this.sprite.zindex = 5; // why do we set it to 5?
			drawContainer.addChild(this.sprite);
			drawContainer.addChild(this.usernameText);
			this.ready = true;
		});
	}
	setPosition (x, y) {
		// this needs to not only set the position of the sprite 
		// but also the position of the name/anything attached to the player
		if (this.sprite){
			this.sprite.x = x;
			this.sprite.y = y;
		}
		if (this.usernameText){
			this.usernameText.x = x;
			this.usernameText.y = y - parseInt(this.sprite.height/2);
		}
	}
}

class Grid {
	constructor(game, parentContainer, gridWidth, gridHeight, squareSize) {
		this.game = game

		this.gridWidth = gridWidth;
		this.gridHeight = gridHeight;
		this.squareSize = squareSize;

		this.parentContainer = parentContainer;

		this.grid = []; // 2D array to store squares


		this.context = null;
		
		this.container = new PIXI.Container({}); // Container for the grid
		this.container.interactive = true;
		this.container.on("pointerleave", (() => {this.game.dropContext = null;}).bind(this))

		this.container.x = (game.app.screen.width / 2) - (squareSize * gridWidth)/2;
		this.container.y = (game.app.screen.height / 2) - (squareSize * gridHeight)/2;

		parentContainer.addChild(this.container);

		this.initGrid();

	}

	initGrid() {
		for (let y = 0; y < this.gridHeight; y++) {
			const row = [];
			for (let x = 0; x < this.gridWidth; x++) {
				const square = new PIXI.Graphics();
				square.rect(0, 0, this.squareSize, this.squareSize)
					.fill("#1f2122")
					.rect(0, 0, this.squareSize, this.squareSize)
					.stroke({ color: 0xffffff, pixelLine: false, width: 1 })

				// Set position
				square.x = x * this.squareSize;
				square.y = y * this.squareSize;
				square.parentContainer = this.container;

				// Store its grid position
				square.gridPosition = { x, y };
				square.containsTile = false;

				// Add event listeners
				square.interactive = true;
				square.buttonMode = true;
				square.on('pointerover', () => this.highlightSquare(square));
				square.on('pointerout', () => this.unhighlightSquare(square));
				square.on('pointerdown', () => this.selectSquare(square));

				// Add to container and row
				this.container.addChild(square);
				row.push(square);
			}
			this.grid.push(row);
		}
	}

	highlightSquare(square) {
		square.tint = 0xAAAAAA; // Highlight color
		this.game.dropContext = square;
	}

	unhighlightSquare(square) {
		square.tint = 0xFFFFFF; // Default color
	}

	selectSquare(square) {
		square.fill(0xFF0000).rect(0, 0, this.squareSize, this.squareSize); // Change to red
	}

	centerGrid() {
		this.container.x = (this.game.app.screen.width / 2) - (this.squareSize * this.gridWidth)/2;
		this.container.y = (this.game.app.screen.height / 2) - (this.squareSize * this.gridHeight)/2;
	}

	assignTileToSquare( tile, square ) {
		if (square.containsTile === false || tile.onSquare === square)
		{square.containsTile = tile;}
		else {console.error(`Trying to place tile ${tile.identity} on square that already contains tile ${square.containsTile.identity}.`);throw new Error("Tile already populated");}
	}

	removeTileFromSquare ( tile, square ) {
		if (square.containsTile === tile && !square.containsTile.is_played) {
			square.containsTile = false;
		}
		else if (square.containsTile !== tile) {console.error("Attempted to remove tile from a square that doesn't parent it.")}
		else {console.error(`Attempted to remove a tile that has already been played.`)}
	}
}

class Tile {
	constructor (game, parentContainer, identity, score, parentWord) {
		this.game = game;
		this.parentContainer = parentContainer;

		this.identity = identity;
		this.score = score;

		this.container = new PIXI.Container();
		this.container.interactive = true;

		this.graphic = null;
		this.text = null;

		this.size = 30;

		this.isPickedUp = false;

		this.is_placed = false;

		// This section for played tile information sent from server
			this.is_played = false;
			this.played_score = false;
			this.played_by = null;
		// end 

		this.onSquare = false;
		this.position = null;

		this.onGlobalMouseMove = this.onDragTile.bind(this);
		this.onGlobalMouseUp = this.onReleased.bind(this);

		parentContainer.addChild(this.container);

		this.parentWord = parentWord || null;
	}

	createGraphic (tileSize, color) {
		this.size = tileSize || 30;
		color = color || 0xA0A000;
		if (this.graphic) {
			this.graphic.destroy();
			this.text.destroy();
		}
		this.graphic = new PIXI.Graphics();
		this.graphic.rect(0, 0, tileSize, tileSize).fill(color).rect(0, 0, tileSize, tileSize).stroke({ color: 0xffffff, pixelLine: true, width: 1 });
		this.text = new PIXI.Text({text:this.identity || "#err", style:{fill:"#fff", fontSize: tileSize * 0.6, align: 'center'}});
		this.text.anchor.set(0.5,0.5);
		this.text.x = this.graphic.width / 2;
		this.text.y = this.graphic.height / 2;
		this.container.addChild(this.graphic);
		this.container.addChild(this.text);
		
		// On mouse down "pickup" the tile.
		this.container.on("pointerdown", this.onClicked.bind(this));
		this.container.on("pointerenter", this.addToContext.bind(this))
		this.container.on("pointerleave", this.removeFromContext.bind(this))
	}

	setPosition (x,y) {
		this.container.x = x;// - (this.size / 2);
		this.container.y = y;// - (this.size / 2); 
	}

	del () {
		this.text.destroy();
		this.graphic.destroy();
		this.container.destroy();
	}

	changeParent (newParent) {
		console.log(newParent);
		this.parentContainer.removeChild(this.container);
		this.parentContainer = newParent;
		this.parentContainer.addChild(this.container);
	}

	onClicked (event) { // Click event is unique as it should only trigger in the context of the tile, while drag and release are in the context of the window.
		this.isPickedUp = true;
		this.game.holdingTile = true;
		if (this.is_placed) {			
			if (event.data.originalEvent.pointerType === 'mouse' && event.data.originalEvent.button == 2)
			{
				this.returnToHandOnRightClick();
				return;
			}
			this.game.dropContext = this.onSquare;
		}
		this.changeParent(this.game.uiContainer);
		this.setPosition(event.pageX - (this.size / 2), event.pageY - (this.size / 2));
		this.container.interactive = false;
		this.container.interactiveChildren = false;
		window.addEventListener("pointermove", this.onGlobalMouseMove);
		window.addEventListener("pointerup", this.onGlobalMouseUp);
	}

	onDragTile (event) {
		// Update position
		const rect = this.game.app.canvas.getBoundingClientRect();
		const mouseX = event.clientX - rect.left;
		const mouseY = event.clientY - rect.top;

		this.setPosition(mouseX - this.size / 2, mouseY - this.size / 2);
	}

	updateGlobalDropContext (what) {
		what = what || this;
		if (!this.isPickedUp) {
			this.game.dropContext = what;
		}
	}
	addToContext () {
		if (!this.is_placed && !this.is_played)
		{this.updateGlobalDropContext(this);}
		else if (this.game.holdingTile) {
			this.updateGlobalDropContext(null);
		}
	}
	removeFromContext () {
		this.updateGlobalDropContext(null);
	}

	onReleased (event) {
		this.isPickedUp = false;
		this.game.holdingTile = false;
		// Stop tracking the tile globally
		window.removeEventListener("pointermove", this.onGlobalMouseMove);
		window.removeEventListener("pointerup", this.onGlobalMouseUp);

		this.container.interactive = true;
		this.container.interactiveChildren = true;
		this.game.handleTilePlacement(this);
	}

	placeOnSquare ( square ) {
		if (this.is_played) {throw new Error("Cannot place a tile that is already played.")}
		this.is_placed = true;
		this.changeParent(square.parentContainer);
		this.setPosition(square.x, square.y);
		this.position = square.gridPosition;
		this.onSquare = square;
	
	}

	returnToHandOnRightClick () {
		if (this.onSquare)
		{
			this.game.removeTileFromGrid( this, this.onSquare);
		} else {
			this.returnToHand();
		}
	}

	returnToHand (  ) {
		if (this.is_played) {throw new Error("Cannot return a tile to hand that is not part of your hand.")}
		this.is_placed = false;
		this.changeParent(this.game.ui.handContainer);
		this.game.ui.orderTilesInHand();
		this.position = null;
		this.onSquare = false;
	}

}

class Word {
	/*
	A word is a collection of tiles THAT HAS BEEN PLAYED,
	they will be sent from the server in some form
	*/
	constructor (game, tiles, word) {
		this.game = game;
		this.board = game.board;
		this.tiledata = tiles;
		this.word = word;
		this.meaning = null;
	}
}

class UI {
	constructor (game, parentContainer) {
		this.tSize = 50;
		this.tMargin = 20;
		this.handData = [];
		this.hand = [];
		this.score = 0;
		
		this.game = game;
		this.parentContainer = parentContainer;

		this.handContainer = new PIXI.Container();
		this.handGraphic = new PIXI.Graphics();
		this.draw_handContainer();
		this.handContainer.y = game.app.screen.height - this.handGraphic.height;
		this.handContainer.x = (game.app.screen.width - this.handGraphic.width)/ 2;
		
		this.submitButton = new PIXI.Container();
		this.drawSubmitButton();
		this.submitButton.y = this.handContainer.y - this.submitButtonGraphic.height;
		this.submitButton.x = this.handContainer.x + (this.handGraphic.width / 2) - (this.submitButtonGraphic.width / 2);

		
		this.handContainer.addChild(this.handGraphic);
		this.parentContainer.addChild(this.submitButton);
		this.parentContainer.addChild(this.handContainer);
		this.game.resizeEvents.push(this.onResizeEvent.bind(this));
	}

	drawSubmitButton () {
		this.submitButtonGraphic = new PIXI.Graphics();
		this.submitButtonText = new PIXI.Text(
			{text:"submit", style:{fill:"#fff", fontSize: 25, align: 'center'}}
		);
		this.submitButton.interactive = true
		this.submitButton.buttonMode = true;
		this.submitButton.cursor = 'not-allowed';
		this.submitButton.addChild(this.submitButtonGraphic);
		this.submitButton.addChild(this.submitButtonText);
		this.submitButtonGraphic
			.rect(0, 0, (this.tMargin * 2) + this.submitButtonText.width, (this.tMargin * 2) + this.submitButton.height).fill(0x252525);
		//this.submitButtonText.anchor.set(0.5,0.5)
		this.submitButtonText.x = this.tMargin;
		this.submitButtonText.y = this.tMargin;
	}

	draw_handContainer () {
		this.handGraphic
			.rect(0, 0, this.tMargin + ((this.tSize + this.tMargin) * 7), this.tMargin * 2 + this.tSize)
			.fill(0xAFAF00)
	}

	updateScore (score) {
		// update the score but also make sure to update any text objects.
		this.score = score;
	}

	swapTilesInHand (tile, tile2) {
		let pos1 = this.hand.indexOf(tile);
		let pos2 = this.hand.indexOf(tile2);
		this.hand[pos1] = tile2;
		this.hand[pos2] = tile;
		tile.returnToHand();
	}

	updateHand (handData) {
		// update the hand graphics here.
		let checked = []
		this.handData = handData;
		if (this.hand.length != 0){
		for (let i = 0; i < this.handData.length; i++){ // loop through all the hand tiles sent from server
			let c = this.handData[i].identity;
			for (let p = 0; p < this.hand.length; i++){ // loop through tiles currently in hand so we can create the new tiles
				if (this.hand[i] in checked){continue;}
				if (this.hand[i].identity == c){
					checked.push(this.hand[i]);
				}
				else {
					this.hand.push(new Tile(this.game, this.handContainer, c, this.handData[i].score));
				}
			}
		}}
		else {
			for (let i = 0; i < this.handData.length; i++){
				let c = this.handData[i].identity;
				this.hand.push(new Tile(this.game, this.handContainer, c, this.handData[i].score));
			}
		}
		this.orderTilesInHand();
	}

	orderTilesInHand () {
		var x_pos = this.tMargin;
		for (let i = 0; i < this.hand.length; i++) 
		{
			let t = this.hand[i];
			if (t.is_placed){
				continue;
			}
			if (!t.graphic){t.createGraphic(this.tSize)};
			t.setPosition(x_pos, this.tMargin);
			x_pos += this.tSize + this.tMargin;
		}
	}

	onResizeEvent () {
		this.handContainer.y = game.app.screen.height - this.handGraphic.height;
		this.handContainer.x = (game.app.screen.width - this.handGraphic.width)/ 2;
		this.submitButton.y = this.handContainer.y - this.submitButtonGraphic.height;
		this.submitButton.x = this.handContainer.x + (this.handGraphic.width / 2) - (this.submitButtonGraphic.width / 2);
	}

	enableSubmitButton () {
		this.submitButton.cursor = 'pointer';
		this.submitButton.on("pointerup", this.submitButtonPressed.bind(this));
	}

	submitButtonPressed () {
		console.log("submitting words!")
	}

	disableSubmitButton () {
		this.submitButton.cursor = 'not-allowed';
		this.submitButton.off("pointerup");
	}
}

class GameState {
	constructor (namespace, username, canvas) {
		this.app = new PIXI.Application();
		this.app.init({
			canvas : canvas,
			background :  0x1F2122,
			resizeTo : window,
		});

		this.resizeEvents = [];
		this.gameContainer = new PIXI.Container();
		this.gameContainer.interactive = true;
		this.app.stage.addChild(this.gameContainer);

		this.uiContainer = new PIXI.Container();
		this.app.stage.addChild(this.uiContainer);

		this.currentPlayer = new Player(username);
		//this.currentPlayer.loadSprite(this.gameContainer); // will just leave the player in the corner for now.

		this.ui = null;
		this.board = null;

		new ResizeObserver(this.onResize.bind(this)).observe(document.documentElement);
		window.addEventListener("resize", this.onResize.bind(this));

		this.socket = io("/zeta/"+namespace);
		this.socket_initial_recv = 0;

		this.socket.on("connect", this.onSocketConnected.bind(this));
		this.socket.on("disconnect", this.onSocketDisconnected.bind(this));

		this.holdingTile = false;
		this.dropContext = null;

		this.wordCheckTimeout = null;
	}

	onUpdateGameState (data) {
		if (!this.board && !data.board_size){
			throw new Error("No board size returned from server");
		}

		if (this.board === null){
			this.board = new Grid(this, this.gameContainer, data.board_size[0], data.board_size[1], 50);
			this.resizeEvents.push(this.board.centerGrid.bind(this.board));
		}
		
		if (this.ui === null){
			this.ui = new UI(this, this.uiContainer);
		}

		setTimeout((() => {if (this.ui.hand.length < 7) {this.socket.emit("request_hand", {"timestamp" : null})};}).bind(this), 100);
	}

	onUpdatePlayerState (data) {
		if (!data.username || data.username != this.currentPlayer.username){throw new Error("Wrong player data returned from server.")}
		if (Object.hasOwn(data, "tiles")){
			if (this.ui.handData != data.tiles){this.ui.updateHand(data.tiles)};
		}else{throw new Error("No hand provided")}
		if (Object.hasOwn(data, "score")){
			if (this.ui.score != data.score){this.ui.updateScore(data.score)};
		}else{throw new Error("No Score Provided")}
	}

	onSocketConnected () {
		if (this.socket_initial_recv) {return;}
		this.socket_initial_recv = 1;
		this.socket.on("board_state", this.onUpdateGameState.bind(this));
		this.socket.on("player_state", this.onUpdatePlayerState.bind(this));
		this.socket.emit("request_game_state", {"timestamp" : null});
	}

	onSocketDisconnected () {
		console.log("lost connection to socket.")
		// should handle safely here or server gets spammed with requests.
	}

	onResize () {
		for (let i = 0; i < this.resizeEvents.length; i++) {this.resizeEvents[i]()};
	}

	placeTileOnGrid ( tile, square ) {
		if (square.containsTile && square.containsTile !== tile) {throw new Error("Square already contains a letter.")}
		if (tile.is_played) {throw new Error("Cannot place a tile that is played")};
		if (tile.is_placed) {this.board.removeTileFromSquare(tile, tile.onSquare)};
		this.board.assignTileToSquare( tile, square );
		tile.placeOnSquare( square );
	}
	removeTileFromGrid ( tile, square ) {
		if (!square.containsTile) {throw new Error("Cannot remove tile from empty square.")}
		this.board.removeTileFromSquare( tile, square );
		tile.returnToHand();
	}

	handleTilePlacement ( tile ) {
		var context = this.dropContext;
		if (context && this.board.grid.some(innerArray => innerArray.some(obj => obj === context))){
			this.placeTileOnGrid( tile, this.dropContext );
			clearTimeout(this.wordCheckTimeout);
			this.wordCheckTimeout = setTimeout(this.checkWords.bind(this), 300);
		} else if ( context && this.ui.hand.includes(context) && context.is_placed != true) {
			if (tile.is_placed){this.removeTileFromGrid( tile, tile.onSquare )};
			this.ui.swapTilesInHand(tile, context);
		} else {
			if (tile.onSquare) {
				this.removeTileFromGrid(tile, tile.onSquare);
			} else {
				tile.returnToHand();
			}
		}
	}

	async wordIsLegal( word ){
		try {
			// load word list on server side
			let addr = 0; // https://github.com/dwyl/english-words 
			console.log("checking word: ", addr)
			const response = await fetch(addr);
			if (response.status == 404) {return false;}
			else {
				let jsn = await response.json();
				//word.meaning = jsn;
				console.log(jsn);
				return true;
			}
		} catch (error) {
			console.error("encountered error", error)
			return false;
		}
		return false;
	}

	async processWords ( words ) {
		const result = await Promise.all(words.map(word => this.wordIsLegal(word)));
		const allSame = result.every(result => result === true);
		if (allSame) {
			console.log("Words are ok!");
		}
		else {
			console.log("One or more word is not ok!");
		}
	}

	checkWords (  ) {
		let tilesToCheck = [];
		for (let i = 0; i < this.ui.hand.length; i++){if (this.ui.hand[i].is_placed){tilesToCheck.push(this.ui.hand[i])}};
		// validate that any and all tile placements are valid
		//console.log(tilesToCheck);
		let primary_word = '';
		let rows = new Set();
		let cols = new Set();
		tilesToCheck.forEach(t => {
			rows.add(t.position.y);
			cols.add(t.position.x);
		});
		if (rows.size !== 1  && cols.size !== 1) {return ;}
		let is_horiz = rows.size === 1;
		//console.log(`is horiz: ${is_horiz}`);
		if ( is_horiz ) {
			let row = [...rows][0]; // This is so foul lol
			// ... is spread (converts iterable to array)
			// then index 0 ;
			let cols_to_check = tilesToCheck.map(t => t.position.x)
			//console.log(cols_to_check)
			let min_col = Math.min(...cols_to_check);
			let max_col = Math.max(...cols_to_check);
			//console.log(`iterating: ${min_col} and ${max_col} at row ${row}`)
			for (let col = min_col; col < max_col + 1; col++) {
				let tile = this.board.grid[row][col].containsTile;
				//console.log(`Tile ${tile}`);
				if (tile){primary_word += tile.identity}
				else {break};
			}
		} else {
			let col = [...cols][0]; 
			let rows_to_check = tilesToCheck.map(t => t.position.y);
			let min_row = Math.min(...rows_to_check);
			let max_row = Math.max(...rows_to_check);
			for (let row = min_row; row < max_row + 1; row++) {
				let tile = this.board.grid[row][col].containsTile;
				if (tile){primary_word += tile.identity}
				else {break};
			}
		}
		let words = []
		console.log(primary_word);
		words.push(primary_word);


		// Check for adjacent words:
		this.getAdjacentWords(tilesToCheck, is_horiz).forEach((str) => {
			words.push(str);
		});

		console.log(words);
		// create an async pool to check each word is a word in the dictionary
		// See dict api: 
		// https://api.dictionaryapi.dev/api/v2/entries/en/<word>
		this.processWords(words);
	}

	getAdjacentWords( placedTiles, is_horiz ) {
		let words = [];
		let board = this.board.grid;
		placedTiles.forEach(({position : {y : r, x: c}, identity: char}) => {
			// NOTE: if tiles store the words they are part of when places this should be reduced.
			let adjWord = "";
			//console.log(`col ${c} and row ${r} with tile ${char}`);
			if (is_horiz) {
				let topPart = "";
				for (let row = r; row >= 0; row--){ // loop UPWARDS from the character to 0;
					if(board[row][c].containsTile && row !== r){ // this check comes first as it wil occur most often
						topPart = board[row][c].containsTile.identity + topPart;
					} else if (row == r) {
						topPart = char + topPart;
					} else {
						break;
					};
				};
				let bottomPart = "";
				for (let row = r + 1; row < board.length; row++) { // Loop downwards from the square under 0 to max board;
					if (board[row][c].containsTile) {
						bottomPart += board[row][c].containsTile.identity
					} else {
						break;
					}
				}
				adjWord = topPart + bottomPart;
				//console.log(`horiz ${is_horiz} with word ${adjWord}`)
			} else {
				let leftPart = "";
				for (let col = c; col >= 0; col--) { // loop through columns right to left until 0
					if (board[r][col].containsTile && col !== c) { // this check comes first as it wil occur most often
						leftPart += board[r][col].containsTile.identity + leftPart;
					} else if (col === c) {
						leftPart = char + leftPart;
					} else {
						break ;
					}
				}
				let rightPart = "";
				for (let col = c + 1; col < board[0].length; col++) { // loop through column left to right from the right of the tile until max board
					if (board[r][col].containsTile) {
						rightPart += board[r][col].identity;
					} else {
						break ;
					}
				}
				adjWord = leftPart + rightPart;
				//console.log(`horiz ${is_horiz} with word ${adjWord}`)
			}
			if (adjWord.length > 1) {
				words.push(adjWord);
			}
		});
		return words;
	}
}

var game = null;
const initialPath = new URL(window.location.href).pathname;
const currentPath = initialPath.split('/')[1] || '';
document.addEventListener("DOMContentLoaded", async () => {
	const zetaCanvas = document.getElementById("zetaCanvas");
	game = new GameState(currentPath, zetaCanvas.dataset.userid, zetaCanvas);
	document.addEventListener('contextmenu', (e) => e.preventDefault());
	setTimeout( () => {document.getElementById("zetaCanvas").style.display = "block";}, 100);
})