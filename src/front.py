import os
import base64
from dotenv import load_dotenv
from flask import Flask,request,render_template,redirect,url_for, flash, send_file
from crypto import *
from pass_check import *
from flask_pymongo import pymongo
from email_checking.email_checking import *
from flask_bcrypt import Bcrypt


app = Flask(__name__)

### ENV VARIABLES
load_dotenv('.env')
app.secret_key = os.getenv("SECRET_KEY")
MONGO_URI = os.getenv("MONGO_URI")

### MONGODB 
client = pymongo.MongoClient(MONGO_URI)
db = client.get_database('crypto_users')
user_collection = db['user_collection']
cryptomail_collection = db['cryptomail_collection']

### PUBKEY & PRIVKEY GENERATION
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

### BCRYPT
bcrypt = Bcrypt(app)

def generate_hashed_password(password):
    return bcrypt.generate_password_hash(password)

def check_password_hashed(pass_hash, password):
    return bcrypt.check_password_hash(pass_hash, password)

### INDEX PAGE
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

### LOGIN PAGE
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        existing_mail = user_collection.find_one({"email": email})

        if existing_mail:
            user_pass_b64 = existing_mail.get("password")
            user_pass = base64.b64decode(user_pass_b64).decode()
            if check_password_hashed(user_pass, password):
                if existing_mail.get("status") == "Inactive":
                    flash("Veuillez d'abord vérifier votre certificat.", "error")
                    return redirect(url_for('verify'))
                if check_certificate_validity_login(email) != "valid":
                    flash("Certificat révoqué ou expiré.", "error")
                    return redirect(url_for('login'))
                return "Authentification terminée"
            else:
                flash("Utilisateur ou mot de passe incorrect", "error")
                return redirect(url_for('login'))
        else:
            flash("Utilisateur ou mot de passe incorrect", "error")
            return redirect(url_for('login'))    

    return render_template('login.html')

# VERIFY CERTIFICATE PAGE
@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'GET':
        
        return render_template('verify.html')

    if request.method == 'POST':
        if 'certificate' in request.files:
            certificate_file = request.files['certificate']
            email = request.form['email']
            existing_mail = user_collection.find_one({"email": email})

            if existing_mail:
                if certificate_file.filename != '':
                    serial = existing_mail.get("serial_number")
                    certificate_file.save(f'/tmp/{certificate_file.filename}')
                    file_loc = f'/tmp/{certificate_file.filename}'
                    res = check_certificate_validity_register(file_loc, email, path, public_key)
                    if res != "valid":
                        flash("Certificat invalide.", "error")
                        return redirect(url_for('verify'))
                    
                    db.user_collection.update_one({"email": email}, {"$set": {"status": "Active"}})
                    flash("Certificat valide.", "info")
                    return redirect(url_for('login'))
                flash("Erreur d'upload.", "error")
                return redirect(url_for('verify'))
            else:
                flash("Email incorrect.", "error")
                return redirect(url_for('verify'))

        return redirect(url_for('verify'))

    return render_template('verify.html')

### SIGN-UP PAGE
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        nom = request.form['nom']
        prenom = request.form['prenom']

        if not validate_password(password):
            flash("Le mot de passe ne respecte pas les conditions requises.", "error")
            return render_template('signup.html')

        hashed_password = generate_hashed_password(password)
        hashed_password_b64 = base64.b64encode(hashed_password).decode()
        
        existing_email = db.user_collection.find_one({"email": email})
        if existing_email:
            flash(f"{email} est déjà utilisé", "error")
            return redirect(url_for('signup'))
        else:
            db.user_collection.insert_one({"email": email, "password" : hashed_password_b64, "nom": nom, "prenom": prenom, 
            "serial_number" : "" ,"status": "Inactive"})
            send_mail(email, cryptomail_collection)
            return redirect(url_for('code'))
    return render_template('signup.html')

### CODE VERIFICATION PAGE
@app.route('/code', methods=['GET', 'POST'])
def code():
    if request.method == 'POST':
        email = request.form['email']
        code = request.form['code']

        if verify_mail(email, cryptomail_collection, code):
            existing_mail = user_collection.find_one({"email": email})
            nom = existing_mail.get("nom")
            prenom = existing_mail.get("prenom")
            pem_cert, serial_number = generate_attribute_certificate(prenom, nom, email, private_key,public_key)
            with open(f"{path}/certificates_ca/{serial_number}.pem", 'wb') as file:
                file.write(pem_cert)
            db.user_collection.update_one({"email": email}, {"$set": {"serial_number": serial_number}})
            flash("Code valide.", "info")
            return redirect(url_for('certificate'))
        else:
            flash("Email ou code incorrect.", "error")
            return redirect(url_for('code'))
    return render_template('code.html')

### CERTIFICATE WITH AUTHENTICATION PAGE
@app.route('/certificate', methods=['GET', 'POST'])
def certificate():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        existing_mail = user_collection.find_one({"email": email})

        if existing_mail:
            user_pass_b64 = existing_mail.get("password")
            user_pass = base64.b64decode(user_pass_b64).decode()
            if check_password_hashed(user_pass, password):
                serial = existing_mail.get("serial_number")
                file_path = f'certificates_ca/{serial}.pem'
                return redirect(url_for('download_certificate', serial=serial))
            else:
                flash("Utilisateur ou mot de passe incorrect.", "error")
                return redirect(url_for('certificate'))
        else:
            flash("Utilisateur ou mot de passe incorrect.", "error")
            return redirect(url_for('certificate'))    

    return render_template('certificate.html')

### DOWNLOAD CERTIFICATE PAGE
@app.route('/download_certificate/<serial>', methods=['GET'])
def download_certificate(serial):
    file_path = f'certificates_ca/{serial}.pem'
    return send_file(file_path, as_attachment=True) 

if __name__ == '__main__':
    app.run(debug=False)