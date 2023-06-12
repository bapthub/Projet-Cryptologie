import os
import datetime
import logging
import pymongo
from typing import Tuple
from random import randint
from cryptography import x509
from dotenv import load_dotenv
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa,padding

#MONGODB
load_dotenv('.env')
MONGO_URI = os.getenv("MONGO_URI")
client = pymongo.MongoClient(MONGO_URI)
db = client.get_database('crypto_users')
serial_collection = db['serial_collection']
revoked_collection = db['revoked_collection']
user_collection = db['user_collection']

#RSA
#===================================================================================================
def generate_key_pair() -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]: 
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend())
    public_key = private_key.public_key()
    return private_key, public_key

def store_key_pair(private_key:rsa.RSAPrivateKey, public_key:rsa.RSAPublicKey,
                   private_key_file:str, public_key_file:str) -> None:
    # Serialize the private key
    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption())
    # Serialize the public key
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    # Write the private key to a file
    with open(private_key_file, 'wb') as file:
        file.write(private_key_bytes)
    # Write the public key to a file
    with open(public_key_file, 'wb') as file:
        file.write(public_key_bytes)
        
def load_key_pair(private_key_file:str, public_key_file:str) -> Tuple[rsa.RSAPrivateKey,
                                                                        rsa.RSAPublicKey]:
    # Read the private key from the file
    with open(private_key_file, 'rb') as file:
        private_key_bytes = file.read()
        private_key = serialization.load_pem_private_key(
            private_key_bytes,password=None,backend=default_backend())

    # Read the public key from the file
    with open(public_key_file, 'rb') as file:
        public_key_bytes = file.read()
        public_key = serialization.load_pem_public_key(
            public_key_bytes,backend=default_backend())
    return private_key, public_key

#===================================================================================================
#Certificate  
def generate_serial_number() -> int:
    serial_number = randint(1, 2**63 - 1)
    while serial_collection.find_one({'serial_number': serial_number}) != None:
        serial_number = randint(1, 2**63 - 1)
    #insert serial number in database
    try:
        serial_collection.insert_one({"serial_number":serial_number})
    except Exception as e:
        logging.debug(f"Can't insert serial number {serial_number} in database. Error: {e}")
    return serial_number

def generate_attribute_certificate(holder_name:str,holder_surname:str,holder_email:str,
                                    private_key:rsa.RSAPrivateKey,
                                    public_key:rsa.RSAPublicKey) -> Tuple[bytes,int]:
    # Create certificate template
    builder = x509.CertificateBuilder()
    serial_number = generate_serial_number()
    builder = builder.serial_number(serial_number)
    builder = builder.subject_name(x509.Name([
        x509.NameAttribute(x509.NameOID.COMMON_NAME, f"{holder_name} {holder_surname}"),
        x509.NameAttribute(x509.NameOID.EMAIL_ADDRESS, holder_email)]))
    builder = builder.issuer_name(x509.Name([
        x509.NameAttribute(x509.NameOID.COMMON_NAME, 'Cryptomail'),]))
    builder = builder.not_valid_before(datetime.datetime.utcnow())
    expiry_time = datetime.datetime.utcnow() + datetime.timedelta(days=365)
    # expiry_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=1) #for testing
    builder = builder.not_valid_after(expiry_time)
    
    builder = builder.public_key(public_key)
    # Add attributes or extensions as needed
    # builder = builder.add_extension(extension, critical=False)
    
    # Sign the certificate
    certificate = builder.sign(
        private_key=private_key,
        algorithm=hashes.SHA256(),
        backend=default_backend())

    # Encode the certificate
    pem_cert = certificate.public_bytes(encoding=serialization.Encoding.PEM)
    return pem_cert,serial_number

def check_certificate_validity(cert_path:str,email:str,path:str,
                               public_key:rsa.RSAPublicKey) -> str:
    #Get certificate bytes from file
    with open(cert_path, 'rb') as cert_file:
        cert_bytes = cert_file.read()

    # Load the certificate from the PEM-encoded data
    try:
        certificate = x509.load_pem_x509_certificate(cert_bytes, default_backend())
    except ValueError:
        logging.debug("Can't load certificate from file")
        return "invalid"
    serial_number = certificate.serial_number

    # Verify the certificate's signature and integrity
    cert_public_key = certificate.public_key()
    try:
        cert_public_key.verify(
            certificate.signature,
            certificate.tbs_certificate_bytes,
            padding.PKCS1v15(),
            certificate.signature_hash_algorithm)
        # Check the issuer name
        issuer_name = certificate.issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
        if issuer_name[0].value != 'Cryptomail':
            logging.debug("Issuer name isn't Cryptomail")
            raise Exception
        # Check the public key corresponds to the issuer key
        if cert_public_key != public_key:
            logging.debug("Public key doesn't match provider public key")
            raise Exception
        # Check if certificate has been revoked
        if revoked_collection.find_one({'serial_number': serial_number}) != None:
            logging.debug("Certificate has been revoked")
            raise Exception
        # Check if certificate email corresponds to user
        cert_email = certificate.subject.get_attributes_for_oid(x509.NameOID.EMAIL_ADDRESS)[0].value
        if email != cert_email:
            logging.debug("Email does not match")
            raise Exception
    except Exception:
        return "invalid"

    # Check the certificate's validity period
    current_time = datetime.datetime.now()
    if certificate.not_valid_before > current_time or certificate.not_valid_after < current_time:
        return "expired"

    return "valid"
    
def revoke_certificate(serial_number:int):
    try:
        revoked_collection.insert_one({"serial_number":serial_number})
    except Exception as e:
        logging.debug(f"Can't insert serial number {serial_number} in database. Error: {e}")
        
def revoke_all_certificates():
    for cert in serial_collection.find():
        serial_number = cert["serial_number"]
        # Insert each document into the target collection
        revoked_collection.insert_one({"serial_number":serial_number})
