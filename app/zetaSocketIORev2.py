from flask import request
from flask_socketio import Namespace, emit, join_room, leave_room
from flask_login import current_user

'''
The aim of this is to try and utilise Namespace sub classes to implement.
See devlog for details
'''


class zeta(Namespace):
    zetaRooms = {}
    sidMap = {}

    @classmethod
    def unamesInRoom (cls, room):
         return list(set([cls.sidMap[sid] for sid in cls.zetaRooms[room]]))

    def on_connect(self):
        '''
        Add the sid to the username map
        '''
        print(f"client connected {current_user.username}")
        zeta.sidMap[request.sid] = current_user.username

    def on_disconnect(self):
        '''
        Remove the sid from the username map
        '''
        n = zeta.sidMap.pop(request.sid, None)
        print(f"Client Disconnected: {n}")
        # also remove the sid from any zetaRooms:
        
        # or each room(if user in a room pop SID and return room name, if not in a room return a false)
        removeFromZRoom = list(map(lambda tRoom : zeta.zetaRooms.pop(n, False) and tRoom, zeta.zetaRooms.keys()))
        print(f"remove list :\n{removeFromZRoom}")
        if any(removeFromZRoom):
            print(f"removed sid{n} from rooms:{','.join(set(removeFromZRoom))}")
             

    def on_joined(self, data):
        '''
        if sid is already in zetaRoom the sid is still added to the socketio.room but not added to the zetaRoom
        meaning the sid will revieve messages from the server but will not emit any to other players.

        on leaving the sid will need to be removed from the room
        a check will need to be conducted to test wheather to also let evryrone know they have left and remove them from the zetaRoom
        '''
        print("\njoinedStart")
        assert "room" in data.keys() 
        if data["room"] == '':
            data['room'] = '/'
        
        if data['room'] not in zeta.zetaRooms.keys():
                zeta.zetaRooms[data['room']] = []
        
        if current_user:
            for sid in zeta.zetaRooms[data['room']]:
                 emit(
                        "joined", 
                        {
                            "username": zeta.sidMap[sid], 
                            "x": data["x"] if "x" in data.keys() else 0, 
                            "y": data["y"] if "y" in data.keys() else 0
                        },
                        to=request.sid,
                 )

            if not request.sid in zeta.zetaRooms[data["room"]] and current_user.username not in zeta.unamesInRoom(data['room']):
                emit("joined", 
                    {"username": current_user.username, 
                     "x": data["x"] if "x" in data.keys() else 0, 
                    "y": data["y"] if "y" in data.keys() else 0
                    },
                    to=data['room'],
                    include_self=False
                )
                zeta.zetaRooms[data["room"]].append(request.sid)
                print(f"user: {current_user.username} joined room: {data['room']} with SID:{request.sid}")
            else:
                print(f"SID:{request.sid} added to room {data['room']}")

        join_room(data["room"])
        print("joinedEnd")


    def on_left(self, data):
        print("\nleftStart")
        assert "room" in data.keys()
        if data["room"] == '':
            data['room'] = '/'
        if data['room'] not in zeta.zetaRooms.keys():
                zeta.zetaRooms[data['room']] = []
        
        if current_user and request.sid in zeta.zetaRooms[data["room"]]:
            emit("left",
                {"username": current_user.username},
                to=data['room'],
                include_self=False
            )
            zeta.zetaRooms[data['room']].remove(request.sid)
            print(f"user: {current_user.username} left room: {data['room']} with SID:{request.sid}")
        else:
            print(f"SID:{request.sid} left room {data['room']}")
        leave_room(data["room"])
        print("leftEnd")


    def on_moved(self, data):
        print("\nmoveStart")
        assert "room" in data.keys()
        assert "x" in data.keys()
        assert "y" in data.keys()
        if data["room"] == '':
            data['room'] = '/'
        if data['room'] not in zeta.zetaRooms.keys():
                zeta.zetaRooms[data['room']] = []
        if current_user is None:
            return
        
        if request.sid not in zeta.zetaRooms[data['room']]:
             return

        print(f"{current_user.username} MOVING {data} with SID:{request.sid}")
        emit("moved", 
            {
                "username" : current_user.username,
                "x" : data["x"],
                "y" : data["y"]
            },
            to=data['room'],
            include_self=False
        )
        print("moveEnd")




