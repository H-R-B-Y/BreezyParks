import string, random, re, datetime
import requests as req

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from app import app, db, schema, socketio, zetaSocketIO


emailPattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

def doTurnstile (turnstileResponse, connectingIp):
    cfUrl = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    cfData = {"secret" : app.config['cfSecretKey'],
        "response" : turnstileResponse
    }
    if connectingIp:
        cfData["remoteip"] = connectingIp
    
    return req.post(cfUrl, data=cfData)


# BASIC ROUTES
socketio.on_namespace(zetaSocketIO.zeta("/zeta/"))
@app.route('/')
def index():
    return render_template("index.html.jinja")


@app.route('/about')
def about ():
    return "this is about page"


# Login and Reg Routes
@app.route('/register', methods=["GET", "POST"])
def register():
    # Redirects and errors.
    if request.method == "GET": return render_template("register.html.jinja") if not current_user.is_authenticated else redirect(url_for("user"))
    if not request.method == "POST": return "Resource not found.", 404
    if not request.form: return "No data.", 400
    
    # Validation for form data.
    if ('username' not in request.form or 
        not "email" in request.form or 
        'password' not in request.form or 
        'cf-turnstile-response' not in request.form):
        return "Malformed data.", 400

    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    
    # Username Length Check.
    if len(username) > 80: flash("Username is too long, must be 80 characters of less."); return redirect(url_for("register"))
    if len(username) < 1: flash("Username is too Short, must be 1 characters or more."); return redirect(url_for("register"))
    if emailPattern.match(username): flash("Username cannot be an email address."); return redirect(url_for("register"))

    # Email validation check.
    if not emailPattern.match(email): flash("Invalid email address."); return redirect(url_for("register"))
    
    # User already created.
    user : schema.User = schema.User.query.filter_by(username=username).first()
    if user: flash("Username already in use!"); return redirect(url_for("register"))
    user : schema.User = schema.User.query.filter_by(email_address=email).first()
    if user: flash("Email already in use!"); return redirect(url_for("register"))
    
    # Password validity check.
    if len(password) < 8 or not any(char.isupper() for char in password) or not any(char.isdigit() for char in password):
        flash ("Password does not meet security requirements.")
        return redirect(url_for("register")), 403

    # Turnstile check.
    resp = doTurnstile(request.form['cf-turnstile-response'], request.headers.get('CF-Connecting-IP', None))
    if not resp.json()['success']: flash("Could not verify turnstile."); return redirect(url_for("register"))

    # Commit to database.
    alphabet = string.ascii_letters + string.digits
    
    user = schema.User(username=username)
    user.set_password(password)
    user.email_auth_code = ''.join([random.choice(alphabet) for x in range(10)])
    user.email_address = email
    user.created_date = datetime.datetime.utcnow()
    
    db.session.add(user)
    db.session.commit()
    
    # send authentiation email here
    #mailQ.put(emailAuthRoutes.emailQueueItem(email, user.email_auth_code, username))

    return redirect(url_for("login"))


@app.route('/login', methods=["GET","POST"])
def login():
    if request.method == "POST" and request.form and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        if ('cf-turnstile-response' not in request.form or 
            request.headers.get('CF-Connecting-IP', False)):
            return "Malformed Request", 400
    
        resp = doTurnstile(request.form['cf-turnstile-response'], request.headers.get('CF-Connecting-IP'))
        if not resp.json()['success']: flash("Could not verify turnstile."); return redirect(url_for("register")), 403

        user : schema.User = schema.User.query.filter_by(username=username).first()
        if user and user.check_password(password=password):
            flash("Login Success")
            login_user(user, remember = request.form.get("remember_me")=='on')
            return redirect(url_for('user'))        

        flash("Login failed")

    return render_template("login.html.jinja")


@app.route('/logout', methods=["GET"])
def logout():logout_user();return redirect(url_for('login'))

@app.route('/user')
@login_required
def user():
    if not current_user.is_email_auth: flash("User is not currently authorised. Un-authorised accounts will be deleted after 30 days. Please check your email for authorisation instructions.")
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
    if not user: return 'User not found', 404
    return jsonify({'username':user.username, 'sprite':user.image_token}), 200
    

@app.route('/<int:userid>/sprite', methods=["GET"])
def get_user_sprite_id (userID:int):
    user = schema.User.get_user_by_id(userID)
    if not user: return 'User not found', 404
    return jsonify({'username':user.username, 'sprite':user.image_token}), 200
    