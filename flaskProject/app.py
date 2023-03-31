import sqlite3
from sqlite3 import Error
from flask import Flask, render_template, request, redirect
from flask_bcrypt import Bcrypt

DATABASE = 'C:/Users/brian/Documents/DTS-Database-Assignment/maoridictionary.db'
app = Flask(__name__)
bcrypt = Bcrypt(app)


@app.route('/')
def render_homepage():
    return render_template('home.html')


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


@app.route('/dictionary')
def render_words():
    return render_template('dictionary.html')


@app.route('/login', methods=['POST', 'GET'])
def render_login():
    return render_template('login.html')


@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
    if request.method == 'POST':
        print(request.form)
        first_name = request.form.get('first_name').title().strip()
        last_name = request.form.get('last_name').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if password != password2:
            return redirect("\signup?error=Passwords+do+not+match")

        if len(password) < 8:
            return redirect("\signup?error=Password+must+be+at+least+8+characters")

        hashed_password = bcrypt.generate_password_hash(password)
        con = create_connection(DATABASE)
        query = "INSERT INTO user(first_name, last_name, email, password) VALUES (?, ?, ?, ?)"
        cur = con.cursor()

        try:
            cur.execute(query, (first_name, last_name, email, hashed_password))
        except sqlite3.IntegrityError:
            con.close()
            return redirect('\signup?error=Email+is+already+used')

        con.commit()
        con.close()

        return redirect("\login")

    return render_template('signup.html')


app.run(host='0.0.0.0', debug=True)
