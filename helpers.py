from functools import wraps
from flask import current_app, g, request, redirect, url_for
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