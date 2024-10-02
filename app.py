from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import os

# from helpers import apology, login_required, usd

# Configure application
app = Flask(__name__)

# Enable debug mode here
if __name__ == "__main__":
    app.run(debug=True)  

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_sessions')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNED_COOKIE'] = False
Session(app)

# Connect to the SQLite database
connect = sqlite3.connect("expenses.db")
cursor = connect.cursor()

@app.route('/')
def index():
    # Testing the local server and phpLiteAdmin
    return render_template("index.html")

@app.route('/register', methods=["GET","POST"])
def register():
    if request.method == "POST":
        return render_template("register.html")
    else:
        return render_template("register.html")