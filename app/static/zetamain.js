app = 0;
document.addEventListener('DOMContentLoaded', function() {
    const zetaSocket = new WebSocket('ws://127.0.0.1:5001')

    zetaSocket.onopen = function(event) {
        // Send the client ID after the connection is established
        zetaSocket.send(Math.random());
        app = new PIXI.Application({
            view : document.getElementById("zetaCanvas"),
            background: "#171717A0",
            resizeTo: window,
        }); 
        setupHandlers(zetaSocket);
    };
});

    
function setupHandlers (zetaSocket) {

    zetaSocket.onmessage = function(event) {
        // Handle received messages from the server
        console.log('Received message:', event.data);
        if (String(event.data).startsWith("Click")){
            parts = String(event.data).split("|");
            let sprite = PIXI.Sprite.from("/static/generichamster.png");
            sprite.height = 30
            sprite.width = 30
            sprite.x = parts[1]
            sprite.y = parts[2]
            app.stage.addChild(sprite);
        }
    };

    document.addEventListener("click", (event) => zetaSocket.send("Click|"+event.clientX+"|"+event.clientY))
}