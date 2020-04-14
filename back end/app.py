from flask import Flask, request, jsonify
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
class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    admin = db.Column(db.Boolean)
    username = db.Column(db.String(10), unique=True )
    password = db.Column(db.String(10))

    def __init__(self, name, permissions):
        self.name = name
        self.permissions = permissions

class Question_Sets(db.Model):
    qs_id = db.Column(db.Integer, primary_key=True)

class Questions(db.Model):
    q_id = db.Column(db.Integer, primary_key=True)

class Answers(db.Model):
    a_id = db.Column(db.Integer, primary_key=True)

class Submissions(db.Model):
    s_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)

class Log(db.Model):
    action_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    action = db.Column(db.String(30))


# url routing
@app.route('/', methods=['GET'])
# get action performed when user navigates to that url
def get():
    # replace with actual JSON data from database
    return jsonify({ 'msg': 'Hello World'})


# runs server
if __name__ == "__main__":
    # switch debug to false before assignment submission
    app.run(debug=True)