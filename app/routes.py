from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, logout_user, login_required, current_user

from app import app, db, schema, loginMan

from urllib import parse
import requests as req
import base64, datetime


# BASIC ROUTES
@app.route('/')
def index():
    return render_template("index.html.jinja")


@app.route('/about')
def about ():
    return "this is about page"


# Login and Reg Routes

@app.route('/register', methods=["GET", "POST"])
def register ():
    if request.method == "POST" and request.form and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        
        if len(username) > 80:
            flash("Username is too long, must be 80 characters of less")
            return redirect(url_for("register"))

        # check username not in use
        user : schema.User = schema.User.query.filter_by(username=username).first()
        if user:
            flash("Username already in use!")
            return redirect(url_for("register"))
        
        # check password is valid
        if len(password) < 8 or not any(char.isupper() for char in password) or not any(char.isdigit() for char in password):
            flash ("Password does not meet security requirements.")
            return redirect(url_for("register"))
        
        # user is valid
        user = schema.User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))

    return render_template("register.html.jinja")


@app.route('/login', methods=["GET","POST"])
def login ():
    if request.method == "POST" and request.form and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        user : schema.User = schema.User.query.filter_by(username=username).first()

        if user and user.check_password(password=password):
            flash("Login Success")
            login_user(user, remember = request.form.get("remember_me")=='on')
            return redirect(url_for('user'))

        flash("Login failed")

    return render_template("login.html.jinja")


@app.route('/logout', methods=["GET"])
def logout ():
    logout_user()
    return redirect(url_for('login'))


@app.route('/user')
@login_required
def user ():
    #return jsonify({"User" : f"{current_user.username}"}), 200
    return render_template("user.html.jinja", img1=schema.sprites[0], img2=schema.sprites[1], img3=schema.sprites[2], img4=schema.sprites[3], img5=schema.sprites[4])

@app.route('/setimg', methods=["GET","POST"])
@login_required
def set_img ():
    if request.method == "POST" and request.form and 'Sprite' in request.form:
        sprite : str = request.form['Sprite']
        if not sprite.isdigit() and int(sprite) not in [0,1,2,3,4]:
            app.logger.info("Invalid selection")
            flash('invalid selection')
            return redirect(url_for('user'))

        sprite = int(sprite)
        current_user.image_index = sprite
        current_user.image_token = schema.sprites[sprite]
        db.session.commit()
        app.logger.info(f"image set to {sprite}")

    return redirect(url_for('user'))


@app.route('/<string:username>/sprite', methods=["GET"])
def get_user_sprite_username (username:str):
    user = schema.User.get_user_by_name(username)
    if not user:
        return 'User not found', 404
    return jsonify({'username':user.username, 'sprite':user.image_token}), 200
    

@app.route('/<int:userid>/sprite', methods=["GET"])
def get_user_sprite_id (userID:int):
    user = schema.User.get_user_by_id(userID)
    if not user:
        return 'User not found', 404
    return jsonify({'username':user.username, 'sprite':user.image_token}), 200
    