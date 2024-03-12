import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from multiprocessing import Queue

from app import app, db, routes

# const
emailProcessOutput = Queue()

class emailQueueItem ():
    def __init__(self, toAddress, secretCode, username):
        self.toAddress = toAddress
        self.secretCode = secretCode
        self.username = username

    def getMessage(self):
        mailTemplate = f"""Hello {self.username},
Welcome to BreezyParks,
Please enter the code at the following link to verify account details:
https://breezyparks.com/emailauth/{self.username}/{self.secretCode}/authorise

If the above link is not working please enter the following code at https://www.breezyparks.com/emailauth/authorise 
\n
{self.secretCode}

If you are recieving this and have not signed up for a BreezyParks account please use the following link to request for account deletion:
"""
        return mailTemplate

def authEmailLoop(loginAddress, fromAddress, password, mailQueue):
    '''
    Creates a mail loop that reads the mail queue.
    Once a mail items is recieved the message is formed.
    the connection to the smtp server is started and the email is sent.
    Then a loop continues to pull new messages from the queue.
    If the loop is empty the connection to the smtp server is disconnected 
    and the function blocks until the queue has a new item.
    '''
    print(loginAddress)
    print(fromAddress)
    port = 465
    emailContext = ssl.create_default_context()
    while True:
        print("recieving")
        emailTask = mailQueue.get(block=True) # block until an item is put
        print(emailTask)
        # exit or skip condition.
        if emailTask is None: break
        if type(emailTask) is not emailQueueItem: continue
        
        # connect to smtp server.
        with smtplib.SMTP_SSL("smtp.zoho.eu", port) as mailServer:
            # login and recieve message from message item. 
            mailServer.login(loginAddress, password)
            print("Server connection established")
            mailMessage = MIMEMultipart()
            mailMessage["To"] = emailTask.toAddress
            mailMessage["From"] = fromAddress
            mailMessage["Subject"] = "Email Auth Code."
            mailMessage.attach(MIMEText(emailTask.getMessage(), "plain"))

            # try to send the email, put response into output queue or put error into output queue.
            try: 
                resp = mailServer.sendmail(from_addr=fromAddress, to_addrs=emailTask.toAddress, msg=mailMessage.as_string())
                emailProcessOutput.put_nowait(resp)
            except smtplib.SMTPException as e: emailProcessOutput.put_nowait(e)
            
            # secondary mail loop while connected to the server to avoid disconnect/re-connect when items still in queue.
            while not mailQueue.empty():
                emailTask = mailQueue.get()
                if emailTask is None: break
                if type(emailTask) is not emailQueueItem: continue
                mailMessage = MIMEMultipart()
                mailMessage["To"] = emailTask.toAddress
                mailMessage["From"] = fromAddress
                mailMessage["Subject"] = "Email Auth Code."
                mailMessage.attach(MIMEText(emailTask.getMessage(), "plain"))
                try: 
                    resp = mailServer.sendmail(from_addr=fromAddress, to_addrs=emailTask.toAddress, msg=mailMessage.as_string())
                    emailProcessOutput.put_nowait(resp)
                except smtplib.SMTPException as e: emailProcessOutput.put_nowait(e)
    return emailProcessOutput

            
        

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
    if request.method == "GET" :
        if not current_user.is_email_auth: return render_template("authorise.html.jinja")
        elif current_user.is_email_auth: flash("Already Authorised."); return redirect(url_for("user"))
        else: return "Something went wrong!", 500
    
    if request.method == "POST" and request.form and not "authCode" in request.form:
        return "Malformed Request", 400
    
    if ('cf-turnstile-response' not in request.form or 
        request.headers.get('CF-Connecting-IP', False)):
        return "Malformed Request", 400
    
    resp = routes.doTurnstile(request.form['cf-turnstile-response'], request.headers.get('CF-Connecting-IP'))
    if not resp.json()['success']: flash("Could not verify turnstile."); return redirect(url_for("register")), 403

    if request.form["authCode"] != current_user.email_auth_code:
        flash("Codes do not match!")
        return redirect(url_for("authoriseFromPage"))
    
    current_user.is_email_auth = True
    db.session.commit()
    flash("Authorised successully.")
    return redirect(url_for("user"))

    



@app.route('/emailauth/<string:username>/<string:authCode>/authorise')
def authoriseFromCode(username:str, authCode:str):
    pass


@app.route('/emailauth/<string:authCode>/unauthorise')
def unauthoriseFromCode(authCode:str):
    pass
