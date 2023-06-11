import os
from dotenv import load_dotenv
from flask import Flask,request,render_template,redirect,url_for, flash, send_file
from crypto import *
from flask_pymongo import pymongo
from email_checking.email_checking import *


app = Flask(__name__)
app.secret_key = "dev"

load_dotenv('.env')
MONGO_URI = os.getenv("MONGO_URI")
client = pymongo.MongoClient(MONGO_URI)

db = client.get_database('crypto_users')
user_collection = pymongo.collection.Collection(db,'user_collection')
cryptomail_collection = pymongo.collection.Collection(db,'code_check')

path = os.getcwd()
private_key_file = f"{path}/private_key.pem"
public_key_file = f"{path}/public_key.pem"
    
if not os.path.exists(f"{path}/certificates_ca"):
    os.makedirs(f"{path}/certificates_ca")

if not os.path.exists(private_key_file) or not os.path.exists(public_key_file):
    # Generate the key pair if the files don't exist
    private_key, public_key = generate_key_pair()
    store_key_pair(private_key, public_key, private_key_file, public_key_file)

else:
    # Load the existing key pair from files
    private_key, public_key = load_key_pair(private_key_file, public_key_file)

def flask_mongodb_atlas():
    return "flask mongodb atlas!"

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        if 'certificate' in request.files:
            certificate_file = request.files['certificate']
            email = request.form['email']
            existing_mail = user_collection.find_one({"email": email})
            serial = existing_mail.get("serial_number")
            if certificate_file.filename != '':
                certificate_file.save(f'/tmp/{serial}.pem')
                file_loc = f"/tmp/{serial}.pem"
                res = check_certificate_validity(file_loc, path, public_key)
                if res != "valid":
                    return "invalid certificate"
                db.user_collection.update_one({"email": email}, {"$set": {"status": "Active"}})
                return "Success"
            return "Upload error"

        return redirect(url_for('login'))

    return render_template('login.html')

# SIGN-UP PAGE
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        nom = request.form['nom']
        prenom = request.form['prenom']

        existing_email = db.user_collection.find_one({"email": email})
        if existing_email:
            flash(f"{email} already taken")
            return redirect(url_for('signup'))
        else:
            db.user_collection.insert_one({"email": email, "nom": nom, "prenom": prenom, 
            "serial_number" : "" ,"status": "Inactive"})
            send_mail(email, cryptomail_collection)
            return redirect(url_for('code'))
    return render_template('signup.html')

# CODE CHECKER PAGE
@app.route('/code', methods=['GET', 'POST'])
def code():
    if request.method == 'POST':
        email = request.form['email']
        code = request.form['code']

        if verify_mail(email, cryptomail_collection, code):
            flash("correct code")
            nom = "ds"
            prenom = "ds"
            pem_cert, serial_number = generate_attribute_certificate(prenom, nom, email, private_key,public_key)
            # Save the certificate into a file
            with open(f"{path}/certificates_ca/{serial_number}.pem", 'wb') as file:
                file.write(pem_cert)
            db.user_collection.update_one({"email": email}, {"$set": {"serial_number": serial_number}})
             
            return redirect(url_for('certificate'))
        else:
            flash("wrong code")
            return redirect(url_for('code'))
    return render_template('code.html')

@app.route('/certificate', methods=['GET'])
def certificate():
    # Chemin vers le fichier que vous souhaitez télécharger
    existing_mail = user_collection.find_one({"email": "daniel.sarmiento@epita.fr"})
    serial = existing_mail.get("serial_number")
    file_path = f'certificates_ca/{serial}.pem'

    return render_template('certificate.html')

@app.route('/download_certificate', methods=['GET'])
def download_certificate():
    # files = os.listdir("./certificates_ca/")
    # return "<br>".join(files)
    # Chemin vers le fichier que vous souhaitez télécharger
    existing_mail = user_collection.find_one({"email": "daniel.sarmiento@epita.fr"})
    serial = existing_mail.get("serial_number")
    file_path = f'certificates_ca/{serial}.pem'

    # Télécharger le fichier en utilisant send_file
    return send_file(file_path, as_attachment=True)


@app.route('/dashboard')
def dashboard():
    return "Welcome to the dashboard!"

@app.route('/delete/<username>', methods=['POST'])
def delete_entries():
    # Supprimer toutes les entrées pour l'utilisateur actuel dans la base de données
    db.user_collection.delete_many({"username": username})
    flash("All entries have been deleted.")
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)