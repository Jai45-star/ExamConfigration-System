"""
seed_admin.py — Creates a default super-admin user.
Run this ONCE after setting up the database.
"""
import sys
import os
from sqlalchemy.orm import Session

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import SessionLocal, run_schema
from database.models import AdminUser
from security.hashing import hash_password

def seed():
    # Ensure tables exist
    print("Initializing schema...")
    try:
        run_schema()
    except Exception as e:
        print(f"Warning/Error running schema: {e}")

    db: Session = SessionLocal()
    
    username = "JAIRAJ"
    password = "qwertyuiop"
    
    existing = db.query(AdminUser).filter(AdminUser.username == username).first()
    if existing:
        print(f"Admin user '{username}' already exists. Skipping.")
        return

    admin = AdminUser(
        username=username,
        password_hash=hash_password(password),
        role="super_admin"
    )
    
    db.add(admin)
    db.commit()
    print(f"Successfully created super-admin user.")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print("!!! PLEASE CHANGE THIS PASSWORD AFTER LOGIN !!!")
    db.close()

if __name__ == "__main__":
    seed()
