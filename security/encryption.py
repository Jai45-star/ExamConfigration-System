"""
security/encryption.py — AES-256-CBC and RSA-2048 OAEP encryption.
"""
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def generate_aes_key() -> bytes:
    """Generates a 32-byte (256-bit) AES key."""
    return os.urandom(32)

def encrypt_aes_cbc(data: bytes, key: bytes) -> bytes:
    """
    Encrypts data using AES-256-CBC. 
    16-byte random IV is prepended to the ciphertext.
    """
    iv = os.urandom(16)
    # PKCS7 padding for AES blocks (128 bits / 16 bytes)
    pad_len = 16 - (len(data) % 16)
    padded_data = data + bytes([pad_len] * pad_len)
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return iv + ciphertext

def decrypt_aes_cbc(ciphertext_with_iv: bytes, key: bytes) -> bytes:
    """
    Decrypts data using AES-256-CBC.
    Extracts the first 16 bytes as the IV.
    """
    iv = ciphertext_with_iv[:16]
    ciphertext = ciphertext_with_iv[16:]
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Remove PKCS7 padding
    pad_len = padded_data[-1]
    return padded_data[:-pad_len]

def encrypt_rsa_oaep(data: bytes, public_key_pem: bytes) -> bytes:
    """Encrypts data with RSA-2048 OAEP."""
    public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())
    encrypted = public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted

def decrypt_rsa_oaep(encrypted_data: bytes, private_key_pem: bytes) -> bytes:
    """Decrypts data with RSA-2048 OAEP."""
    private_key = serialization.load_pem_private_key(private_key_pem, password=None, backend=default_backend())
    decrypted = private_key.decrypt(
        encrypted_data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted

def generate_rsa_keypair(private_key_path: str, public_key_path: str):
    """Generates and saves RSA-2048 keypair."""
    from cryptography.hazmat.primitives.asymmetric import rsa
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Save private key
    os.makedirs(os.path.dirname(private_key_path), exist_ok=True)
    with open(private_key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
        
    # Save public key
    public_key = private_key.public_key()
    with open(public_key_path, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
