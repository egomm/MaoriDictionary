from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt

import os
import json
import re
import math
import datetime
import time

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
    print("LOGGED IN", session.get("id") is not None)
    return session.get("id") is not None


def sort_words(words, selected_language, sorting_method):
    """
    Sort words using a lambda function that takes an element of the tuple as its parameter
    :param words:
    words[0] = maoriword
    words[1] = englishword
    words[2] = definition
    words[3] = level
    :param selected_language: The selected language for sorting (English-Māori or Māori-English)
    :param sorting_method: The sorting method (A-Z or LEVEL)
    :return: The sorted list
    """
    word_list = []
    if sorting_method == "LEVEL":  # sort by level then alphabetically if there are multiple instances of the same level
        if selected_language == "English-Māori":  # LEVEL with english-maori
            word_list = sorted(words, key=lambda x: (x[3], x[1]))
        elif selected_language == "Māori-English":  # LEVEL with maori-english
            word_list = sorted(words, key=lambda x: (x[3], x[0]))
    elif sorting_method == "A-Z":  # sort by A-Z
        if selected_language == "English-Māori":  # A-Z with english-maori
            word_list = sorted(words, key=lambda x: x[1])
        elif selected_language == "Māori-English":  # A-Z with maori-english
            word_list = sorted(words, key=lambda x: x[0])
    return word_list


# Context processor allows injection into the template as it runs before the template is rendered
@app.context_processor
def inject_data():  # Used for getting the data when there is an ajax post
    print("hi?")
    print(request.method)
    if request.method == "POST":
        json_data = request.get_json()  # check where the data came from, proceed accordingly
        if "type" in json_data:
            if json_data["type"] == "login":  # Login post
                session['id'] = json_data["userid"]  # Set the session id to the userid
            elif json_data["type"] == "signup":  # Signup post
                print("SIGN UP")
                con = open_database(DATABASE)
                query = "INSERT INTO users (firstName, lastName, username, email, password, administrator) " \
                        "VALUES (?, ?, ?, ?, ?, ?)"  # Insert sign up information into the users database
                cur = con.cursor()
                cur.execute(query,
                            (json_data["firstname"], json_data["lastname"], json_data["username"], json_data["email"],
                             bcrypt.generate_password_hash(json_data["password"]), json_data["role"]))
                con.commit()
                con.close()
            elif json_data["type"] == "resetpassword":  # Reset password post
                con = create_connection(DATABASE)
                cur = con.cursor()
                # Update the users database with the new bcrypt password
                query = "UPDATE users SET password=? WHERE username=?"
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


@app.route('/categories/<category>/<page>', methods=['POST', 'GET'])
def categories(category, page):
    # VALIDATE IT IF THE USER PUT IN A NON EXISTENT PAGE/CATEGORY
    print(request.method)
    con = open_database(DATABASE)
    cur = con.cursor()
    query = "SELECT level from levels"
    cur.execute(query)
    levels = [level[0] for level in cur.fetchall()]
    con.close()
    print("start")
    print(levels)
    if session.get("selected-values") is None:
        session["selected-values"] = levels
    all_levels_selected = "all" in session["selected-values"]
    if all_levels_selected:
        selected_levels = levels
    else:
        selected_levels = [int(x) for x in session["selected-values"]]
    print("SELECTED")
    print(selected_levels)
    print("end")
    if session.get("selected-language") is None:
        session["selected-language"] = "English-Māori"  # This is the 'origin language'
    if session.get("selected-sorting-method") is None:
        session["selected-sorting-method"] = "A-Z"  # A-Z
    if session.get("selected-words-per-page") is None:
        session["selected-words-per-page"] = "12"  # store as a string as this can be All
    if request.method == "POST":
        json_data = request.get_json()
        if "type" in json_data:  # failsafe
            if json_data["type"] == "category-language":
                session["selected-language"] = json_data["language"]
            if json_data["type"] == "sorting-methods":
                session["selected-sorting-method"] = json_data["selectedvalue"]
            if json_data["type"] == "words-per-page":
                session["selected-words-per-page"] = json_data["selectedvalue"]
            if json_data["type"] == "level-filter":
                session["selected-values"] = json_data["checkboxes"]
            print(session["selected-values"])
            print("abc")
    con = open_database(DATABASE)
    cur = con.cursor()
    query = "SELECT category_name FROM categories"
    cur.execute(query)
    category_list = [x[0] for x in cur.fetchall()]
    con.close()
    current_category = 0
    print(category)
    sanitised_category_list = [x.replace("/", "").lower() for x in category_list]
    sanitised_category_list = [re.sub(r'\s+', '-', x) for x in sanitised_category_list]
    for i in range(len(category_list)):
        if sanitised_category_list[i] == category:
            current_category = i + 1
            break
    print(current_category)
    selected_language = session["selected-language"]
    print(selected_language)
    sorting_method = session["selected-sorting-method"]
    print(sorting_method)
    words_per_page = session["selected-words-per-page"]
    print(words_per_page)
    # Need to render the words dependent on all of these constraints
    question_marks = "{}".format(','.join(['?'] * len(selected_levels)))
    if current_category > 0:
        con = open_database(DATABASE)
        cur = con.cursor()
        query = f"SELECT maoriword, englishword, definition, level, image FROM words WHERE cat_id = ? and" \
                f" level IN ({question_marks})"
        cur.execute(query, (current_category, *tuple(selected_levels)))
        word_list = sort_words(cur.fetchall(), selected_language, sorting_method)
        con.close()
    else:  # current category is 0 (or error has occurred so just display all)
        con = open_database(DATABASE)
        cur = con.cursor()
        query = f"SELECT maoriword, englishword, definition, level, image FROM words WHERE level" \
                f" IN ({question_marks})"
        cur.execute(query, (*tuple(selected_levels),))
        word_list = sort_words(cur.fetchall(), selected_language, sorting_method)
        con.close()
    # [0] is maoriword, [1] is english word, [2] is definition, [3] is level, [4] is image
    # NEED TO MAKE SURE THAT THE WORD ID WORKS WHEN THE CATEGORY ISN'T all-categories
    if current_category > 0:
        category_name = sanitised_category_list[current_category - 1]
    else:
        category_name = "all-categories"
    print(word_list)
    total_words = len(word_list)
    sorted_word_list = []
    page = int(page)
    current_page = page - 1
    if words_per_page != "All":
        words_per_page = int(words_per_page)
        actual_words_per_page = words_per_page
        page_count = math.ceil(len(word_list) / words_per_page)
        for i in range(0, len(word_list), words_per_page):
            sorted_word_list.append(list(word_list[i:i + words_per_page]))
    else:  # Display all words
        page_count = 1
        sorted_word_list = [word_list]
        actual_words_per_page = len(sorted_word_list[current_page])

    print(all_levels_selected)
    print(selected_levels)
    print(levels)
    if len(sorted_word_list) > 0:
        minimum_value = (current_page * actual_words_per_page) + 1
        maximum_value = min((current_page + 1) * actual_words_per_page,
                            (current_page * actual_words_per_page) + len(sorted_word_list[current_page]))
    else:
        minimum_value = 0
        maximum_value = 0
    return render_template('categories.html', logged_in=json.dumps(is_logged_in()), category_list=category_list,
                           sanitised_category_list=sanitised_category_list, current_category=current_category,
                           category_name=category_name, sorting_method=sorting_method,
                           selected_language=selected_language, words_per_page=words_per_page,
                           word_list=sorted_word_list, page_count=page_count, total_words=total_words,
                           current_page=current_page, display_page=page, minimum_value=minimum_value,
                           maximum_value=maximum_value, levels=levels, all_levels_selected=all_levels_selected,
                           selected_levels=selected_levels)


# make the request go under a custom thing
@app.route('/contact', methods=['POST', 'GET'])
def contact():
    if request.method == 'POST':
        # name = request.form.get('name')
        # email = request.form.get('email')
        # message = request.form.get('message')
        # Do something with the form data (e.g., store it in a database)
        return redirect(url_for('contact'))
    else:
        return render_template('contact.html', logged_in=json.dumps(is_logged_in()))


@app.route('/translate/<word>', methods=['POST', 'GET'])
def translate(word):  # Using the word and not the word id as its more readable to the user
    translated_word = "test"
    print(session["selected-language"])
    # if English-Māori make sure that the english word is first, then the māori word is second and vice versa
    con = open_database(DATABASE)
    cur = con.cursor()
    query = "SELECT englishword FROM words WHERE englishword = ?"
    cur.execute(query, (word,))
    has_word = False
    if cur.fetchone() is not None:
        print("English word")
        has_word = True
        query = "SELECT maoriword, definition, level, image, added_by, time_added FROM words WHERE englishword = ?"
    else:
        query = "SELECT maoriword FROM words WHERE maoriword = ?"
        cur.execute(query, (word,))
        if cur.fetchone() is not None:
            print("Maori Word")
            has_word = True
            query = "SELECT englishword, definition, level, image, added_by, time_added FROM words WHERE maoriword = ?"
    if has_word:
        cur.execute(query, (word,))
        word_information = cur.fetchone()
        # [0] = translated word, [1] = definition, [2] = level, [3] = image
        print(word_information)
        current_word = word  # The word which the user clicked on
        translated_word = word_information[0]
        definition = word_information[1]
        level = word_information[2]
        image = word_information[3]
        added_by = word_information[4]
        query = "SELECT username FROM users WHERE user_id = ?"
        cur.execute(query, (added_by,))
        user_added = cur.fetchone()[0]  # user who added the word
        time_added = int(word_information[5] / 1000)  # time added (in seconds -> as 1s = 1000ms)
        datetime_object = datetime.datetime.fromtimestamp(time_added)
        data_date = datetime_object.strftime("%d/%m/%Y")
        data_time = datetime_object.strftime("%H:%M")
        data_time = datetime.datetime.strptime(data_time, "%H:%M").strftime("%I:%M%p").lower()
        con.close()
        return render_template('translate.html', current_word=current_word, translated_word=translated_word,
                               definition=definition, level=level, image=image, user_added=user_added, time=data_time,
                               date=data_date, logged_in=json.dumps(is_logged_in()))
    else:
        return redirect("/categories/all-categories/1")


if __name__ == '__main__':
    app.run()
    # app.run(host='0.0.0.0', debug=True)
    # runs website locally
