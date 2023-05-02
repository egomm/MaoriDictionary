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


def is_logged_in():  # Returns if the user is logged in based on the session id (from user_id)
    return session.get("id") is not None


# Context processor allows injection into the template as it runs before the template is rendered
@app.context_processor
def inject_data():  # Used for getting the data when there
    # is a ajax post
    if request.method == "POST":
        json_data = request.get_json()  # check where the data came from, proceed accordingly
        if json_data["type"] == "login":  # Login post
            session['id'] = json_data["userid"]  # Set the session id to the userid
        elif json_data["type"] == "signup":  # Signup post
            con = open_database(DATABASE)
            query = "INSERT INTO users (firstName, lastName, username, email, password, administrator) " \
                    "VALUES (?, ?, ?, ?, ?, ?)"  # Insert sign up information into the users database
            cur = con.cursor()
            cur.execute(query, (json_data["firstname"], json_data["lastname"], json_data["username"], json_data["email"]
                                , bcrypt.generate_password_hash(json_data["password"]), json_data["role"]))
            con.commit()
            con.close()
        elif json_data["type"] == "resetpassword":  # Reset password post
            con = create_connection(DATABASE)
            cur = con.cursor()
            query = "UPDATE users SET password=? WHERE username=?"  # Update the users database with the new bcrypt password
            cur.execute(query, (bcrypt.generate_password_hash(json_data["newpassword"]), json_data["username"]))
            con.commit()
            con.close()
    return {}  # Nothing needs to be returned as this is on the context processor


def checkhasusername(username):
    """
    Function for checking if a username exists in the users database
    :param username: username which will be checked
    :return: whether the users database contains the given username
    """
    con = create_connection(DATABASE)
    cur = con.cursor()
    query = "SELECT username FROM users"
    cur.execute(query)
    usernames = [username[0] for username in cur.fetchall()]
    con.close()
    return [x.lower() for x in usernames].count(username.lower()) > 0


def checkhasemail(email):
    """
    Function for checking if an email exists in the users database
    :param email: email which will be checked
    :return: whether the users databse contains the given email
    """
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
    emailusernameid = -1
    if hasemail or hasusername:
        con = open_database(DATABASE)
        cur = con.cursor()
        if hasemail:
            query = "SELECT user_id FROM users WHERE email = ?"
            cur.execute(query, (emailusername,))
        elif hasusername:
            query = "SELECT user_id FROM users WHERE username = ?"
            cur.execute(query, (emailusername,))
        emailusernameid = cur.fetchone()[0]
        query = "SELECT password FROM users WHERE user_id = ?"
        cur.execute(query, (emailusernameid,))
        hashedpassword = cur.fetchone()[0]
        con.close()
        if bcrypt.check_password_hash(hashedpassword, password):
            matches = True
    return jsonify({'validLogin': matches, 'email': hasemail, 'userId': emailusernameid})


@app.route('/getchangepasswordinformation', methods=['POST'])
def changepassword_data_manager():
    data = request.get_json()
    firstname = data['firstname']
    lastname = data['lastname']
    username = data['username']
    email = data['email']
    matches = False
    hasusername = checkhasusername(username)
    if hasusername:
        con = open_database(DATABASE)
        cur = con.cursor()
        query = "SELECT * FROM users WHERE username = ?"
        cur.execute(query, (username,))
        user_information = cur.fetchall()[0]
        con.close()
        if firstname == user_information[1] and lastname == user_information[2] and email == user_information[4]:
            matches = True
    # Base the check off the inserted username, all the data needs to be validated to allow password reset
    return jsonify({"validInformation": matches})


@app.route('/getsignupinformation', methods=['POST'])
def signup_data_manager():  # function for managing the data which comes through from the modal requests
    data = request.get_json()  # get the data from the html
    email = data['email']
    username = data['username']
    # return the validated data back to the html
    return jsonify({'usernameUsed': checkhasusername(username), 'emailUsed': checkhasemail(email)})


@app.route('/logout')
def logout():
    [session.pop(key) for key in list(session.keys())]
    return redirect('/')


@app.route('/', methods=['POST', 'GET'])
def home():  # put application's code here
    return render_template('home.html', logged_in=json.dumps(is_logged_in()))


@app.route('/categories', methods=['POST', 'GET'])
def categories():
    con = open_database(DATABASE)
    cur = con.cursor()
    query = "SELECT category_name FROM categories"
    cur.execute(query)
    category_list = [x[0] for x in cur.fetchall()]
    con.close()
    return render_template('categories.html', logged_in=json.dumps(is_logged_in()), category_list=category_list)


# make the request go under a custom thing
@app.route('/contact', methods=['POST', 'GET'])
def contact():
    return render_template('contact.html', logged_in=json.dumps(is_logged_in()))


@app.route('/translate', methods=['POST', 'GET'])
def translate():
    return render_template('translate.html', text=request.form.get("text"), logged_in=json.dumps(is_logged_in()))


if __name__ == '__main__':
    app.run()
    # app.run(host='0.0.0.0', debug=True)
    # runs website locally
