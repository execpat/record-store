import sqlite3


def db_connection():
    """Open a connection with foreign keys enforced.
    SQLite ignores foreign keys unless this PRAGMA is set on EVERY connection,
    so use this helper in your Flask views too."""
    db = sqlite3.connect("albumStore.db")
    db.execute("PRAGMA foreign_keys = ON")
    db.row_factory = sqlite3.Row  # lets you use row["albumName"] in code/templates
    return db


def init_db():
    db = db_connection()
    cursor = db.cursor()

    # Albums in the shop
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            RecordID    INTEGER PRIMARY KEY AUTOINCREMENT,
            albumName   TEXT NOT NULL,
            albumArtist TEXT NOT NULL,
            albumGenre  TEXT,
            albumYear   INTEGER,
            albumPrice  REAL NOT NULL DEFAULT 0,
            albumCover  BLOB          
        )
    ''')

    # Registered users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            UserID       INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT NOT NULL UNIQUE,
            email        TEXT NOT NULL UNIQUE,
            password     TEXT NOT NULL   
        )
    ''')

    # Favourites: one row per (user, album) pair
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favourites (
            UserID   INTEGER NOT NULL,
            RecordID INTEGER NOT NULL,
            addedAt  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (UserID, RecordID),   
            FOREIGN KEY (UserID)   REFERENCES users(UserID)     ON DELETE CASCADE,
            FOREIGN KEY (RecordID) REFERENCES records(RecordID) ON DELETE CASCADE
        )
    ''')

    db.commit()
    db.close()


if __name__ == "__main__":
    init_db()


# ---------------------------------------------------------------------------
# Example queries for your Flask views
# ---------------------------------------------------------------------------
#
# Add a favourite (INSERT OR IGNORE means clicking twice does nothing bad):
#   db.execute("INSERT OR IGNORE INTO favourites (UserID, RecordID) VALUES (?, ?)",
#              (user_id, record_id))
#
# Remove a favourite:
#   db.execute("DELETE FROM favourites WHERE UserID = ? AND RecordID = ?",
#              (user_id, record_id))
#
# Get a user's favourites for the favourites page:
#   db.execute("""
#       SELECT r.* FROM records r
#       JOIN favourites f ON f.RecordID = r.RecordID
#       WHERE f.UserID = ?
#       ORDER BY f.addedAt DESC
#   """, (user_id,)).fetchall()
#
# Search on the browse page:
#   db.execute("""
#       SELECT * FROM records
#       WHERE albumName LIKE ? OR albumArtist LIKE ?
#   """, (f"%{q}%", f"%{q}%")).fetchall()
#
# Passwords (Flask already ships with werkzeug):
#   from werkzeug.security import generate_password_hash, check_password_hash