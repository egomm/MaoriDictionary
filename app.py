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
    con = open_database(DATABASE)
    query = "INSERT INTO users (username, email, password, administrator, firstName, lastName) " \
            "VALUES (?, ?, ?, ?, ?, ?)"
    cur = con.cursor()
    cur.execute(query, (usernamevalue, emailvalue, passwordvalue, teacher, firstnamevalue, lastnamevalue))
    con.commit()
    con.close()


@app.context_processor
def inject_data():  # Used for getting the data when there
    # is a ajax post
    if request.method == "POST":
        json_data = request.get_json()
        if json_data["type"] == "signup":  # check where the data came from, proceed accordingly
            signup(json_data["role"], json_data["firstname"], json_data["lastname"],
                   json_data["username"], json_data["email"], bcrypt.generate_password_hash(json_data["password"]))
    return {}


def checkhasusername(username):
    con = create_connection(DATABASE)
    cur = con.cursor()
    query = "SELECT username FROM users"
    cur.execute(query)
    usernames = [username[0] for username in cur.fetchall()]
    con.close()
    return [x.lower() for x in usernames].count(username.lower()) > 0


def checkhasemail(email):
    con = create_connection(DATABASE)
    cur = con.cursor()
    query = "SELECT email FROM users"
    cur.execute(query)
    emails = [email[0] for email in cur.fetchall()]
    con.close()
    return [x.lower() for x in emails].count(email.lower()) > 0


@app.route('/getlogininformation', methods=['POST'])
def login_data_manager():
    data = request.get_json()
    emailusername = data['emailusername']
    password = data['password']
    matches = False
    hasemail = checkhasemail(emailusername)
    hasusername = checkhasusername(emailusername)
    if hasemail or hasusername:
        con = open_database(DATABASE)
        cur = con.cursor()
        if hasemail:
            query = "SELECT user_id FROM users WHERE email = ?"
            cur.execute(query, (emailusername,))
        elif hasusername:
            query = "SELECT user_id FROM users WHERE username = ?"
            cur.execute(query, (emailusername,))
        emailusernameId = cur.fetchone()[0]
        query = "SELECT password FROM users WHERE user_id = ?"
        cur.execute(query, (emailusernameId,))
        hashedpassword = cur.fetchone()[0]
        if bcrypt.check_password_hash(hashedpassword, password):
            matches = True
    return jsonify({'validLogin': matches})


@app.route('/getsignupinformation', methods=['POST'])
def signup_data_manager():  # function for managing the data which comes through from the modal requests
    data = request.get_json()  # get the data from the html
    email = data['email']
    username = data['username']
    # return the validated data back to the html
    return jsonify({'usernameUsed': checkhasusername(username), 'emailUsed': checkhasemail(email)})


@app.route('/', methods=['POST', 'GET'])
def home():  # put application's code here
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
