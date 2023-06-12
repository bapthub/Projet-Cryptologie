# CryptoMail

CryptoMail est une application web basée sur Flask qui fournit une authentification sécurisée pour les utilisateurs. 
Une caractéristique clé de cette application est l'utilisation de certificats d'attributs pour une authentification robuste et fiable.


## Prérequis

- Docker : [Télécharger Docker](https://www.docker.com/products/docker-desktop)
- Un compte MongoDB 
- Une adresse mail Google avec les mots de passes d'application de configurés [Configuration](https://support.google.com/mail/answer/185833?hl=fr)

## Utilisation

1. Cloner le dépôt :
    ```bash
    git clone https://github.com/bapthub/Projet-Cryptologie.git
    cd Projet-Cryptologie
    ```
2. Créer un fichier `.env` dans le répertoire 'src' du projet et y ajouter vos variables d'environnement (remplacez `your-mongodb-uri`, `your-smtp-mail`, `your-smtp-password` et `your-secret-key` par vos propres valeurs) :
    ```
    MONGO_URI=your-mongodb-uri
    MAIL_SMTP=your-smtp-mail
    PASSWORD_SMTP=your-smtp-password
    SECRET_KEY=your-secret-key
    ```
3. Construire et exécuter l'application à l'aide de Docker :
    ```bash
    make run
    ```
    Ceci construit l'image Docker de l'application et démarre un conteneur Docker qui expose l'application sur le port 5000.

4. Ouvrez votre navigateur web et accédez à `http://localhost:5000` pour interagir avec l'application.

5. Pour arrêter et supprimer le conteneur Docker, exécutez :
    ```bash
    make kill
    ```

## Caractéristiques

1. **Gestion des utilisateurs** : Les utilisateurs peuvent s'inscrire et se connecter en utilisant leurs adresses email. Le mot de passe de l'utilisateur est haché avec Bcrypt (qui utilise l'algorithme Blowfish), puis encodé en base64. Les hachages bcrypt sont des données binaires, et l'encodage en base64 permet de les convertir en chaînes de caractères qui peuvent être facilement stockées dans la base de données MongoDB.

2. **Génération de certificat avec chiffrage RSA** : Pour sécuriser les informations sensibles, l'application utilise le chiffrage RSA. Le fichier crypto.py contient les fonctions pour générer des paires de clés RSA, pour générer des certificats d'attributs et pour vérifier leur validité.

3. **Vérification de validité des certificats d'attributs** : La validité des certificats d'attributs des utilisateurs est vérifiée avant chaque connexion. Les certificats expirés ou révoqués ne sont pas acceptés.

4. **Authentification par certificat d'attributs** : Lors de l'inscription, chaque utilisateur reçoit un certificat d'attributs unique qui doit être téléchargé et utilisé à chaque authentification. Ces certificats sont générés avec des paires de clés RSA et sont stockés sur le serveur.

5. **Vérification par email** : Lorsqu'un utilisateur s'inscrit, un email de vérification avec un code unique est envoyé à l'adresse email de l'utilisateur. Ce code doit être saisi dans l'application pour compléter le processus d'inscription.


## Remarque

- Il est possible de déployer cette application pour qu'elle soit accessible en ligne en la déployant dans une instance d'un fournisseur Cloud tiers.