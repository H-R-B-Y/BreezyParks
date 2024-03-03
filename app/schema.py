import bcrypt
import json
from app import db
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# so autocomplete works
db : SQLAlchemy = db

with open ('./app/static/availableSprite.json') as file:
    sprites = json.load(file)


class User(UserMixin, db.Model):
    """ This is the schema for the user.

    New user can be created by instanciating this class and then using the db.session to add a row and commit.
    DO NOT instaciate using password keyword, instead use set_password before commiting user instance.
    
    Keyword arguments:
    username -- The username for the user
    Return: user instance
    """
    
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    image_token = db.Column(db.String(100), nullable = True)
    image_index = db.Column(db.Integer, nullable = True)
    is_admin = db.Column(db.Boolean, unique=False, default=False, nullable=False)


    def set_password (self, password) -> None :  
        """ Sets the passowrd for the current instance
        
        Keyword arguments:
        password -- the unencrypted password.
        Return: None
        """
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def check_password(self, password) -> bool:
        """ Checks an unhashed password against the hashed password stored on user
        
        Keyword arguments:
        password - the unhashed password you would like to check.
        Return: bool
        """
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash)
    
    @classmethod
    def get_user_by_name (cls, name):
        """ Gets a user from a given username
        
        Keyword arguments:
        name -- username
        Return: schema.user if found else None
        """
        user = User.query.filter_by(username=name).first()
        if user:
            return user
        else:
            return None
        
    @classmethod
    def get_user_by_id (cls, id):
        user = user.query.filter_by(id=id).first()
        if user:
            return user
        else: return None
    