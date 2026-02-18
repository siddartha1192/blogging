#!/usr/bin/env python3
"""
Standalone Admin Account Manager — PostgreSQL edition.

Reads DATABASE_URL from the environment or from a .env file in the same
directory. Works directly against PostgreSQL so it is safe to use while
the Docker container is running.

Usage (from the project root on the HOST):
    python3 create_admin_standalone.py

Or from inside the running container:
    docker-compose exec app python create_admin_standalone.py
"""

import os
import sys
import getpass
from datetime import datetime


# ── Load .env so DATABASE_URL is available without exporting manually ──────
def _load_dotenv(path=None):
    path = path or os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

_load_dotenv()


# ── Resolve DATABASE_URL ───────────────────────────────────────────────────
DATABASE_URL = os.environ.get('DATABASE_URL', '')

# docker-compose sets it as postgresql://...; psycopg2 accepts that too.
if not DATABASE_URL:
    print("ERROR: DATABASE_URL is not set.")
    print("  Set it in your .env file or export it before running this script.")
    sys.exit(1)


# ── Password hashing ───────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    try:
        from werkzeug.security import generate_password_hash
        return generate_password_hash(password, method='pbkdf2:sha256')
    except ImportError:
        import hashlib, secrets
        salt = secrets.token_hex(8)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260000)
        return f"pbkdf2:sha256:260000${salt}${dk.hex()}"


# ── DB connection (supports both psycopg2 and psycopg) ────────────────────
def get_connection():
    try:
        import psycopg2
        return psycopg2.connect(DATABASE_URL), psycopg2
    except ImportError:
        pass
    try:
        import psycopg
        return psycopg.connect(DATABASE_URL), psycopg
    except ImportError:
        pass
    print("ERROR: No PostgreSQL driver found.")
    print("  Install one:  pip install psycopg2-binary")
    sys.exit(1)


def ensure_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            last_login TIMESTAMP
        )
    """)


def prompt_password() -> str:
    password = getpass.getpass("New password (min 6 chars): ")
    if len(password) < 6:
        print("ERROR: Password must be at least 6 characters.")
        sys.exit(1)
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("ERROR: Passwords do not match.")
        sys.exit(1)
    return password


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    print("\n" + "=" * 55)
    print("   TechBobbles — Admin Account Manager (PostgreSQL)")
    print("=" * 55 + "\n")

    conn, _ = get_connection()
    conn.autocommit = False
    cur = conn.cursor()

    ensure_table(cur)
    conn.commit()

    cur.execute("SELECT id, username, email FROM admin ORDER BY id")
    existing = cur.fetchall()

    if existing:
        print("Existing admin accounts:")
        for row in existing:
            print(f"  {row[0]}. {row[1]} ({row[2]})")
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
                    target = next(r for r in existing if r[0] == int(num))
                except (ValueError, StopIteration):
                    print("Invalid selection.")
                    sys.exit(1)

            print(f"\nResetting password for: {target[1]} ({target[2]})")
            password = prompt_password()
            pw_hash = hash_password(password)

            cur.execute(
                "UPDATE admin SET password_hash = %s WHERE id = %s",
                (pw_hash, target[0])
            )
            conn.commit()
            cur.close()
            conn.close()

            print("\n" + "=" * 55)
            print("  Password reset successfully!")
            print("=" * 55)
            print(f"  Username : {target[1]}")
            print(f"  Login at : /admin/login")
            print("=" * 55 + "\n")
            return

        elif choice != '2':
            print("Invalid choice.")
            sys.exit(1)

    # Create new admin
    print("Creating a new admin account...\n")

    username = input("Username: ").strip()
    if not username:
        print("ERROR: Username cannot be empty.")
        sys.exit(1)

    cur.execute("SELECT id FROM admin WHERE username = %s", (username,))
    if cur.fetchone():
        print(f"ERROR: Username '{username}' is already taken.")
        sys.exit(1)

    email = input("Email: ").strip()
    if not email or '@' not in email:
        print("ERROR: A valid email address is required.")
        sys.exit(1)

    cur.execute("SELECT id FROM admin WHERE email = %s", (email,))
    if cur.fetchone():
        print(f"ERROR: Email '{email}' is already in use.")
        sys.exit(1)

    password = prompt_password()
    pw_hash = hash_password(password)

    cur.execute(
        "INSERT INTO admin (username, password_hash, email, created_at) VALUES (%s, %s, %s, %s)",
        (username, pw_hash, email, datetime.utcnow())
    )
    conn.commit()
    cur.close()
    conn.close()

    print("\n" + "=" * 55)
    print("  Admin account created successfully!")
    print("=" * 55)
    print(f"  Username : {username}")
    print(f"  Email    : {email}")
    print(f"  Login at : /admin/login")
    print("=" * 55 + "\n")


if __name__ == '__main__':
    main()
