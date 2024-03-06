import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, logout_user, login_required, current_user
from multiprocessing import Queue, Process, Lock

from app import app, db, schema, loginMan

# const
emailQueue = Queue()
emailProcessOutput = Queue()

class emailQueueItem ():
    def __init__(self, toAddress, secretCode, username):
        self.toAddress = toAddress
        self.secretCode = secretCode
        self.username = username

    def getMessage(self):
        mailTemplate = """Hello {username},
Welcome to BreezyParks,
Please enter the code at the following link to verify account details:
https://breezyparks.com/emailauth/{username}/{secretCode}/authorise

If the above link is not working please enter the following code at https://www.breezyparks.com/emailauth/authorise
{secretCode}

If you are recieving this and have not signed up for a BreezyParks account please use the following link to request for account deletion:
{unauthoriseLink}
"""

def authEmailLoop(loginAddress, fromAddress, password):
    port = 587
    while True:
        emailTask = emailQueue.get() # block until an item is put
        if emailTask is None: break
        with smtplib.SMTP("smtp.gmail.com", port) as mailServer:
            mailServer.login(loginAddress, password)
            mailMessage = emailTask.getMessage()
            try: resp = mailServer.sendmail(from_addr=fromAddress, to_addrs=emailTask.toAddress, msg=mailMessage)
            except smtplib.SMTPException as e: emailProcessOutput.put_nowait(e)
            while not emailQueue.empty():
                emailTask = emailQueue.get()
                if emailTask is None: break
                mailMessage = emailTask.getMessage
                try: resp = mailServer.sendmail(from_addr=fromAddress, to_addrs=emailTask.toAddress, msg=mailMessage)
                except smtplib.SMTPException as e: emailProcessOutput.put_nowait(e)
    return

            
        

# Flask app routes        
@app.route('/emailauth/authorise', methods=["GET","POST"])
@login_required
def authoriseFromPage():
    '''
    This endpoint has a form allowing user to enter the registration code.
    MUST BE SIGNED IN TO THE ACCOUNT THAT IS BEING AUTHORISED.
    On post check the current user row for the auth code and compare to the one sent:
        If same account is authorised.
        If not same reload with a flash.
    '''
    pass



@app.route('/emailauth/<string:username>/<string:authCode>/authorise')
def authoriseFromCode(username:str, authCode:str):
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