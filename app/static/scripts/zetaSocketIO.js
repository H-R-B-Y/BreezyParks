
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
			this.sprite.anchor.set(0.5,0.6);
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

const initialPath = new URL(window.location.href).pathname;
const currentPath = initialPath.split('/')[1] || '';
const socket = io("/zeta/"+currentPath);

const userContainer = new PIXI.Container();
const lobbyContainer = new PIXI.Container();
const uiContainer = new PIXI.Container();

var app = null;
var players = {};
var currentPlayer = null;

function onJoined(data){
	if(!data.username){return};
	if(data.username == currentPlayer.username){return};
	if(data.username in players){return};
	console.log("New Player: ", data);

	players[data.username] = new Player(data.username);
	players[data.username].loadSprite(lobbyContainer);
};

function onLeft(data){
	if(!data.username){return};
	if(data.username == currentPlayer.username){throw new Error("Recieved Disconnect event for current player.");};
	console.log("Disconnecting player", data);
	lobbyContainer.removeChild(players[data.username].sprite);
	lobbyContainer.removeChild(players[data.username].usernameText);
	players[data.username].sprite.destroy();
	players[data.username].usernameText.destroy();
	delete players[data.username];
};

function onMove(data){
	if(!data.username){return};
	console.log("Moving Player: ", data);
	if(!data.x || !data.y){throw new Error("Move recieved with no position!")};
	if(data.username == currentPlayer.username){currentPlayer.setPosition(data.x, data.y)};
	if(!(data.username in players)){throw new Error("Tried to move non existant player!")};
	players[data.username].setPosition(data.x, data.y);
};

document.addEventListener("DOMContentLoaded", () => {
	currentPlayer = new Player(document.getElementById("zetaCanvas").dataset.userid);

	app = new PIXI.Application();
	app.init({
		canvas : document.getElementById("zetaCanvas"),
		background : "#1f2122",
		resizeTo: window
	});
	// Stack order for containers
	app.stage.addChild(lobbyContainer);
	app.stage.addChild(userContainer);
	app.stage.addChild(uiContainer);
	app.stage.sortableChildren = true;
	
	currentPlayer.loadSprite(userContainer);
	document.addEventListener("click", (event) => {
		// Should probably move this function into a method of the player?
		// Should also probably just use PIXI js event handling so we can know what was clicked, I.E. to bring up user profiles.
		currentPlayer.setPosition(parseInt(event.clientX), parseInt(event.clientY));
		if (socket.connected){
			socket.emit("moved", {"x":currentPlayer.sprite.x, "y":currentPlayer.sprite.y});
		};
	});
	
	socket.on("connect", () => {
		console.log("Connected to room!");
	});
	
	socket.on("joined", onJoined);
	socket.on("left", onLeft);
	socket.on("moved", onMove);
	setTimeout( () => {document.getElementById("zetaCanvas").style.display = "block";}, 100);
});