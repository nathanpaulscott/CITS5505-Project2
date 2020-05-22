from flask import Flask, request, jsonify, render_template, redirect, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash, safe_str_cmp
import jwt    #pip install pyjwt   (do not install jwt or python-jwt, install them first)
#---------------------------
import re
import os
import json
import statistics as st
from datetime import datetime as dt 
import time


# initialise app
app = Flask(__name__)
app.config['BASE_PATH'] = os.path.abspath(os.path.dirname(__file__))
app.config['IMAGE_FOLDER'] = '/static/images'
app.config['LOGIN_DORMANT_TIME_S'] = 15*60    #15 mins
app.config['LOGIN_MAX_TIME_S'] = 30*60    #30 mins
app.config['SECRET_KEY'] = 'FsE4Hb72SpJe'    #for jwt


# Database
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(app.config['BASE_PATH'], 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False   #True  #?
# initialise database
db = SQLAlchemy(app)



#############################################################################
#Models
#############################################################################

# tables in database - move each to separate file
class User(db.Model):
    __tablename__ = 'user'
    u_id = db.Column(db.Integer, primary_key=True)
    admin = db.Column(db.Boolean)
    username = db.Column(db.String(30), unique=True )
    password = db.Column(db.Text)
    last_req = db.Column(db.Text)
    login_att = db.Column(db.Integer)

    # creates a user
    def __init__(self, u_id, admin, username, password, last_req, login_att):
        self.admin = admin
        self.u_id = u_id
        self.username = username
        self.password = password
        self.last_req = last_req
        self.login_att = login_att

class Question_Set(db.Model):
    __tablename__ = 'question_set'
    qs_id = db.Column(db.Integer, primary_key=True)
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id'), primary_key=True)
    enabled = db.Column(db.Boolean)
    topic = db.Column(db.String(50))
    time = db.Column(db.Integer)      #time in mins NOT seconds!!!

    # creates a question set
    def __init__(self, qs_id, u_id, enabled, topic, time):
        self.qs_id = qs_id
        self.u_id = u_id
        self.enabled = enabled
        self.topic = topic
        self.time = time

class Question(db.Model):
    __tablename__ = 'question'
    qs_id = db.Column(db.Integer, db.ForeignKey('question_set.qs_id'), primary_key=True)  # id of the question set the question belongs to
    q_id = db.Column(db.Integer, primary_key=True)   #n part of a compound primary key with qs_id
    q_marks = db.Column(db.Integer)     #marks available
    q_data = db.Column(db.Text)         #question data, stored as a json string
    a_type = db.Column(db.String(10))   #mc/text
    a_data = db.Column(db.Text)         #mc answer options, stored as a json string
    a_correct = db.Column(db.Text)      #correct answer (just a string of an integer for mc)

    # creates a question
    def __init__(self, qs_id, q_id, q_marks, q_data, a_type, a_data, a_correct):
        self.qs_id = qs_id
        self.q_id = q_id
        self.q_marks = q_marks
        self.q_data = q_data
        self.a_type = a_type
        self.a_data = a_data
        self.a_correct = a_correct

class Submission(db.Model):
    __tablename__ = 'submission'
    qs_id = db.Column(db.Integer, db.ForeignKey('question_set.qs_id'), primary_key=True)
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id'), primary_key=True)
    status = db.Column(db.String(30))

    # creates a submission
    def __init__(self, qs_id, u_id, status):
        self.qs_id = qs_id
        self.u_id = u_id
        self.status = status

class Submission_Answer(db.Model):
    __tablename__ = 'submission_answer'
    qs_id = db.Column(db.Integer, db.ForeignKey('question_set.qs_id'), primary_key=True)
    q_id = db.Column(db.Integer, db.ForeignKey('question.q_id'), primary_key=True)
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id'), primary_key=True)
    data = db.Column(db.Text)        #sqlite3 Text
    mark = db.Column(db.Float)    #sqlite3 real
    comment = db.Column(db.Text)     #sqlite3 Text

    # creates an answer
    def __init__(self, qs_id, q_id, u_id, data, mark, comment):
        self.qs_id = qs_id
        self.q_id = q_id
        self.u_id = u_id
        self.data = data
        self.mark = mark
        self.comment = comment

class Log(db.Model):
    __tablename__ = 'log'
    time = db.Column(db.Integer, primary_key=True)    #ms since epoch
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id'), primary_key=True)
    action_id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.Text)

    # creates an log entry
    def __init__(self, action_id, u_id, action, time):
        self.time = time
        self.u_id = u_id
        self.action_id = action_id
        self.action = action


#############################################################################
#GET/POST pre-entry route functions, everything that is pre-login
#############################################################################

@app.route('/', methods=['GET'])
@app.route('/landing.html', methods=['GET'])
def get_home():
    write_log(0,1,'landing page entry')
    return render_template('landing.html')


@app.route('/forgot-password.html', methods=['GET'])
def get_forgot_password():
    write_log(0,2,'forgot password entry')
    return render_template('forgot-password.html')


@app.route('/login.html', methods=['GET', 'POST'])
def get_login():
    error_target = '/login.html'

    if request.method == 'GET':
        write_log(0,3,'login page entry')
        return render_template('login.html')
    
    elif request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]

    #verify the user exists and the password is correct 
    #also get the admin status and u_id from the DB
    user = User.query.filter_by(username=username).first()
    if user is None:
        #no username found
        write_log(0,4,'failed login from username not found')
        return jsonify ({"status":"error", 
                        "msg":'Username {} not found'.format(username),
                        "target":error_target})
    
    if user.login_att is None:
        user.login_att = 1
        db.session.commit()
    elif user.login_att > 5:
        #make another page here to inform the user to stop trying and contact admin
        write_log(user.u_id,5,'failed login from too many failed attempts')
        return jsonify ({"status":"error", 
                        "msg":'Too many failed login attempts',
                        "target":"./landing.html"})

    #check the password
    if not check_password_hash(user.password, password):
        #wrong password
        user.login_att = user.login_att + 1
        db.session.commit()
        write_log(user.u_id,6,'failed login from incorrect password')
        return jsonify ({"status":"error", 
                        "msg":'incorrect password',
                        "target":"./login.html"})

    #user gets logged in, reset the attempts counter and set the login time in the session token
    t_now = time_now()
    token = jwt.encode(
        {'u_id':user.u_id,
        'username':user.username, 
        'login_time' : t_now,
        'expiry' : t_now + app.config['LOGIN_MAX_TIME_S']}, 
        app.config['SECRET_KEY'])
                            
    user.login_att = 0
    #if I was to implement memory to go back to the last attempted page, you would do it here, 
    #but because I am rendering in js, it becomes a little difficult to do that as I need to tell it 
    #the js function to go to, its not impossible, but a bit of a pain, so, instead, I just reset this field in the db
    user.last_req = ''
    db.session.commit()

    #return the session token to the client
    write_log(user.u_id, 7, 'successful login')
    target = url_for('get_student_summary') 
    if user.admin:
        target = url_for('get_admin_summary') 

    return jsonify({'status':'ok',
                    'target':target,
                    'data':{'token':token.decode('utf-8'),
                            'username':user.username,
                            'u_id':user.u_id}})
        

@app.route('/register.html', methods=['GET','POST'])
def register_request():
    # navigate to register page
    if request.method == 'GET':
        write_log(0,8,'registration page entry')
        return render_template('register.html')

    # add new user
    elif request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        admin = False
        if request.form["admin"] == "1":      
            admin = True
        
        if register(username, password, admin) == True:
            #log the user in
            return jsonify ({'status':'ok'})
        else:
            return jsonify ({"status":'error',
                            'msg':'User {} is already registered.'.format(username),
                            'target':'./register.html'})

# separated from function above to allow testability
def register(username, password, admin):
        # check if username taken
        result = User.query.filter_by(username=username).first()
        if result is not None:
            write_log(0,9,'failed registration as username "' + username + '" is taken')
            return False
        else:
            # determines the next unused u_id from database
            u_id = 1
            result = db.engine.execute('SELECT MAX(u_id) FROM user;').fetchone()[0]
            if result is not None:
                u_id = result + 1
    
            #hashes the password
            password_h = generate_password_hash(password) #, method='pbkdf2:sha256:500000')
            
            # add new user to database
            new_user = User(u_id=u_id, 
                            admin=admin, 
                            username=username, 
                            password=password_h, 
                            last_req=json.dumps({'fn':'init'}),
                            login_att=0)
            db.session.add(new_user)
            db.session.commit()
            return True


#used by the manage users functions to add/edit/delete
@app.route('/edit_user', methods=['POST'])
def edit_user():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token()
    if not result['status'] == 'ok':
        if result['msg'] == 'no token': 
            return redirect(result['target'])   #return html as requester was just a browser
        return jsonify (result)
    #extract params
    #admin id
    u_id = result['data'].u_id
    username = result['data'].username
    #these are the edited user details
    u_id_edit = request.get_json()["u_id"]
    username_edit = request.get_json()["username"]
    password_edit = request.get_json()["password"]
    admin_edit = False
    if request.get_json()["admin"] == "1":
        admin_edit = True
    
    #DELETE USER CASE
    elif request.get_json()["admin"] == "":
        User.query.filter_by(u_id=u_id_edit).delete()
        Submission.query.filter_by(u_id=u_id_edit).delete()
        Submission_Answer.query.filter_by(u_id=u_id_edit).delete()
        db.session.commit()
        write_log(0,103,'user delete success, u_id = ' + u_id_edit)
        return jsonify ({'status':'ok',
                        'msg':'The user was deleted successfully',
                        'target':'/manage_users.html'})

    #ADD USER CASE
    if u_id_edit == "":
        if register(username_edit, password_edit, admin_edit) == True:
            write_log(0,101,'Add user success')
            return jsonify ({'status':'ok',
                            'msg':'Add user success',
                            'target':'/manage_users.html'})
        else:
            write_log(0,101,'Add user failed due to username conflict')
            return jsonify ({'status':'error',
                            'msg':'Username {} is already taken.'.format(username_edit)})
    
    #EDIT USER CASE
    else:
        #get the current user details
        result = User.query.filter_by(u_id=u_id_edit).first()
        #do the username
        if result.username != username_edit:
            # check if username taken
            temp_result = User.query.filter_by(username=username_edit).first()
            if temp_result is not None:
                write_log(0,100,'failed as username "' + username_edit + '" is taken')
                return jsonify ({'status':'error',
                                'msg':'Username {} is already taken.'.format(username_edit)})

        #do the password
        password_h = result.password
        if password_edit != "":
            #only hashes the new password if it has changed (blank means it has not changed)
            password_h = generate_password_hash(password_edit)

        #edit user in the DB
        result.admin=admin_edit 
        result.username=username_edit
        result.password=password_h 
        result.last_req=json.dumps({'fn':'init'})
        result.login_att=0
        db.session.commit()
        write_log(0,102,'user edit success, u_id = ' + u_id_edit)
        return jsonify ({'status':'ok',
                        'msg':'Your edit was successfull',
                        'target':'/manage_users.html'})






#############################################################################
#GET route functions, correspond to the different web pages
#############################################################################

#this is to load the student_summary basic template
@app.route('/student_summary.html', methods=['GET'])
def get_student_summary():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token()
    if not result['status'] == 'ok':
        if result['msg'] == 'no token': 
            return redirect(result['target'])   #return html as requester was just a browser
        return jsonify (result)
    #extract params
    u_id = result['data'].u_id
    username = result['data'].username

    #this is the output data header to be passed back to the client, list of lists
    qset_summary =  \
    [["Status","Quiz Id","Topic","Tot Qs","MC Qs","Time(mins)","Marks Available","Marks Attained","Marks Mean","Marks SD"]]

    #fills qset_summary from the DB
    qsets = Question_Set.query.all()
    #will have qs_id, u_id, enabled, topic, time
    #need to fill the rest of the fields ["Status","Tot Qs","MC Qs","Time(mins)","Score","Score Mean","Score SD"]
    for qset in qsets:
        qs_id = qset.qs_id
        # get num questions
        qset.tot_qs = len(Question.query.filter_by(qs_id=qs_id).all())
        qset.mc_qs = len(Question.query.filter_by(qs_id=qs_id, a_type='mc').all())
        # get the student status for the qset
        result = Submission.query.filter_by(qs_id=qs_id, u_id=u_id).first()
        if result is None:
            qset.status = 'Not Attempted'
        else:
            qset.status = result.status
        #get the marks available
        result = Question.query.filter_by(qs_id=qs_id).all()
        qset.marks_avail = sum([x.q_marks for x in result])
        #get the marks given
        result = Submission_Answer.query.filter_by(qs_id=qs_id, u_id=u_id).all()
        qset.marks = 0
        if len(result) > 0:
            qset.marks = sum([x.mark for x in result])
        #get the marks stats
        result = Submission_Answer.query.filter_by(qs_id=qs_id).all()
        marks = []
        qset.marks_mean = 0
        qset.marks_sd = 0
        for submitter in set([x.u_id for x in result]):
            marks.append(sum([x.mark for x in result if x.u_id == submitter]))
        if len(marks) >= 1:
            qset.marks_mean = round(st.mean(marks),2)
        if len(marks) >= 2:
            qset.marks_sd = round(st.stdev(marks),2)

        #fill the output list with data
        qset_summary.append([qset.status, 
                            qset.qs_id, 
                            qset.topic,
                            qset.tot_qs,
                            qset.mc_qs,
                            qset.time,
                            qset.marks_avail,
                            qset.marks,
                            qset.marks_mean,
                            qset.marks_sd])

    #if all was ok
    write_log(u_id, 12, 'student summary successful')
    return jsonify ({'status' : 'ok',
                    'msg':'',
                    'html':render_template('student_summary.html'),
                    'data':{'data':qset_summary}})


@app.route('/admin_summary.html', methods=['GET'])
def get_admin_summary():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token()
    if not result['status'] == 'ok':
        if result['msg'] == 'no token': 
            return redirect(result['target'])   #return html as requester was just a browser
        return jsonify (result)
    #extract params
    u_id = result['data'].u_id
    username = result['data'].username
    
    qset_summary =  \
    [["Quiz Id","Marked","Completed","Attempted","Topic","Tot Qs","MC Qs","Time(mins)","Owner","Enabled","Img.Missing","Marks Available","Mark Mean","Mark SD"]]

    #fills qset_summary from the DB
    qsets = Question_Set.query.all()
    #will have qs_id, u_id, enabled, topic, time
    #need to fill the rest of the fields ["Marked","Completed","Attempted","Tot Qs","MC Qs","Img.Missing","Score Mean","Score SD"]
    for qset in qsets:
        qs_id = qset.qs_id
        
        # get num questions
        qset.tot_qs = len(Question.query.filter_by(qs_id=qs_id).all())
        qset.mc_qs = len(Question.query.filter_by(qs_id=qs_id, a_type='mc').all())
        
        # get the status numbers for the qset
        result = Submission.query.filter_by(qs_id=qs_id, status="Completed").all()
        qset.completed = len(result)
        result = Submission.query.filter_by(qs_id=qs_id, status="Marked").all()
        qset.marked = len(result)
        result = Submission.query.filter_by(qs_id=qs_id, status="Attempted").all()
        qset.attempted = len(result)
        
        #get the marks available
        result = Question.query.filter_by(qs_id=qs_id).all()
        qset.marks_avail = sum([x.q_marks for x in result])
        
        #get the marks stats
        result = Submission_Answer.query.filter_by(qs_id=qs_id).all()
        marks = []
        qset.marks_mean = 0
        qset.marks_sd = 0
        for user in set([x.u_id for x in result]):
            marks.append(sum([x.mark for x in result if x.u_id == user]))
        if len(marks) >= 1:
            qset.marks_mean = round(st.mean(marks),2)
        if len(marks) >= 2:
            qset.marks_sd = round(st.stdev(marks),2)
        
        #get the num images missing
        result = Question.query.filter_by(qs_id=qs_id).all()
        qset.img_missing = 0
        image_refs = []
        
        #get all the images refs in all questions in the question set
        #go through each question in the qset
        for row in result:
            #convert the question data to a json object
            q_data = json.loads(row.q_data)
        
            #go through each part
            for item in q_data:
                #if the part is an image ref extract it
                if item['type'] == "image":
                    image_refs.append(item['data'])
        
        #find the image files in the static/images folder
        image_files = []
        for root,dirs,files in os.walk(app.config['BASE_PATH'] + '/' + app.config['IMAGE_FOLDER'], topdown=True):
            for file in files:
                image_files.append(file)
        
        #does the crosschecking
        for image in image_refs:
            if image not in image_files:
                qset.img_missing += 1

        #fill the output list with data
        qset_summary.append([qset.qs_id, 
                            qset.marked, 
                            qset.completed,
                            qset.attempted,
                            qset.topic,
                            qset.tot_qs,
                            qset.mc_qs,
                            qset.time,
                            qset.u_id,
                            qset.enabled,
                            qset.img_missing,
                            qset.marks_avail,
                            qset.marks_mean,
                            qset.marks_sd])

    #if all ok
    write_log(u_id,13,'admin summary successfull')
    return jsonify ({'status' : 'ok',
                    'msg':'',
                    'html':render_template('admin_summary.html'),
                    'data':{'data':qset_summary}})


@app.route('/edit_quiz.html', methods=['GET'])
def get_edit_quiz():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token()
    if not result['status'] == 'ok':
        if result['msg'] == 'no token': 
            return redirect(result['target'])   #return html as requester was just a browser
        return jsonify (result)
    #extract params
    u_id = result['data'].u_id
    username = result['data'].username
    qs_id = request.args['qs_id']
    s_u_id = u_id
    include_submission = request.args['include_submission']
    include_submitters = request.args['include_submitters']
    
    result = load_qset_json(u_id, username, qs_id, s_u_id, include_submission, include_submitters)
    if not result['status'] == 'ok':
        return jsonify (result)

    write_log(u_id,15,'edit quiz success')
    return jsonify ({'status' : 'ok',
                    'msg':'',
                    'html':render_template('edit_quiz.html'),
                    'data':{'data':result['data']}})


@app.route('/manage_users.html', methods=['GET'])
def get_manage_users():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token()
    if not result['status'] == 'ok':
        if result['msg'] == 'no token': 
            return redirect(result['target'])   #return html as requester was just a browser
        return jsonify (result)
    #extract params
    u_id = result['data'].u_id
    username = result['data'].username

    ##fill the users_data from the DB
    users_data = [["User_Id", "Role", "Username", "Password"]]
    users = User.query.all()
    for user in users:
        users_data.append([ user.u_id, 
                            "Teacher" if user.admin else "Student", 
                            user.username,
                            "***"])   #user.password])

    #if all was ok
    write_log(u_id,23,'manage users success')
    return jsonify ({'status' : 'ok',
                    'msg':'',
                    'html':render_template('manage_users.html'),
                    'data':{'data':users_data}})


#for a student to actually do the quiz and make a submission
@app.route('/take_quiz.html', methods=['GET'])
def get_take_quiz():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token()
    if not result['status'] == 'ok':
        if result['msg'] == 'no token': 
            return redirect(result['target'])   #return html as requester was just a browser
        return jsonify (result)
    #extract params
    u_id = result['data'].u_id
    username = result['data'].username
    qs_id = request.args['qs_id']
    preview_flag = request.args['preview_flag']
    s_u_id = u_id
    include_submission = request.args['include_submission']
    include_submitters = request.args['include_submitters']
    
    ################################################################
    #set the submission status for that user to 'Attempted' immediately 
    #incase they just look at the questions and exit the tool, if you wanted to be more stringent
    #you woud set the submission status to 'Completed' here and not even have an 'Attempted' status
    #basically there will a submission entry, but no submission_answers, 
    #the rest of the code handles that case though, it just says the answers are blank
    #if the user then actually gives sme answers later, they are add to the DB
    status='Attempted'   #'Completed'
    user_submission = Submission.query.filter_by(qs_id=qs_id, u_id=s_u_id).first()
    if user_submission is None:
        user_submission = Submission(qs_id,u_id,status)
        db.session.add(user_submission)
        db.session.commit()
    ################################################################

    #run the load_qset_json function
    result = load_qset_json(u_id, username, qs_id, s_u_id, include_submission, include_submitters)
    if not result['status'] == 'ok':
        return jsonify (result)
    
    if preview_flag == 'false':
        write_log(u_id,25,'take quiz success')
    else:
        write_log(u_id,39,'preview quiz success')

    return jsonify ({'status' : 'ok',
                    'msg':'',
                    'html':render_template('take_quiz.html'),
                    'data':{'data':result['data'],
                            'submitters':result['submitters'],
                            'submission_status':result['submission_status']}})


#for student to review a submission and marks if available
@app.route('/review_quiz.html', methods=['GET'])
def get_review_quiz():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token()
    if not result['status'] == 'ok':
        if result['msg'] == 'no token': 
            return redirect(result['target'])   #return html as requester was just a browser
        return jsonify (result)
    #extract params
    u_id = result['data'].u_id
    username = result['data'].username
    qs_id = request.args['qs_id']
    s_u_id = u_id
    include_submission = request.args['include_submission']
    include_submitters = request.args['include_submitters']

    result = load_qset_json(u_id, username, qs_id, s_u_id, include_submission, include_submitters)
    if not result['status'] == 'ok':
        return jsonify (result)
    
    write_log(u_id,28,'review quiz success')
    return jsonify ({'status' : 'ok',
                    'msg':'',
                    'html':render_template('review_quiz.html'),
                    'data':{'data':result['data'],
                            'submitters':result['submitters'],
                            'submission_status':result['submission_status']}})


#you load the qset via json with the include_submission = true
@app.route('/mark_quiz.html', methods=['GET'])
def get_mark_quiz():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token()
    if not result['status'] == 'ok':
        if result['msg'] == 'no token': 
            return redirect(result['target'])   #return html as requester was just a browser
        return jsonify (result)
    #extract params
    u_id = result['data'].u_id
    username = result['data'].username
    qs_id = request.args['qs_id']
    s_u_id = request.args['s_u_id']
    include_submission = request.args['include_submission']
    include_submitters = request.args['include_submitters']

    result = load_qset_json(u_id, username, qs_id, s_u_id, include_submission, include_submitters)
    if not result['status'] == 'ok':
        return jsonify (result)

    write_log(u_id,29,'mark quiz success')
    return jsonify ({'status' : 'ok',
                     'msg':'',
                     'html':render_template('mark_quiz.html'),
                     'data':{'data':result['data'],
                            'submitters':result['submitters'],
                            'submission_status':result['submission_status']}})


@app.route('/admin_stats.html', methods=['GET'])
def get_admin_stats():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token()
    if not result['status'] == 'ok':
        if result['msg'] == 'no token': 
            return redirect(result['target'])   #return html as requester was just a browser
        return jsonify (result)
    #extract params
    u_id = result['data'].u_id
    username = result['data'].username
    qs_id = request.args['qs_id']

    #get the list of marked qs_ids
    marked_qsets = Submission.query.filter_by(status='Marked').all()
    marked_qsets = list({x.qs_id for x in marked_qsets})

    #exit if no qs_ids have submissions
    if len(marked_qsets) == 0:
        return jsonify ({'status' : 'cancel',
                        'msg':'there are no marked submissions',
                        'target':'/admin_summary.html'})

    #set the first qs_id if none was specified
    if qs_id == "init":
        qs_id = marked_qsets[0]

    #get the marks array for the given qs_id
    data = [['result']]
    sub_ans = Submission_Answer.query.filter_by(qs_id=qs_id).all()
    users = {x.u_id for x in sub_ans}
    for user in users:
        mark = sum([x.mark for x in sub_ans if x.u_id == user])
        data.append([mark])

    #this is fake data, if there was enough data in the system you would just query Submission_Answers and sum all marks for each submission and put into a list here
    data = [['result'],[84.4257772852282],[89.4693179302548],[49.5593304581194],[79.345133048903],[51.9096961003536],[98.8033358634526],[89.2828277401471],[53.0921280077312],[73.2753440911822],[49.5950135456858],[55.1764143323547],[48.8999096236483],[99.2552867665214],[48.9303513422541],[45.782851122722],[92.1920379976026],[41.9355188343786],[46.7441399423919],[48.9945880849947],[82.0079215955978],[54.9083127810454],[56.1145506453414],[70.2565384603848],[57.9578139587877],[76.3454364082939],[43.776269018809],[96.988814784362],[54.0242374950292],[60.1726117266932],[89.4981499923428],[50.5551352133415],[45.1569142732216],[45.473861009385],[86.5871984611095],[40.0018683934542],[66.561912811091],[78.8706073542424],[52.1706364882529],[78.6028946967799],[91.5449675589667],[58.2346991109606],[54.3347270448909],[94.4711003804518],[68.770516989694],[49.2444127004075],[97.7086693617995],[80.0252590068608],[96.29442738469],[71.7321550374989],[52.0638658819387],[80.9021983716369],[69.4072003434748],[51.6500219577238],[54.9970026129783],[64.5083054732161],[69.8292137875009],[59.9974456329616],[59.5738293588547],[94.8330426365692],[42.8566898052862],[43.4401424519009],[71.0143019218858],[90.7729817712481],[57.6084731481772],[44.1709607509413],[55.2321837004732],[41.1531787070256],[66.4494993820611],[95.5851093177609],[79.6228936564239],[49.3368335968584],[50.1894356822269],[63.8987502955756],[43.9732873583358],[58.808630755764],[41.5441643393859],[76.4846763928035],[90.7653234367312],[85.9850281678165],[77.8416671555094],[61.9002397252503],[87.0108068328847],[65.0032802427099],[65.31389489352],[60.2233717347607],[83.6047102979214],[93.1433768040218],[55.6893235892971],[63.0299378939421],[50.5303403035409],[81.2348501911943],[98.5229244503118],[44.4411954666087],[43.3798964069613],[60.0509862558667],[80.6589299568999],[66.2367581805563],[89.9179762089854],[41.2440618185382],[40.9704350442741],[61.0821885614607],[47.283201646352],[94.6449182945026],[60.7643400730902],[65.0863400433449],[62.0244983429791],[79.7114002917038],[87.8615265825256],[52.0954521730295],[87.8177412466257],[42.2639524988504],[85.8963406012161],[63.516843591485],[92.8217412036546],[61.2100411621562],[74.2916363688685],[60.4948573697237],[94.4670773890678],[77.6880498160307],[67.7482312521744],[57.8829392537742],[57.5303424061006],[70.5844329626594],[78.1065757681086],[48.6298698194049],[98.4472597731454],[81.6002009507819],[52.7470204029164],[69.5675227931534],[70.6377583648163],[92.5534851190146],[42.6306569154924],[80.018645587894],[97.1303619972043],[98.1753697159191],[65.74119811827],[81.546906106995],[50.994187625315],[89.3443977936425],[79.4024584071307],[76.9307421077986],[78.5953861040503]]

    write_log(u_id,15,'admin stats success')
    return jsonify ({'status' : 'ok',
                    'msg':'',
                    'html':render_template('admin_stats.html'),
                    'data':{'data':data,
                            'qs_id':qs_id,
                            'qsets':marked_qsets}})


@app.route('/student_stats.html', methods=['GET'])
def get_student_stats():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token()
    if not result['status'] == 'ok':
        if result['msg'] == 'no token': 
            return redirect(result['target'])   #return html as requester was just a browser
        return jsonify (result)
    #extract params
    u_id = result['data'].u_id
    username = result['data'].username
    qs_id = request.args['qs_id']

    #get the list of marked qs_ids for that student
    marked_qsets = Submission.query.filter_by(u_id=u_id, status='Marked').all()
    marked_qsets = list({x.qs_id for x in marked_qsets})

    #exit if no qs_ids have submissions for this user
    if len(marked_qsets) == 0:
        return jsonify ({'status' : 'cancel',
                        'msg':'you have no marked submissions',
                        'target':'/student_summary.html'})
    
    #set the first qs_id if none was specified
    if qs_id == "init":
        qs_id = marked_qsets[0]

    #get the marks array for the given qs_id
    data = [['result']]
    sub_ans = Submission_Answer.query.filter_by(qs_id=qs_id).all()
    users = {x.u_id for x in sub_ans}
    mark_u_id = 0
    for user in users:
        mark = sum([x.mark for x in sub_ans if x.u_id == user])
        if user == u_id:
            mark_u_id = mark
        data.append([mark])

    #this is fake data, if there was enough data in the system you would just query Submission_Answers and sum all marks for each submission and put into a list here
    data = [['result'],[84.4257772852282],[89.4693179302548],[49.5593304581194],[79.345133048903],[51.9096961003536],[98.8033358634526],[89.2828277401471],[53.0921280077312],[73.2753440911822],[49.5950135456858],[55.1764143323547],[48.8999096236483],[99.2552867665214],[48.9303513422541],[45.782851122722],[92.1920379976026],[41.9355188343786],[46.7441399423919],[48.9945880849947],[82.0079215955978],[54.9083127810454],[56.1145506453414],[70.2565384603848],[57.9578139587877],[76.3454364082939],[43.776269018809],[96.988814784362],[54.0242374950292],[60.1726117266932],[89.4981499923428],[50.5551352133415],[45.1569142732216],[45.473861009385],[86.5871984611095],[40.0018683934542],[66.561912811091],[78.8706073542424],[52.1706364882529],[78.6028946967799],[91.5449675589667],[58.2346991109606],[54.3347270448909],[94.4711003804518],[68.770516989694],[49.2444127004075],[97.7086693617995],[80.0252590068608],[96.29442738469],[71.7321550374989],[52.0638658819387],[80.9021983716369],[69.4072003434748],[51.6500219577238],[54.9970026129783],[64.5083054732161],[69.8292137875009],[59.9974456329616],[59.5738293588547],[94.8330426365692],[42.8566898052862],[43.4401424519009],[71.0143019218858],[90.7729817712481],[57.6084731481772],[44.1709607509413],[55.2321837004732],[41.1531787070256],[66.4494993820611],[95.5851093177609],[79.6228936564239],[49.3368335968584],[50.1894356822269],[63.8987502955756],[43.9732873583358],[58.808630755764],[41.5441643393859],[76.4846763928035],[90.7653234367312],[85.9850281678165],[77.8416671555094],[61.9002397252503],[87.0108068328847],[65.0032802427099],[65.31389489352],[60.2233717347607],[83.6047102979214],[93.1433768040218],[55.6893235892971],[63.0299378939421],[50.5303403035409],[81.2348501911943],[98.5229244503118],[44.4411954666087],[43.3798964069613],[60.0509862558667],[80.6589299568999],[66.2367581805563],[89.9179762089854],[41.2440618185382],[40.9704350442741],[61.0821885614607],[47.283201646352],[94.6449182945026],[60.7643400730902],[65.0863400433449],[62.0244983429791],[79.7114002917038],[87.8615265825256],[52.0954521730295],[87.8177412466257],[42.2639524988504],[85.8963406012161],[63.516843591485],[92.8217412036546],[61.2100411621562],[74.2916363688685],[60.4948573697237],[94.4670773890678],[77.6880498160307],[67.7482312521744],[57.8829392537742],[57.5303424061006],[70.5844329626594],[78.1065757681086],[48.6298698194049],[98.4472597731454],[81.6002009507819],[52.7470204029164],[69.5675227931534],[70.6377583648163],[92.5534851190146],[42.6306569154924],[80.018645587894],[97.1303619972043],[98.1753697159191],[65.74119811827],[81.546906106995],[50.994187625315],[89.3443977936425],[79.4024584071307],[76.9307421077986],[78.5953861040503]]

    write_log(u_id,15,'student stats success')
    return jsonify ({'status' : 'ok',
                    'msg':'',
                    'html':render_template('student_stats.html'),
                    'data':{'data':data,
                            'qs_id':qs_id,
                            'qsets':marked_qsets,
                            'mark_u_id':mark_u_id}})



#############################################################################
#POST route functions, receiving, processing, possibly returning data
#############################################################################
#accept answer submission and save to DB
@app.route('/submit_answers_json', methods=['POST'])
def submit_answers_json():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token()
    if not result['status'] == 'ok':
        if result['msg'] == 'no token': 
            return redirect(result['target'])   #return html as requester was just a browser
        return jsonify (result)
    #extract params
    u_id = result['data'].u_id
    username = result['data'].username
    qs_id = request.get_json()["qs_id"]
    a_data = request.get_json()["a_data"]
    final_flag = request.get_json()["final_flag"]
    status = 'Attempted'
    if final_flag:
        status = 'Completed'

    #check that the submission is legal
    result = Submission.query.filter_by(qs_id=qs_id, u_id=u_id).all()
    if  len(result) > 0 and result[0].status in ['Completed','Marked']:
        write_log(u_id,26,'submit answers failure: quiz status is already complete or marked')
        return jsonify ({'status':'error',
                         'msg':'no further submissions possible'})

    #remove any existing submissions
    Submission.query.filter_by( qs_id=qs_id, u_id=u_id).delete()
    Submission_Answer.query.filter_by(  qs_id=qs_id, u_id=u_id).delete()

    #add submissions to the DB
    new_sub = Submission(qs_id,u_id,status)
    db.session.add(new_sub)

    #add submission_answers
    q_id = 1
    for answer in a_data:
        new_sub_ans = Submission_Answer(qs_id=qs_id,
                                        q_id=q_id,
                                        u_id=u_id,
                                        data=answer,
                                        mark=0,
                                        comment='')
        db.session.add(new_sub_ans)
        q_id += 1 

    # commit changes
    db.session.commit()

    #if all was ok
    write_log(u_id,27,'submit answers success, quiz status: ' + status)
    return jsonify ({'status':'ok', 
                    "msg":""})


#accept marking of submission and save to DB
@app.route('/submit_marks_json', methods=['POST'])
def submit_marks_json():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token()
    if not result['status'] == 'ok':
        if result['msg'] == 'no token': 
            return redirect(result['target'])   #return html as requester was just a browser
        return jsonify (result)
    #extract params
    u_id = result['data'].u_id
    username = result['data'].username
    data = request.get_json()["data"]
    qs_id = data[0]["qs_id"]
    s_u_id = data[0]["s_u_id"]

    #update marks in the DB
    result = Submission.query.filter_by(qs_id=qs_id, u_id=s_u_id).first()
    if result is not None:
        result.status = 'Marked'
        db.session.commit()
        for i in range(1,len(data)):
            result = Submission_Answer.query.filter_by(qs_id=qs_id, q_id=i, u_id=s_u_id).first()
            if result is not None:
                result.mark = float(data[i]["mark"])
                result.comment = data[i]["comment"]
                db.session.commit()

    #if all was ok
    write_log(u_id,30,'submit marks success')
    return jsonify ({'status':'ok', 
                     'msg':''})


#import quiz function for the admin_summary page import feature and the submit edit quiz page
@app.route('/upload_quiz', methods=['POST'])
def upload_quiz():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token()
    if not result['status'] == 'ok':
        if result['msg'] == 'no token': 
            return redirect(result['target'])   #return html as requester was just a browser
        return jsonify (result)
    #extract params
    u_id = result['data'].u_id
    username = result['data'].username
    upload_data = request.get_json()["upload_data"]
    import_flag = request.get_json()["import_flag"]

    #import the qset data into the DB
    qs_id_req = import_quiz_data(u_id, upload_data, import_flag)

    if import_flag:
        write_log(u_id,16,'quiz data import success, qs_id: ' + str(qs_id_req))
    else:
        write_log(u_id,17,'quiz data edits upload success, qs_id: ' + str(qs_id_req))
    return jsonify ({'status':'ok',
                     'msg':'quiz data upload success, qs_id: ' + str(qs_id_req)})



#this is for the import image function in the admin_summary page
@app.route('/upload_image', methods=['POST'])
def upload_image():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token()
    if not result['status'] == 'ok':
        if result['msg'] == 'no token': 
            return redirect(result['target'])   #return html as requester was just a browser
        return jsonify (result)

    if 'file' not in request.files:
        write_log(0,18,'image upload fail: bad form format')
        return jsonify ({'status':'error', 'msg':'bad form format'})
    
    file = request.files['file']
    if file.filename == '':
        write_log(0,19,'image upload fail: no file selected')
        return jsonify ({'status':'error', 'msg':'no file selected'})
    
    file = request.files['file']
    filename = secure_filename(file.filename)
    file.save(app.config['BASE_PATH'] + '/' + app.config['IMAGE_FOLDER'] + '/' + filename)

    write_log(0,20,'image upload success: ' + filename)
    return jsonify ({'status':'ok', 'msg':'Server recieved: ' + filename})



#this is for the export quiz function in the admin_summary page
@app.route('/download_quiz', methods=['POST'])
def download_quiz():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token()
    if not result['status'] == 'ok':
        if result['msg'] == 'no token': 
            return redirect(result['target'])   #return html as requester was just a browser
        return jsonify (result)
    #extract params
    u_id = result['data'].u_id
    username = result['data'].username
    qs_id_req = request.get_json()["qs_id_req"]

    #get the standard qset_json format for each requested qs_id and put in a list to send back to the user
    #so qset_data will be a list of qset jsons, each of which are a list of questions
    qset_data = extract_quiz_data(qs_id_req)

    write_log(u_id,21,'export quiz success, qs_id: ' + str(qs_id_req))
    return jsonify ({'status':'ok',
                     'msg':qs_id_req,
                     'data':qset_data})



#this is for the delete quiz function in the admin_summary page
@app.route('/delete_quiz', methods=['POST'])
def delete_quiz_request():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token()
    if not result['status'] == 'ok':
        if result['msg'] == 'no token': 
            return redirect(result['target'])   #return html as requester was just a browser
        return jsonify (result)
    #extract params
    u_id = result['data'].u_id
    qs_ids = request.get_json()["qs_id_req"]

    delete_quiz(qs_ids)

    # if all was ok
    write_log(u_id,22,'delete quiz success, qs_ids: ' + str(qs_ids))
    return jsonify ({'status':'ok',
                     'msg':qs_ids})


#########################################################
#Non Route functions
#########################################################

#########################################################
#token verification
def verify_token():
    error_target = '/login.html'

    #read token from request header
    token = None
    if not 'Authorization' in request.headers:
        write_log(0,100,'verification failure: no token')
        return {'status':'error',
                'msg': 'no token',
                'target':error_target}

    #try to decode the token
    token = request.headers['Authorization'].encode()
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'])
    except:
        write_log(0,101,'verification failure: bad token encoding')
        return {'status':'error',
                'msg': 'bad token encoding', 
                'target':error_target}

    #verify the token data: u_id
    user = User.query.filter_by(u_id=data['u_id']).first()
    if user is None:
        write_log(0,102,'verification failure: bad token u_id')
        return {'status':'error',
                'msg': 'bad token u_id', 
                'target':error_target}

    #verify the token data: expiry
    #save entry time for take_quiz (exam start time)    
    if re.search("take_quiz\.html$", request.path):
        user.last_req = json.dumps({'path':request.path, 
                                    'args':request.args,
                                    'time':time_now(),
                                    'expired':False})
        db.session.commit()
    
    #set the token length from login
    max_time_s = app.config['LOGIN_MAX_TIME_S']
    #for the submit answers (end of the take quiz page), we use the stored take quiz load time
    #as the test start time to determine whether to accept the submission
    #we just modify the max_time_s variable basically
    if request.path == '/submit_answers_json': 
        #extract the qs_id form the request => was a post request, so use get_json() not args
        qs_id = request.get_json()['qs_id']
        #get the test start time from the DB, we already have the user object
        test_start_time = json.loads(user.last_req)['time']
        #get the test time from the DB
        result = Question_Set.query.filter_by(qs_id=qs_id).first()
        if result is not None:
            max_time_s = result.time*60 + int(test_start_time) - int(data['login_time'])
            #give a 2 minute buffer
            max_time_s = max_time_s + 120

    #do the actual test for an expired request   
    if time_now() - int(data['login_time']) > max_time_s:
        #we have an expired request
        if re.search("\.html$", request.path):
            #save the last .html get requested page
            user.last_req = json.dumps({'path':request.path, 
                                        'args':request.args,
                                        'time':time_now(),
                                        'expired':True})
            db.session.commit()
        write_log(0,103,'verification failure: expired token')
        return {'status':'error',
                'msg':'expired token', 
                'target':error_target}

    #verification success
    return {'status':'ok',
            'data':user}
#########################################################


#this is to load a qset questions via json
#this is used by all the pages that need to load the question set data
def load_qset_json(u_id, username, qs_id, s_u_id, include_submission, include_submitters):
    submission_status = ''
    qset_data = []
    submitters = []
    #set the cancel target
    user = User.query.filter_by(u_id=u_id).first()
    cancel_target = '/student_summary.html'
    if user.admin:
        cancel_target = '/admin_summary.html'
    error_target = '/login.html'

    ######################################
    def get_user_by_status(qs_id, get_one):
        submitters = []
        statuses = ['Completed','Marked','Attempted']
        for status in statuses:
            subs = Submission.query.filter_by(qs_id=qs_id, status=status).all()
            for sub in subs:
                user = User.query.filter_by(u_id=sub.u_id).first()
                if user is not None:
                    if get_one:
                        return user.u_id
                    submitters.append(user.username + ' (' + str(user.u_id) + '), ' + status)
        if get_one:
            return None
        return submitters
    #######################################                

    #get the data from the DB
    if include_submitters == '1':
        #get the list of submissions for this qs_id along with their status
        submitters = get_user_by_status(qs_id, False)
        cancel_target = ""

    #get the standard qset data json format to send to the user
    if include_submission == '1':
        if s_u_id == 'init':    
            #this is sent by the mark_quiz code when it launches as it doesn't have a target s_u_id, so we need to find the next s_u_id to use
            s_u_id = get_user_by_status(qs_id, True)
            #check if we have a suitable s_u_id
            if s_u_id is None:
                write_log(u_id,31,'load quiz with submission json failure: no submissions for that qs_id yet')
                return {'status':'cancel', 
                        'msg':'no submissions yet for that question set', 
                        'target':cancel_target}

        #get the status
        result = Submission.query.filter_by(qs_id=qs_id, u_id=s_u_id).first()
        if result is not None:
            submission_status = result.status
        else:
            submission_status = 'Not Attempted'
        
        #construct qset_data to return
        qset = query2list_of_dict(Question_Set.query.filter_by(qs_id=qs_id).all())
        if len(qset) == 0:
            write_log(u_id,32,'load quiz with submissions json failure: question set does not exist')
            return {'status':'cancel', 
                    'msg':"question set doesn't exist", 
                    'target':cancel_target}
        qset = qset[0]
        
        #add s_u_id and s_unsername
        qset['s_u_id'] = s_u_id
        result = User.query.filter_by(u_id=s_u_id).first()
        if result is None:
            write_log(u_id,33,"load quiz with submissions json failure: user " + s_u_id + " doesn't exist")
            return {'status':'cancel', 
                    'msg':"user " + s_u_id + " doesn't exist", 
                    'target':cancel_target}
        qset['s_username'] = result.username

        #add to qset_data
        qset_data.append(qset)

        #add the questions
        questions = Question.query.filter_by(qs_id=qs_id).all()
        if len(questions) == 0:
            write_log(u_id,34,"load quiz with submissions json failure: no questions in that question set")
            return {'status' : 'cancel', 
                    'msg' : "no questions in that question set",
                    'target':cancel_target}
        
        for question in questions:
            #this is the regular question data
            temp = {'question':[], 'answer':{}}
            temp['question'].append({'q_id':question.q_id, 'marks':question.q_marks})
            temp['question'].extend(json.loads(question.q_data))
            temp['answer']['type'] = question.a_type
            temp['answer']['correct'] = question.a_correct
            if question.a_type == "mc":
                temp['answer']['data'] = json.loads(question.a_data)

            #get the submission_answer data
            result = Submission_Answer.query.filter_by(qs_id=qs_id, q_id=question.q_id, u_id=s_u_id).all()
            answer = ''
            mark = 0
            comment = ''
            if len(result) > 0:
                result = result[0]
                answer = result.data
                mark = result.mark
                comment = result.comment
            temp['answer']['answer'] = answer
            temp['answer']['grade'] = mark
            temp['answer']['comment'] = comment
            #add to the qset list
            qset_data.append(temp)

    else:
        #construct qset_data to return
        qset = query2list_of_dict(Question_Set.query.filter_by(qs_id=qs_id).all())
        if len(qset) == 0:
            write_log(u_id,35,'load quiz json failure: question set does not exist')
            return {'status' : 'cancel', 
                    'msg' : "question set doesn't exist",
                    'target':cancel_target}
        qset = qset[0]
        #add to qset_data
        qset_data.append(qset)
        #add the questions
        questions = Question.query.filter_by(qs_id=qs_id).all()
        if len(questions) == 0:
            write_log(u_id,36,"load quiz json failure: no questions in that question set")
            return {'status':'cancel', 
                    'msg':'no questions in that question set',
                    'target':cancel_target}
        for question in questions:
            #this is the regular question data
            temp = {'question':[], 'answer':{}}
            temp['question'].append({'q_id':question.q_id, 'marks':question.q_marks})
            temp['question'].extend(json.loads(question.q_data))
            temp['answer']['type'] = question.a_type
            temp['answer']['correct'] = question.a_correct
            if question.a_type == "mc":
                temp['answer']['data'] = json.loads(question.a_data)

            #add to the qset list
            qset_data.append(temp)

    #if all was ok
    return {'status':'ok', 
            "msg":"", 
            "data":qset_data, 
            "submitters":submitters, 
            "submission_status":submission_status}



#imports quiz data, overwrites if qs_id already exists, used for the import quiz function 
#and the edit quiz function
def import_quiz_data(u_id, upload_data, import_flag):
    #go through the qset data that is not blank
    qs_id_req = []
    for qset_data in [x for x in upload_data if x != []]:
        if not import_flag:
            #if we are just updating quiz edits, we know the qs_id
            qs_id = qset_data[0]["qs_id"]
        else:
            #we are importing, so try to read the qs_id from the data
            if "qs_id" in qset_data[0]:
                qs_id = qset_data[0]["qs_id"]
            else:
                #here there was no qs_id supplied, so we have to find one
                #determines the next unused qs_id from database
                #this is not a real world soluton, but works for the project
                qs_id = 1
                result = db.engine.execute('SELECT MAX(qs_id) FROM question_set;').fetchone()[0]
                if result is not None:
                    qs_id = result + 1
                    #add it to the DB to minimise contention overwrites from other concurrent users
                    new_qs = Question_Set(qs_id=qs_id, u_id=u_id, enabled=False, topic='', time=-1)
                    db.session.add(new_qs)
                    db.session.commit()

        #get the topic
        topic = "Unspecified"
        if "topic" in qset_data[0]: topic = qset_data[0]["topic"]
        #get the time
        time = -1
        if 'time' in qset_data[0]: time = qset_data[0]["time"]
        #get enabled
        enabled = False
        if 'enabled' in qset_data[0]: enabled = qset_data[0]["enabled"]

        #update the DB for question sets
        #----------------------------------------
        #remove any conflicting data from the DB first
        Question_Set.query.filter_by(qs_id=qs_id).delete()
        Question.query.filter_by(qs_id=qs_id).delete()
        #add qsets to the DB
        new_qs = Question_Set(qs_id, u_id, enabled, topic, time)
        db.session.add(new_qs)
        db.session.commit()

        #add questions to the DB, not reading the q_id field, just assigning it sequentially 
        #----------------------------------------
        q_id = 1
        for q in qset_data[1:]:
            q_marks = 0
            if 'marks' in q["question"][0]:
                q_marks = q["question"][0]["marks"]
            q_data = json.dumps(q["question"][1:])
            a_type = q["answer"]["type"]
            a_correct = q["answer"]["correct"]
            a_data = ""
            if a_type == "mc":
                a_data = json.dumps(q["answer"]["data"])
            #add to the DB
            new_q = Question(qs_id=qs_id, q_id=q_id, q_marks=q_marks, q_data=q_data, a_type=a_type, a_data=a_data, a_correct=a_correct)
            db.session.add(new_q)
            q_id += 1

        # commit changes
        db.session.commit()
        qs_id_req.append(qs_id)

    #success
    return qs_id_req



#extract quiz data for download
def extract_quiz_data(qs_id_req):
    qset_data = []
    qsets = query2list_of_dict(Question_Set.query.all())
    #filter out only the ones requested, too hard to do with sqlalchemy
    qsets = [x for x in qsets if str(x['qs_id']) in qs_id_req]
    for qset in qsets:
        data = [qset]
        questions = Question.query.filter_by(qs_id=qset['qs_id']).all()
        for question in questions:
            temp = {'question':[], 'answer':{}}
            temp['question'].append({'q_id':question.q_id, 'marks':question.q_marks})
            temp['question'].extend(json.loads(question.q_data))
            temp['answer']['type'] = question.a_type
            temp['answer']['correct'] = question.a_correct
            if question.a_type == "mc":
                temp['answer']['data'] = json.loads(question.a_data)
            #add to the qset list
            data.append(temp)
        #add the qset list to the output list
        qset_data.append(data)
    #success
    return qset_data


def delete_quiz(qs_ids):
    # deletes the requested qsets and questions from the DB
    for qs_id in qs_ids:
        Question_Set.query.filter_by(qs_id=qs_id).delete()
        Question.query.filter_by(qs_id=qs_id).delete()
        Submission.query.filter_by(qs_id=qs_id).delete()
        Submission_Answer.query.filter_by(qs_id=qs_id).delete()

    # commit changes
    db.session.commit()



def write_log(u_id,action_id,action):
    #this makes a log entry
    #need to check for errors from the timestamp being the same as the last log entry of the same type (primary key constraint => if get error wait and try again)
    #NOTE: log entry time is in ms since epoch
    cnt = 0
    while True:
        try:
            log_entry = Log(time=int(dt.now().timestamp()*1000), 
                            u_id=u_id, 
                            action_id=action_id, 
                            action=action)
            db.session.add(log_entry)
            db.session.commit()
            break
        except Exception as e:
            print('got log primary key conflict due to time.  Rollback, wait and try again')
            db.session.rollback()
            time.sleep(1)
        cnt += 1
        if cnt > 3:
            #try 3x then give up
            break


def query2list_of_dict(result):
    #this converts the returned object from sqlalchemy to an Python list of dicts
    #the field names are in the dict of each element
    if len(result) == 0:
        return []
    fields = [x.name for x in result[0].__table__.columns]
    return [{field:vars(row)[field] for field in fields} for row in result]


def query2list_of_list(result):
    #this converts the returned object from sqlalchemy to an Python list of lists
    #the first element are the field names
    output = []
    if len(result) == 0:
        return output
    fields = [x.name for x in result[0].__table__.columns]
    output.append(fields)
    for row in result:
        output.append([vars(row)[field] for field in fields])
    return output


def time_now():
    #returns the seconds since epoch
    return int(dt.now().timestamp())


# runs server
if __name__ == "__main__":
    # switch debug to false before assignment submission
    app.run(host='127.0.0.1', port=5000, debug=True)
    #app.run(debug=True)