#!/usr/bin/env python3
"""
Standalone Admin User Creation / Password Reset Script
Works directly with the SQLite database — no app dependencies needed.

Usage: python3 create_admin_standalone.py
"""

import sqlite3
import sys
import os
import getpass
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'techblog.db')


def get_password_hash(password):
    try:
        from werkzeug.security import generate_password_hash
        return generate_password_hash(password, method='pbkdf2:sha256')
    except ImportError:
        import hashlib, secrets
        salt = secrets.token_hex(8)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260000)
        return f"pbkdf2:sha256:260000${salt}${dk.hex()}"


def ensure_admin_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(80) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
    """)
    conn.commit()


def get_new_password():
    password = getpass.getpass("New password (min 6 chars): ")
    if len(password) < 6:
        print("Error: Password must be at least 6 characters.")
        sys.exit(1)
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Error: Passwords do not match.")
        sys.exit(1)
    return password


def main():
    print("\n" + "=" * 50)
    print("   TechBobbles — Admin Account Manager")
    print("=" * 50 + "\n")

    if not os.path.exists(DB_PATH):
        print(f"Database not found at: {DB_PATH}")
        print("Run this script from the project root directory.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_admin_table(conn)

    existing = conn.execute("SELECT id, username, email FROM admin").fetchall()

    if existing:
        print("Existing admin accounts:")
        for i, row in enumerate(existing, 1):
            print(f"  {i}. {row['username']} ({row['email']})")
        print()
        print("Options:")
        print("  1. Reset password for an existing admin")
        print("  2. Create a brand-new admin account")
        choice = input("\nChoose [1/2]: ").strip()

        if choice == '1':
            if len(existing) == 1:
                target = existing[0]
            else:
                num = input(f"Enter account number (1-{len(existing)}): ").strip()
                try:
                    target = existing[int(num) - 1]
                except (ValueError, IndexError):
                    print("Invalid selection.")
                    sys.exit(1)

            print(f"\nResetting password for: {target['username']} ({target['email']})")
            password = get_new_password()
            password_hash = get_password_hash(password)
            conn.execute("UPDATE admin SET password_hash = ? WHERE id = ?",
                         (password_hash, target['id']))
            conn.commit()
            conn.close()

            print("\n" + "=" * 50)
            print("  Password reset successfully!")
            print("=" * 50)
            print(f"  Username : {target['username']}")
            print(f"  Login at : http://localhost:8080/admin/login")
            print("=" * 50 + "\n")
            return

        elif choice != '2':
            print("Invalid choice. Exiting.")
            sys.exit(1)

    # Create new admin
    print("Creating a new admin account...\n")

    username = input("Username: ").strip()
    if not username:
        print("Error: Username cannot be empty.")
        sys.exit(1)
    if conn.execute("SELECT id FROM admin WHERE username = ?", (username,)).fetchone():
        print(f"Error: Username '{username}' is already taken.")
        sys.exit(1)

    email = input("Email: ").strip()
    if not email or '@' not in email:
        print("Error: A valid email address is required.")
        sys.exit(1)
    if conn.execute("SELECT id FROM admin WHERE email = ?", (email,)).fetchone():
        print(f"Error: Email '{email}' is already in use.")
        sys.exit(1)

    password = get_new_password()
    password_hash = get_password_hash(password)
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    conn.execute(
        "INSERT INTO admin (username, password_hash, email, created_at) VALUES (?, ?, ?, ?)",
        (username, password_hash, email, now)
    )
    conn.commit()
    conn.close()

    print("\n" + "=" * 50)
    print("  Admin account created successfully!")
    print("=" * 50)
    print(f"  Username : {username}")
    print(f"  Email    : {email}")
    print(f"  Login at : http://localhost:8080/admin/login")
    print("=" * 50 + "\n")


if __name__ == '__main__':
    main()
