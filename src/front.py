from flask import Flask,request,render_template,redirect,url_for, flash
from crypto import *
from flask_pymongo import pymongo

app = Flask(__name__)
app.secret_key = "dev"

MONGO_URI = "mongodb+srv://danielsarmiento:nG9xkw5b3zkJhf3@epita.xqy9hdp.mongodb.net/?retryWrites=true&w=majority"
client = pymongo.MongoClient(MONGO_URI)

db = client.get_database('crypto_users')
user_collection = pymongo.collection.Collection(db,'user_collection')
code_check_collection = pymongo.collection.Collection(db,'code_check')


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
            db.user_collection.insert_one({"email": email, "nom": nom, "prenom": prenom, "status": "Inactive"})
            return redirect(url_for('code'))
    return render_template('signup.html')

# CODE CHECKER PAGE
@app.route('/code', methods=['GET', 'POST'])
def code():
    if request.method == 'POST':
        email = request.form['email']
        code = request.form['code']

        code_check = db.code_check_collection.find_one({"email": code, "code": code})
        if code_check:
            flash("correct code")
            db.user_collection.update_one({"email": email}, {"$set": {"status": "Active"}})
            return redirect(url_for('code'))
        else:
            flash("wrong code")
            return redirect(url_for('code'))
    return render_template('code.html')


@app.route('/dashboard')
def dashboard():
    return "Welcome to the dashboard!"

@app.route('/delete/<username>', methods=['POST'])
def delete_entries(username):
    # Supprimer toutes les entrées pour l'utilisateur actuel dans la base de données
    db.user_collection.delete_many({"username": username})
    flash("All entries have been deleted.")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)