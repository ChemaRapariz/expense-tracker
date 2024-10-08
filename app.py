from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta
import sqlite3
import os

from helpers import get_db, close_db, login_required

# Configure application
app = Flask(__name__)

# Enable debug mode here
if __name__ == "__main__":
    app.run(debug=True)  

# Set up configuration to use the filesystem
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_sessions')
app.config['SESSION_PERMANENT'] = False
Session(app)

# Register the teardown function
app.teardown_appcontext(close_db)

# Configure headers to prevent caching
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route('/')
@login_required
def index():
    return render_template("index.html")

@app.route('/login', methods=["GET", "POST"])
def login():

    # Forget any session data
    session.clear()

    if request.method == "POST":
        # Check if the user is registered
        username = request.form.get('username')
        password = request.form.get('password')

        # Get the database connection
        db = get_db()

        # Create a cursor
        cursor = db.cursor()

        # Check if the username is in the database
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        current_user = cursor.fetchone()

        if not current_user:
            flash("Username is not registered")
            return redirect('/login')
        elif current_user:
            username = current_user["username"]
            hashed_password = current_user["hashed_passwords"]
        

        # Check if the password send through the form is correct
        if not check_password_hash(hashed_password, password):
            flash("Incorrect password")
            return redirect('/login')
    
        # Flash message, login completed  
        flash("Logged In Correctly")

        # Store user data in session
        session['username'] = username

        return redirect("/")
    else:
        return render_template("login.html")

@app.route('/register', methods=["GET","POST"])
def register():

    # Forget any session data
    session.clear()
    
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
            return redirect("/register")

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

        # Flash registered message
        flash("Registered correctly!")

        return redirect("/login")
    else:
        return render_template("register.html")

@app.route('/logout')
def logout():

    # Clear all session data
    session.clear()

    flash("You have been logged out")
    return redirect("/login")

@app.route('/add', methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":

        # Flash expense added message
        flash("Expense added successfully!")

        return redirect("/add")
    else:
        return render_template("add.html")