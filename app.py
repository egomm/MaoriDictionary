from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


@app.route('/')
def home():  # put application's code here
    return render_template('newhome.html')


# make the request go under a custom thing
@app.route('/contact', methods=['POST', 'GET'])
def contact():
    return render_template('contact.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    return render_template("login.html")


@app.route('/translate', methods=['POST', 'GET'])
def translate():
    return render_template('translate.html', text=request.form.get("text"))


if __name__ == '__main__':
    app.run()
