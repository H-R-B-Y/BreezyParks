import asyncio
import websockets


# Dictionary to store client connections
connected_clients = {}

async def handle_client(websocket, path):
    # Assume some form of identification for clients (e.g., usernames or IDs)
    client_id = await websocket.recv()  # Assuming client sends an ID upon connection
    connected_clients[client_id] = websocket
    print (f"recieved : {client_id}")
    try:
        async for message in websocket:
            # Process the received message
            print(f"Received message from {client_id}: {message}")

            # Broadcast the received message to all clients except the sender
            await broadcast_message(message, client_id)
    finally:
        del connected_clients[client_id]  # Remove client from the connected clients dictionary upon disconnection

async def broadcast_message(message, sender_id):
    # Iterate through connected clients and send the message to all except the sender
    for client_id, client_ws in connected_clients.items():
        if client_id != sender_id:
            await client_ws.send(message)

start_server = websockets.serve(handle_client, "localhost", 5001)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()