import sqlite3
from sqlite3 import Error
from flask import Flask, render_template, request, redirect, session
from flask_bcrypt import Bcrypt

DATABASE = 'C:/Users/brian/Documents/DTS-Database-Assignment/maoridictionary.db'
app = Flask(__name__)
bcrypt = Bcrypt(app)





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
    cur.execute(query, (cat_id, ))
    words_list = cur.fetchall()


    return render_template('dictionary.html', logged_in=logged_in_checker(), categories=get_all_category(), words=words_list)


@app.route('/login', methods=['POST', 'GET'])
def render_login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()
        query = "SELECT id, first_name, password, user_type FROM users WHERE email = ?"
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()
        print(user_data)

        if user_data is None:
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


app.run(host='0.0.0.0', debug=True)
