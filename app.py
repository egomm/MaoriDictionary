from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt

import os
import json

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


def signup(teacher, firstnamevalue, lastnamevalue, usernamevalue, emailvalue, passwordvalue):
    administrator = teacher == "Teacher"
    con = open_database(DATABASE)
    query = "INSERT INTO users (username, email, password, administrator, firstName, lastName) VALUES (?, ?, ?, ?, ?, ?)"
    cur = con.cursor()
    cur.execute(query, (usernamevalue, emailvalue, passwordvalue, administrator, firstnamevalue, lastnamevalue))
    con.commit()
    con.close()
    print("{}, {}, {}, {}, {}, {}".format(teacher, firstnamevalue, lastnamevalue, usernamevalue, emailvalue, passwordvalue))


@app.context_processor
def inject_data():
    print("SENT REQUEST")
    if request.method == "POST":
        json_data = request.get_json()
        if json_data["type"] == "signup":
            print("{} {} {} {} {} {}".format(json_data["role"], json_data["firstname"], json_data["lastname"], json_data["username"], json_data["email"], json_data["password"]))
            signup(json_data["role"], json_data["firstname"], json_data["lastname"],
                   json_data["username"], json_data["email"], bcrypt.generate_password_hash(json_data["password"]))
            print("WHY")
        else:
            print("not sign up")
    return {}


@app.route('/your-flask-route', methods=['POST'])
def your_function():
    data = request.get_json()
    email = data['email']
    username = data['username']
    con = create_connection(DATABASE)
    cur = con.cursor()
    query = "SELECT username FROM users"
    cur.execute(query)
    usernames = [username[0] for username in cur.fetchall()]
    hasusername = False
    for eachUsername in usernames:
        if eachUsername.lower() == username.lower():
            hasusername = True
            break
    query = "SELECT email FROM users"
    cur.execute(query)
    emails = [email[0] for email in cur.fetchall()]
    hasemail = False
    for eachEmail in emails:
        if eachEmail.lower() == email.lower():
            hasemail = True
            break
    return jsonify({'usernameUsed': hasusername, 'emailUsed': hasemail})


@app.route('/', methods=['POST', 'GET'])
def home():  # put application's code here
    # if request.method == "POST":
    #     return redirect(url_for('home'))
    return render_template('home.html')


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
    # app.run(host='0.0.0.0', debug=True)
    # runs website locally
