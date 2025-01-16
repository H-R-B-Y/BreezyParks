
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
	constructor(app, parentContainer, gridWidth, gridHeight, squareSize) {
		this.app = app; // PIXI.Application instance
		this.gridWidth = gridWidth;
		this.gridHeight = gridHeight;
		this.squareSize = squareSize;
		this.parentContainer = parentContainer;
		this.grid = []; // 2D array to store squares
		this.container = new PIXI.Container(); // Container for the grid
		this.container.x = (app.screen.width / 2) - (squareSize * gridWidth)/2;
		this.container.y = (app.screen.height / 2) - (squareSize * gridHeight)/2;
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
					.stroke({ color: 0xffffff, pixelLine: true, width: 1 })

				// Set position
				square.x = x * this.squareSize;
				square.y = y * this.squareSize;

				// Store its grid position
				square.gridPosition = { x, y };

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
	}

	unhighlightSquare(square) {
		square.tint = 0xFFFFFF; // Default color
	}

	selectSquare(square) {
		console.log(`Square selected at: ${square.gridPosition.x}, ${square.gridPosition.y}`);
		square.fill(0xFF0000).rect(0, 0, this.squareSize, this.squareSize); // Change to red
	}

	centerGrid() {
		this.container.x = (app.screen.width / 2) - (this.squareSize * this.gridWidth)/2;
		this.container.y = (app.screen.height / 2) - (this.squareSize * this.gridHeight)/2;
	}
}

class Tile {
	constructor (app, parentContainer, identity, score) {
		this.app = app;
		this.identity = identity;
		this.score = score;

		this.parentContainer = parentContainer;
		this.container = new PIXI.Container();
		
		this.square = new PIXI.Graphics();
		this.container.addChild(this.square);


		this.text = new PIXI.Text({text:this.identity, style:{fill:"#fff"}});
		this.text.anchor(0.5,0.5);
		this.container.addChild(this.text);
		
		parentContainer.addChild(this.container);
	}
}

class UI {
	constructor (app, parentContainer) {

		this.parentContainer = parentContainer;

		this.hand_container = new PIXI.Container();
		this.hand_container.y = app.screen.height * 0.8;
		this.hand_graphic = new PIXI.Graphics();
		this.draw_hand_container();
		this.hand_container.addChild(this.hand_graphic);

		this.parentContainer.addChild(this.hand_container);
	}

	draw_hand_container() {
		let tile_in_hand_size = 30;
		let margin_for_tile = 10;
		this.hand_graphic
			.rect(0, 0, margin_for_tile + ((tile_in_hand_size + margin_for_tile) * 7), margin_for_tile * 2 + tile_in_hand_size)
			.fill(0xAFAF00)
	}
}

class GameState {
	constructor(app, currentPlayer, userContainer, gameContainer, uiContainer) {
		this.app = app;
		this.board = null;
		this.hand = [];
		this.currentPlayer = currentPlayer; 
		this.currentScore = 0;

		this.ui = null;

		this.userContainer = userContainer;
		this.gameContainer = gameContainer;
		this.uiContainer = uiContainer;
	}

	updateGameState (data) {
		console.log("recieved game state: ", data);
		if (!this.board && !data.board_size){
			throw new Error("No board size returned from server");
		}

		if (this.board === null){
			this.board = new Grid(this.app, this.gameContainer, data.board_size[0], data.board_size[1], 50);
		}
		
		if (this.ui === null){
			this.ui = new UI(this.app, this.uiContainer);
		}

	}

	updatePlayerState(data) {
		console.log(data);
		if (!data.username || data.username != this.currentPlayer.username){throw new Error("Wrong player data returned from server.")}
		if (Object.hasOwn(data, "tiles"))
		{this.hand = data.tiles;}else{throw new Error("No hand provided")}
		if (Object.hasOwn(data, "score"))
		{this.currentScore = data.score;}else{throw new Error("No Score Provided")}
	}
}

const initialPath = new URL(window.location.href).pathname;
const currentPath = initialPath.split('/')[1] || '';
const socket = io("/zeta/"+currentPath);



const zetaCanvas = document.getElementById("zetaCanvas");

var game = null;

function onJoined(data){
	if(!data.username){return};
	if(data.username == currentPlayer.username){return};
	if(data.username in players){return};
	console.log("New Player: ", data);

	players[data.username] = new Player(data.username);
	players[data.username].loadSprite(userContainer);
};

async function init_protocol(){
	socket.on("board_state", (data) => {game.updateGameState(data)});
	socket.on("player_state", (data) => {game.updatePlayerState(data)});
	console.log("requesting game state");
	socket.emit("request_game_state", {"timestamp":null});
	if (game.hand.length === 0)
	{
		socket.emit("request_hand", {"timestamp":null});
	}
}

function resizecallback(){
	if (game.board){game.board.centerGrid();};
}

document.addEventListener("DOMContentLoaded", () => {
	const userContainer = new PIXI.Container();
	const gameContainer = new PIXI.Container();
	const uiContainer = new PIXI.Container();
	currentPlayer = new Player(document.getElementById("zetaCanvas").dataset.userid);
	app = new PIXI.Application();
	app.init({
		canvas : zetaCanvas,
		background : "#1f2122",
		resizeTo : window
	});
	
	new ResizeObserver(resizecallback).observe(document.documentElement);
	window.addEventListener("resize", resizecallback)
	
	app.stage.addChild(userContainer);
	app.stage.addChild(uiContainer);
	app.stage.addChild(gameContainer);
	app.stage.sortableChildren = true;
	
	// currentPlayer.loadSprite(userContainer);
	
	game = new GameState(app, currentPlayer, userContainer, gameContainer, uiContainer);
	socket.on("connect", () => {
		console.log("Connected to room!");
		init_protocol();
	});
	
	setTimeout( () => {document.getElementById("zetaCanvas").style.display = "block";}, 100);
}
)