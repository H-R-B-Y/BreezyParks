from app import app, db
from flask import request
from app.schema import User
import datetime
import random

# return username or none
def getUsername (currentUser : User):
    if not currentUser.is_authenticated:
        return None

    return currentUser.username

def rndid ():
    return random.randint(1,1000)

app.jinja_env.globals.update(getUsername = getUsername)
app.jinja_env.globals.update(rndId = rndid)
app.jinja_env.globals.update(conf = app.config)