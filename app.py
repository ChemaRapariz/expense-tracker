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
        return redirect("/")
    else:
        return render_template("login.html")

@app.route('/register', methods=["GET","POST"])
def register():
    if request.method == "POST":
        # Store the data of the user that registers
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Get the database connection
        db = get_db()

        # Create a cursor
        cursor = db.cursor()

        # Check the username introduced
        if not username:
            flash("Username cannot be empty")
            return redirect("/register")
        
        # Check if the username already exists
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Username is already taken. Please choose another")
            return redirect("/register")

        # Check that the username is exclusively made up of letters or/and numbers
        if not username.isalnum():
            flash("Username must be made up of letters and/or numbers")
            return redirect("/register")

        # Check that the user has introduced both passwords
        if not password or not confirm_password:
            flash("Password fields cannot be empty")
            return redirect("/register")

        # Check the lenght of the password
        if len(password) < 8 or len(confirm_password) < 8:
            flash("Password should be at least 8 characters long")

        # Check if both passwords match
        if password != confirm_password:
            flash("Passwords should match")
            return redirect("/register")

        # Generate password hash
        hash = generate_password_hash(password, method="pbkdf2", salt_length=16)

        # Execute the insert of the new user
        cursor.execute("INSERT INTO users (username, total_expenses, hashed_passwords) VALUES (?, ?, ?)", (username, 0, hash))

        # Commit changes and close the connection
        db.commit()

        # Store user data in session
        session['username'] = username

        # Flash registered message

        return redirect("/login")
    else:
        return render_template("register.html")