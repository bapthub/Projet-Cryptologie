from flask import Flask,request,render_template,redirect,url_for
from crypto import *
# from flask_pymongo import pymongo

app = Flask(__name__)
# app.secret_key = ""

# MONGO_URI = ""
# client = pymongo.MongoClient(MONGO_URI)

# db = client.get_database('')
# user_collection = pymongo.collection.Collection(db, 'user_collection')

# def flask_mongodb_atlas():
#     return "flask mongodb atlas!"

@app.route('/', methods=['GET', 'POST'])
def index():
    return "Welcome to the homepage!"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Perform login authentication
        username = request.form['username']
        password = request.form['password']
        
        # Add your authentication logic here (e.g., check credentials against a database)
        # For simplicity, let's assume the username is 'admin' and password is 'password'
        if username == 'admin' and password == 'password':
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials. Please try again."
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return "Welcome to the dashboard!"

# @app.route('/delete/<username>', methods=['POST'])
# def delete_entries(username):
#     # Supprimer toutes les entrées pour l'utilisateur actuel dans la base de données
#     db.city_collection.delete_many({"username": username})
#     flash("All entries have been deleted.")
#     return redirect(url_for('visited', username=username))

if __name__ == '__main__':
    app.run(debug=True)