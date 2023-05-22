import sqlite3
from sqlite3 import Error
from flask import Flask, render_template, request, redirect, session
from flask_bcrypt import Bcrypt
from datetime import datetime

DATABASE = 'C:/Users/brian/Documents/DTS-Database-Assignment/maoridictionary.db'
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "2u9repokheij"


# This function creates a connection with a table.
def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


# This function checks if the user is logged in or not.
# If the user is logged in, it then checks if the user is a teacher or student.
def logged_in_checker():
    if session.get('email') is None:
        return None
    elif session.get('user_type') == 1:
        return 0
    elif session.get('user_type') == 2:
        return 1


# This function returns all the category names from the categories table.
def get_all_category():
    con = create_connection(DATABASE)
    cur = con.cursor()
    query = "SELECT * FROM categories"
    cur.execute(query, )
    return cur.fetchall()


# This renders the home page.
@app.route('/')
def render_homepage():
    return render_template('home.html', logged_in=logged_in_checker(), categories=get_all_category())


# This renders the dictionary page.
# It renders the page with all the words in the category with the appropriate id.
@app.route('/category/<cat_id>')
def render_words(cat_id):
    con = create_connection(DATABASE)
    cur = con.cursor()
    query = "SELECT * FROM vocab_list WHERE category = ?"
    cur.execute(query, (cat_id,))
    words_list = cur.fetchall()

    return render_template('dictionary.html', logged_in=logged_in_checker(), categories=get_all_category(),
                           words=words_list)


# This renders the login page.
@app.route('/login', methods=['POST', 'GET'])
def render_login():
    # If the request method is post then this will run.
    if request.method == 'POST':
        # This will add two form sections for the user to input their email and password in order to login.
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        # This gets the information of the user with the appropriate email.
        query = "SELECT id, first_name, password, user_type FROM user WHERE email = ?"
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()
        print(user_data)

        # If the email is not in the users database this redirects the user to the start of the login page.
        if not bool(user_data):
            return redirect('/login')

        # If the user's data isn't within the database then it redirects the user to the start of the login page.
        try:
            user_id = user_data[0][0]
            user_name = user_data[0][1]
            db_password = user_data[0][2]
            user_type = user_data[0][3]
        except IndexError:
            return redirect('/login')

        # This checks if the password inputted matches with the hashed password in the database.
        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=Password+incorrect")

        # Lists the current logged in user's data as the current session's user.
        session['email'] = email
        session['user_id'] = user_id
        session["name"] = user_name
        session["user_type"] = user_type

        print(session)

        # Then redirects the user back to the home page.
        return redirect('/')
    return render_template('login.html', logged_in=logged_in_checker(), categories=get_all_category())


# Signup page.
@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
    if request.method == 'POST':
        print(request.form)
        # Form that asks for the first name, last name, email, and password of the user.
        # Asks the user to confirm their password, and if they are a student or a teacher.
        first_name = request.form.get('first_name').title().strip()
        last_name = request.form.get('last_name').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')
        user_type = request.form['user-type']

        # If the password doesn't match up with the second input then this will reload the page with the appropriate
        # error message.
        if password != password2:
            return redirect("\signup?error=Passwords+do+not+match")

        # Reloads the page with an error message if the password is less than 8 characters.
        if len(password) < 8:
            return redirect("\signup?error=Password+must+be+at+least+8+characters")

        # Hashes the password and then inputs all the inputted data into the user database.
        hashed_password = bcrypt.generate_password_hash(password)
        con = create_connection(DATABASE)
        query = "INSERT INTO user(first_name, last_name, email, password, user_type) VALUES (?, ?, ?, ?, ?)"
        cur = con.cursor()

        # Then this tries to execute the query in order to put the user data into the database.
        # If the email is already in the database then it will reload the page with an appropriate error message.
        try:
            cur.execute(query, (first_name, last_name, email, hashed_password, user_type))
        except sqlite3.IntegrityError:
            con.close()
            return redirect('\signup?error=Email+is+already+used')

        con.commit()
        con.close()

        # returns the user to the login page.
        return redirect("\login")
    return render_template('signup.html', logged_in=logged_in_checker(), categories=get_all_category())


# Logout function.
@app.route("/logout")
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect("/")


# Function for displaying a singular word.
@app.route('/worddisplay/<word_id>')
def render_worddisplay(word_id):
    con = create_connection(DATABASE)
    cur = con.cursor()
    # Uses inner join in order to pull from multiple tables and uses the foreign keys to pull specific items in the
    # list.
    query = "SELECT vocab_list.id, vocab_list.maori_word, vocab_list.english_translation, categories.category, " \
            "vocab_list.definition, vocab_list.level, vocab_list.image, user.first_name, vocab_list.last_edit_time " \
            "FROM vocab_list INNER JOIN categories ON vocab_list.category=categories.id INNER JOIN user ON " \
            "vocab_list.author=user.id WHERE vocab_list.id = ?"
    cur.execute(query, (word_id,))
    words_list = cur.fetchall()
    return render_template('worddisplay.html', logged_in=logged_in_checker(), categories=get_all_category(),
                           word=words_list)


# Function for adding a word to the vocab list database.
@app.route('/addword', methods=['POST', 'GET'])
def render_addword():

    # Redirects the user to the home page if they are not a teacher.
    if logged_in_checker() != 1:
        redirect('/')

    if request.method == 'POST':
        # Forms to get the necessary information about the word being added.
        maori_word = request.form.get('maori_text')
        english_translation = request.form.get('english_text')
        definition = request.form.get('definition_text')
        category = request.form.get('category_text')
        level = request.form.get('level_text')

        # Records who added the word and when.
        author = session.get('user_id')
        time = datetime.now()

        # Actually inserts the word into the database using the data given earlier.
        con = create_connection(DATABASE)
        cur = con.cursor()
        query = "INSERT INTO vocab_list (maori_word, english_translation, definition, last_edit_time, author, level, " \
                "category) VALUES (?, ?, ?, ?, ?, ?, ?)"
        cur.execute(query, (maori_word, english_translation, definition, time, author, level, category))
        con.commit()
    return render_template('add.html', logged_in=logged_in_checker(), categories=get_all_category())


# Function to remove a word.
@app.route('/removeword', methods=['POST', 'GET'])
def removeword():

    # Redirects the user to the home page if they are not a teacher.
    if logged_in_checker() != 1:
        redirect('/')

    if request.method == 'POST':
        # Form asking if the user want's to remove the word.
        print(request.form)
        removal_id = request.form.get('removal_id')

        # Deletes word with the appropriate id.
        con = create_connection(DATABASE)
        cur = con.cursor()
        query = "DELETE FROM vocab_list WHERE id = ?"
        cur.execute(query,(removal_id,))
        con.commit()
        con.close()

    # If the /removeword was added to the url directly, redirects the user to the homepage.
    elif request.method == 'GET':
        return redirect("/")

    return redirect("/")


app.run(host='0.0.0.0', debug=True)
