import sqlite3
from sqlite3 import Error
from flask import Flask, render_template, request, redirect
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


if __name__ == '__main__':
    app.run()
