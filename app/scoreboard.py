import string, random, datetime
import requests as req

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from app import app, db, schema, socketio, zetaSocketIO

socketio.on_namespace(zetaSocketIO.zeta("/scoreboard/"))
@app.route('/scoreboard')
def scoreboard ():

    return render_template("scoreboardtest.html.jinja")