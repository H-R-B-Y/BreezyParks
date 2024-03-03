from flask import request
from flask_socketio import Namespace, emit, join_room, leave_room
from flask_login import current_user
from app import socketio

'''
The aim of this is to try and utilise Namespace sub classes to implement.
See devlog for details
'''

class zeta(Namespace):
    def __init__(self, *args, **kwargs):
        '''
        Initialise room data, then initialise the namespace as normal.
        '''
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
        '''
        Currently just emits the new position out to all connected sessions.
        In future might need to change the code to account for Local/Global positioning.
        '''
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


'''
Create a function for initialising the namespace.
Might want to consider making the namespace custom, like adding custom event listeners or making them only available to certain players i.e. Admins.
'''