

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
        })
        .catch(error =>{
            this.sprite = PIXI.Sprite.from("/static/generichamster.png");
            this.sprite.width = 64;
            this.sprite.height = 64;
            this.setPosition(parseInt(window.innerWidth/2), parseInt(window.innerHeight/2));
            this.sprite.zindex = 5
            this.ready = true
            //console.error("Problem fetching sprite: ", error);
        }).finally(() => {
            if (typeof onReady === 'function'){
                onReady();
            };
        });  
    };
    
    setPosition (x, y) {
        var sizex = 64;
        var sizey = 64;
        var xpos = parseInt(x - (sizex/2));
        var ypos = parseInt(y - (sizey/2));
        this.sprite.x = xpos;
        this.sprite.y = ypos;

    }

};

app = null;
zetaSocket = null;

const userContainer = new PIXI.Container();
const lobbyContainer = new PIXI.Container();
const uiContainer = new PIXI.Container();


players = {};
currentPlayer = null;
currentPath = new URL(window.location.href).pathname;
currentPath = currentPath.substring(0,currentPath.indexOf("/",4));


document.addEventListener('DOMContentLoaded', function() {
    currentPlayer = new Player(document.getElementById("zetaCanvas").dataset.userid);
    zetaSocket = new WebSocket('ws://'+ window.location.hostname +':50001');

    zetaSocket.onopen = function(event) {
        zetaSocket.send("CN|"+currentPlayer.playerId+"|"+currentPath);    
        app = new PIXI.Application({
            view : document.getElementById("zetaCanvas"),
            background: "#464a4a",
            resizeTo: window,
        }); 

        app.stage.addChild(lobbyContainer);
        app.stage.addChild(userContainer);
        app.stage.addChild(uiContainer);

        app.stage.sortableChildren = true;

        currentPlayer.loadSprite(() => {
            if (currentPlayer.ready){
                userContainer.addChild(currentPlayer.sprite);
                document.addEventListener("click", (event) => {
                    currentPlayer.setPosition(parseInt(event.clientX), parseInt(event.clientY));
                    zetaSocket.send("MV|"+event.clientX+"|"+event.clientY)
                });
                zetaSocket.send("MV|"+currentPlayer.sprite.x+"|"+currentPlayer.sprite.y)
            };
        });

        zetaSocket.onmessage = function(event) {
            console.log("Recieved message", event.data);
            handleMessages(event.data);
        };
    };
});


function handleNewPlayer (id, xPos, yPos){
    console.log(id, xPos, yPos)
    p = new Player(id);
    players[id] = p;
    p.loadSprite(() => {
        p.sprite.x = xPos;
        p.sprite.y = yPos;
        lobbyContainer.addChild(p.sprite);
    });

};

function handlePlayerMovement (id, xPos, yPos){
    if (id in players){
        p = players[id];
        p.setPosition(xPos, yPos)
    };
};


function handleMessages (message){
    parts = message.split("|");
    if (parts[0] === "CN" && parts.length === 4){
        handleNewPlayer(parts[1], parts[2], parts[3])

    } else if (parts[0] === "MV" && parts.length === 4) {
        handlePlayerMovement(parts[1], parts[2], parts[3])

    } else if (parts[0] === "DC" && parts.length === 2){
        if (parts[1] in players){
            p = players[parts[1]];
            lobbyContainer.removeChild(p.sprite);
            delete players[parts[1]];
            delete p;
        };
    }

};

