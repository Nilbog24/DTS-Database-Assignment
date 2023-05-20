import sqlite3
from sqlite3 import Error
from flask import Flask, render_template, request, redirect, session
from flask_bcrypt import Bcrypt
from datetime import datetime

DATABASE = 'C:/Users/brian/Documents/DTS-Database-Assignment/maoridictionary.db'
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "2u9repokheij"


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


def logged_in_checker():
    if session.get('email') is None:
        return None
    elif session.get('user_type') == 1:
        return 0
    elif session.get('user_type') == 2:
        return 1


def get_all_category():
    con = create_connection(DATABASE)
    cur = con.cursor()
    query = "SELECT * FROM categories"
    cur.execute(query, )
    return cur.fetchall()


@app.route('/')
def render_homepage():
    return render_template('home.html', logged_in=logged_in_checker(), categories=get_all_category())


@app.route('/category/<cat_id>')
def render_words(cat_id):
    con = create_connection(DATABASE)
    cur = con.cursor()
    query = "SELECT * FROM vocab_list WHERE category = ?"
    cur.execute(query, (cat_id,))
    words_list = cur.fetchall()

    return render_template('dictionary.html', logged_in=logged_in_checker(), categories=get_all_category(),
                           words=words_list)


@app.route('/login', methods=['POST', 'GET'])
def render_login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        query = "SELECT id, first_name, password, user_type FROM user WHERE email = ?"
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()
        print(user_data)

        if not bool(user_data):
            return redirect('/login')

        try:
            user_id = user_data[0][0]
            user_name = user_data[0][1]
            db_password = user_data[0][2]
            user_type = user_data[0][3]
        except IndexError:
            return redirect('/login')

        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=Password+incorrect")

        session['email'] = email
        session['user_id'] = user_id
        session["name"] = user_name
        session["user_type"] = user_type

        print(session)

        return redirect('/')
    return render_template('login.html', logged_in=logged_in_checker(), categories=get_all_category())


@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
    if request.method == 'POST':
        print(request.form)
        first_name = request.form.get('first_name').title().strip()
        last_name = request.form.get('last_name').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')
        user_type = request.form['user-type']

        if password != password2:
            return redirect("\signup?error=Passwords+do+not+match")

        if len(password) < 8:
            return redirect("\signup?error=Password+must+be+at+least+8+characters")

        hashed_password = bcrypt.generate_password_hash(password)
        con = create_connection(DATABASE)
        query = "INSERT INTO user(first_name, last_name, email, password, user_type) VALUES (?, ?, ?, ?, ?)"
        cur = con.cursor()

        try:
            cur.execute(query, (first_name, last_name, email, hashed_password, user_type))
        except sqlite3.IntegrityError:
            con.close()
            return redirect('\signup?error=Email+is+already+used')

        con.commit()
        con.close()

        return redirect("\login")

    return render_template('signup.html', logged_in=logged_in_checker(), categories=get_all_category())


@app.route("/logout")
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect("/")


@app.route('/worddisplay/<word_id>')
def render_worddisplay(word_id):
    con = create_connection(DATABASE)
    cur = con.cursor()
    query = "SELECT vocab_list.id, vocab_list.maori_word, vocab_list.english_translation, categories.category, " \
            "vocab_list.definition, vocab_list.level, vocab_list.image, user.first_name, vocab_list.last_edit_time " \
            "FROM vocab_list INNER JOIN categories ON vocab_list.category=categories.id INNER JOIN user ON " \
            "vocab_list.author=user.id WHERE vocab_list.id = ?"
    cur.execute(query, (word_id,))
    words_list = cur.fetchall()
    return render_template('worddisplay.html', logged_in=logged_in_checker(), categories=get_all_category(),
                           word=words_list)


@app.route('/addword', methods=['POST', 'GET'])
def render_addword():

    if logged_in_checker() != 1:
        redirect('/')

    if request.method == 'POST':
        maori_word = request.form.get('maori_text')
        english_translation = request.form.get('english_text')
        definition = request.form.get('definition_text')
        category = request.form.get('category_text')
        level = request.form.get('level_text')

        author = session.get('user_id')
        time = datetime.now()

        con = create_connection(DATABASE)
        cur = con.cursor()
        query = "INSERT INTO vocab_list (maori_word, english_translation, definition, last_edit_time, author, level, " \
                "category) VALUES (?, ?, ?, ?, ?, ?, ?)"
        cur.execute(query, (maori_word, english_translation, definition, time, author, level, category))
        con.commit()
    return render_template('add.html', logged_in=logged_in_checker(), categories=get_all_category())


@app.route('/removeword', methods=['POST', 'GET'])
def removeword():

    if logged_in_checker() != 1:
        redirect('/')

    if request.method == 'POST':
        print(request.form)
        removal_id = request.form.get('removal_id')

        con = create_connection(DATABASE)
        cur = con.cursor()
        query = "DELETE FROM vocab_list WHERE id = ?"
        cur.execute(query,(removal_id,))
        con.commit()
        con.close()
    return redirect("/")


app.run(host='0.0.0.0', debug=True)
