import sqlite3

from flask import Blueprint, render_template, request, url_for, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import db_connection


views = Blueprint('views', __name__)
ALLOWED = {"jpg", "jpeg", "png"}

@views.route('/')
def home():
    return render_template("index.html")


@views.route('/records')
def records():
    connection = db_connection()
    try:
        albums = connection.execute(
            "SELECT * FROM records"
        ).fetchall()
    finally:
        connection.close()

    return render_template("records.html", albums=albums)


@views.route('/account', methods=["GET", "POST"])
def account():
    connection = db_connection()

    if request.method == "POST":
        new_user = request.form.get("newUsername", "").strip()
        new_email = request.form.get("newEmail", "").strip()
        new_psw = request.form.get("newPassword", "").strip()
        album_form = request.form.get("add_album")

        user = connection.execute(
            "SELECT * FROM users WHERE username = ?", (session["username"],)
        ).fetchone()

        if new_user:
            try:
                connection.execute(
                    "UPDATE users SET username = ? WHERE UserID = ?",
                    (new_user, user["UserID"]),
                )
                connection.commit()
            except sqlite3.IntegrityError:
                flash("Username already exists!")
            else:
                session["username"] = new_user
                flash("Username updated!")

        elif new_email:
            try:
                connection.execute(
                    "UPDATE users SET email = ? WHERE UserID = ?",
                    (new_email, user["UserID"]),
                )
                connection.commit()
                flash("Email updated!")
            except sqlite3.IntegrityError:
                flash("Email already exists!")

        elif new_psw:
            connection.execute(
                "UPDATE users SET password = ? WHERE UserID = ?",
                (generate_password_hash(new_psw), user["UserID"]),
            )
            connection.commit()
            flash("Password updated!")

        #Adding album into database handler
        elif album_form:
            album_name = request.form["new_albumName"]
            album_artist = request.form["new_albumArtist"]
            album_genre = request.form["new_albumGenre"]
            album_year = request.form["new_albumYear"]
            album_price = request.form["new_albumPrice"]
            album_cover = request.files.get("new_albumCover")

            cover_data = None

            if album_cover:
                ext = album_cover.filename.rsplit(".", 1)[-1].lower()
                if ext not in ALLOWED:
                    flash("Invalid image type.")
                    return redirect(url_for("views.account"))
                else:
                    existing = connection.execute(
                        "SELECT 1 FROM records "
                        "WHERE albumName = ? "
                        "AND albumArtist = ? "
                        "AND albumGenre = ? "
                        "AND albumYear = ? ",
                        (album_name, album_artist, album_genre, album_year),
                    ).fetchone()

                    if existing:
                        flash("Album already exists!", "danger")
                        connection.close()
                        return redirect(url_for("views.account"))

                cover_data = album_cover.read()  # bytes

                try:
                    connection.execute(
                        "INSERT INTO records (albumName, albumArtist, albumGenre, albumYear, albumPrice, albumCover) VALUES (?, ?, ?, ?, ?, ?)",
                        (album_name, album_artist, album_genre, album_year, album_price, cover_data),
                    )
                except sqlite3.IntegrityError:
                    flash("Error", "danger")
                finally:
                    connection.commit()
                    flash("Successfully Added!", "success")
                    connection.close()
            else:
                flash("Album cover not found!", "danger")

        return redirect(url_for("views.account"))  # reload the page to show the message

    connection.close()
    return render_template("account.html", username=session["username"])


@views.route('/favourites')
def favourite_list():
    return render_template("list.html")


@views.route('/buy_records')
def buy_records():
    return render_template("buy_records.html")


# ACCOUNT PAGES

@views.route("/register", methods=["GET", "POST"])
def register():

    # Session check moved to the top
    if "username" in session:
        return redirect(url_for("views.account"))

    if request.method == "GET":
        return render_template("register.html")

    username = request.form["regUsername"]
    email = request.form["regEmail"]
    password = request.form["regPassword"]

    # Validation
    errors = []
    if not username or not email or not password:
        errors.append("Please fill in every field.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if "@" not in email:
        errors.append("Please enter a valid email address.")

    # Check for dupes
    if not errors:
        connection = db_connection()
        try:
            existing = connection.execute(
                "SELECT username, email FROM users WHERE username = ? OR email = ?",
                (username, email),
            ).fetchall()

            for row in existing:
                if row["username"] == username:
                    errors.append("That username is already taken.")
                if row["email"] == email:
                    errors.append("That email is already registered.")

            if not errors:
                connection.execute(
                    "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                    (username, email, generate_password_hash(password)),
                )
                connection.commit()
                flash("Account created! Please log in.", "success")
                return redirect(url_for("views.login"))
        finally:
            connection.close()

    for error in errors:
        flash(error, "danger")
    return render_template("register.html", username=username, email=email)


@views.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["nm"]
        password = request.form["psw"]

        connection = db_connection()
        user = connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password_hash(user["password"], password):
            session.permanent = True
            session["username"] = user["username"]
            connection.close()
            return redirect(url_for("views.account"))

        return redirect(url_for("views.account"))

    elif "username" in session:
        flash("You are already logged in!", "info")
        return redirect(url_for("views.account"))
    else:
        return render_template("login.html")

@views.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("views.login"))
