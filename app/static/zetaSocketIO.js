
class Player {
    constructor(username){
        this.username = username;
        this.sprite = null;
        this.usernameText = null;
        this.ready = null;
    }

    loadSprite (drawContainer){
        this.usernameText = new PIXI.Text(self.username);
        this.usernameText.anchor.set(0.5,1);    
        fetch('/'+this.username+'/sprite').then((response) => {
            if (!response.ok){throw new Error("Not OK")};
            self.sprite = new PIXI.Sprite.from(response.json().sprite);
        }).catch(error => {
            console.log(error);
            this.sprite = new PIXI.Sprite.from("/static/generichamster.png");
        }).then(() => {
            this.sprite.width = 64;
            this.sprite.width = 64;
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
            this.sprite.x = xpos;
            this.sprite.y = ypos;
        }
        if (this.usernameText){
            this.usernameText.x = x;
            this.usernameText.y = y - parseInt(this.sprite.height/2);
        }
    }

}


const currentPath = new URL(window.location.href).pathname.substring(0,currentPath.indexOf("/",4)) == '' ? '/' : currentPath;
const socket = io("/zeta"+currentPath);

const userContainer = new PIXI.Container();
const lobbyContainer = new PIXI.Container();
const uiContainer = new PIXI.Container();

var app = null;
var players = {};
var currentPlayer = null;

function onJoined(data){
    if(!data.username){return};
    if(data.username == currentPlayer.username){return};
    console.log("New Player: ", data);

    players[data.username] = new Player(data.username);
    players[data.username].loadSprite(lobbyContainer);
};

function onLeft(data){
    if(!data.username){return};
    if(data.username == currentPlayer.username){throw new Error("Recieved Disconnect event for current player.");};
    console.log("Disconnecting player", data);
    lobbyContainer.removeChild(players[data.username]);
    delete players[data.username];
};

function onMove(data){
    if(!data.username){return};
    console.log("Moving Player: ", data);
    if(!data.x || !data.y){throw new Error("Move recieved with no position!")};
    if(!(data.username in players)){throw new Error("Tried to move non existant player!")};
    players[data.username].setPosition(data.x, data.y);
};

document.addEventListener("DOMContentLoaded", () => {
    currentPlayer = new Player(document.getElementById("zetaCanvas").dataset.userid);

    app = new PIXI.Application({
        view : document.getElementById("zetaCanvas"),
        background : "#464a4a",
        resizeTo: window
    });

    // Stack order for containers
    app.stage.addChild(lobbyContainer);
    app.stage.addChild(userContainer);
    app.stage.addChild(uiContainer);
    app.stage.sortableChildren = true;

    currentPlayer.loadSprite(userContainer);
    document.getElementById("zetaCanvas").addEventListener("click", (event) => {
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

});