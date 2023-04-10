from flask import Flask, render_template, request, redirect

app = Flask(__name__)


@app.route('/')
def home():  # put application's code here
    return render_template('newhome.html')


# make the request go under a custom thing
@app.route('/contact', methods=['POST', 'GET'])
def contact():
    print(request.form.get("text"))
    print(len(request.form.get("text")))
    return render_template('contact.html')


@app.route('/translate/<word>', methods=['POST', 'GET'])
def translate():
     # need to validate the search
     return render_template('translate.html')


if __name__ == '__main__':
    app.run()
