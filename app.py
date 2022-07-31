import os
import re
import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    cash = db.execute("SELECT cash FROM users WHERE id=?", session["user_id"])
    # Declare lists and vars to store info
    symbol = []
    shares = []
    name = []
    price = []
    sum = []
    total = 0

    # Look up stock symbol and amount based on user_id
    stocks = db.execute(
        "SELECT symbol, amount FROM owned WHERE user_id=?", session["user_id"])
    for dict in stocks:
        # Store symbols in list
        symbol.append(dict["symbol"])

        # Store share amounts in list
        share_number = dict["amount"]
        shares.append(share_number)

        # Look up stock info for each stock
        info = lookup(dict["symbol"])

        # Store stock info in lists
        name.append(info["name"])
        share_price = info["price"]
        price.append(share_price)

        # Update total, store stock price sums in a list
        total += share_number * share_price
        sum.append(share_number * share_price)

    # Get number of iterations based on list length
    rows = len(symbol)

    # Add cash to total
    cash = float(cash[0]["cash"])
    total += cash

    # Input data into template, more optimal to use a dict next time, lazy to reimplement here
    return render_template("index.html", cash=cash, symbol=symbol, shares=shares, name=name, price=price, sum=sum, total=total, rows=rows)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        # Get info from form
        symbol = request.form.get("symbol")
        try:
            shares = int(request.form.get("shares"))
        except ValueError:
            return apology("Number of shares must be an integer", 400)

        # Check for input errors
        if not symbol:
            return apology("Must provide stock symbol", 400)

        if not shares:
            return apology("Must specify number of shares", 400)

        if shares < 1:
            return apology("Number of shares must be one or higher", 400)

        # Look up share price
        info = lookup(symbol)

        try:
            symbol = info["symbol"]
            price = info["price"]
        except TypeError:
            return apology("Invalid company", 400)

        # Check user cash
        find_cash = db.execute("SELECT cash FROM users WHERE id=?",
                               session["user_id"])

        # Convert list of dict data to int
        cash = int(find_cash[0]["cash"])

        # Check if user has enough to buy
        total = price * shares
        if total > cash:
            return apology("Not enough money to buy shares", 400)

        found_stock = None
        check_stock = db.execute(
            "SELECT symbol FROM owned WHERE user_id=?", session["user_id"])
        # For every dict in check_stock list find key/value pairs
        # If pair matches user's symbol, set found-stock to said symbol
        for dict in check_stock:
            for k, v in dict.items():
                if k == "symbol" and v == symbol:
                    found_stock = v

        # Update values if match found
        if found_stock == symbol:
            db.execute("UPDATE owned SET amount=amount+? WHERE user_id=? AND symbol=?",
                       shares, session["user_id"], symbol)
        # Insert values if match not found
        # Should just keep insert and add timestamp col/table?
        # This way, we don't need history table.
        # Would have to group data to display it in jinja tho
        else:
            db.execute("INSERT INTO owned (user_id, symbol, amount) VALUES (?, ?, ?)",
                       session["user_id"], symbol, shares)

        # Update users database with new cash value
        db.execute("UPDATE users SET cash=cash-? WHERE id=?",
                   total, session["user_id"])
        flash("Bought!")

        # Add history record with positive shares
        db.execute("INSERT INTO history (history_id, symbol, amount, price) VALUES(?, ?, ?, ?)",
                   session["user_id"], symbol, shares, price)

        # Return to homepage
        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    info = db.execute(
        "SELECT * FROM history WHERE history_id=?", session["user_id"])
    print(info)
    """Show history of transactions"""
    return render_template("history.html", info=info)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        # Look up company info based on symbol
        symbol = request.form.get("symbol")
        info = lookup(symbol)

        try:
            company = info["name"]
            price = info["price"]
            symbol = info["symbol"]
        except TypeError:
            return apology("Invalid company", 400)

        return render_template("quoted.html", company=company, price=price, symbol=symbol)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # This outputs a list of dicts
    usernames = db.execute("SELECT username FROM users")
    username_list = []

    # Contert list of dicts into a list
    for dict in usernames:
        for value in dict.values():
            username_list.append(value)

    username = request.form.get("username")
    password = request.form.get("password")
    confirmPassword = request.form.get("confirmation")

    if request.method == "POST":
        # Error messages if input not valid
        if not username:
            return apology("Must provide username", 400)

        if not password:
            return apology("Must provide password", 400)

        if password != confirmPassword:
            return apology("Passwords must match", 400)

        if username in username_list:
            return apology("Sorry, your username is taken", 400)

        # Validate passowords to have:
        # 1. At least one number
        # 2. At least one uppercase and one lowercase character
        # 3. At least one special sybmol
        # 4. 6 to 20 characters

        # Define pattern
        reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{4,20}$"
        pat = re.compile(reg)

        mat = re.search(pat, password)

        if not mat:
            return apology("password must have 1 number, 1 uppercase, 1 lowercase character, 1 special symbol", 403)

        # Generate password hash
        hashed_pw = generate_password_hash(
            password, method='pbkdf2:sha256', salt_length=8)

        # Add username and hashed password to database, return to homepage
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)",
                   username, hashed_pw)
        flash("Registered!")

        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "POST":
        symbol = request.form.get("symbol")
        try:
            amount = int(request.form.get("shares"))
        except ValueError:
            return apology("Number of shares must be an integer", 400)

        find_stocks = db.execute(
            "SELECT amount FROM owned WHERE user_id=? AND symbol=?", session["user_id"], symbol)
        try:
            owned_stocks = int(find_stocks[0]["amount"])
        except IndexError:
            return apology("Invalid stock", 403)

        if amount > owned_stocks:
            return apology("Not enough stocks to sell", 400)

        if amount < 1:
            return apology("Must sell one stock or more", 400)

        find_price = lookup(symbol)
        price = float(find_price["price"])
        total = price * amount

        db.execute("UPDATE users SET cash=cash+? WHERE id=?",
                   total, session["user_id"])
        db.execute("UPDATE owned SET amount=amount-? WHERE user_id=? AND symbol=?",
                   amount, session["user_id"], symbol)

        check_stock = db.execute(
            "SELECT amount FROM owned WHERE user_id=? AND symbol=?", session["user_id"], symbol)
        owned_stocks = int(check_stock[0]["amount"])
        if owned_stocks == 0:
            db.execute("DELETE FROM owned WHERE user_id=? AND symbol=?",
                       session["user_id"], symbol)

        # Add history record with negative shares
        db.execute("INSERT INTO history (history_id, symbol, amount, price) VALUES(?, ?, ?, ?)",
                   session["user_id"], symbol, -amount, price)

        flash("Sold!")
        return redirect("/")

    else:
        # Find owned stocks from database
        find_symbols = db.execute(
            "SELECT symbol FROM owned WHERE user_id=?", session["user_id"])
        # Store symbols in list
        symbol = []

        for s in find_symbols:
            symbol.append(s["symbol"])

        # Find number of iterations for jinja loop
        rows = len(symbol)
        # Sort symbol list alphabetically
        symbol.sort()

        return render_template("sell.html", symbol=symbol, rows=rows)


@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
    if request.method == "POST":

        current_password = request.form.get("current-password")
        new_password = request.form.get("password")
        confirm_new_password = request.form.get("confirmation")

        # Check basic input
        if not current_password:
            return apology("Must enter current password", 400)

        if not new_password:
            return apology("Must enter new password", 400)

        if not confirm_new_password:
            return apology("Must confirm new password", 400)

        if new_password != confirm_new_password:
            return apology("New passwords must match", 400)

        # Check if current password matches
        find_hash = db.execute("SELECT hash FROM users WHERE id=?",
                               session["user_id"])

        if len(find_hash) != 1 or not check_password_hash(find_hash[0]["hash"], current_password):
            return apology("Current password does not match", 400)

        # Define pattern for the check
        reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{4,20}$"
        pat = re.compile(reg)

        mat = re.search(pat, new_password)

        if not mat:
            return apology("New password must have 1 number, 1 uppercase, 1 lowercase character, 1 special symbol", 400)

        # Hash new password and update db
        hashed_pw = generate_password_hash(
            new_password, method='pbkdf2:sha256', salt_length=8)
        db.execute("UPDATE users SET hash=? WHERE id=?",
                   hashed_pw, session["user_id"])

        # Log out user
        session.clear()

        flash("Password Changed! Log in again")
        return render_template("login.html")

    else:
        isChange = True
        return render_template("change.html", isChange=isChange)
