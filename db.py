import sqlite3
from config import DATABASE_FILE
from datetime import datetime
import os
import hashlib

def get_db():
    """Возвращает соединение с базой данных."""
    db = sqlite3.connect(DATABASE_FILE)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    """Инициализирует базу данных."""
    if not os.path.exists(os.path.dirname(DATABASE_FILE)):
        os.makedirs(os.path.dirname(DATABASE_FILE))

    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            image_path TEXT,
             tags TEXT
        )
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        left_banner_image TEXT,
        right_banner_image TEXT
    )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL,
             theme TEXT DEFAULT 'light'
        )
    """)
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            user_id INTEGER NOT NULL,
            article_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, article_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (article_id) REFERENCES articles(id)
        )
    """)
    
    settings = db.execute("SELECT * FROM settings").fetchone()
    if settings is None:
        db.execute("INSERT INTO settings (left_banner_image, right_banner_image) VALUES (?, ?)", ("", ""))
    db.commit()
    db.close()

def get_settings():
    """Возвращает все настройки"""
    db = get_db()
    settings = db.execute("SELECT * FROM settings").fetchone()
    db.close()
    return settings

def update_settings(left_banner_image, right_banner_image):
        """Обновляет настройки в базе данных."""
        db = get_db()
        db.execute(
            "UPDATE settings SET left_banner_image = ?, right_banner_image = ? WHERE id = 1",
            (left_banner_image, right_banner_image),
        )
        db.commit()
        db.close()


def insert_article(title, content, image_path, tags):
    """Добавляет статью в базу данных."""
    now = datetime.now().isoformat()
    db = get_db()
    db.execute(
        "INSERT INTO articles (title, content, created_at, updated_at, image_path, tags) VALUES (?, ?, ?, ?, ?, ?)",
        (title, content, now, now, image_path, tags),
    )
    db.commit()
    db.close()

def update_article(article_id, title, content, image_path, tags):
    """Обновляет статью в базе данных."""
    now = datetime.now().isoformat()
    db = get_db()
    db.execute(
        "UPDATE articles SET title = ?, content = ?, updated_at = ?, image_path = ?, tags = ? WHERE id = ?",
        (title, content, now, image_path, tags, article_id),
    )
    db.commit()
    db.close()

def delete_article(article_id):
  """Удаляет статью по ID из БД."""
  db = get_db()
  db.execute("DELETE FROM articles WHERE id = ?", (article_id,))
  db.commit()
  db.close()

def get_articles():
    """Возвращает все статьи из базы данных."""
    db = get_db()
    articles = db.execute("SELECT * FROM articles").fetchall()
    db.close()
    return articles

def get_article_by_id(article_id):
    """Возвращает статью по ID из базы данных."""
    db = get_db()
    article = db.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
    db.close()
    return article

def insert_user(username, password):
    """Добавляет пользователя в базу данных."""
    now = datetime.now().isoformat()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
            (username, hashed_password, now),
        )
        db.commit()
        db.close()
        return True
    except sqlite3.IntegrityError:
      db.close()
      return False

def get_user_by_username(username):
    """Возвращает пользователя по имени пользователя из базы данных."""
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    db.close()
    return user

def add_like(user_id, article_id):
    """Добавляет лайк в базу данных."""
    db = get_db()
    try:
        db.execute("INSERT INTO likes (user_id, article_id) VALUES (?, ?)", (user_id, article_id))
        db.commit()
        db.close()
        return True
    except sqlite3.IntegrityError:
      db.close()
      return False

def remove_like(user_id, article_id):
    """Удаляет лайк из базы данных."""
    db = get_db()
    db.execute("DELETE FROM likes WHERE user_id = ? AND article_id = ?", (user_id, article_id))
    db.commit()
    db.close()

def get_likes_count(article_id):
    """Возвращает количество лайков для статьи."""
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM likes WHERE article_id = ?", (article_id,)).fetchone()[0]
    db.close()
    return count

def has_user_liked(user_id, article_id):
    """Проверяет, лайкнул ли пользователь статью."""
    db = get_db()
    like = db.execute("SELECT * FROM likes WHERE user_id = ? AND article_id = ?", (user_id, article_id)).fetchone()
    db.close()
    return bool(like)

def update_user_nickname(user_id, username):
    """Обновляет никнейм пользователя."""
    db = get_db()
    try:
        db.execute("UPDATE users SET username = ? WHERE id = ?", (username, user_id))
        db.commit()
        db.close()
        return True
    except sqlite3.IntegrityError:
       db.close()
       return False


def update_user_password(user_id, password):
    """Обновляет пароль пользователя."""
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    db = get_db()
    db.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id))
    db.commit()
    db.close()

def update_user_theme(user_id, theme):
    """Обновляет тему пользователя."""
    db = get_db()
    db.execute("UPDATE users SET theme = ? WHERE id = ?", (theme, user_id))
    db.commit()
    db.close()

def get_user_by_id(user_id):
     """Возвращает пользователя по ID из базы данных."""
     db = get_db()
     user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
     db.close()
     return user