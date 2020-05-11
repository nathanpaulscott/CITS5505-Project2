from flask import Flask, request, jsonify, render_template, redirect, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash, safe_str_cmp
import jwt
#---------------------------
import re
import os
import json
import statistics as st
from datetime import datetime as dt
import threading as th
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



#########################################################
#########################################################
# #run this if request is for a protected page, 
#verify the user from the token
def verify_token(request):
    #read token from request header
    token = None
    if not 'Authorization' in request.headers:
        write_log(0,100,'verification failure: no token')
        return {'status':'error','msg': 'no token'}

    #try to decode the token
    token = request.headers['Authorization'].encode()
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'])
    except:
        write_log(0,101,'verification failure: bad token encoding')
        return {'status':'error','msg': 'bad token encoding'}

    #verify the token data: u_id
    user = User.query.filter_by(u_id=data['u_id']).first()
    if user is None:
        write_log(0,102,'verification failure: bad token u_id')
        return {'status':'error','msg': 'bad token u_id'}

    #verify the token data: expiry
    #save entry time for take_quiz (exam start time)    
    if re.search("take_quiz\.html$", request.path):
        user.last_req = json.dumps({'path':request.path, 
                                    'args':request.args,
                                    'time':time_now(),
                                    'expired':False})
        db.session.commit()
    
    #set the token length from login, it uses the value set by app for all cases except
    #for the take quiz answer submission, where we allow submissions up to the 
    #allotted quiz time since the loading of the take_quiz.html page
    max_time_s = app.config['LOGIN_MAX_TIME_S']
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
        
    if time_now() - int(data['login_time']) > max_time_s:
        #save the last .html get requested page (not the post *_json pages)
        if re.search("\.html$", request.path):
            user.last_req = json.dumps({'path':request.path, 
                                        'args':request.args,
                                        'time':time_now(),
                                        'expired':True})
            db.session.commit()
        write_log(0,103,'verification failure: expired token')
        return {'status':'error','msg': 'expired token'}

    #verification success
    return {'status':'ok','data':user}
#########################################################
#########################################################

            



# url routing
# get action performed when user navigates to that url
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
    login_timeout = 30*3600
    if request.method == 'GET':
        write_log(0,3,'login page entry')
        return render_template('login.html')
    
    elif request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]

    #verify the user exists and the password is correct 
    # and log them in with a login flag in the DB
    #also get the admin status and u_id from the DB
    user = User.query.filter_by(username=username).first()
    if user is None:
        #no username found
        write_log(0,4,'failed login from username not found')
        error = 'Username {} not found'.format(username)
        return jsonify ({"status":"error", "msg":error,"target":"./register.html"})
    
    if user.login_att is None:
        user.login_att = 1
        db.session.commit()
    elif user.login_att > 5:
        #make another page here to inform the user to stop trying and contact admin
        write_log(user.u_id,5,'failed login from too many failed attempts')
        error = 'Too many failed login attempts'
        return jsonify ({"status":"error", "msg":error,"target":"./landing.html"})

    #check the password
    if not check_password_hash(user.password, password):
        #wrong password
        user.login_att = user.login_att + 1
        db.session.commit()
        write_log(user.u_id,6,'failed login from incorrect password')
        error = 'incorrect password'
        return jsonify ({"status":"error", "msg":error,"target":"./login.html"})

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
    #target = url_for('get_student_summary', username=user.username, u_id=user.u_id) 
    target = url_for('get_student_summary') 
    if user.admin:
        #target = url_for('get_admin_summary', username=user.username, u_id=user.u_id) 
        target = url_for('get_admin_summary') 

    return jsonify({'status':'ok',
                    'target':target,
                    'admin':user.admin,
                    'data':{'token':token.decode('utf-8'),
                            'username':user.username,
                            'u_id':user.u_id}})
        


@app.route('/register.html', methods=['GET','POST'])
def register():
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

        # check if username taken
        result = User.query.filter_by(username=username).first()
        if result is not None:
            error = 'User {} is already registered.'.format(username)
            write_log(0,9,'failed registration as username "' + username + '" is taken')
            return jsonify ({ "status" : error})
        else:
            #determines the next unused u_id from database
            #this is not a real world soluton, but works for the project
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

            #now log the user in
            return redirect(url_for('get_login'))




@app.route('/admin_stats.html', methods=['GET'])
def get_admin_stats():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token(request)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})

    u_id = result['data'].u_id
    username = result['data'].username

    write_log(u_id,15,'admin stats success')
    return jsonify ({'status' : 'ok',
                    'msg':'',
                    'html':render_template('admin_stats.html'),
                    'data':{'data':{}}})





@app.route('/student_stats.html', methods=['GET'])
def get_student_stats():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token(request)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})

    u_id = result['data'].u_id
    username = result['data'].username

    write_log(u_id,15,'student stats success')
    return jsonify ({'status' : 'ok',
                    'msg':'',
                    'html':render_template('student_stats.html'),
                    'data':{'data':{}}})





#this is to load the student_summary basic template
@app.route('/student_summary.html', methods=['GET'])
def get_student_summary():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token(request)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})
    
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
        result = Submission_Answer.query.filter_by(qs_id=qs_id,u_id=u_id).all()
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
    result = verify_token(request)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})

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
    result = verify_token(request)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})

    u_id = result['data'].u_id
    username = result['data'].username
    qs_id = request.args['qs_id']
    s_u_id = u_id
    include_submission = request.args['include_submission']
    include_submitters = request.args['include_submitters']
    
    result = load_qset_json(u_id, username, qs_id, s_u_id, include_submission, include_submitters)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})

    write_log(u_id,15,'edit quiz success')
    return jsonify ({'status' : 'ok',
                    'msg':'',
                    'html':render_template('edit_quiz.html'),
                    'data':{'data':result['data']}})






@app.route('/manage_users.html', methods=['GET'])
def get_manage_users():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token(request)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})

    u_id = result['data'].u_id
    username = result['data'].username

    ##fill the users_data from the DB
    users_data = [["User_Id", "Role", "Username", "Password"]]
    users = User.query.all()
    for user in users:
        users_data.append([user.u_id, 
                            "Teacher" if user.admin else "Student", 
                            user.username,
                            user.password])

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
    result = verify_token(request)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})

    u_id = result['data'].u_id
    username = result['data'].username
    qs_id = request.args['qs_id']
    preview_flag = request.args['preview_flag']
    s_u_id = u_id
    include_submission = request.args['include_submission']
    include_submitters = request.args['include_submitters']
    
    result = load_qset_json(u_id, username, qs_id, s_u_id, include_submission, include_submitters)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})
    
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




# accept answer submission and save to DB
@app.route('/submit_answers_json', methods=['POST'])
def submit_answers_json():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token(request)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})

    u_id = result['data'].u_id
    username = result['data'].username
    qs_id = request.get_json()["qs_id"]
    a_data = request.get_json()["a_data"]
    final_flag = request.get_json()["final_flag"]
    status = 'Attempted'
    if final_flag:
        status = 'Completed'

    #check that the submission is legal
    result = Submission.query.filter_by(qs_id=qs_id,u_id=u_id).all()
    if len(result) > 0 and result[0].status in ['Completed','Marked']:
        write_log(u_id,26,'submit answers failure: quiz status is already complete or marked')
        return jsonify ({'status' : 'error', 'msg' : 'no further submissions possible'})

    #remove any existing submissions
    Submission.query.filter_by(qs_id=qs_id,u_id=u_id).delete()
    Submission_Answer.query.filter_by(qs_id=qs_id,u_id=u_id).delete()

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
    return jsonify ({'status':'ok', "msg":""})




#for student to review a submission and marks if available
@app.route('/review_quiz.html', methods=['GET'])
def get_review_quiz():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token(request)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})
    
    u_id = result['data'].u_id
    username = result['data'].username
    qs_id = request.args['qs_id']
    s_u_id = u_id
    include_submission = request.args['include_submission']
    include_submitters = request.args['include_submitters']

    result = load_qset_json(u_id, username, qs_id, s_u_id, include_submission, include_submitters)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})
    
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
    result = verify_token(request)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})
  
    u_id = result['data'].u_id
    username = result['data'].username
    qs_id = request.args['qs_id']
    s_u_id = request.args['s_u_id']
    include_submission = request.args['include_submission']
    include_submitters = request.args['include_submitters']

    result = load_qset_json(u_id, username, qs_id, s_u_id, include_submission, include_submitters)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})

    write_log(u_id,29,'mark quiz success')
    return jsonify ({'status' : 'ok',
                    'msg':'',
                    'html':render_template('mark_quiz.html'),
                    'data':{'data':result['data'],
                            'submitters':result['submitters'],
                            'submission_status':result['submission_status']}})




# accept answer submission and save to DB
@app.route('/submit_marks_json', methods=['POST'])
def submit_marks_json():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token(request)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})

    u_id = result['data'].u_id
    username = result['data'].username
    data = request.get_json()["data"]
    qs_id = data[0]["qs_id"]
    s_u_id = data[0]["s_u_id"]

    #update marks in the DB
    result = Submission.query.filter_by(qs_id=qs_id,u_id=s_u_id).first()
    if result is not None:
        result.status = 'Marked'
        db.session.commit()
        for i in range(1,len(data)):
            result = Submission_Answer.query.filter_by(qs_id=qs_id,q_id=i,u_id=s_u_id).first()
            if result is not None:
                result.mark = float(data[i]["mark"])
                result.comment = data[i]["comment"]
                db.session.commit()

    #if all was ok
    write_log(u_id,30,'submit marks success')
    return jsonify ({'status' : 'ok', "msg" : ""})





# import quiz function for the admin_summary page import feature and the submit edit quiz page
@app.route('/upload_quiz', methods=['POST'])
def upload_quiz():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token(request)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})
    
    u_id = result['data'].u_id
    username = result['data'].username
    upload_data = request.get_json()["upload_data"]
    import_flag = request.get_json()["import_flag"]

    #go through the qset data that is not blank
    qs_id_req = []
    for qset_data in [x for x in upload_data if x != []]:
        #if we are just updating quiz edits, we know the qs_id
        if not import_flag:
            qs_id = qset_data[0]["qs_id"]
        else:
            #get the qs_id
            if "qs_id" in qset_data[0]:
                qs_id = qset_data[0]["qs_id"]
            else:
                #determines the next unused qs_id from database
                #this is not a real world soluton, but works for the project
                qs_id = 1
                result = db.engine.execute(
                    'SELECT MAX(qs_id) FROM question_set;'
                ).fetchone()[0]
                if result is not None:
                    qs_id = result + 1
                    #add it to the DB to minimise contention overwrites from other concurrent users
                    new_qs = Question_Set(qs_id=qs_id,
                                        u_id=u_id,
                                        enabled=False,
                                        topic='',
                                        time=-1)
                    db.session.add(new_qs)
                    db.session.commit()

        #get the topic
        topic = "Unspecified"
        if "topic" in qset_data[0]:
            topic = qset_data[0]["topic"]

        #get the time
        time = -1
        if 'time' in qset_data[0]:
            time = qset_data[0]["time"]

        #get enabled
        enabled = False
        if 'enabled' in qset_data[0]:
            enabled = qset_data[0]["enabled"]

        #update the DB
        #----------------------------------------
        #remove any conflicting data from the DB first
        Question_Set.query.filter_by(qs_id=qs_id).delete()
        Question.query.filter_by(qs_id=qs_id).delete()

        #add qsets to the DB, ignores the u_id field in the data and uses the uploader u_id
        new_qs = Question_Set(qs_id,u_id,enabled,topic,time)
        db.session.add(new_qs)

        # commit changes
        db.session.commit()

        #add questions to the DB, not reading the qs_id field, just assigning it sequentially 
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
            new_q = Question(qs_id=qs_id,
                            q_id=q_id,
                            q_marks=q_marks,
                            q_data=q_data,
                            a_type=a_type,
                            a_data=a_data,
                            a_correct=a_correct)
            db.session.add(new_q)
            q_id += 1

        # commit changes
        db.session.commit()
        qs_id_req.append(qs_id)

    if import_flag:
        write_log(u_id,16,'quiz data import success, qs_id: ' + str(qs_id_req))
    else:
        write_log(u_id,17,'quiz data edits upload success, qs_id: ' + str(qs_id_req))

    return jsonify ({'status':'ok','msg':'quiz data upload success, qs_id: ' + str(qs_id_req)})





#this is for the import image function in the admin_summary page
@app.route('/upload_image', methods=['POST'])
def upload_image():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token(request)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})

    if 'file' not in request.files:
        write_log(0,18,'image upload fail: bad form format')
        return jsonify ({ 'status' : 'error', 'msg':'bad form format'})
    file = request.files['file']
    if file.filename == '':
        write_log(0,19,'image upload fail: no file selected')
        return jsonify ({ 'status' : 'error', 'msg':'no file selected'})
    file = request.files['file']
    filename = secure_filename(file.filename)
    file.save(app.config['BASE_PATH'] + '/' + app.config['IMAGE_FOLDER'] + '/' + filename)

    write_log(0,20,'image upload success: ' + filename)
    return jsonify ({ 'status' : 'ok', 'msg':'Server recieved: ' + filename})





#this is for the export quiz function in the admin_summary page
@app.route('/download_quiz', methods=['POST'])
def download_quiz():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token(request)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})
    
    u_id = result['data'].u_id
    username = result['data'].username
    qs_id_req = request.get_json()["qs_id_req"]

    #get the standard qset_json format for each requested qs_id and put in a list to send back to the user
    #so qset_data will be a list of qset jsons, each of which are a list of questions
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

    write_log(u_id,21,'export quiz success, qs_id: ' + str(qs_id_req))
    return jsonify ({'status' : 'ok','msg':qs_id_req,'data':qset_data})





#this is for the delete quiz function in the admin_summary page
@app.route('/delete_quiz', methods=['POST'])
def delete_quiz():
    #does the jwt verification => input is the token, output is the user object
    result = verify_token(request)
    if not result['status'] == 'ok':
        return jsonify ({'status' : 'error', 'msg':result['msg'], 'target':'/login.html'})

    u_id = result['data'].u_id
    username = result['data'].username
    qs_id_req = request.get_json()["qs_id_req"]

    #deletes the requested qsets and questions from the DB
    for qs_id in qs_id_req:
        Question_Set.query.filter_by(qs_id=qs_id).delete()
        Question.query.filter_by(qs_id=qs_id).delete()
        Submission.query.filter_by(qs_id=qs_id).delete()
        Submission_Answer.query.filter_by(qs_id=qs_id).delete()

    # commit changes
    db.session.commit()

    #if all was ok
    write_log(u_id,22,'delete quiz success, qs_ids: ' + str(qs_id_req))
    return jsonify ({'status' : 'ok',"msg":qs_id_req})





#########################################################
#########################################################
#########################################################

#this is to load a qset via json
#this is used by all the pages that need to load the question set data
def load_qset_json(u_id, username, qs_id, s_u_id, include_submission, include_submitters):
    submission_status = ''
    qset_data = []
    submitters = []

    def get_user_by_status(qs_id, get_one):
        submitters = []
        statuses = ['Completed','Marked','Attempted']
        for status in statuses:
            subs = Submission.query.filter_by(qs_id=qs_id,status=status).all()
            for sub in subs:
                user = User.query.filter_by(u_id=sub.u_id).first()
                if user is not None:
                    if get_one:
                        return user.u_id
                    submitters.append(user.username + ' (' + str(user.u_id) + '), ' + status)
        if get_one:
            return None
        return submitters
                    

    #get the data from the DB
    if include_submitters == "1":
        #get the list of submissions for this qs_id along with their status
        submitters = get_user_by_status(qs_id, False)
    
    #get the standard qset data json format to send to the user
    if include_submission == '1':
        if s_u_id == 'init':    
            #this is sent by the mark_quiz code when it launches as it doesn't have a target s_u_id, so we need to find the next s_u_id to use
            s_u_id = get_user_by_status(qs_id, True)
            #check if we have a suitable s_u_id
            if s_u_id is None:
                write_log(u_id,31,'load quiz with submission json failure: no submissions for that qs_id yet')
                return {'status':'error', 'msg':'no submissions yet for that question set'}

        #get the status
        result = Submission.query.filter_by(qs_id=qs_id,u_id=s_u_id).first()
        if result is not None:
            submission_status = result.status
        else:
            submission_status = 'Not Attempted'
        
        #construct qset_data to return
        qset = query2list_of_dict(Question_Set.query.filter_by(qs_id=qs_id).all())
        if len(qset) == 0:
            write_log(u_id,32,'load quiz with submissions json failure: question set does not exist')
            return {'status':'error', 'msg':"question set doesn't exist"}
        qset = qset[0]
        
        #add s_u_id and s_unsername
        qset['s_u_id'] = s_u_id
        result = User.query.filter_by(u_id=s_u_id).first()
        if result is None:
            write_log(u_id,33,"load quiz with submissions json failure: user " + s_u_id + " doesn't exist")
            return {'status':'error', 'msg':"user " + s_u_id + " doesn't exist"}
        qset['s_username'] = result.username

        #add to qset_data
        qset_data.append(qset)

        #add the questions
        questions = Question.query.filter_by(qs_id=qs_id).all()
        if len(questions) == 0:
            write_log(u_id,34,"load quiz with submissions json failure: no questions in that question set")
            return {'status' : 'error', 'msg' : "no questions in that question set"}
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
            result = Submission_Answer.query.filter_by(qs_id=qs_id,q_id=question.q_id,u_id=s_u_id).all()
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
            return {'status' : 'error', 'msg' : "question set doesn't exist"}
        qset = qset[0]

        #add to qset_data
        qset_data.append(qset)

        #add the questions
        questions = Question.query.filter_by(qs_id=qs_id).all()
        if len(questions) == 0:
            write_log(u_id,36,"load quiz json failure: no questions in that question set")
            return {'status' : 'error', 'msg' : "no questions in that question set"}
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



#this code will periodically check users login status or usage status and log them out if they are dormant
#the issue with this is that it locks the code and you can't quit the code, the code runs, but you can't quit
'''
def check_login_status(cancel_flag):
    #this periodically checks users login status and kicks them out if they have been logged in too long
    if not cancel_flag.is_set():
        #start the timer again
        th.Timer(15*3600, check_login_status, [cancel_flag]).start()
        #check that the user has made some actions in the last 60mins otherwise logout
        users = User.query.filter_by(login_status='logged in').all()
        for user in users:
            log = Log.query.filter_by(u_id=user.u_id).order_by(Log.time.desc()).first()
            if log is not None:
                if time_now() - log.time > 60*3600:
                    user.login_status = 'logged out'
                    db.session.commit()
            elif user.login_time is not None:
                if time_now() - user.login_time > 60*3600:
                    user.login_status = 'logged out'
                    db.session.commit()
            

#start the periodic timer
cancel_flag = th.Event()
check_login_status(cancel_flag)
'''


# runs server
if __name__ == "__main__":
    # switch debug to false before assignment submission
    app.run(debug=True)