# app/services/credential_manager.py
from cryptography.fernet import Fernet
import json

class CredentialManager:
    def __init__(self):
        self.cipher = Fernet(os.environ['ENCRYPTION_KEY'])
    
    def encrypt_credentials(self, credentials):
        """Encrypt database credentials before storing"""
        json_str = json.dumps(credentials)
        return self.cipher.encrypt(json_str.encode()).decode()
    
    def decrypt_credentials(self, encrypted):
        """Decrypt credentials when needed"""
        decrypted = self.cipher.decrypt(encrypted.encode())
        return json.loads(decrypted)
    
    def store_user_connection(self, user_id, connection_name, credentials):
        """Store user's database connection securely"""
        encrypted = self.encrypt_credentials(credentials)
        # Store in your database
        db.execute(
            "INSERT INTO user_connections (user_id, name, credentials) VALUES (%s, %s, %s)",
            (user_id, connection_name, encrypted)
        )