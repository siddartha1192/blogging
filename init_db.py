from app import app, init_db

if __name__ == "__main__":
    print("Initializing the database...")
    init_db()
    print("Database initialization complete!")