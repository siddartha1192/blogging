#!/usr/bin/env python3
"""
Create Admin User Script
Run this script to create your first admin user for TechBobbles CMS.
"""

from app import app, db, Admin
from werkzeug.security import generate_password_hash
import sys

def create_admin():
    with app.app_context():
        # Check if admin already exists
        admin = Admin.query.first()
        if admin:
            print("⚠️  An admin user already exists!")
            print(f"   Username: {admin.username}")
            print(f"   Email: {admin.email}")
            overwrite = input("\n   Do you want to create a new admin anyway? (yes/no): ")
            if overwrite.lower() != 'yes':
                print("Exiting...")
                return

        print("\n" + "="*50)
        print("   TechBobbles Admin User Creation")
        print("="*50 + "\n")

        # Get admin details
        username = input("Enter admin username: ").strip()
        if not username:
            print("❌ Username cannot be empty!")
            sys.exit(1)

        email = input("Enter admin email: ").strip()
        if not email:
            print("❌ Email cannot be empty!")
            sys.exit(1)

        password = input("Enter admin password: ").strip()
        if not password:
            print("❌ Password cannot be empty!")
            sys.exit(1)

        confirm_password = input("Confirm password: ").strip()
        if password != confirm_password:
            print("❌ Passwords do not match!")
            sys.exit(1)

        # Create admin user
        try:
            new_admin = Admin(
                username=username,
                email=email,
                password_hash=generate_password_hash(password, method='pbkdf2:sha256')
            )

            db.session.add(new_admin)
            db.session.commit()

            print("\n" + "="*50)
            print("✅ Admin user created successfully!")
            print("="*50)
            print(f"\nUsername: {username}")
            print(f"Email: {email}")
            print(f"\nYou can now login at: http://localhost:8080/admin/login")
            print("\n" + "="*50 + "\n")

        except Exception as e:
            print(f"\n❌ Error creating admin user: {str(e)}")
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    create_admin()
