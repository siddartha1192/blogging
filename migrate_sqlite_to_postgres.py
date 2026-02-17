#!/usr/bin/env python3
"""
Migrate data from SQLite (techblog.db) → PostgreSQL.

Usage:
  # From your VPS, after docker compose is running:
  docker compose cp ./instance/techblog.db app:/app/instance/techblog.db
  docker compose exec app python migrate_sqlite_to_postgres.py

  # Or locally if you have Postgres running:
  DATABASE_URL=postgresql://user:pass@localhost/techblog python migrate_sqlite_to_postgres.py
"""

import os
import sys
import sqlite3
from datetime import datetime

# Ensure we can import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL env var is not set.")
    print("This script migrates FROM SQLite TO PostgreSQL.")
    print("Set DATABASE_URL to your Postgres connection string.")
    sys.exit(1)

# Find the SQLite database
SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'techblog.db')
if not os.path.exists(SQLITE_PATH):
    # Also check root directory (older Flask versions)
    SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'techblog.db')
if not os.path.exists(SQLITE_PATH):
    print(f"ERROR: SQLite database not found.")
    print(f"Looked in: instance/techblog.db and techblog.db")
    sys.exit(1)

print(f"SQLite source : {SQLITE_PATH}")
print(f"Postgres target: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")
print()

# ── Connect to SQLite ───────────────────────────────────────────
sqlite_conn = sqlite3.connect(SQLITE_PATH)
sqlite_conn.row_factory = sqlite3.Row

# ── Import Flask app (connects to Postgres via DATABASE_URL) ────
from app import app, db, Category, Author, Post, Topic, User, Subscriber, Admin, post_topics


def get_sqlite_rows(table_name):
    """Fetch all rows from a SQLite table."""
    cursor = sqlite_conn.execute(f"SELECT * FROM {table_name}")
    return [dict(row) for row in cursor.fetchall()]


def table_exists_in_sqlite(table_name):
    """Check if a table exists in the SQLite database."""
    cursor = sqlite_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def parse_datetime(value):
    """Parse a datetime string from SQLite into a Python datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(value, fmt)
        except (ValueError, TypeError):
            continue
    return None


def migrate_table(model_class, table_name, datetime_fields=None):
    """Migrate a single table from SQLite to Postgres."""
    datetime_fields = datetime_fields or []

    if not table_exists_in_sqlite(table_name):
        print(f"  SKIP {table_name} (not in SQLite)")
        return 0

    rows = get_sqlite_rows(table_name)
    if not rows:
        print(f"  SKIP {table_name} (empty)")
        return 0

    # Get valid column names from the model
    valid_columns = {c.name for c in model_class.__table__.columns}

    count = 0
    for row in rows:
        # Filter to only valid columns
        data = {k: v for k, v in row.items() if k in valid_columns}

        # Parse datetime fields
        for field in datetime_fields:
            if field in data:
                data[field] = parse_datetime(data[field])

        # Check if row already exists (by primary key)
        existing = db.session.get(model_class, data['id'])
        if existing:
            continue

        obj = model_class(**data)
        db.session.add(obj)
        count += 1

    return count


def migrate_post_topics():
    """Migrate the post_topics association table."""
    if not table_exists_in_sqlite('post_topics'):
        print("  SKIP post_topics (not in SQLite)")
        return 0

    rows = get_sqlite_rows('post_topics')
    if not rows:
        print("  SKIP post_topics (empty)")
        return 0

    count = 0
    for row in rows:
        # Check if association already exists
        exists = db.session.execute(
            post_topics.select().where(
                (post_topics.c.post_id == row['post_id']) &
                (post_topics.c.topic_id == row['topic_id'])
            )
        ).fetchone()

        if not exists:
            db.session.execute(post_topics.insert().values(
                post_id=row['post_id'],
                topic_id=row['topic_id']
            ))
            count += 1

    return count


def reset_sequences():
    """Reset Postgres auto-increment sequences to match migrated data."""
    tables = ['category', 'author', 'post', 'topic', 'user', 'subscriber', 'admin']
    for table in tables:
        try:
            db.session.execute(db.text(
                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {table}), 0) + 1, false)"
            ))
        except Exception:
            pass  # Table might not exist or be empty


def main():
    with app.app_context():
        # Create all tables in Postgres
        db.create_all()
        print("Postgres tables created.\n")

        print("Migrating data...")

        # Order matters: parents before children (foreign keys)
        counts = {}

        counts['category'] = migrate_table(Category, 'category')
        counts['author'] = migrate_table(Author, 'author')
        counts['topic'] = migrate_table(Topic, 'topic')
        counts['user'] = migrate_table(User, 'user', datetime_fields=['created_at', 'last_login'])
        counts['subscriber'] = migrate_table(Subscriber, 'subscriber', datetime_fields=['subscribed_on'])
        counts['admin'] = migrate_table(Admin, 'admin', datetime_fields=['created_at', 'last_login'])
        counts['post'] = migrate_table(Post, 'post', datetime_fields=['publish_date'])
        counts['post_topics'] = migrate_post_topics()

        # Commit all data
        db.session.commit()
        print()

        # Fix Postgres sequences so new inserts get correct IDs
        reset_sequences()
        db.session.commit()

        # Summary
        total = sum(counts.values())
        print("─" * 40)
        for table, count in counts.items():
            status = f"{count} rows" if count > 0 else "skipped"
            print(f"  {table:15s} → {status}")
        print("─" * 40)
        print(f"  Total: {total} rows migrated")
        print()

        if total > 0:
            print("Migration complete! Your data is now in PostgreSQL.")
        else:
            print("No new data to migrate (Postgres already has the data, or SQLite was empty).")

    sqlite_conn.close()


if __name__ == '__main__':
    main()
