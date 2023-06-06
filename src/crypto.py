from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

# Génération des clés pour les certificats
def generate_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key

# Génération d'un certificat d'attributs pour un employé
def generate_attribute_certificate(employee_id, role, access_zones):
    private_key, public_key = generate_key_pair()
    certificate = {
        'employee_id': employee_id,
        'role': role,
        'access_zones': access_zones,
        'public_key': public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
    }
    return certificate, private_key

# Vérification du certificat d'attributs lors de l'accès à une zone sécurisée
def access_secure_zone(certificate, zone):
    # Vérification du certificat
    public_key = serialization.load_pem_public_key(
        certificate['public_key'].encode('utf-8'),
        backend=default_backend()
    )
    # Vérification des autorisations d'accès
    if zone in certificate['access_zones']:
        print("Accès autorisé à la zone sécurisée.")
    else:
        print("Accès refusé à la zone sécurisée.")

# Génération du certificat pour un employé
certificate, private_key = generate_attribute_certificate("12345", "employe", ["zone1", "zone2"])

# Simulation d'une demande d'accès à une zone sécurisée
requested_zone = "zone1"
access_secure_zone(certificate, requested_zone)
