import asyncio
import websockets


class Player:
    def __init__(self, playerId, websocket, xPos = 0, yPos = 0):
        self.playerId = playerId
        self.websocket = websocket
        self.x = xPos
        self.y = yPos
    
    def getUsername (self):
        """gets the username for the user
        
        Connect to database via sql alchemy?
        Do we need the username on the socket?

        Keyword arguments:
        argument -- description
        Return: return_description
        """
        pass


class Room:
    """Room is a path at depth 3
    
    arguments:
    room_id -- the depth 3 path from the client.

    Return: Room
    """
    def __init__(self, roomId):
        self.roomId = roomId
        self.connectedClients = []

    def addClient(self, player):
        """Add player to clients list.
        
        Arguments:
        Player -- Player object to add to room.

        Return: None
        """
        self.connectedClients.append(player)

    def removeClient(self, player):
        """Remove player from a Room.
        
        Arguments:
        player -- Player object to be removed.

        Return: None
        """
        self.connectedClients.remove(player)

    async def broadcastMessage (self, sender : Player = None, message : str = "", feedback : bool = False):
        """Broad cast a message to clients in server
        
        Keyword arguments:
        sender -- the player that sent the message 
        message -- the message to send
        feedback -- return message to sender (default:false)

        Return: none
        """
        for player in self.connectedClients:
            if player != sender:
                await player.websocket.send(message)




class WebSocketServer:
    def __init__(self):
        self.rooms = {}

    async def handleClient(self, websocket, path):
        message = await websocket.recv()
        parts = message.split('|')
        
        print(message)

        if len(parts) == 3 and parts[0] == 'CN': # handle connection without coordinates
            playerId, roomId = parts[1], parts[2]

            if roomId not in self.rooms:
                self.rooms[roomId] = Room(roomId)

            player = Player(playerId, websocket)
            self.rooms[roomId].addClient(player)

            print(f"Client {playerId} has connected to room {roomId}")

            await self.returnUsersInLobby(player, roomId)

            await self.handlePlayerMessages(websocket, player, roomId)

        if len(parts) == 5 and parts[0] == 'CN' and parts[3].isdigit() and parts[4].isdigit():
            playerId, roomId, xPos, yPos = parts[1], parts[2], parts[3], parts[4]

            if roomId not in self.rooms:
                self.rooms[roomId] = Room(roomId)

            player = Player(playerId=playerId, websocket=websocket, xPos=xPos, yPos=yPos)
            self.rooms[roomId].addClient(player)

            print(f"Client {playerId} has connected to room {roomId}")

            await self.returnUsersInLobby(player, roomId=roomId)
            await self.handlePlayerMessages(websocket=websocket, player=player, roomId=roomId)

        else: 
            # Handle other types of messages like server connections or something.
            pass


    async def handlePlayerMessages (self, websocket, player, roomId):
        try:
            while True:
                message = await websocket.recv()
                print (f"Message recieved {message}")
                parts = message.split('|')
                
                if parts[0] == "MV" and len(parts) == 3:
                    player.x, player.y = parts[1:]
                    returnMessage = f"MV|{player.playerId}|{parts[1]}|{parts[2]}"
                    await self.rooms[roomId].broadcastMessage(sender=player,message=returnMessage)


        except websockets.exceptions.ConnectionClosedOK:
            print(f"Client {player.playerId} has disconnected")
            await self.removeDisconnectedClient(player)

        except websockets.exceptions.ConnectionClosed:
            print(f"Client {player.playerId} has disconnected")
            await self.removeDisconnectedClient(player)


    async def returnUsersInLobby (self, player, roomId):
        room = self.rooms[roomId]
        for client in room.connectedClients:
            if player != client:
                await player.websocket.send(f"CN|{client.playerId}|{client.x}|{client.y}")
                await client.websocket.send(f"CN|{player.playerId}|{player.x}|{player.y}")

    
    async def removeDisconnectedClient(self, playerDC):
        for room in self.rooms.values():
            for player in room.connectedClients:
                if player == playerDC:
                    room.removeClient(playerDC)
                    await room.broadcastMessage(message=f"DC|{playerDC.playerId}")
                    del(playerDC)


    async def startServer(self):
        server = await websockets.serve(self.handleClient, "localhost", 5069)

        async with server:
            await server.wait_closed()

if __name__ == "__main__":
    wsServer = WebSocketServer()
    asyncio.run(wsServer.startServer())