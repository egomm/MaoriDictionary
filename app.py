from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/')
def home():  # put application's code here
    return render_template('newhome.html')


@app.route('/contact', methods=['POST', 'GET'])
def contact():
    print(request.form.get("text"))
    return render_template('contact.html')


if __name__ == '__main__':
    app.run()
