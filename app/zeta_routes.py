import os
from datetime import datetime
from app import app, db, google, loginman, zetaSocketIO
from app.schema import User
from flask import Flask, redirect, url_for, session, request, render_template, flash
from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


