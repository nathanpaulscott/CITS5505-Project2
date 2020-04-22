from flask import Flask, request, jsonify, render_template, redirect, send_from_directory, url_for
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import os


# initialise app
basedir = os.path.abspath(os.path.dirname(__file__))
image_folder = '/static/images'

app = Flask(__name__)



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
    author = db.Column(db.String(20))
    enabled = db.Column(db.Boolean)

class Question(db.Model):
    q_id = db.Column(db.Integer, primary_key=True)

    # id of the question set the question belongs to
    qs_id = db.Column(db.Integer)

    # the quiz question text
    text = db.Column(db.String(50))

    # id of the quiz_option that is the correct answer to this question
    answer_id = db.Column(db.Integer)

    topic = db.Column(db.String(10))
    time = db.Column(db.Integer)

# provded possible answer for multiple choice questions
class Quiz_Option(db.Model):
    qo_id = db.Column(db.Integer, primary_key=True)

    # id of the question the answer option belongs to
    q_id = db.Column(db.Integer)

    # the quiz option text
    text = db.Column(db.String(50))

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

@app.route('/student_summary.html', methods=['GET'])
def get_student_summary():
    return render_template('student_summary.html')

@app.route('/take_quiz.html', methods=['GET'])
def get_take_quiz():
    return render_template('take_quiz.html')

@app.route('/admin_summary.html', methods=['GET'])
def get_admin_summary():
    return render_template('admin_summary.html')

@app.route('/edit_quiz.html', methods=['GET'])
def get_edit_quiz():
    return render_template('edit_quiz.html')

@app.route('/register.html', methods=['GET','POST'])
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






#nathan...testing
##########################################################
#code to handle the upload function of the admin summary
@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify ({ 'Status' : 'error', 'msg':'bad form format'})
    file = request.files['file']
    if file.filename == '':
        return jsonify ({ 'Status' : 'error', 'msg':'no file selected'})
    file = request.files['file']
    filename = secure_filename(file.filename)
    file.save(basedir + '/' + image_folder + '/' + filename)
    #for testing
    return jsonify ({ 'Status' : 'ok', 'msg':'Server recieved: ' + filename})
    #return jsonify ({ 'Status' : 'ok'})
    #FYI for later, how to redirect, this sends the user to this page with these params
    #return redirect(url_for('get_admin_summary', filename=filename))


@app.route('/upload_quiz', methods=['POST'])
def upload_quiz():
    if request.method == 'POST':
        qs_data = request.get_json()
        #so qs_data is the json object, need to put it in the DB now
        #for testing
        return jsonify ({ 'Status' : 'ok'})
        #return qs_data




""" 
The format for the .quiz files for the question set specification is:
///////////////////////////////////////////////
{"qset_id":"some alpha-numeric string" (optional),
    1:{"question":{1:{"type":"text","data":"some text for Q1"},
            2:{"type":"image","data":"some_image.jpg"},
            3:{"type":"text","data":"some text"}}, 
    "answer":{"type":"mc","data":["ans1","ans2","ans3","ans4"]}},
    2:{"question":{1:{"type":"text","data":"some text for Q2"}},
    3:{"question":{1:{"type":"text","data":"some text for Q3"},
            2:{"type":"image","data":"some_image.jpg"},
            3:{"type":"image","data":"some_image.jpg"},
            4:{"type":"text","data":"some text"}, 
            5:{"type":"image","data":"some_image.jpg"}},
    "answer":{"type":"mc","data":["ans1","ans2","ans3","ans4","ans5"]}},
    4:{"question":{1:{"type":"text","data":"some text for Q4"}},
    5:{"question":{1:{"type":"text","data":"some text for Q5"}},
    6:{"question":{1:{"type":"text","data":"some text for Q6"}}}
////////////////////////////////////////
NOTE: The browser will add object["user_id"]="the user id" to the incoming json object before upg to the server
NOTE: if the qset_id is missing, then the browser adds this field to the json object using the next available qset_id (say qset_ids are "qs" + a number)
NOTE: the browser will also add the q_id parameter to object[q_seq]["q_id"]="some question id".  Where maybe question id = qset_id + "_" + q_seq, eg. qs456_3
//////////////////////////////////////////////////////
So what gets sent to the server is:
//////////////////////////////////////////////////////
{"qset_id":"some alpha-numeric string",
"u_id": "the id of the current admin user",
    1:{"q_id":qset_id + "_1",
    "question":{1:{"type":"text","data":"some text for Q1"},
            2:{"type":"image","data":"some_image.jpg"},
            3:{"type":"text","data":"some text"}}, 
    "answer":{"type":"mc","data":["ans1","ans2","ans3","ans4"]}},
    2:{"q_id":qset_id + "_2",
    "question":{1:{"type":"text","data":"some text for Q2"}},
    3:{"q_id":qset_id + "_3",
    "question":{1:{"type":"text","data":"some text for Q3"},
            2:{"type":"image","data":"some_image.jpg"},
            3:{"type":"image","data":"some_image.jpg"},
            4:{"type":"text","data":"some text"}, 
            5:{"type":"image","data":"some_image.jpg"}},
    "answer":{"type":"mc","data":["ans1","ans2","ans3","ans4","ans5"]}},
    4:{"q_id":qset_id + "_4",
    "question":{1:{"type":"text","data":"some text for Q4"}},
    5:{"q_id":qset_id + "_5",
    "question":{1:{"type":"text","data":"some text for Q5"}},
    6:{"q_id":qset_id + "_6",
    "question":{1:{"type":"text","data":"some text for Q6"}}}
//////////////////////////////////////////////////////


to access one question:
--------------------------------
    object_name[3]

to access the mc answer options:
--------------------------------
    object_name[3]["answer"]["data"]

to test if it is text or mc:
--------------------------------
    if ("answer" in object_name[3]) {}

to access the question data of a question:
--------------------------------
    var q_data = object_name[3]["question"]; 
    for (i in q_data) {
        if (q_data["type" == "text"]) {
            //do somehting with the string: q_data["data"]
        } else if (q_data["type" == "image"]) {
            //do something with the filename string: q_data["data"]
        }
    }

/////////////////////////////////////////////////////
Then at the server this json object needs to go in the question_set table and the question table as so:
/////////////////////////////////////////////////////
table: question_set, one row per question set
col(PK): qset_id => gets the object["qset_id"]
col: qset_name => dunno, maybe add a name field to the import for text names, object["qset_name"]
col: owner => object["u_id"]
col: status => give it an initial status of "not active"
col: q_list => write a list of the q_ids, 
    i.e. something like..... json.dump([object[x]["q_id"] for x in object.keys() if (x != "qset_id" and x != "u_id")])

table: questions, one row per question
for q_seq in [x for x in object.keys() if (x != "qset_id" and x != "u_id")]:
    col(PK): q_id => object[q_seq]["q_id"]
    col: q_seq => q_seq (numeric)
    col: a_type: object[q_seq]["answer"]["type"]
    col: a_data: json.dumps(object[q_seq]["answer"]["data"])
    col: q_data: [object[q_seq]["question"][x] for x in object[q_seq]["question"].keys()]


 """


#########################################################







# runs server
if __name__ == "__main__":
    # switch debug to false before assignment submission
    app.run(debug=True)