from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import os

from helpers import get_db, close_db

# Configure application
app = Flask(__name__)

# Enable debug mode here
if __name__ == "__main__":
    app.run(debug=True)  

# Set up configuration to use the filesystem
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_sessions')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNED_COOKIE'] = False
Session(app)

# Register the teardown function
app.teardown_appcontext(close_db)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Check if the user is logged in
        return render_template("/")
    else:
        return render_template("/login.html")

@app.route('/register', methods=["GET","POST"])
def register():
    if request.method == "POST":
        # Store the data of the user that registers
        username = request.form.get('username')
        password = request.form.get('password')

        # Check the data introduced

        # Generate password hash
        hash = generate_password_hash(password, method="pbkdf2", salt_length=16)

        # Get the database connection
        db = get_db()

        # Create a cursor and execute the insert
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (username, total_expenses, hashed_passwords) VALUES (?, ?, ?)", (username, 0, hash))

        # Commit changes and close the connection
        db.commit()

        # Store user data in session
        session['username'] = username

        # Flash registered message

        return render_template("login.html")
    else:
        return render_template("register.html")