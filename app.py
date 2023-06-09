from flask import Flask, render_template, request, redirect, session, jsonify
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

# Get the path of the database
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
    :return: a connection of the file
    """
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


def is_logged_in():
    """
    Checks if the user is logged in from the session (getting the id key)
    :return: if the user is logged in
    """
    return session.get("id") is not None


def is_administrator():
    """
    Checks if the user is an administrator (checks if the user is a teacher)
    :return: if the user is an administrator
    """
    is_admin = False
    if is_logged_in():
        # Create a connection to the database
        con = create_connection(DATABASE)
        # Creating a cursor object for executing SQL statements and retrieving data from the database
        cur = con.cursor()
        # SQL query to retrieve the administrator status of a user based on their user_id
        query = "SELECT administrator FROM users WHERE user_id = ?"
        # Executing the SQL query with the user's session ID as a parameter
        cur.execute(query, (session.get("id"),))
        # Fetch and assign the administrator status value from the query result
        is_admin = cur.fetchone()[0]
        # Close the connection
        con.close()
    return is_admin


def remove_extra_whitespace(string):
    """
    This function selects all whitespace between different words and makes sure there is only one space
    This is done by using a regular expression by substituting this with only one space
    :param string: The word to remove the extra whitespace from
    :return: The word which the extra white space has been removed
    """
    return re.sub(' +', ' ', string)


def sort_words(words, selected_language, sorting_method):
    """
    Sort words using a lambda function that takes an element of the tuple as its parameter
    :param words:
    words[0] = maori_word
    words[1] = english_word
    words[2] = definition
    words[3] = level
    :param selected_language: The selected language for sorting (English-Māori or Māori-English)
    :param sorting_method: The sorting method (A-Z or LEVEL)
    :return: The sorted list
    """
    word_list = []
    # Sort by level, then sort alphabetically if there are multiple instances of the same level
    if sorting_method == "LEVEL":
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


@app.route('/login', methods=['POST'])
def login():
    """
    This function logs in the user
    :return: {} (effectively nothing as this route only accepts post methods)
    """
    json_data = request.get_json()
    session['id'] = json_data["userid"]
    return {}


@app.route('/resetpassword', methods=['POST'])
def reset_password():
    """
    This function resets the user's password
    :return: {} (effectively nothing as this route only accepts post methods)
    """
    json_data = request.get_json()
    con = create_connection(DATABASE)
    cur = con.cursor()
    # Update the users database with the new bcrypt password
    query = "UPDATE users SET password=? WHERE username=?"
    cur.execute(query, (bcrypt.generate_password_hash(json_data["newpassword"]), json_data["username"].lower()))
    con.commit()
    con.close()
    return {}


@app.route('/signup', methods=['POST'])
def sign_up():
    """
    This function signs up the user
    :return: {} (effectively nothing as this route only accepts post methods)
    """
    json_data = request.get_json()
    con = open_database(DATABASE)
    query = "INSERT INTO users (first_name, last_name, username, email, password, administrator) " \
            "VALUES (?, ?, ?, ?, ?, ?)"  # Insert sign up information into the users database
    cur = con.cursor()
    cur.execute(query,
                (json_data["firstname"].lower(), json_data["lastname"].lower(), json_data["username"].lower(),
                 json_data["email"].lower(), bcrypt.generate_password_hash(json_data["password"]),
                 json_data["role"]))
    con.commit()
    con.close()
    return {}


@app.route('/getlogininformation', methods=['POST'])
def login_data_manager():
    """
    This function manages the login data in order to validate it
    This route is called by the base.html login modal when the user is logging in
    This route is only accessible by a post method (the user cannot access this route)
    :return: if the login is valid, if the email exists in the database,
    if the user_id exists in the database, and if the user is an administrator
    """
    data = request.get_json()
    emailusername = data['emailusername'].lower()
    password = data['password']
    administrator = False
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
        if bcrypt.check_password_hash(hashedpassword, password):
            query = "SELECT administrator FROM users WHERE user_id = ?"
            cur.execute(query, (emailusernameid,))
            administrator = cur.fetchone()[0]
            matches = True
        con.close()
    # Use javascript conventions for the return (camelCase)
    return jsonify({'validLogin': matches, 'email': hasemail, 'userId': emailusernameid,
                    'administrator': administrator})


@app.route('/getchangepasswordinformation', methods=['POST'])
def change_password_data_manager():
    """
    This function manages the change password information
    This route is called by the base.html when the user is changing their password
    This route is only accessible by a post method (the user cannot access this route)
    :return: If the information provided is valid (if the user information exists in the database)
    """
    data = request.get_json()
    firstname = data['firstname'].lower()
    lastname = data['lastname'].lower()
    username = data['username'].lower()
    email = data['email'].lower()
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
    return jsonify({"validInformation": matches})


@app.route('/getsignupinformation', methods=['POST'])
def signup_data_manager():
    """
    Function for validating the signup data by checking if the username or email exists in the database
    This route is only accessible by a post method (the user cannot access this route)
    :return: If the username exists in the database, if the email exists in the database
    """
    data = request.get_json()  # Get the json data from the html
    email = data['email'].lower()
    username = data['username'].lower()
    # Return the validated data back to the html
    return jsonify({'usernameUsed': checkhasusername(username), 'emailUsed': checkhasemail(email)})


@app.route('/getwordinformation', methods=['POST'])
def word_manager():
    """
    Function for validating the word information to check if the english word or maori word exits in the database
    This route is only accessible by a post method (the user cannot access this route)
    :return: If the english word exists in the database, if the maori word exists in the database
    """
    data = request.get_json()
    maori_word = data['maori'].lower()
    english_word = data['english'].lower()
    con = open_database(DATABASE)
    cur = con.cursor()
    query = "SELECT maori_word, english_word FROM words"  # Used for validation
    cur.execute(query)
    words = cur.fetchall()
    maori_words = [x[0].lower() for x in words]
    has_maori_word = maori_word in maori_words
    english_words = [x[1].lower() for x in words]
    has_english_word = english_word in english_words
    return jsonify({'hasEnglishWord': has_english_word, 'hasMaoriWord': has_maori_word})


@app.route('/getwordfromid', methods=['POST'])
def word_from_id():
    """
    Function for getting the word information from the word id
    This route is only accessible by a post method (the user cannot access this route)
    :return: the english word, the maori word, the category name, the word definition,
    the word level, and the word image
    """
    data = request.get_json()
    word_id = data["id"]
    con = open_database(DATABASE)
    cur = con.cursor()
    query = "SELECT maori_word, english_word, cat_id, definition, level, image FROM words WHERE word_id = ?"
    cur.execute(query, (word_id,))
    word_information = cur.fetchall()[0]
    maori_word = word_information[0]
    english_word = word_information[1]
    category_id = word_information[2]
    definition = word_information[3]
    level = word_information[4]
    image = word_information[5]
    query = "SELECT category_name FROM categories WHERE category_id = ?"
    cur.execute(query, (category_id,))
    category = cur.fetchall()
    return jsonify({'englishWord': english_word, 'maoriWord': maori_word, 'category': category,
                    'wordDefinition': definition, 'wordLevel': level, 'wordImage': image})


@app.route('/getwordidfromword', methods=['POST'])
def word_id_from_word():
    """
    Function for getting the word id from the english and maori word
    This route is only accessible by a post method (the user cannot access this route)
    :return: The word id from the provided information
    """
    data = request.get_json()
    maori_word = data["maori"]
    english_word = data["english"]
    con = open_database(DATABASE)
    cur = con.cursor()
    query = "SELECT word_id FROM words WHERE maori_word = ? and english_word = ?"
    cur.execute(query, (maori_word, english_word))
    word_id = cur.fetchone()[0]
    con.close()
    return {'wordId': word_id}


@app.route('/hascategory', methods=['POST'])
def has_category():
    """
    Function for checking if a category exists given a category name
    This route is only accessible by a post method (the user cannot access this route)
    :return: If the category name has already been used
    """
    data = request.get_json()
    category_name = data["category"].lower()
    con = create_connection(DATABASE)
    cur = con.cursor()
    query = "SELECT category_name FROM categories"
    cur.execute(query)
    category_names = [x[0].lower() for x in cur.fetchall()]
    contains_category = category_name.lower() in category_names
    con.close()
    return {'hasCategory': contains_category}


@app.route('/addword', methods=['POST'])
def add_word():
    """
    Function for adding a word given information about the word
    :return: {} (effectively nothing as this route only accepts post methods)
    """
    english_word = remove_extra_whitespace(request.form["englishWord"].lower())
    maori_word = remove_extra_whitespace(request.form["maoriWord"].lower())
    category = request.form["category"]
    definition = request.form["definition"]
    level = request.form["level"]
    image_name_refined = None
    if "image" in request.files:
        image = request.files["image"]
        image_name = image.filename
        extension = "." + image_name.rsplit('.', 1)[-1].lower()  # Get the extension (png, jpeg, etc)
        image_name_refined = english_word.strip() + extension
        similar_images = []
        directory = os.path.join(app.root_path, 'static', 'images')
        for filename in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, filename)):
                file_name = os.path.splitext(filename)
                if file_name[1] == extension and english_word.strip() in file_name[0]:
                    similar_images.append(file_name)
        if len(similar_images) > 0:
            image_name_refined = english_word.strip() + str(len(similar_images)) + extension
        image_path = os.path.join(app.root_path, 'static', 'images', image_name_refined)
        image_path = image_path.replace('\\', '/')  # Replace backslashes with forward slashes
        image.save(image_path)
    if is_administrator():
        con = open_database(DATABASE)
        query = "INSERT INTO words (maori_word, english_word, cat_id, definition, level, image, added_by, time_added) " \
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        cur = con.cursor()
        cur.execute(query, (maori_word, english_word, category, definition, level, image_name_refined,
                            session.get("id"), int(time.time() * 1000)))
        con.commit()
        con.close()
    return {}


@app.route('/deleteword', methods=['POST'])
def delete_word():
    """
    Function for deleting a word given the word id
    :return: {} (effectively nothing as this route only accepts post methods)
    """
    json_data = request.get_json()
    word_id = json_data["wordId"]
    con = create_connection(DATABASE)
    cur = con.cursor()
    query = "DELETE FROM words WHERE word_id = ?"
    cur.execute(query, (word_id,))
    con.commit()
    con.close()
    return {}


@app.route('/deletewordfromdata', methods=['POST'])
def delete_word_from_data():
    """
    This function is an alternative method for deleting a word through using the maori or english word
    :return: {} (effectively nothing as this route only accepts post methods)
    """
    json_data = request.get_json()
    current_word = json_data["currentWord"]
    translated_word = json_data["translatedWord"]
    con = create_connection(DATABASE)
    cur = con.cursor()
    # The query alternates between current_word and translated word as there can be English-Maori or Maori-English
    query = "DELETE FROM words WHERE maori_word = ? OR english_word = ? OR maori_word = ? OR english_word = ?"
    cur.execute(query, (current_word, translated_word, translated_word, current_word))
    con.commit()
    con.close()
    return {}


@app.route('/getcategoryid', methods=['POST'])
def get_category_id():
    """
    This function gets the category id given a provided category name
    This route is only accessible by a post method (the user cannot access this route)
    :return: The category id from the provided category name
    """
    json_data = request.get_json()
    category_name = json_data["categoryName"]
    con = create_connection(DATABASE)
    cur = con.cursor()
    query = "SELECT category_id FROM categories WHERE category_name = ?"
    cur.execute(query, (category_name,))
    category_id = cur.fetchone()[0]
    con.close()
    return {"categoryId": category_id}


@app.route('/addcategory', methods=['POST'])
def add_category():
    """
    Function for adding a category from a given category name
    :return: {} (effectively nothing as this route only accepts post methods)
    """
    json_data = request.get_json()
    category_name = remove_extra_whitespace(json_data["categoryName"])
    con = create_connection(DATABASE)
    cur = con.cursor()
    query = "INSERT INTO categories (category_name) VALUES (?)"
    cur.execute(query, (category_name,))
    con.commit()
    con.close()
    return {}


@app.route('/deletecategory', methods=['POST'])
def delete_category():
    """
    Function for deleting a category given a category name
    :return: {} (effectively nothing as this route only accepts post methods)
    """
    json_data = request.get_json()
    category_name = json_data["categoryName"]
    con = create_connection(DATABASE)
    # Enable foreign keys
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()
    query = "DELETE FROM categories WHERE category_name = ?"
    cur.execute(query, (category_name,))
    con.commit()
    con.close()
    return {}


@app.route('/logout')
def logout():
    """
    Function and route for the user to log out
    Iterate over all the current session keys and remove each key if the user is logged in
    :return: a redirect to the home page
    """
    if is_logged_in():
        [session.pop(key) for key in list(session.keys())]
    return redirect('/')


@app.route('/', methods=['POST', 'GET'])
def home():
    """
    This is the route for the home page, the home page manages the search feature on the home page
    If the request method is post :return: a redirect to the category search
    If the request method is get :return: the home page with information about if the user is logged in,
    or if the user is an administrator
    """
    if request.method == "POST":
        search_input = request.form.get("text")
        return redirect(f"/categories/all-categories/search/{search_input}/1")
    else:
        return render_template('home.html', logged_in=json.dumps(is_logged_in()), logged_in_clean=is_logged_in(),
                               administrator=is_administrator(), admin_clean=json.dumps(is_administrator()))


@app.route('/categories/<category>/<page>', defaults={'search': None}, methods=['POST', 'GET'])
@app.route('/categories/<category>/search/<search>/<page>')
def categories(category, page, search):
    """
    Function for accessing the category page
    :param category: the category name of the active category
    :param page: the current page number
    :param search: the current search (this can be None)
    If the request method is get :return: information about the current category to display in categories.html,
    this information includes: if the user is logged in, if the user is administrator, the raw category list,
    the sanitised category list, the current category id, the current category name, the sorting method,
    the selected language, the amount of words to display per page, the word list, the total page count,
    the total number of words, the current page (as an index), the display page, the minimum word index on the page,
    the maximum word index on the page, all the levels, if all levels are selected, the current select levels,
    and the current search
    If the request method is post :return: a redirect to the search which had just been inputted
    """
    using_search = "category-search-bar" in request.form
    if not using_search:
        con = open_database(DATABASE)
        cur = con.cursor()
        query = "SELECT level from levels"
        cur.execute(query)
        levels = [level[0] for level in cur.fetchall()]
        con.close()
        if session.get("selected-values") is None:
            session["selected-values"] = "all"
        all_levels_selected = "all" in session["selected-values"]
        if all_levels_selected:
            selected_levels = levels
        else:
            selected_levels = [int(x) for x in session["selected-values"]]
        if session.get("selected-language") is None:
            session["selected-language"] = "English-Māori"  # This is the 'origin language'
        if session.get("selected-sorting-method") is None:
            session["selected-sorting-method"] = "A-Z"  # A-Z
        if session.get("selected-words-per-page") is None:
            session["selected-words-per-page"] = "12"  # store as a string as this can be All
        if request.method == "POST":
            json_data = request.get_json()
            if "type" in json_data:  # This provides as a failsafe
                if json_data["type"] == "category-language":
                    session["selected-language"] = json_data["language"]
                if json_data["type"] == "sorting-methods":
                    session["selected-sorting-method"] = json_data["selectedvalue"]
                if json_data["type"] == "words-per-page":
                    session["selected-words-per-page"] = json_data["selectedvalue"]
                if json_data["type"] == "level-filter":
                    session["selected-values"] = json_data["checkboxes"]
        con = open_database(DATABASE)
        cur = con.cursor()
        query = "SELECT category_name FROM categories"
        cur.execute(query)
        category_list = sorted([x[0] for x in cur.fetchall()])
        current_category = 0
        # In order to avoid an internal server error (500) with an extra /, replace the /'s with +'s
        sanitised_category_list = [x.replace("/", "+").lower() for x in category_list]
        # replace the whitespace with -
        sanitised_category_list = [re.sub(r'\s+', '-', x) for x in sanitised_category_list]
        category_sanitised = category.title().replace("-", " ").replace("+", "/")
        # Iterate over each word of category sanitised
        category_sanitised_array = category_sanitised.split(" ")
        new_category_sanitised = ""
        for string in category_sanitised_array:
            if len(string) > 1:
                # Convert everything to lowercase except for the first character of the string
                string = string[0] + string[1:len(string)].lower()
            new_category_sanitised += string + " "
        category_sanitised = new_category_sanitised.strip()
        if category_sanitised != "All Categories":
            query = "SELECT category_id FROM categories WHERE category_name = ?"
            cur.execute(query, (category_sanitised,))
            current_category = cur.fetchall()[0][0]
            con.close()
        selected_language = session["selected-language"]
        sorting_method = session["selected-sorting-method"]
        words_per_page = session["selected-words-per-page"]
        # Need to render the words dependent on all of these constraints
        question_marks = "{}".format(','.join(['?'] * len(selected_levels)))
        if current_category > 0:
            con = open_database(DATABASE)
            cur = con.cursor()
            query = f"SELECT maori_word, english_word, definition, level, image, word_id FROM words WHERE cat_id = ?" \
                    f" and level IN ({question_marks})"
            cur.execute(query, (current_category, *tuple(selected_levels)))
            word_list = sort_words(cur.fetchall(), selected_language, sorting_method)
            con.close()
        else:  # current category is 0 (or error has occurred so just display all)
            con = open_database(DATABASE)
            cur = con.cursor()
            query = f"SELECT maori_word, english_word, definition, level, image, word_id FROM words WHERE level" \
                    f" IN ({question_marks})"
            cur.execute(query, (*tuple(selected_levels),))
            word_list = sort_words(cur.fetchall(), selected_language, sorting_method)
            con.close()
        # [0] is maori_word, [1] is english_word, [2] is definition, [3] is level, [4] is image, [5] is word id
        # Only reset the current search when the category has changed
        current_search = ""
        if search is not None:
            current_search = search
            matching_words = []
            for word in word_list:
                if word[1].lower().startswith(search.lower()):
                    matching_words.append(word)
                elif word[0].lower().startswith(search.lower()):
                    matching_words.append(word)
            word_list = matching_words
        if current_category > 0:
            category_name = category
        else:
            category_name = "all-categories"
        total_words = len(word_list)
        sorted_word_list = []
        page = int(page)
        current_page = page - 1
        category_index = 0
        for i in range(len(category_list)):
            if sanitised_category_list[i] == category.lower():
                category_index = i + 1
                break
        if words_per_page != "All":
            words_per_page = int(words_per_page)
            actual_words_per_page = words_per_page
            page_count = math.ceil(len(word_list) / words_per_page)
            if len(word_list) > 0:
                for i in range(0, len(word_list), words_per_page):
                    # Append the words to the sorted world list
                    sorted_word_list.append(list(word_list[i:i + words_per_page]))
        else:  # Display all words
            page_count = 1
            if len(word_list) > 0:
                sorted_word_list = [word_list]
                actual_words_per_page = len(sorted_word_list[page - 1])
            else:
                actual_words_per_page = 0
        if len(sorted_word_list) > 0:
            minimum_value = (current_page * actual_words_per_page) + 1
            maximum_value = min((current_page + 1) * actual_words_per_page,
                                (current_page * actual_words_per_page) + len(sorted_word_list[page - 1]))
        else:
            minimum_value = 0
            maximum_value = 0
        return render_template('categories.html', logged_in=json.dumps(is_logged_in()),
                               administrator=is_administrator(), category_list=category_list,
                               sanitised_category_list=sanitised_category_list, current_category=category_index,
                               category_name=category_name, sorting_method=sorting_method,
                               selected_language=selected_language, words_per_page=words_per_page,
                               word_list=sorted_word_list, page_count=page_count, total_words=total_words,
                               current_page=current_page, display_page=page, minimum_value=minimum_value,
                               maximum_value=maximum_value, levels=levels, all_levels_selected=all_levels_selected,
                               selected_levels=selected_levels, current_search=current_search,
                               admin_clean=json.dumps(is_administrator()), logged_in_clean=is_logged_in())
    else:
        search_input = request.form.get("category-search-bar")
        if len(search_input) > 0:
            return redirect(f'/categories/{category}/search/{search_input}/1')
        else:
            previous_search = request.form.get("previous-search")
            if len(previous_search) > 0:  # There was a previous search
                return redirect(f'/categories/{category}/1')
            else:
                return redirect(f'/categories/{category}/{int(page) + 1}')


@app.route('/translate/<word>', defaults={'word_id': None}, methods=['POST', 'GET'])
@app.route('/translate/<word>/<word_id>', methods=['POST', 'GET'])
def translate(word, word_id):
    """
    This route is for getting information about a word based on the word and/or the word id
    :param word: The english word or the maori word
    :param word_id: The word id - this isn't a required field, so it can be None,
    although using the word id is more efficient
    If the word exists :return: information about the word: the current word, the translated word,
    the word's definition, the word's level, the word's image, the user who added the word, the time the word was added,
    the word id, if the user is logged in, and if the user is an administrator
    If the word doesn't exist :return: a return to the first page of the all categories section
    """
    con = open_database(DATABASE)
    cur = con.cursor()
    query = "SELECT english_word FROM words WHERE english_word = ?"
    cur.execute(query, (word,))
    has_word = False
    if cur.fetchone() is not None:
        has_word = True
        if word_id is not None:
            query = "SELECT maori_word, definition, level, image, added_by, time_added FROM words WHERE word_id = ?"
        else:
            query = "SELECT maori_word, definition, level, image, added_by, time_added FROM words " \
                    "WHERE english_word = ?"
    else:
        query = "SELECT maori_word FROM words WHERE maori_word = ?"
        cur.execute(query, (word,))
        if cur.fetchone() is not None:
            has_word = True
            if word_id is not None:
                query = "SELECT english_word, definition, level, image, added_by, time_added FROM words " \
                        "WHERE word_id = ?"
            else:
                query = "SELECT english_word, definition, level, image, added_by, time_added FROM words " \
                        "WHERE maori_word = ?"
    if has_word:
        if word_id is not None:
            cur.execute(query, (word_id,))
        else:
            cur.execute(query, (word,))
        word_information = cur.fetchone()
        # [0] = translated word, [1] = definition, [2] = level, [3] = image
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
                               date=data_date, logged_in=json.dumps(is_logged_in()),
                               administrator=is_administrator(), word_id=word_id,
                               admin_clean=json.dumps(is_administrator()), logged_in_clean=is_logged_in())
    else:
        return redirect("/categories/all-categories/1")


@app.route("/admin", methods=["POST", "GET"])
def admin():
    """
    This route is for accessing the admin page in order to add/delete words and add/delete categories
    If the user is an administrator :return: if the user is logged in, if the user is an administrator (failsafe),
    the category ids, the category names, the levels, the english words, and the maori words
    """
    if is_administrator():
        con = open_database(DATABASE)
        cur = con.cursor()
        query = "SELECT * FROM categories"
        cur.execute(query)
        category_information = sorted(cur.fetchall(), key=lambda x: x[1])
        category_ids = [x[0] for x in category_information]
        category_names = [x[1] for x in category_information]
        # Levels
        query = "SELECT * FROM levels"
        cur.execute(query)
        levels = [x[0] for x in cur.fetchall()]
        # English words
        query = "SELECT english_word, word_id FROM words"
        cur.execute(query)
        english_words = sorted(cur.fetchall(), key=lambda x: x[0])
        # Maori words
        query = "SELECT maori_word, word_id FROM words"
        cur.execute(query)
        maori_words = sorted(cur.fetchall(), key=lambda x: x[0])
        con.close()
        return render_template("admin.html", logged_in=json.dumps(is_logged_in()),
                               administrator=is_administrator(), category_ids=category_ids,
                               category_names=category_names, levels=levels, english_words=english_words,
                               maori_words=maori_words, admin_clean=json.dumps(is_administrator()),
                               logged_in_clean=is_logged_in())
    else:
        return redirect("/")  # Return user to the home page if they aren't admin


if __name__ == '__main__':
    app.run()  # Run the website
