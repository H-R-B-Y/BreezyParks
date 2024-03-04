import requests
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, logout_user, login_required, current_user

from app import app, db, schema, loginMan


def sendAuthEmail():
    pass


def idkDoSomething():
    pass


@app.route('/emailauth/<string:authCode>/authorise')
def authoriseFromCode(authCode:str):
    pass


@app.route('/emailauth/<string:authCode>/unauthorise')
def unauthoriseFromCode(authCode:str):
    pass


#   The idea is that when a user registers, they get an auth code generated.
#   They then get an email send to them with the auth code url
#   They can then navigate to the url and as long as they are signed into the same user as the auth code
#   They will be authorised.
#
#   Not sure if this is the best way to go about it but it should work.
#
#
#   Work out the flow for this.
#
#
#