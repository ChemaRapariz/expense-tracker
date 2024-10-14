from flask import Flask, flash, redirect, render_template, request, session 
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta, datetime
import calendar
import sqlite3
import os
import re

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

    # Get the database connection
    db = get_db()

    # Create a cursor
    cursor = db.cursor()

    # Get the current year and month
    current_year = datetime.now().year
    current_month = datetime.now().month

    # Calculate the first and last days of the month
    first_day_of_month = f'{current_year}-{current_month:02d}-01'
    if current_month == 12:
        next_month_first_day = f'{current_year + 1}-01-01'
    else:
        next_month_first_day = f'{current_year}-{current_month + 1:02d}-01'
    
    # SQL query to get the 6 most recent expenses for the current month and year
    query = """
    SELECT category, note, amount, payment_method, date FROM expenses
    WHERE user_id = ?
    AND date >= ?
    AND date < ?
    ORDER BY date DESC, created_at DESC
    LIMIT 6
    """

    # Execute the query 
    cursor.execute(query, (session['user_id'], first_day_of_month, next_month_first_day))
    rows = cursor.fetchall()

    # Query to calculate total expenses of the user this month
    total_expenses_query = """
    SELECT SUM(amount) as total_expenses
    FROM expenses
    WHERE user_id = ?
    AND date >= ?
    AND date < ?
    """

    cursor.execute(total_expenses_query, (session['user_id'], first_day_of_month, next_month_first_day))
    result = cursor.fetchone()

    # Get total expenses, defaulting to 0 if there are no expenses
    total_expenses = result['total_expenses'] if result['total_expenses'] is not None else 0

    # Get the number of days in the current month
    days_in_month = calendar.monthrange(current_year, current_month)[1]

    # Calculate the daily average expense
    daily_expenses = round(total_expenses / days_in_month, 2) if days_in_month > 0 else 0
 

    return render_template("index.html", rows=rows, total_expenses=total_expenses, daily_expenses=daily_expenses)

@app.route('/login', methods=["GET", "POST"])
def login():

    # Temporaly save the flashed messages
    flashed_messages = session.get('_flashes', [])

    # Clear all session data
    session.clear()

    # Re-flash the previously saved messages
    for category, message in flashed_messages:
        flash(message)

    if request.method == "POST":
        # Check if the user is registered
        username = request.form.get('username')
        password = request.form.get('password')

        # Remove spaces at the beginning and at the end of the username string
        username = username.strip()

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
            user_id = current_user["id"]
            hashed_password = current_user["hashed_passwords"]
        

        # Check if the password send through the form is correct
        if not check_password_hash(hashed_password, password):
            flash("Incorrect password")
            return redirect("/login")
    
        # Flash message, login completed  
        flash("Logged In Correctly")

        # Store user data in session
        session['username'] = username
        session['user_id'] = user_id
        
        return redirect("/")
    else:
        return render_template("login.html")

@app.route('/register', methods=["GET","POST"])
def register():

    # Temporaly save the flashed messages
    flashed_messages = session.get('_flashes', [])

    # Clear all session data
    session.clear()

    # Re-flash the previously saved messages
    for category, message in flashed_messages:
        flash(message)
    
    if request.method == "POST":
        # Store the data of the user that registers
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Check the username introduced
        if not username:
            flash("Username cannot be empty")
            return redirect("/register")

        if len(username) > 20:
            flash("Username is too long")
            return redirect("/register")

        # Get the database connection
        db = get_db()

        # Create a cursor
        cursor = db.cursor()
        
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

    # Get database connection
    db = get_db()

    # Create a cursor
    cursor = db.cursor()

    if request.method == "POST":

        # Obtain values and store them in variables
        category = request.form.get('category')
        note = request.form.get('note')
        amount = request.form.get('amount')
        payment_method = request.form.get('payment_method')
        date = request.form.get('date')

        # Check the 'category' value
        if not category or not category.replace(" ", "").isalpha():
            flash("Category must contain only letters and spaces")
            return redirect("/add")

        if len(category) > 80:
            flash("Category is too long")
            return redirect("/add")
        
        category = category.strip().capitalize()

        # Check the 'note' value
        if note:
            note = note.strip().capitalize()
            if len(note) > 180:
                flash("Note is too long")
                return redirect("/add")
            if not note.isprintable():
                flash("Notes must be made up of valid characters")
                return redirect("/add")

        # Check the 'amount' value
        # Regular expression to validate the format euros.cents
        if not amount or not re.match(r"^\d+(\.\d{1,2})?$", amount):
            flash("Invalid amount format. Please enter a valid amount in euros.cents format (e.g., 18.45).")
            return redirect("/add")
        
        # Check the 'payment_method' value
        if not payment_method:
            flash("The payment method must contain letters and/or numbers (e.g., Card).")
            return redirect("/add")

        payment_method = payment_method.strip().capitalize()

        # Check the 'date' value. Validate date format (yyyy-mm-dd)
        if not date or not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            flash("Invalid date format. Please enter a valid date")
            return redirect("/add")        

        cursor.execute("INSERT INTO expenses (user_id, category, note, amount, payment_method, date) VALUES (?, ?, ?, ?, ?, ?)", (session['user_id'], category, note, amount, payment_method, date))

        # Commit changes and close the connection
        db.commit()
        
        # Flash expense added message
        flash("Expense added successfully!")

        return redirect("/add")
    else:

        # Single query to get both distinct categories and payment methods
        cursor.execute("SELECT DISTINCT category, payment_method FROM expenses WHERE user_id = ?", (session['user_id'],))

        # Fetch all rows 
        rows = cursor.fetchall()

        # Use set to avoid duplicate categories and payment methods
        categories = set()
        payment_methods = set()

        # Loop through the rows and add the values to respective sets
        for row in rows:
            if row['category']:
                categories.add(row['category'])
            if row['payment_method']:
                payment_methods.add(row['payment_method'])
        
        # Convert sets to lists for rendering in the template
        categories = list(categories)
        payment_methods = list(payment_methods)

        # Render template and pass the data
        return render_template("add.html", categories=categories, payment_methods=payment_methods)

@app.route('/history', methods = ["GET", "POST"])
@login_required
def history():

    # Get database connection
    db = get_db()

    # Create a cursor
    cursor = db.cursor()

    # Get distinct categories for the dropdown filter
    category_query = "SELECT DISTINCT category FROM expenses WHERE user_id = ?"
    cursor.execute(category_query, (session['user_id'],))
    distinct_categories = cursor.fetchall()

    if request.method == "POST":

        # Store the filter choices of the user
        option = request.form.get("filter")
        limit = request.form.get("limit")
        order = request.form.get("order")
        categories = request.form.get("categories")
        date = request.form.get("date")

        # Sanitize and validate inputs
        valid_options = {"date": "date", "category": "category", "amount": "amount", "payment": "payment_method"}
        valid_limits = ["5", "10", "20", "50", "100", "All"]
        valid_order = ["ASC", "DESC"]

        # Validate 'option' variable
        if option:
            if option not in valid_options:
                flash("Please select a valid filter option")
                return redirect("/history")
            else:
                # Use the sanitized column name for the ORDER BY cluase
                order_by_column = valid_options[option]
        elif not option:
            order_by_column = "date"


        # Sanitize and validate 'limit' variable
        if not limit or limit not in valid_limits:
            flash("Please select one of the avialable limits")
            return redirect("/history")

        # Sanitize and validate 'order' variable
        if not order or order not in valid_order:
            flash("Please selecte a valid order")
            return redirect("/history")

        # Build the SQL query with the order and limit
        query = "SELECT transaction_id, category, note, amount, payment_method, date FROM expenses WHERE user_id = ? "
        params = [session['user_id']]

        # If a date filter is provided, validate it and added it to the query
        if date:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
                flash("Invalid date format. Please enter a valid date")
                return redirect("/add") 
            query += " AND date = ?"
            params.append(date)

        # If a category filter is provided, added it to the query
        if categories:
            query += " AND category = ?"
            params.append(categories)

        # Add sorting (order by column and ASC/DESC)
        query += f"ORDER BY {order_by_column} {order}, created_at {order}"
        

        # Add limit to the query if it is not "All"
        if limit != "All":
            query += " LIMIT ?"
            params.append(int(limit))

        # Execute the query
        cursor.execute(query, params)
        rows = cursor.fetchall()

        flash(f"Ordered by <span>{order_by_column.upper()}</span> in <span>{order}ENDING</span> order <span>{limit}</span> entries")
        if categories:
            flash(f"Category: <span>{categories.upper()}</span>")
        if date:
            flash(f"Date: <span>{date}</span>")
        return render_template("history.html", rows=rows, categories=distinct_categories)


    # Get data from the user
    cursor.execute("SELECT transaction_id, category, note, amount, payment_method, date FROM expenses WHERE user_id = ? ORDER BY date DESC, created_at DESC LIMIT 5", (session['user_id'], ))

    # Fetch data 
    rows = cursor.fetchall()

    flash(f"Ordered by <span>DATE</span> in <span>DESCENDING</span> order <span>5</span> entries")
    return render_template("history.html", rows=rows, categories=distinct_categories)

@app.route('/delete/<int:transaction_id>', methods = ["POST", "GET"])
@login_required
def delete(transaction_id):
    
    # Only process if the method is POST
    if request.method == "POST":
        # Get database connection
        db = get_db()
        cursor = db.cursor()

        # Verify if the expense exists and belongs to the current user
        cursor.execute("SELECT * FROM expenses WHERE user_id = ? AND transaction_id = ?", (session['user_id'], transaction_id))
        result = cursor.fetchone()

        # If the expense is found delte it from the table
        if result:
            cursor.execute("DELETE FROM expenses WHERE user_id = ? AND transaction_id = ?", (session['user_id'], transaction_id))

            # Commit the change
            db.commit()

            flash("Expense deleted successfully!")
        else:

            # If the expense is not found, tell the user
            flash("Expense not found")
    
    return redirect("/history")

@app.route('/summary', methods = ["GET", "POST"])
@login_required
def summary():
    if request.method == "POST":
        return redirect("/summary")
    return render_template("summary.html")

