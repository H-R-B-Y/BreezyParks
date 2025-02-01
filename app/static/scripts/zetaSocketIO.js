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

function resizecallback() {
	new_width = document.documentElement.scrollWidth;
	new_height = document.documentElement.scrollHeight;
	app.renderer.resize(new_width, new_height);
}

document.addEventListener("DOMContentLoaded", () => {
	currentPlayer = new Player(document.getElementById("zetaCanvas").dataset.userid);

	app = new PIXI.Application();
	app.init({
		canvas : document.getElementById("zetaCanvas"),
		background : "#1f2122",
		width : document.documentElement.scrollWidth,
		height : document.documentElement.scrollHeight,
	});
	
	document.getElementById("zetaCanvas").style.position = 'absolute';
	document.getElementById("zetaCanvas").style.top = '0';
	document.getElementById("zetaCanvas").style.left = '0';
	new ResizeObserver(resizecallback).observe(document.documentElement);
	window.addEventListener("resize", resizecallback)
	// Stack order for containers
	app.stage.addChild(lobbyContainer);
	app.stage.addChild(userContainer);
	app.stage.addChild(uiContainer);
	app.stage.sortableChildren = true;
	
	currentPlayer.loadSprite(userContainer);
	document.addEventListener("click", (event) => {
		// Should probably move this function into a method of the player?
		// Should also probably just use PIXI js event handling so we can know what was clicked, I.E. to bring up user profiles.
		x = parseInt(event.pageX);
		y = parseInt(event.pageY);
		currentPlayer.setPosition(x, y);
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