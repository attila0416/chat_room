from flask import Flask, request, send_from_directory, session, redirect, url_for
from flask_session import Session

from tempfile import mkdtemp
from functools import wraps
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

import sqlite3
import threading



# Configure application
app = Flask(__name__)

def dict_factory(cursor, row):
    dictionary = {}
    for i, column in enumerate(cursor.description):
        dictionary[column[0]] = row[i]
    return dictionary


# Configure db
db_connection = sqlite3.connect("chatapp.db", check_same_thread=False)
db_connection.row_factory = dict_factory
db_cursor = db_connection.cursor()

# db = SQL("sqlite:///chatapp.db")
# CREATE TABLE users (id INTEGER PRIMARY KEY, display_name TEXT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL);
# CREATE TABLE messages (display_name TEXT NOT NULL, message TEXT NOT NULL, date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP);
# CREATE TABLE online_users (display_name TEXT NOT NULL);

# Upon start of server, clear everything
db_cursor.execute("DELETE FROM messages;")
db_connection.commit()

db_cursor.execute("DELETE FROM online_users;")
db_connection.commit()



# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# lock for database
lock = threading.Lock()


def login_required(f):
    """
    Decorate routes to require login.
    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


# https://ide-830a2ed237784c8b822a346699de8f24-8080.cs50.ws/
@app.route('/<path:path>')
def serve_static_file(path):
    return send_from_directory('static/', path)


@app.route("/", methods=["GET"])
@login_required
def index():
    return app.send_static_file('index.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    if request.method == "POST":

        data = request.get_json()

        if data:
            username = data["username"]
            password = data["password"]

            # check if data is provided or not
            if not username:
                return {
                    "server_message": "Username not provided.",
                }
            elif not password:
                return {
                    "server_message": "Password not provided.",
                }

            # Query database for username
            lock.acquire(True)
            db_cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            users = db_cursor.fetchall()
            lock.release()

            # Ensure username exists
            if len(users) == 0:
                return {
                    "server_message": "Incorrect username.",
                }

            # Ensure password is correct
            if not check_password_hash(users[0]["hash"], password):
                return {
                    "server_message": "Incorrect password.",
                }

            # Remember which user has logged in
            session["user_id"] = users[0]["id"]

            # Redirect user to home page
            return {
                "redirect": "/",
            }

        else:
            return {
                "server_message": "No data provided.",
            }
    else:
        return app.send_static_file('login.html')


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()

    if request.method == "POST":
        """Register user"""

        data = request.get_json()

        if data:
            display_name = data["display_name"]
            username = data["username"]
            password = data["password"]
            confirmed_password = data["confirmed_password"]

            # check if data is provided or not
            if not display_name:
                return {
                    "server_message": "Display name not provided.",
                }
            elif not username:
                return {
                    "server_message": "Username not provided.",
                }
            elif not password:
                return {
                    "server_message": "Password not provided.",
                }
            elif not confirmed_password:
                return {
                    "server_message": "Password not confirmed.",
                }

            lock.acquire(True)
            # check if username already in db
            db_cursor.execute("SELECT * FROM users WHERE username=?;", (username,))
            users = db_cursor.fetchall()

            if len(users) != 0 or username == "server":
                return {
                    "server_message": "Username already registered.",
                }

            # check if passwords are the same or not
            if password != confirmed_password:
                return {
                    "server_message": "Password does not match.",
                }

            # encrypt password
            encypted_password = generate_password_hash(password, "sha256")

            # add user to database
            db_cursor.execute("INSERT INTO users (display_name, username, hash) VALUES (?, ?, ?);", (display_name, username, encypted_password))
            db_connection.commit()
            lock.release()

            return {
                "redirect": "/login",
            }

        else:
            return {
                "server_message": "No data provided.",
            }
    else:
        return app.send_static_file('register.html')


@app.route("/delete_account")
def delete_account():
    """Delete user's account"""

    lock.acquire(True)
    # Delete user from database
    db_cursor.execute("DELETE FROM users WHERE id=?;", (session["user_id"],))
    db_connection.commit()
    lock.release()

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/api/update_messages", methods=["POST"])
def update_messages():
    data = request.get_json()
    if data and data["message"] != "":
        message = data["message"]

        lock.acquire(True)
        db_cursor.execute("SELECT * FROM users WHERE id=?", (session["user_id"],))
        users = db_cursor.fetchall()

        display_name = users[0]["display_name"]

        # add message to database
        db_cursor.execute("INSERT INTO messages (display_name, message) VALUES (?, ?);", (display_name, message))
        db_connection.commit()
        lock.release()

    return {
        "server_message": "Correctly handled message",
    }


@app.route("/api/get_updates", methods=["GET"])
def api_get_updates():

    lock.acquire(True)
    # get user from database
    if session.get("user_id") is None:
        return {
            "redirect": "/login",
        }

    db_cursor.execute("SELECT * FROM users WHERE id=?", (session["user_id"],))
    users = db_cursor.fetchall()
    display_name = users[0]["display_name"]

    db_cursor.execute("SELECT * FROM messages;")
    messages = db_cursor.fetchall()

    db_cursor.execute("SELECT * FROM online_users;")
    online_users_unformatted = db_cursor.fetchall()
    lock.release()

    return {
        "current_user": display_name,
        "messages": messages,
    }


@app.route("/api/user_status", methods=["POST"])
def api_user_status():
    data = request.get_json()
    if data:
        user_status = data["user_status"]

        # get user from database
        lock.acquire(True)
        db_cursor.execute("SELECT * FROM users WHERE id=?", (session["user_id"],))
        users = db_cursor.fetchall()
        display_name = users[0]["display_name"]

        if user_status == "offline":
            # Delete user from active users
            db_cursor.execute("DELETE FROM online_users WHERE display_name=?;", (display_name,))
            db_connection.commit()

            db_cursor.execute("SELECT * FROM online_users")
            online_users = db_cursor.fetchall()

            # add message to database
            left_message = display_name + " left the chat"
            server_display_name = "server"
            db_cursor.execute("INSERT INTO messages (display_name, message) VALUES (?, ?);", (server_display_name, left_message))
            db_connection.commit()

            if len(online_users) == 0:
                db_cursor.execute("DELETE FROM messages;")
                db_connection.commit()

        elif user_status == "online":
            db_cursor.execute("SELECT * FROM online_users WHERE display_name=?;", (display_name,))
            found_online_users = db_cursor.fetchall()

            if len(found_online_users) == 0:
                # Insert user from active users
                db_cursor.execute("INSERT INTO online_users (display_name) VALUES (?);", (display_name,))
                db_connection.commit()

                # add message to database
                join_message = display_name + " joined the chat"
                server_display_name = "server"
                db_cursor.execute("INSERT INTO messages (display_name, message) VALUES (?, ?);", (server_display_name, join_message))
                db_connection.commit()

        lock.release()

    return {
        "server_message": "Correctly handled user's status",
    }



if __name__ == '__main__':
      app.run(host='0.0.0.0', port=8080)