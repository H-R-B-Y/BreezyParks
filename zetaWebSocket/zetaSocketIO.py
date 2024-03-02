from aiohttp import web
import socketio

sio = socketio.AsyncServer(cors_allowed_origins='http://127.0.0.1:5000')
app = web.Application()
sio.attach(app)


@sio.event
def connect(sid, environ):
    print('connect ', sid)

#@sio.event
#def my_message(sid, data):
#    print('message ', data)
    
@sio.on("hello")
async def anEvent (sid, data):
    print('got hello')
    await sio.emit("world", {"world":"world"}, room=sid)


@sio.event
def disconnect(sid):
    print('disconnect ', sid)

if __name__ == '__main__':
    web.run_app(app, port=8443)
