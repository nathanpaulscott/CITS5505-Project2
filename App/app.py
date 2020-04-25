from flask import Flask, request, jsonify, render_template, redirect, send_from_directory, url_for
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import os
import json

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

    # creates a user
    def __init__(self, admin, username, password):
        self.admin = admin
        self.username = username
        self.password = password

class Question_Set(db.Model):
    qs_id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(20))
    enabled = db.Column(db.Boolean)
    topic = db.Column(db.String(10))
    time = db.Column(db.Integer)

    # creates a question set
    def __init__(self, qs_id, author, enabled, topic, time):
        self.qs_id = qs_id
        self.author = author
        self.enabled = enabled
        self.topic = topic
        self.time = time

class Question(db.Model):
    q_id = db.Column(db.Integer, primary_key=True)

    # id of the question set the question belongs to
    qs_id = db.Column(db.Integer)

    # index within the question set
    qs_index = db.Column(db.Integer)

    # the quiz question text
    text = db.Column(db.String(50))

    # id of the quiz_option that is the correct answer to this question
    answer_id = db.Column(db.Integer)

    # creates a question
    def __init__(self, q_id, qs_id, qs_index, text, answer_id):
        self.q_id = q_id
        self.qs_id = qs_id
        self.qs_index = qs_index
        self.text = text
        self.answer_id = answer_id

# possible answer for multiple choice questions
class Quiz_Option(db.Model):
    qo_id = db.Column(db.Integer, primary_key=True)

    # id of the question the answer option belongs to
    q_id = db.Column(db.Integer)

    # index within the question
    q_index = db.Column(db.Integer)

    # the quiz option text
    text = db.Column(db.String(50))

    # creates a quiz option
    def __init__(self, qo_id, q_id, q_index, text):
        self.qo_id = qo_id
        self.q_id = q_id
        self.q_index = q_index
        self.text = text

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
    #NOTE: I made these temporary changes so I could get rid of the 2 login buttons, I will leave it to you to implement it properly...Nathan
    #basically when the login is page is GET reuqested, it is before it has been filled, once the user presses the submit button, it loads login as a POST request with the username and password, which gets verified and redirected to the correct page.  Again, this is just temporary
    if request.method == 'GET':
        return render_template('login.html')
    
    elif request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        #verify the user exists and the password is correct 
        # and log them in with a login flag in the DB
        #also get the admin status and u_id from the DB

        #temp for testing => if username=="admin" login as admin
        #######################
        u_id = "u1234"
        admin_flag = False
        if username == "admin":
            admin_flag = True
        #######################
        if admin_flag:
            return redirect(url_for('get_admin_summary',
                                    username=username,
                                    u_id=u_id))  
            #307 forces it to be POST and send the login form data
        else:
            return redirect(url_for('get_student_summary',
                                    username=username,
                                    u_id=u_id))



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


# import quiz function in the admin_summary page
@app.route('/upload_quiz', methods=['POST'])
def upload_quiz():
    if request.method == 'POST':
        qset_data = request.get_json()["qset_data"]
        #print(qset_data)

        # determines the next unused qs_id from database
        max_id = db.engine.execute(
            'SELECT MAX(qs_id) FROM question__set;'
        ).fetchone()[0]
        qs_id = max_id + 1

        # need to replace with user id supplied by browser
        author = "admin"

        enabled = 1
        
        if (qset_data[0]["topic"] is not None):
            topic = qset_data[0]["topic"]
        else:
            topic = "General"
        if (qset_data[0]["time"] is not None):
            time = qset_data[0]["time"]
        else:
            time = 999


        new_qs = Question_Set(qs_id,author,enabled,topic,time)
        db.session.add(new_qs)

        # Populate database with questions for that question set
        index = 0
        max_qid = None
        max_qoid = None
        
        for item in qset_data:
            # skips info about question_set
            if (index == 0):
                index += 1
                continue

            else:
                if (max_qid is None):
                    # determines the next unused q_id from database
                    max_qid = db.engine.execute(
                        'SELECT MAX(q_id) FROM question;'
                    ).fetchone()[0]
                max_qid += 1
                q_id = max_qid

                # to ensure starts from 0
                qs_index = index - 1
                text = item["question"]["data"]
                answer_id = item["answer"]["correct_index"]
                new_q = Question(q_id,qs_id,qs_index,text,answer_id)
                db.session.add(new_q)
                index += 1

                # populates DB with answers for that question
                q_index = 0
                for answer in item["answer"]["data"]:
                    if (max_qoid is None):
                        # determines the next unused qo_id from database
                        max_qoid = db.engine.execute(
                            'SELECT MAX(qo_id) FROM quiz__option;'
                        ).fetchone()[0]
                    
                    print(max_qoid)
                    max_qoid += 1
                    qo_id = max_qoid

                    text = answer

                    new_qo = Quiz_Option(qo_id,q_id,q_index,text)
                    db.session.add(new_qo)

                    q_index += 1

        # add all to database
        db.session.commit()

        return jsonify ({ 'Status' : 'ok'})



@app.route('/student_summary.html', methods=['GET'])
def get_student_summary():
    return render_template('student_summary.html',
                            username=request.args['username'], 
                            u_id=request.args['u_id'])



@app.route('/admin_summary.html', methods=['GET'])
def get_admin_summary():
    return render_template('admin_summary.html',
                            username=request.args['username'], 
                            u_id=request.args['u_id'])



@app.route('/manage_users.html', methods=['GET'])
def get_manage_users():
    return render_template('manage_users.html',
                            username=request.args['username'], 
                            u_id=request.args['u_id'])


@app.route('/edit_quiz.html', methods=['GET'])
def get_edit_quiz():
    return render_template('edit_quiz.html',
                            username=request.args['username'], 
                            u_id=request.args['u_id'],
                            qset_id=request.args['qset_id'])


#for a student to actually do the quiz and make a submission
@app.route('/take_quiz.html', methods=['GET'])
def get_take_quiz():
    return render_template('take_quiz.html',
                            username=request.args['username'], 
                            u_id=request.args['u_id'],
                            qset_id=request.args['qset_id'])


#for student to review a submission and marks if available
@app.route('/review_quiz.html', methods=['GET'])
def get_review_quiz():
    return render_template('review_quiz.html',
                            username=request.args['username'], 
                            u_id=request.args['u_id'],
                            qset_id=request.args['qset_id'])


#nathan...testing
##########################################################
#to be written, for the assessor to mark quizes
#you load the qset via json with the include_submission = true
@app.route('/mark_quiz.html', methods=['GET'])
def get_mark_quiz():
    return render_template('mark_quiz.html',
                            username=request.args['username'], 
                            u_id=request.args['u_id'],
                            s_u_id=request.args['s_u_id'],
                            qset_id=request.args['qset_id'])




#this is to load a qset via json
@app.route('/load_qset_json', methods=['POST'])
def load_qset_json():
    if request.method == 'POST':
        u_id = request.get_json()["u_id"]
        qset_id = request.get_json()["qset_id"]
        include_submission = request.get_json()["include_submission"]
        include_submitters = request.get_json()["include_submitters"]
        s_u_id = u_id  #for the review submission by student case
        if "s_u_id" in request.get_json():
            s_u_id = request.get_json()["s_u_id"]   #for the mark submission case
        
        #u_id will have the user_id that is asking for the page, and qset_id is the question set being requested
        qset_data = []
        submitters = []

        #DB action required!!
        if include_submitters == "1":
            #need to pull the list of users as a list
            #it has to be of ALL users with submissions for the given qset_id
            #ranked by submission status in this order (Completed, Marked, Attempted, Not Yet Attempted)
            #each item in the list is a string made up of: "u_id: username, status"
            #here is a sample:
            submitters =  \
            [
            "43: Fred Flintstone, Completed",
            "64: John Connor, Completed",
            "42: James Scott, Completed",
            "22: Donald Duck, Completed",
            "425: Jim Banks, Marked",
            "1: Agnes Monica, Marked",
            "244: Margaret Thatcher, Marked",
            "33: Bart Simpson, Marked",
            "111: Barney Rubble, Attempted",
            "54: Peppa Pig, Attempted",
            "21: Hoot, Attempted",
            "25: Noddy, Not yet Attempted",
            "65: Eggs on Toast, Not yet Attempted"
            ]

        #get the standard qset data json format to send to the user
        if include_submission == "1":
            if s_u_id == "init":
                #you need to query the unmarked submissions and return the first unmarked s_u_id
                #if there are no unmarked submissions, then pick any submission and return that s_u_id
                s_u_id = 23   #this is temporary
            #else 
                #s_u_id is a valid id

            #use s_u_id and qset_id to return data from the submissions table like answers, grade, comments
            #then merge it into the answer parts of the complete qset data object
            
            #get the submitter username from the s_u_id
            s_username = "some person"
            
            qset_data = \
            [
            {"qset_id":"243","qset_name":"some question set name","s_u_id":s_u_id,"s_username":s_username},
            {"question":[{"q_id":"1","marks":"10"},
                        {"type":"text","data":"question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here."},
                        {"type":"image","data":"test_image4.jfif"},
                        {"type":"text","data":"question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here."},
                        {"type":"image","data":"test_image3.jfif"},
                        {"type":"image","data":"test_image.jpg"}],
            "answer":{"type":"text","answer":"some answer","grade":"5","comment":"good answer!"}},
            {"question":[{"q_id":"2","marks":"20"},
                        {"type":"text","data":"question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here,"},
                        {"type":"image","data":"test_image1.jfif"},
                        {"type":"text","data":"question 2 text here, question 2 text here, question 2 text here."}],
            "answer":{"type":"mc","answer":"3","grade":"15","comment":"good answer!",
                    "data":["option1","option2","option3","option4"]}},
            {"question":[{"q_id":"3","marks":"5"},
                        {"type":"text","data":"question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here."}],
            "answer":{"type":"text","answer":"some answer","grade":"4","comment":"good answer!"}},
            {"question":[{"q_id":"4","marks":"10"},
                        {"type":"text","data":"question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here."}],
            "answer":{"type":"mc","answer":"4","grade":"8","comment":"good answer!",
                    "data":["option1","option2","option3","option4","option5"]}},
            {"question":[{"q_id":"5","marks":"12"},
                        {"type":"text","data":"question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here,"},
                        {"type":"image","data":"test_image2.jfif"}],
            "answer":{"type":"text","answer":"some answer","grade":"3","comment":"bad answer!"}}
            ]
        else:
            qset_data = \
            [
            {"qset_id":"243","qset_name":"some question set name"},
            {"question":[{"q_id":"1","marks":"10"},
                        {"type":"text","data":"question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here."},
                        {"type":"image","data":"test_image4.jfif"},
                        {"type":"text","data":"question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here."},
                        {"type":"image","data":"test_image3.jfif"},
                        {"type":"image","data":"test_image.jpg"}],
            "answer":{"type":"text"}},
            {"question":[{"q_id":"2","marks":"10"},
                        {"type":"text","data":"question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here,"},
                        {"type":"image","data":"test_image1.jfif"},
                        {"type":"text","data":"question 2 text here, question 2 text here, question 2 text here."}],
                "answer":{"type":"mc",
                        "data":["option1","option2","option3","option4"]}},
            {"question":[{"q_id":"3","marks":"10"},
                        {"type":"text","data":"question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here."}],
            "answer":{"type":"text"}},
            {"question":[{"q_id":"4","marks":"10"},
                        {"type":"text","data":"question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here."}],
                "answer":{"type":"mc",
                        "data":["option1","option2","option3","option4","option5"]}},
            {"question":[{"q_id":"5","marks":"10"},
                        {"type":"text","data":"question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here,"},
                        {"type":"image","data":"test_image2.jfif"}],
            "answer":{"type":"text"}}
            ]

        #if all was ok
        return jsonify ({'Status' : 'ok', "msg" : "", "data" : qset_data, "submitters" : submitters})





# accept answer submission and save to DB
@app.route('/submit_marks_json', methods=['POST'])
def submit_marks_json():
    if request.method == 'POST':
        marking_data = request.get_json()["data"]
        print(marking_data)
        #DB action required!!
        #store the marks in the DB
        '''
        mark_data has the following format:
        [
        {qset_id:qset_id, u_id:u_id, s_u_id:s_u_id, final_submit: 1/0},
        {grade:grade,comment:comment}
        {grade:grade,comment:comment}
        {grade:grade,comment:comment}
        {grade:grade,comment:comment}
        {grade:grade,comment:comment}
        ]
        NOTE: the q_id is the index of the element 1 to end
        NOTE: mark_data[0] always has the header 
        '''
        #if all was ok
        return jsonify ({'Status' : 'ok', "msg" : ""})




# accept answer submission and save to DB
@app.route('/submit_answers_json', methods=['POST'])
def submit_answers_json():
    if request.method == 'POST':
        a_data = request.get_json()["a_data"]
        #print(a_data)

        #DB action required!!
        #store this submission in the DB
        '''
        a_data has the following format:
        [
        {qset_id: qset_id, u_id: u_id, final_submit: 1/0},
        "answer text for text answer",
        "4",
        "2",
        "answer text for text answer",
        ]
        NOTE: the q_id is the index of the element 1 to end
        NOTE: a_data[0] always has the header 
        '''
        #if all was ok
        return jsonify ({'Status' : 'ok', 
                        "msg" : ""})




# accept quiz edits and save to DB
@app.route('/submit_qset_edits_json', methods=['POST'])
def submit_qset_edits_json():
    if request.method == 'POST':
        qset_data = request.get_json()["qset_data"]

        #DB action required!!
        #write the contents of qset_data to the DB

        #if all was ok
        return jsonify ({'Status' : 'ok', "msg" : ""})



#this is for the import image function in the admin_summary page
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
    return jsonify ({ 'Status' : 'ok', 'msg':'Server recieved: ' + filename})
    #return jsonify ({ 'Status' : 'ok'})



#this is for the export quiz function in the admin_summary page
@app.route('/download_quiz', methods=['POST'])
def download_quiz():
    if request.method == 'POST':
        qset_id_req = request.get_json()["qset_id_req"]

        #DB action required!!
        #get the standard qset_json format for each requested qset_id and put in a list to send back to the user
        qset_data = []
        qset_data.append([{"qset_id":"243","qset_name":"some question set name"}, {"question":[{"q_id":"1","marks":"10"},  {"type":"text","data":"question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here.","marks":"10"},{"type":"image","data":"test_image4.jfif","marks":"10"},{"type":"text","data":"question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here.","marks":"10"},{"type":"image","data":"test_image3.jfif","marks":"10"},{"type":"image","data":"test_image.jpg"}]},{"question":[{"q_id":"2","marks":"10"},{"type":"text","data":"question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here,","marks":"10"},{"type":"image","data":"test_image1.jfif","marks":"10"},{"type":"text","data":"question 2 text here, question 2 text here, question 2 text here."}],"answer":{"type":"mc","data":["option1","option2","option3","option4"]}},{"question":[{"q_id":"3","marks":"10"},{"type":"text","data":"question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here."}]},{"question":[{"q_id":"4","marks":"10"},{"type":"text","data":"question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here."}],"answer":{"type":"mc","data":["option1","option2","option3","option4","option5"]}},{"question":[{"q_id":"5","marks":"10"},{"type":"text","data":"question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here,","marks":"10"},{"type":"image","data":"test_image2.jfif"}]}])
        qset_data.append([{"qset_id":"23","qset_name":"some question set name"}, {"question":[{"q_id":"1","marks":"10"},  {"type":"text","data":"question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here.","marks":"10"},{"type":"image","data":"test_image4.jfif","marks":"10"},{"type":"text","data":"question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here.","marks":"10"},{"type":"image","data":"test_image3.jfif","marks":"10"},{"type":"image","data":"test_image.jpg"}]},{"question":[{"q_id":"2","marks":"10"},{"type":"text","data":"question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here,","marks":"10"},{"type":"image","data":"test_image1.jfif","marks":"10"},{"type":"text","data":"question 2 text here, question 2 text here, question 2 text here."}],"answer":{"type":"mc","data":["option1","option2","option3","option4"]}},{"question":[{"q_id":"3","marks":"10"},{"type":"text","data":"question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here."}]},{"question":[{"q_id":"4","marks":"10"},{"type":"text","data":"question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here."}],"answer":{"type":"mc","data":["option1","option2","option3","option4","option5"]}},{"question":[{"q_id":"5","marks":"10"},{"type":"text","data":"question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here,","marks":"10"},{"type":"image","data":"test_image2.jfif"}]}])
        qset_data.append([{"qset_id":"54","qset_name":"some question set name"}, {"question":[{"q_id":"1","marks":"10"},  {"type":"text","data":"question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here.","marks":"10"},{"type":"image","data":"test_image4.jfif","marks":"10"},{"type":"text","data":"question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here.","marks":"10"},{"type":"image","data":"test_image3.jfif","marks":"10"},{"type":"image","data":"test_image.jpg"}]},{"question":[{"q_id":"2","marks":"10"},{"type":"text","data":"question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here,","marks":"10"},{"type":"image","data":"test_image1.jfif","marks":"10"},{"type":"text","data":"question 2 text here, question 2 text here, question 2 text here."}],"answer":{"type":"mc","data":["option1","option2","option3","option4"]}},{"question":[{"q_id":"3","marks":"10"},{"type":"text","data":"question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here."}]},{"question":[{"q_id":"4","marks":"10"},{"type":"text","data":"question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here."}],"answer":{"type":"mc","data":["option1","option2","option3","option4","option5"]}},{"question":[{"q_id":"5","marks":"10"},{"type":"text","data":"question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here,","marks":"10"},{"type":"image","data":"test_image2.jfif"}]}])
        
        return jsonify ({'Status' : 'ok','msg':qset_id_req,'data':qset_data})



#this is for the delete quiz function in the admin_summary page
@app.route('/delete_quiz', methods=['POST'])
def delete_quiz():
    if request.method == 'POST':
        qset_id_req = request.get_json()["qset_id_req"]

        #DB action required!!
        #delete these qset_id's and associated q_id's from the DB
        
        #if all was ok
        return jsonify ({'Status' : 'ok',"msg":qset_id_req})



#this is to load the manage_users json data
@app.route('/manage_users_json', methods=['POST'])
def manage_users_json():
    if request.method == 'POST':
        u_id = request.get_json()["u_id"]

        #DB action required!!
        ##fill the users_data from the DB
        users_data =  \
        [
        ["User_Id", "Username", "Role"],
        ["43", "Fred Flintstone", "Teacher"],
        ["64", "John Connor", "Student"],
        ["42", "James Scott", "Student"],
        ["22", "Donald Duck", "Teacher"],
        ["425", "Jim Banks", "Student"],
        ["1", "Agnes Monica", "Teacher"],
        ["244", "Margaret Thatcher", "Student"],
        ["33", "Bart Simpson", "Student"],
        ["111", "Barney Rubble", "Student"],
        ["54", "Peppa Pig", "Teacher"],
        ["21", "Hoot", "Student"],
        ["25", "Noddy", "Student"],
        ["65", "Eggs on Toast", "Teacher"]
        ]

        #if all was ok
        return jsonify ({'Status' : 'ok',"msg":"","data":users_data})



#this is to load the admin_summary json data
@app.route('/admin_summary_json', methods=['POST'])
def admin_summary_json():
    if request.method == 'POST':
        u_id = request.get_json()["u_id"]

        #DB action required!!
        ##fill the admin summary data from the DB
        qset_summary =  \
        [
        ["Quiz Id","Marked","Completed","Attempted","Topic","Tot Qs","MC Qs","Time(mins)","Owner","Status","Img.Missing","Score Mean","Score SD"],
        ["1",9,25,4,"Topic A",10,5,50,"u_id","Active",0,59.3,13.4],
        ["2",33,45,8,"Topic B",20,10,100,"u_id","Active",0,68.3,8.4],
        ["3",32,35,3,"Topic C",30,20,150,"u_id","Active",0,62.3,7.4],
        ["4",0,65,0,"Topic A",10,5,30,"u_id","Active",0,-1,-1],
        ["5",3,25,5,"Topic C",15,7,70,"u_id","Active",0,90.3,20.1],
        ["6",0,0,0,"Topic C",12,8,60,"u_id","Pending",4,-1,-1],
        ["7",22,35,2,"Topic A",20,10,80,"u_id","Active",0,70.3,12],
        ["8",45,45,7,"Topic D",20,15,90,"u_id","Closed",0,67.2,8.3],
        ["9",60,65,4,"Topic B",15,10,65,"u_id","Active",0,60.3,9.2],
        ["10",30,45,3,"Topic B",10,5,40,"u_id","Active",0,63.3,11.1],
        ["11",2,25,0,"Topic A",5,5,25,"u_id","Active",0,80.3,22.7]
        ]

        #if all was ok
        return jsonify ({'Status' : 'ok',"msg":"","data":qset_summary})


#this is to load the student_summary json data
@app.route('/student_summary_json', methods=['POST'])
def student_summary_json():
    if request.method == 'POST':
        u_id = request.get_json()["u_id"]

        #DB action required!!
        #fill the student summary data from the DB
        qset_summary =  \
        [["Status","Quiz Id","Topic","Tot Qs","MC Qs","Time(mins)","Score","Score Mean","Score SD"],
        ["Not Attempted","1","Topic A",10,5,50,-1,59.3,13.4],
        ["Completed","2","Topic B",20,10,100,-1,68.3,8.4],
        ["Marked","3","Topic A",30,20,150,85.7,62.3,7.4],
        ["Attempted","4","Topic A",10,5,30,-1,-1,-1],
        ["Not Atttempted","5","Topic C",15,7,70,-1,90.3,20.1],
        ["Marked","6","Topic C",12,8,60,65.3,-1,-1],
        ["Completed","7","Topic A",20,10,80,-1,70.3,12],
        ["Marked","8","Topic D",20,15,90,88.1,67.2,8.3],
        ["Not Atttempted","9","Topic B",15,10,65,-1,60.3,9.2],
        ["Marked","10","Topic B",10,5,40,46.2,63.3,11.1],
        ["Completed","11","Topic A",5,5,25,-1,80.3,22.7]]

        #if all was ok
        return jsonify ({'Status' : 'ok',"msg":"","data":qset_summary})


#//////////////////////////////////////////////////////
#//////////////////////////////////////////////////////
#//////////////////////////////////////////////////////
#//////////////////////////////////////////////////////
#//////////////////////////////////////////////////////
#//////////////////////////////////////////////////////
""" 
The format for the .quiz files for the question set specification is:
NOTE: I am not validating this format right now, the JS just passes wahtever JSON you give to the server as long as it is JSON
///////////////////////////////////////////////
[
{"qset_name":"some question set name"},
{"question":[{"q_id":"1","marks":"10"},
            {"type":"text","data":"question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here."},
            {"type":"image","data":"test_image4.jfif"},
            {"type":"text","data":"question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here."},
            {"type":"image","data":"test_image3.jfif"},
            {"type":"image","data":"test_image.jpg"}]},
{"question":[{"q_id":"2","marks":"10"},
            {"type":"text","data":"question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here,"},
            {"type":"image","data":"test_image1.jfif"},
            {"type":"text","data":"question 2 text here, question 2 text here, question 2 text here."}],
   "answer":{"type":"mc",
            "data":["option1","option2","option3","option4"]}},
{"question":[{"q_id":"3","marks":"10"},
            {"type":"text","data":"question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here."}]},
{"question":[{"q_id":"4","marks":"10"},
            {"type":"text","data":"question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here."}],
   "answer":{"type":"mc",
            "data":["option1","option2","option3","option4","option5"]}},
{"question":[{"q_id":"5","marks":"10"},
            {"type":"text","data":"question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here,"},
            {"type":"image","data":"test_image2.jfif"}]}
]
////////////////////////////////////////
NOTE: The browser will add object["user_id"]="the user id" to the incoming json object before upg to the server
NOTE: if the qset_id is missing, then the browser adds this field to the json object using the next available qset_id (say qset_ids are "qs" + a number)
//////////////////////////////////////////////////////
So what gets sent to the server is:
//////////////////////////////////////////////////////
[
{"qset_id":"453","qset_name":"some question set name", "u_id":"u_id"},
{"question":[{"q_id":"1","marks":"10"},
            {"type":"text","data":"question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here."},
            {"type":"image","data":"test_image4.jfif"},
            {"type":"text","data":"question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here."},
            {"type":"image","data":"test_image3.jfif"},
            {"type":"image","data":"test_image.jpg"}]},
{"question":[{"q_id":"2","marks":"10"},
            {"type":"text","data":"question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here,"},
            {"type":"image","data":"test_image1.jfif"},
            {"type":"text","data":"question 2 text here, question 2 text here, question 2 text here."}],
    "answer":{"type":"mc",
            "data":["option1","option2","option3","option4"]}},
{"question":[{"q_id":"3","marks":"10"},
            {"type":"text","data":"question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here."}]},
{"question":[{"q_id":"4","marks":"10"},
            {"type":"text","data":"question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here."}],
    "answer":{"type":"mc",
            "data":["option1","option2","option3","option4","option5"]}},
{"question":[{"q_id":"5","marks":"10"},
            {"type":"text","data":"question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here,"},
            {"type":"image","data":"test_image2.jfif"}]}
]

//////////////////////////////////////////////////////
to access the qset header:
--------------------------------
    object_name[0]

to access one question:
--------------------------------
    object_name[q_id]

to access the mc answer options:
--------------------------------
    object_name[q_id]["answer"]["data"]

to test if it is text or mc:
--------------------------------
    if ("answer" in object_name[3] && object_name[q_id]["answer"]["type"] == "mc")

to access the question header of a question:
--------------------------------
    object_name[q_id]["question"][0]

to access the question data of a question:
--------------------------------
    object_name[q_id]["question"][1:]

/////////////////////////////////////////////////////
Then at the server this json object needs to go in the question_set table and the question table as so:
/////////////////////////////////////////////////////
table: question_set, one row per question set
col(PK): qset_id => jsut a unique integer
col: qset_name
col: owner => object["u_id"]
col: status => give it an initial status of "not active"

table: questions, one row per question
col(PK): qset_id
col(PK): q_id => the question sequence integer in the qset
col: marks: the marks available for this question
col: answer_type: text/mc
col: answer_data: json.dumps(object[q_id]["answer"]["data"][1:])
col: question_data: json.dumps(object[q_id]["question"][1:])

table: submissions, one row per question per student
col(PK): qset_id
col(PK): q_id => the question sequence integer in the qset
col(PK): u_id
col: complete: true/false   (only true if the submit was a final submit, otherwise it is an uncomplete attempt)
col: answer_type: text/mc
col: answer_data: the answer text
col: grade: the marks given or this answer
col: comment: the markers comment for this answer

"""


#########################################################







# runs server
if __name__ == "__main__":
    # switch debug to false before assignment submission
    app.run(debug=True)