from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3

# from helpers import apology, login_required, usd

# Configure application
app = Flask(__name__)

# Connect to the SQLite database
connect = sqlite3.connect("expenses.db")
cursor = connect.cursor()

# Configure session to use filesystem (instead of signed cookies)
# app.config["SESSION PERMANENT"] = False 
# app.config["SESSION TYPE"] = "filesystem"
# Session(app)


@app.route('/')
def index():
    "Testing the local server and phpLiteAdmin"
    return render_template("index.html")
