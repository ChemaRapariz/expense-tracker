from functools import wraps
from flask import current_app, g, request, redirect, url_for, session
import sqlite3

# Function to get or create a database connection
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('expenses.db', check_same_thread = False)

        # Makes rows behave like dicts
        g.db.row_factory = sqlite3.Row
    return g.db

# Closing the connection automatically after the request ends
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Login Required Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        # Safely check if 'username' exists in session and is not None or empty
        if not session.get('username'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function