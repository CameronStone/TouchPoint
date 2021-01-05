import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
# Add @login_required in next iteration
app = Flask(__name__)

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

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///database.db")



# Home login page
@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")



# Registration: new users
@app.route("/register", methods=["GET", "POST"])
def register():

    # If users pushes register button
    if request.method == "POST":

        u = request.form.get("username")
        p = request.form.get("password")
        pa = request.form.get("passwordcheck")
        col = request.form.get("college")
        ext = request.form.get("extracurricular")
        con = request.form.get("concentration")

        # Check that username was entered
        if not u:
            return ("must provide username", 403)

        # Check that passwords were entered
        elif not p:
            return ("must provide password", 403)
        elif not pa:
            return ("must enter password again", 403)

        # Check that passwords match
        if p != pa:
            return ("incorrect password matches")

        # Check that user input something for each overlap category
        if not col or not ext or not con:
            return ("must enter something into each category (ex: if you do not attend college, put 'No College')", 403)

        # Check that username isn't already taken
        rows = db.execute("SELECT * FROM users WHERE username = ?", u)
        if len(rows) > 0:
            return ("You're already registered",403)

        # Input is valid, so add this user to the table and hash the password
        db.execute("INSERT INTO users ('username', 'password', 'college', 'extracurricular', 'concentration') VALUES (?, ?, ?, ?, ?)", u, generate_password_hash(p), col, ext, con)

        # Remember which user has logged in
        identity = db.execute("SELECT id FROM users WHERE username = ?", u)
        session["user_id"] = identity[0]['id']

        # Redirect user to start page where they enter their friends (this "logs" them in)
        return redirect("/start")

    # If user is registering for first time, send to registration page
    else:
        return render_template("register.html")



# Login: existing users
@app.route("/login", methods=["POST"])
def login():

    u = request.form.get("username")
    p = request.form.get("password")

    # Get actual password other user with that given username that they tried logging in with
    match = db.execute("SELECT password FROM users WHERE username = ?", u)

    # If the password the user entered matches the hashed password for that particular username, log them in
    if (len(match) > 0) and check_password_hash(match[0]['password'], p):
        # Remember which user has logged in
        identity = db.execute("SELECT id FROM users WHERE username = ?", u)
        session["user_id"] = identity[0]['id']
        return redirect("/start")

    # If the username or password is incorrect, simply refresh the page and let them try again
    return redirect("/")



# Input page: user inputs all friends and can see a growing table of who they've inputted
@app.route("/start", methods=["GET","POST"])
def start():

    # When users "adds" a new friend as input (correctly: there was actually a name inputted)
    if request.method == "POST" and request.form.get("name"):

        # Add the friend to the database with priority and connect them to the user with the friend_id
        friends_id = db.execute("INSERT INTO friends (name, priority, friend_id) VALUES (?, ?, ?)", request.form.get("name"), request.form.get("priority"), session["user_id"])

        # If friend shares same college as user, replace default value of '' with the name of college in the friend's row in the database
        college_temp_list = request.form.getlist("col")
        if college_temp_list == ['on']:
            user_temp_info = db.execute("SELECT college FROM users WHERE id = ?", session["user_id"])
            db.execute("UPDATE friends SET college = ? WHERE id = ?", user_temp_info[0]['college'], friends_id)

        # If friend shares same extracurricular as user, replace default value of '' with the name of extracurricular in the friend's row in the database
        extracurricular_temp_list = request.form.getlist("ext")
        if extracurricular_temp_list == ['on']:
            user_temp_info = db.execute("SELECT extracurricular FROM users WHERE id = ?", session["user_id"])
            db.execute("UPDATE friends SET extracurricular = ? WHERE id = ?", user_temp_info[0]['extracurricular'], friends_id)

        # If friend shares same concentration as user, replace default value of '' with the name of concetration in the friend's row in the database
        concentration_temp_list = request.form.getlist("con")
        if concentration_temp_list == ['on']:
            user_temp_info = db.execute("SELECT concentration FROM users WHERE id = ?", session["user_id"])
            db.execute("UPDATE friends SET concentration = ? WHERE id = ?", user_temp_info[0]['concentration'], friends_id)

    # Get all friends (ranked with the most important ones first) associated with that user
    info = db.execute("SELECT * FROM friends WHERE friend_id = ? ORDER BY priority", session["user_id"])

    # Get user's info (ex: college) to pre-fill the check boxes and make it easy to add a new user by checking overlaps
    profile_list = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    profile = profile_list[0]

    # Pass list of friends to be shown in the table. Pass the user's info to be used to enter any additional friends.
    return render_template("start.html", INFO=info, PROFILE=profile)



# TouchPoint algorithm takes into consideration overlaps and adjusts the priority of individuals. User enters the amount of time they wish to spend connecting on this data.html page
@app.route("/data")
def data():

        # Get all friends of the user
        temp = db.execute("SELECT * FROM friends WHERE friend_id = ?", session["user_id"])

        # Loop through every friend
        for row in range(len(temp)):

            # If the user and friend share a trait the name of it will have replaced the default '' value. Use this to check for overlaps.
            # If the trait it shared, give it a "weight" of 1 instead of default value 0
            college_match = 0
            extracurricular_match = 0
            concentration_match = 0
            if temp[row]['college'] != '':
                college_match = 1
            if temp[row]['extracurricular'] != '':
                extracurricular_match = 1
            if temp[row]['concentration'] != '':
                concentration_match = 1

            # TouchPoint algorithm: a friend's priority decreases the more common overlaps that are shared with the user (most "weight" given to same college)
            touchpoint_index = temp[row]['priority'] + 2 * college_match + 1 * extracurricular_match + 1 * concentration_match

            # Assign this new "priority" (TouchPoint index) to each friend as you loop through and calculate it individually
            db.execute("UPDATE friends SET tp_index = ? WHERE id = ?", touchpoint_index, temp[row]['id'])

        # Once every friend has been looped through, get info you need to create updated table of friends ranked by this new TouchPoint index
        info = db.execute("SELECT name, tp_index FROM friends WHERE friend_id = ? ORDER BY tp_index", session["user_id"])

        # Pass that info to html so it can be displayed in a table
        return render_template("data.html", INFO=info)



# Results page: calculates (based off your inputs) how much time per person you should spend
@app.route("/time", methods=["GET", "POST"])
def time():

    # Store number of hours that user inputted as time to spend connecting.
    users_time = request.form.get("time")

    if request.method == "POST" and users_time:

        # Convert inputted time to minutes.
        total_minutes = int(users_time) * 60

        # No TouchPoint Index can exceed value 9 (ex: someone of priority 5 also overlaps with college, extracurricular, and concentration yielding index of 9)
        # In order to use those values in fraction form to represent their true "weight", we must "invert" those values (ex: index 3 becomes value 7, index 8 becomes value 2)
        # Create variable to use to flip indexes into true values that can be used in fractions
        max_index = 10

        # Get friends of user ranked by TouchPoint index
        indexes = db.execute("SELECT id, tp_index FROM friends WHERE friend_id = ? ORDER BY tp_index", session["user_id"])
        # Count the sum of each new value as it is created (to be used as the denominator of our fraction that represents true "weight" each friend has)
        total_indexes = 0

        # Set table of friends to empty table for now
        table = []

        for row in range(len(indexes)):

            # "Invert" or flip the TouchPoint index into a value that will be used in the numerator of the fraction representing a friend's "weight"
            value = max_index - indexes[row]['tp_index']

            # Add these new values to a grand total, which represents the denominator of your fraction representing an individual friend's "weight"
            total_indexes += (value)

        # Once we calculate the total of the indexes-turned-values, use those "weight" fractions (or ratios) to convert total time into time allotted for that specific friend
        for row in range(len(indexes)):

            # Create fraction (or ratio) representing the "weight" carried by that friend
            fraction = (max_index - indexes[row]['tp_index']) / total_indexes

            # Find allotted time for each friend and update in database (based of total time user wants to spend)
            time = int(fraction * float(total_minutes))
            db.execute("UPDATE friends SET time = ? WHERE id = ?", time, indexes[row]['id'])

            # Get info of friends of user ranked by those with most time allotted first
            table = db.execute("SELECT name, time FROM friends WHERE friend_id = ? ORDER BY time DESC", session["user_id"])

        # Pass table of friends info to be displayed as well as the total time the user had inputted to spend connecting with everyone combined
        return render_template("time.html", INFO=table, TIME=users_time)

    else:
        return redirect ("/data")



# Logout
@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")