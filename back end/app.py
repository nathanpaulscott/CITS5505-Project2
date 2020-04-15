from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os


# initialise app
app = Flask(__name__)

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
def get():
    # replace with actual JSON data from database
    return jsonify({ 'msg': 'Hello World'})

# navigate to register page
@app.route('/register')
def get_register():
    return send_from_directory(r'..\Front End Testing', 'register.html')

# add new user
@app.route('/users', methods=['POST'])
def new_user():
    admin = int(request.args.get("admin"))
    username = request.args.get("username")
    password = request.args.get("password")

    new_user = User(admin, username, password)

    # add new user to database
    db.session.add(new_user)
    db.session.commit()

    return jsonify ({ 'status': 'success'})


# runs server
if __name__ == "__main__":
    # switch debug to false before assignment submission
    app.run(debug=True)