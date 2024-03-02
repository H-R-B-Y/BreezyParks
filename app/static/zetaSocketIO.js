class Player {
    constructor(playerId){
        this.playerId = playerId;
        this.sprite = null;
        this.ready = null;
        console.log(this)
    }

    loadSprite (onReady){
        console.log(this)
        fetch('/'+this.playerId+'/sprite')
        .then(response => {
            if (!response.ok){
                throw new Error("Not Ok");
            }
            return response.json();
        })
        .then(spriteData =>{
            console.log("Recieved Data: ",spriteData);
            this.sprite = PIXI.Sprite.from(spriteData.sprite);
            this.sprite.width = 64;
            this.sprite.height = 64;
            this.sprite.zindex = 5
            this.setPosition(parseInt(window.innerWidth/2), parseInt(window.innerHeight/2));
            this.ready = true;
            onReady();
        })
        .catch(error =>{
            this.sprite = PIXI.Sprite.from("/static/generichamster.png");
            this.sprite.width = 64;
            this.sprite.height = 64;
            this.setPosition(parseInt(window.innerWidth/2), parseInt(window.innerHeight/2));
            this.sprite.zindex = 5
            this.ready = true
            onReady();
            //console.error("Problem fetching sprite: ", error);
        });  
    };
    
    setPosition (x, y) {
        var sizex = 64;
        var sizey = 64;
        var xpos = parseInt(x - (sizex/2));
        var ypos = parseInt(y - (sizey/2));
        if (this.ready){
            this.sprite.x = xpos;
            this.sprite.y = ypos;
        }
    }

};


const socket = io("/zeta");

app = null;

const userContainer = new PIXI.Container();
const lobbyContainer = new PIXI.Container();
const uiContainer = new PIXI.Container();

players = {};
currentPlayer = null;
currentPath = new URL(window.location.href).pathname;
currentPath = currentPath.substring(0,currentPath.indexOf("/",4));
currentPath = currentPath == '' ? '/' : currentPath;


document.addEventListener('DOMContentLoaded', function() {
    currentPlayer = new Player(document.getElementById("zetaCanvas").dataset.userid);
    
    app = new PIXI.Application({
        view : document.getElementById("zetaCanvas"),
        background: "#464a4a",
        resizeTo: window,
    });

    // Stack order for containers
    app.stage.addChild(lobbyContainer);
    app.stage.addChild(userContainer);
    app.stage.addChild(uiContainer);
    app.stage.sortableChildren = true;

    // when client connects; send the room connection event and room ID
    socket.on("connect", () => {
        socket.emit("joined", {"room" : currentPath});
        
        window.addEventListener("beforeunload", function(e){
            socket.emit("left", {"room" : currentPath})
         })

        // Init the player sprite and add to user container
        // If this is a reconnect the current player will already be initialised so skip
        if (!currentPlayer.ready){
            currentPlayer.loadSprite(() => {
                if (currentPlayer.ready){
                    userContainer.addChild(currentPlayer.sprite);
                };
                document.addEventListener("click", (event) => {
                    currentPlayer.setPosition(parseInt(event.clientX), parseInt(event.clientY));
                    socket.emit("moved", {"room" : currentPath, "x": currentPlayer.sprite.x, "y": currentPlayer.sprite.y});
                });
            });
        };
    });

    socket.on("joined", (data) => {
        console.log("New player: ", data);
        // WARN: not recieving id will break? handle this please xoxoxoxo
        // should i use ID or username
        if (data["username"] == currentPlayer.playerId){
            return;
        }

        let fromPlayer = new Player(data["username"]);
        players[data["username"]] = fromPlayer;

        // WARN: not recieving coords will break? handle this please xoxoxo
        fromPlayer.loadSprite(() => {
            fromPlayer.sprite.x = data["x"];
            fromPlayer.sprite.y = data["y"];
            lobbyContainer.addChild(fromPlayer.sprite);
        });
    });

    socket.on("moved", (data) => {
        console.log("Move recieved: ", data);
        if (!(data["username"] in players) || data["username"] == currentPlayer.playerId){
            return;
        }
        let fromPlayer = players[data["username"]];
        fromPlayer.setPosition(data["x"], data["y"])
    });

    socket.on("left", (data) => {
        console.log("Disconnect recieved: ", data);
        let fromPlayer = players[data["username"]];
        lobbyContainer.removeChild(fromPlayer.sprite);
        delete players[data["username"]];
    });

    socket.connect();
});

