import random

def generate_email_code():
    code = ""
    for i in range(6):
        code += str(random.randint(0, 9))
    return code

def check_mail():
    # TODO
    return

def send_mail():
    # TODO
    return