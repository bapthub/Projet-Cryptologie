from flask import Flask
# from flask_pymongo import pymongo

if __name__ == '__main__':
    app.run(debug=True)

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
    return 'Hello World!'

# @app.route('/delete/<username>', methods=['POST'])
# def delete_entries(username):
#     # Supprimer toutes les entrées pour l'utilisateur actuel dans la base de données
#     db.city_collection.delete_many({"username": username})
#     flash("All entries have been deleted.")
#     return redirect(url_for('visited', username=username))
