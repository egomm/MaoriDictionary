from flask import Flask, render_template, request, redirect, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt

import os

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

DATABASE = os.path.join(PROJECT_ROOT, "maoridictionary.db")

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "GiJHEtydYtpCIVSeCchIE43rScpzqnKU"


def open_database(db_name):
    """
    Create a connection with the database
    parameter: name of the database file
    returns: a connection to the file
    """
    try:
        connection = sqlite3.connect(db_name)
        return connection
    except Error as e:
        print(e)
    return None


def create_connection(db_file):
    """
    Create a connection with the database
    parameter: name of the database file
    returns: a connection of the file
    """
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


@app.route('/', methods=['POST', 'GET'])
def home():  # put application's code here
    print(request.form.get("login-form") is not None)
    print(request.form.get("signup-form") is not None)
    if request.form.get("signup-form") is not None:
        print(request.form.get("signup-username"))
        print(request.form.get("teacherButton"))
    return render_template('home.html', text="hi")


@app.route('/categories', methods=['POST', 'GET'])
def categories():
    return render_template('categories.html')


# make the request go under a custom thing
@app.route('/contact', methods=['POST', 'GET'])
def contact():
    return render_template('contact.html')


@app.route('/translate', methods=['POST', 'GET'])
def translate():
    return render_template('translate.html', text=request.form.get("text"))


if __name__ == '__main__':
    app.run()
    #app.run(host='0.0.0.0', debug=True) 
    # runs website locally
