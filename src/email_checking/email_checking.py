import random
from email.message import EmailMessage
import ssl
import smtplib
import time
import math
import threading

# Our mail used to send the codes
sender = "cryptomailepita@gmail.com "


def send_mail(receiver, cryptomail_collection):
    # Generate a 6 digits code
    code = generate_email_code()
    # Update the code in MongoDB (in the cryptomail_collection)
    update_code(receiver, cryptomail_collection, code)
    # Send the code to the receiver
    send_verification_mail(receiver, code)
    

def verify_mail(mail, cryptomail_collection, code):
    # Verify that the code is valid for the user
    existing_mail = cryptomail_collection.find_one({"mail": mail})
    if existing_mail and existing_mail["code"] == code:
        # Delete the code in the database
        delete_code(mail, cryptomail_collection, True)
        return True
    else:
        return False


def generate_email_code():
    # Generate a 6 digits code
    code = ""
    for i in range(6):
        code += str(random.randint(0, 9))
    return code


def update_code(receiver, cryptomail_collection, code):
    # Update the code in MongoDB (in the cryptomail_collection)
    current_time = math.floor(time.time())
    # Check if the user is in the database
    existing_mail = cryptomail_collection.find_one({"mail": receiver})
    if existing_mail:
        # Remove the old code
        cryptomail_collection.delete_many({"mail": receiver})
    # Create a new entry for the user
    cryptomail_collection.insert_one({"mail": receiver, "code": code, "time": current_time})
    print(f"The code for {receiver} has been generated and stored.")
    
    # Delete the code after 10 minutes
    delete_code_timer = threading.Timer(600, delete_code, [receiver, cryptomail_collection, False])
    delete_code_timer.start()


def delete_code(receiver, cryptomail_collection, force_delete):
    # Check if the user is in the database
    existing_mail = cryptomail_collection.find_one({"mail": receiver})
    if existing_mail:
        current_time = math.floor(time.time())
        if force_delete or current_time - existing_mail["time"] > 600: # Check if the code is more than 10 minutes old (600 seconds)
            # Delete the code in the database
            cryptomail_collection.delete_many({"mail": receiver})
            print(f"The code for {receiver} has been deleted.")
        else:
            # Delete the code after 10 minutes because it is not old enough
            delete_code_timer = threading.Timer(600, delete_code, [receiver, cryptomail_collection, False])
            delete_code_timer.start()
    else:
        print(f"The code for {receiver} doesn't exist (anymore).")
    

def send_verification_mail(receiver, code):
    # Get the password from the password file
    password = ""
    with open('src/email_checking/password.txt') as f: # TODO change the access to the password 
        password = f.readlines()[0]
    
    # The subject and body of the mail
    subject = "CryptoMail: Verification code"
    body = f"""
    Hello,
    This is your verification code, it expires in 10 minutes.

    {code}

    If you have asked another verification code, this code will not work.
    Do not share this code or forward this e-mail. If you are not the source of this request, you can ignore this e-mail.
    """

    # Fill the EmailMessage object
    em = EmailMessage()
    em['From'] = sender
    em['To'] = receiver
    em['Subject'] = subject
    em.set_content(body)

    # Setup ssl context
    context = ssl.create_default_context()
    
    # Connect to the sender mail and send the code to the receiver
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(sender, password)
        smtp.sendmail(sender, receiver, em.as_string())

    print(f"The mail to {receiver} has been sent with the verification code.")