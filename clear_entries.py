"""
clear_entries.py — Script to wipe previous test data before exhibition.
Clears: ExamEntries, AuditLogs, RevokedTokens.
Keeps: Students, AdminUsers.
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import SessionLocal
from database.models import ExamEntry, AuditLog, RevokedToken

def clear_data():
    db = SessionLocal()
    try:
        print("Cleaning up system logs and entries for exhibition...")
        
        count_entries = db.query(ExamEntry).delete()
        count_audit = db.query(AuditLog).delete()
        count_tokens = db.query(RevokedToken).delete()
        
        db.commit()
        
        print("Done: Success!")
        print(f" - ExamEntries removed: {count_entries}")
        print(f" - AuditLogs removed: {count_audit}")
        print(f" - RevokedTokens removed: {count_tokens}")
        print("\nSystem is now clean and ready for live demo.")
        
    except Exception as e:
        db.rollback()
        print(f"Error during cleanup: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    confirm = input("Are you sure you want to delete ALL verification entries and audit logs? (y/n): ")
    if confirm.lower() == 'y':
        clear_data()
    else:
        print("Cleanup cancelled.")
