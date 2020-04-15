from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import os


# initialise app
# flask expects static pages to be in \templates by default
template_dir = os.path.abspath(r'..\Front End Testing')
app = Flask(__name__, template_folder=template_dir)

basedir = os.path.abspath(os.path.dirname(__file__))


# Database
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# initialise database
db = SQLAlchemy(app)

# tables in database - move each to separate file
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    admin = db.Column(db.Boolean)
    username = db.Column(db.String(10), unique=True )
    password = db.Column(db.String(10))

    def __init__(self, admin, username, password):
        self.admin = admin
        self.username = username
        self.password = password

class Question_Set(db.Model):
    qs_id = db.Column(db.Integer, primary_key=True)

class Question(db.Model):
    q_id = db.Column(db.Integer, primary_key=True)

class Answer(db.Model):
    a_id = db.Column(db.Integer, primary_key=True)

class Submission(db.Model):
    s_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)

class Log(db.Model):
    action_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    action = db.Column(db.String(30))


# url routing
# get action performed when user navigates to that url
@app.route('/', methods=['GET'])
def get_home():
    return render_template('landing.html')

@app.route('/forgot-password.html', methods=['GET'])
def get_forgot_password():
    return render_template('forgot-password.html')

@app.route('/landing.html', methods=['GET'])
def get_landing():
    return render_template('landing.html')

@app.route('/login.html', methods=['GET', 'POST'])
def get_login():
    return render_template('login.html')

@app.route('/quiz.html', methods=['GET'])
def get_quiz():
    return render_template('quiz.html')

@app.route('/take_quiz.html', methods=['GET'])
def get_Take_quiz():
    return render_template('take_quiz.html')


@app.route('/register', methods=['GET','POST'])
def register():
    # navigate to register page
    if request.method == 'GET':
        return render_template('register.html')

    # add new user
    elif request.method == 'POST':
        print(request.form)
        admin = int(request.form["admin"])
        username = request.form["username"]
        password = request.form["password"]

        new_user = User(admin, username, password)

        # check if username taken
        if db.engine.execute(
            'SELECT user_id FROM user WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = 'User {} is already registered.'.format(username)
            return jsonify ({ "Status" : error})
        else:
            # add new user to database
            db.session.add(new_user)
            db.session.commit()

            return jsonify ({ "Status" : "New User Created"})


# runs server
if __name__ == "__main__":
    # switch debug to false before assignment submission
    app.run(debug=True)