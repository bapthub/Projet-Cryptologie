import random
from email.message import EmailMessage
import ssl
import smtplib


# Our mail used to send the codes
sender = "cryptomailepita@gmail.com "


def generate_email_code():
    # Generate a 6 digits code
    code = ""
    for i in range(6):
        code += str(random.randint(0, 9))
    return code


def check_mail():
    # TODO
    return


def send_mail(receiver):
    # Generate a 6 digits code
    code = generate_email_code()
    # Send the code to the receiver
    send_verification_mail(receiver, code)


def send_verification_mail(receiver, code):
    # Get the password from the password file
    password = ""
    with open('src/email-checking/password.txt') as f: # TODO change the access to the password 
        password = f.readlines()[0]
    
    # The subject and body of the mail
    subject = "CryptoMail: Verification code"
    body = f"""
    Hello,
    This is your verification code, it expires in 10 minutes.

    {code}

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