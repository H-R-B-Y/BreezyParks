from flask import request
from flask_socketio import Namespace, emit, join_room, leave_room
from flask_login import current_user

'''
The aim of this is to try and utilise Namespace sub classes to implement.
See devlog for details
'''


class oldZeta(Namespace):
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




class zeta(Namespace):
    def __init__(self, *args, **kwargs):
        self.activeSids = set() # sids currently connected
        self.activeUsers = set() # Users currently connected
        self.sidLookup = {} # sid : username lookup
        super().__init__(*args, **kwargs)

    def on_connect(self):
        '''
        On connect store the sid, the username, and create a lookup value for this sid.
        Active users and active sids are sets so don't need to worry about duplicates
        '''
        # Let users know about other users in the lobby.
        for uName in self.activeUsers:
            emit("joined", {"username":uName, "x":0, "y":0}, to=request.sid, broadcast=False)

        # Broadcast that new user has joined here.
        if current_user:
            emit("joined", {"username":current_user.username, "x":0, "y":0},include_self=False, broadcast=True)
        
        # Add user details to the class (Done after broadcast such that no actions are dispatched for uninitialised users)
        self.activeSids.append(request.sid)
        if current_user:
            self.activeUsers.append(current_user.username)
            self.sidLookup[request.sid] = current_user.username
    
    def on_disconnect(self):
        '''
        On Disconnect we need to remove the sid
        We then need to remove the sids lookup value
        We also need to remove the user from the active users IF and ONLY IF they have no other active session in this namespace.
        '''
        # Code that needs to be executed regardless of whether user  still has active sessions or not:
        self.activeSids.pop(request.sid, False)

        if not current_user:
             return
        
        # Code that needs to be executed IF and ONLY IF the disconnecting session is the last active session for the user.
        self.sidLookup.pop(request.sid)
        if(not any(map(lambda x: x==current_user.username, set(self.sidLookup.values)))):
                self.activeUsers.pop(current_user.username)
                emit("left", {"username":current_user.username}, include_self=False, broadcast=True)
    
    
    def on_moved(self, data):
        if not current_user:
            return
        emit("moved", 
             {
                "username": current_user.username, 
                "x": 0 if not "x" in data.keys() else data["x"], 
                "y": 0 if not "y" in data.keys() else data["y"]
             }, 
             broadcast=True, 
             include_self=False
        )
        

