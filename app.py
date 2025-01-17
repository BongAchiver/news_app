import os
from flask import Flask, render_template, request, redirect, url_for, abort, session
from werkzeug.utils import secure_filename
from config import SECRET_KEY
import db
from datetime import datetime
import hashlib

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

_db_initialized = False

def initialize_database():
    """Инициализация базы данных."""
    global _db_initialized
    if not _db_initialized:
        db.init_db()
        _db_initialized = True

def is_editor():
    return session.get("is_editor", False)

def is_admin():
    return session.get("is_admin", False)

def is_user_logged_in():
    return session.get("user_id", False)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    """Главная страница со списком статей."""
    initialize_database()
    articles = db.get_articles()
    liked_articles = {}
    likes_counts = {}
    current_theme = 'light' # Дефолтная тема
    if is_user_logged_in(): # Добавили проверку на пользователя
      user = db.get_user_by_id(session["user_id"])
      if user: # Добавили проверку на то что пользователь существует
        current_theme = user["theme"] # Получаем тему из базы

    if is_user_logged_in():
        for article in articles:
             liked_articles[article["id"]] = db.has_user_liked(session["user_id"], article["id"])
    
    for article in articles: # Добавили подсчет лайков
        likes_counts[article["id"]] = db.get_likes_count(article["id"])

    return render_template("index.html", articles=articles, liked_articles=liked_articles, likes_counts=likes_counts, current_theme=current_theme)

@app.route("/article/<int:article_id>")
def article(article_id):
    """Страница просмотра отдельной статьи."""
    initialize_database()
    article = db.get_article_by_id(article_id)
    if not article:
        abort(404)
    likes_count = db.get_likes_count(article_id)
    user_liked = False
    current_theme = 'light' # Дефолтная тема
    if is_user_logged_in():
        user_liked = db.has_user_liked(session["user_id"], article_id)
        user = db.get_user_by_id(session["user_id"]) # Получаем пользователя из БД
        if user: # Проверка на существование пользователя
            current_theme = user["theme"]
    return render_template("article.html", article=article, likes_count=likes_count, user_liked=user_liked, current_theme=current_theme)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Страница входа для редакторов."""
    initialize_database()
    if request.method == "POST":
        password = request.form.get("password")
        if password == SECRET_KEY:
            session["is_editor"] = True
            return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Страница входа для админа."""
    initialize_database()
    if request.method == "POST":
        password = request.form.get("password")
        if password == "admin":
            session["is_admin"] = True
            return redirect(url_for("admin_panel"))
    return render_template("admin_login.html")

@app.route("/logout")
def logout():
    """Выход редактора."""
    initialize_database()
    session.pop("is_editor", None)
    return redirect(url_for("index"))

@app.route("/admin/logout")
def admin_logout():
    """Выход админа"""
    initialize_database()
    session.pop("is_admin", None)
    return redirect(url_for("index"))

@app.route("/editor", methods=["GET", "POST"])
def editor():
    """Страница редактора для создания и редактирования статей."""
    initialize_database()
    if not is_editor():
        return redirect(url_for("login"))

    if request.method == "POST":
        article_id = request.form.get("id")
        title = request.form.get("title")
        content = request.form.get("content")
        image = request.files.get("image")
        tags = request.form.get("tags")
        image_path = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

        if article_id:
            db.update_article(article_id, title, content, image_path, tags)
        else:
           db.insert_article(title, content, image_path, tags)

        return redirect(url_for("index"))

    return render_template("editor.html")

@app.route("/editor/edit/<int:article_id>", methods=["GET"])
def edit_article(article_id):
    """Страница редактирования статьи."""
    initialize_database()
    if not is_editor():
        return redirect(url_for("login"))

    article = db.get_article_by_id(article_id)
    if not article:
        abort(404)
    return render_template("editor.html", article=article)

@app.route("/admin/panel", methods=["GET", "POST"])
def admin_panel():
        """Панель управления для администратора"""
        initialize_database()
        if not is_admin():
            return redirect(url_for("admin_login"))
        
        if request.method == "POST":
                left_banner = request.files.get("left_banner")
                right_banner = request.files.get("right_banner")

                left_banner_path = None
                right_banner_path = None

                if left_banner and allowed_file(left_banner.filename):
                    filename = secure_filename(left_banner.filename)
                    left_banner_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    left_banner.save(left_banner_path)

                if right_banner and allowed_file(right_banner.filename):
                    filename = secure_filename(right_banner.filename)
                    right_banner_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    right_banner.save(right_banner_path)


                db.update_settings(left_banner_path, right_banner_path)
                return redirect(url_for("admin_panel"))

        articles = db.get_articles()
        settings = db.get_settings()
        return render_template("admin_panel.html", articles=articles, settings=settings)

@app.route("/admin/delete/<int:article_id>", methods=["POST"])
def delete_article_from_admin_panel(article_id):
        """Удаление статьи через админ панель"""
        initialize_database()
        if not is_admin():
          return redirect(url_for("admin_login"))
        
        db.delete_article(article_id)
        return redirect(url_for("admin_panel"))

@app.route("/register", methods=["GET", "POST"])
def register():
        """Страница регистрации."""
        initialize_database()
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            
            if db.insert_user(username, password):
              return redirect(url_for("login_user"))
            else:
              return render_template("register.html", error="Пользователь с таким именем уже существует")
        
        return render_template("register.html")

@app.route("/login_user", methods=["GET", "POST"])
def login_user():
    """Страница входа для обычных пользователей."""
    initialize_database()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = db.get_user_by_username(username)
        if user and hashlib.sha256(password.encode()).hexdigest() == user["password"]:
          session["user_id"] = user["id"]
          return redirect(url_for("index"))
        else:
          return render_template("login_user.html", error="Неправильный логин или пароль")
    return render_template("login_user.html")

@app.route("/logout_user")
def logout_user():
    """Выход пользователя."""
    initialize_database()
    session.pop("user_id", None)
    return redirect(url_for("index"))

@app.route("/like/<int:article_id>", methods=["POST"])
def like_article(article_id):
    """Лайкает или убирает лайк"""
    if not is_user_logged_in():
        return redirect(url_for("login_user"))
        
    user_id = session["user_id"]
    if db.has_user_liked(user_id, article_id):
        db.remove_like(user_id, article_id)
    else:
        db.add_like(user_id, article_id)
    return redirect(url_for("index"))

@app.route("/settings", methods=["GET", "POST"])
def user_settings():
    """Страница настроек пользователя."""
    initialize_database()
    if not is_user_logged_in():
         return redirect(url_for("login_user"))
    
    user_id = session["user_id"]
    user = db.get_user_by_id(user_id)
    current_theme = user["theme"] # Получаем тему пользователя
    if request.method == "POST":
        if "username" in request.form:
          username = request.form.get("username")
          if db.update_user_nickname(user_id, username):
             return redirect(url_for("user_settings", message="Никнейм успешно изменен"))
          else:
               return render_template("user_settings.html", user=user, current_theme=current_theme, error="Пользователь с таким никнеймом уже существует")
        if "password" in request.form:
           password = request.form.get("password")
           db.update_user_password(user_id, password)
           return redirect(url_for("user_settings", message="Пароль успешно изменен"))
        if "theme" in request.form:
            theme = request.form.get("theme")
            db.update_user_theme(user_id, theme)
            return redirect(url_for("user_settings", message="Тема успешно изменена"))
          
    return render_template("user_settings.html", user=user, current_theme=current_theme) # Передаем current_theme


if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=False, host='0.0.0.0')