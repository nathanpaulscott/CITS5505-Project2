from flask import Flask, request, jsonify, render_template, redirect, send_from_directory, url_for
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import os
import json
import statistics as st


#from flask_migratey import Migrate

# initialise app
basedir = os.path.abspath(os.path.dirname(__file__))
image_folder = '/static/images'
app = Flask(__name__)



# Database
#app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(basedir, 'db2.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# initialise database
db = SQLAlchemy(app)

# tables in database - move each to separate file
class User(db.Model):
    __tablename__ = 'user'
    u_id = db.Column(db.Integer, primary_key=True)
    admin = db.Column(db.Boolean)
    username = db.Column(db.String(10), unique=True )
    password = db.Column(db.String(10))
    #submissions = db.relationship('Submission', backref='user', lazy=True)
    #submission_answers = db.relationship('Submission_Answer', backref='user', lazy=True)

    # creates a user
    def __init__(self, admin, username, password):
        self.admin = admin
        self.username = username
        self.password = password

class Question_Set(db.Model):
    __tablename__ = 'question_set'
    qs_id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(30))
    enabled = db.Column(db.Boolean)
    topic = db.Column(db.String(50))
    time = db.Column(db.Integer)
    #q_ids = db.relationship('Question', backref='question_set', lazy=True)
    #u_ids = db.relationship('Submission', backref='question_set', lazy=True)
    #submissions = db.relationship('Submission', backref='question_set', lazy=True)
    #submission_answers = db.relationship('Submission_Answer', backref='question_set', lazy=True)

    # creates a question set
    def __init__(self, qs_id, author, enabled, topic, time):
        self.qs_id = qs_id
        self.author = author
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
    #submission_answers = db.relationship('Submission_Answer', backref='question', lazy=True)

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
    #total_mark = db.relationship('Submission_Answer', backref='submission', lazy=True)
    #max_mark = db.relationship('Question', backref='submission', lazy=True)

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
    action_id = db.Column(db.Integer, primary_key=True)
    u_id = db.Column(db.Integer)
    action = db.Column(db.String(30))


'''
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
'''


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



#this is to load the student_summary basic template
@app.route('/student_summary.html', methods=['GET'])
def get_student_summary():
    return render_template('student_summary.html',
                            username=request.args['username'], 
                            u_id=request.args['u_id'])


#this is to load the student_summary json data
@app.route('/student_summary_json', methods=['POST'])
def student_summary_json():
    if request.method == 'POST':
        u_id = request.get_json()["u_id"]
        #this is the output data header to be passed back to the client, list of lists
        qset_summary =  \
        [["Status","Quiz Id","Topic","Tot Qs","MC Qs","Time(mins)","Marks Available","Marks Attained","Marks Mean","Marks SD"]]

        #fills qset_summary from the DB
        qsets = Question_Set.query.all()
        #will have qs_id, author, enabled, topic, time
        #need to fill the rest of the fields ["Status","Tot Qs","MC Qs","Time(mins)","Score","Score Mean","Score SD"]
        for qset in qsets:
            qs_id = qset.qs_id
            # get num questions
            qset.tot_qs = len(Question.query.filter_by(qs_id=qs_id).all())
            qset.mc_qs = len(Question.query.filter_by(qs_id=qs_id, a_type='mc').all())
            # get the student status for the qset
            result = Submission.query.filter_by(qs_id=qs_id, u_id=u_id).all()
            if len(result) == 0:
                qset.status = 'Not Attempted'
            else:
                qset.status = result.status
            #get the marks available
            result = Question.query.filter_by(qs_id=qs_id).all()
            qset.marks_avail = sum([x.q_marks for x in result])
            #get the marks given
            result = Submission_Answer.query.filter_by(qs_id=qs_id,u_id=u_id).all()
            qset.marks = -1
            if len(result) > 0:
                qset.marks = sum([x.mark for x in result])
            #get the marks stats
            result = Submission_Answer.query.filter_by(qs_id=qs_id).all()
            marks = []
            qset.marks_mean = -1
            qset.marks_sd = -1
            for user in set([x.u_id for x in result]):
                marks.append(sum([x.mark for x in result if x.u_id == user]))
            if len(marks) > 0:
                qset.marks_mean = st.mean(marks)
                qset.marks_sd = st.stdev(marks)

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
        return jsonify ({'Status' : 'ok',
                        'msg':'',
                        'data':qset_summary})



@app.route('/admin_summary.html', methods=['GET'])
def get_admin_summary():
    return render_template('admin_summary.html',
                            username=request.args['username'], 
                            u_id=request.args['u_id'])


#this is to load the admin_summary json data
@app.route('/admin_summary_json', methods=['POST'])
def admin_summary_json():
    if request.method == 'POST':
        u_id = request.get_json()["u_id"]
        #this is the output data header to be passed back to the client, list of lists
        qset_summary =  \
        [["Quiz Id","Marked","Completed","Attempted","Topic","Tot Qs","MC Qs","Time(mins)","Owner","Enabled","Img.Missing","Marks Available","Mark Mean","Mark SD"]]

        #fills qset_summary from the DB
        qsets = Question_Set.query.all()
        #will have qs_id, author, enabled, topic, time
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
            qset.marks_mean = -1
            qset.marks_sd = -1
            for user in set([x.u_id for x in result]):
                marks.append(sum([x.mark for x in result if x.u_id == user]))
            if len(marks) > 0:
                qset.marks_mean = st.mean(marks)
                qset.marks_sd = st.stdev(marks)
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
            for root,dirs,files in os.walk(basedir + '/' + image_folder, topdown=True):
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
                                qset.author,
                                qset.enabled,
                                qset.img_missing,
                                qset.marks_avail,
                                qset.marks_mean,
                                qset.marks_sd])

        #if all was ok
        return jsonify ({'Status' : 'ok',"msg":"","data":qset_summary})



# import quiz function in the admin_summary page
@app.route('/upload_quiz', methods=['POST'])
def upload_quiz():
    if request.method == 'POST':
        upload_data = request.get_json()["upload_data"]
        u_id = request.get_json()["u_id"]

        #go through the qset data that is not blank
        for qset_data in [x for x in upload_data if x != []]:
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
                    new_qs = Question_Set(qs_id,u_id,False,'',-1)
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
            #add qsets to the DB, ignores the author field and uses the uploader u_id
            new_qs = Question_Set(qs_id,u_id,enabled,topic,time)
            db.session.add(new_qs)
            # commit changes
            db.session.commit()
            #add questions to the DB, not reading the qs_id field, just assigning it sequentially 
            q_id = 1
            for q in qset_data[1:]:
                q_marks = -1
                if 'marks' in q["question"][0]:
                    q_marks = q["question"][0]["marks"]
                q_data = json.dumps(q["question"][1:])
                a_type = q["answer"]["type"]
                a_correct = q["answer"]["correct"]
                a_data = ""
                if a_type == "mc":
                    a_data = json.dumps(q["answer"]["data"])
                #add to the DB
                new_q = Question(qs_id,q_id,q_marks,q_data,a_type,a_data,a_correct)
                db.session.add(new_q)
                q_id += 1

            # commit changes
            db.session.commit()

        return jsonify ({ 'Status' : 'ok'})



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



#this is for the export quiz function in the admin_summary page
@app.route('/download_quiz', methods=['POST'])
def download_quiz():
    if request.method == 'POST':
        qset_id_req = request.get_json()["qset_id_req"]
        
        #get the standard qset_json format for each requested qset_id and put in a list to send back to the user
        #so qset_data will be a list of qset jsons, each of which are a list of questions
        qset_data = []
        qsets = query2list_of_dict(Question_Set.query.all())
        #filter out only the ones requested, too hard to do with sqlalchemy
        qsets = [x for x in qsets if str(x['qs_id']) in qset_id_req]
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

        return jsonify ({'Status' : 'ok','msg':qset_id_req,'data':qset_data})



#this is for the delete quiz function in the admin_summary page
@app.route('/delete_quiz', methods=['POST'])
def delete_quiz():
    if request.method == 'POST':
        qset_id_req = request.get_json()["qset_id_req"]

        #deletes the requested qsets and questions from the DB
        for qs_id in qset_id_req:
            Question_Set.query.filter_by(qs_id=qs_id).delete()
            Question.query.filter_by(qs_id=qs_id).delete()

        # commit changes
        db.session.commit()

        #if all was ok
        return jsonify ({'Status' : 'ok',"msg":qset_id_req})



@app.route('/manage_users.html', methods=['GET'])
def get_manage_users():
    return render_template('manage_users.html',
                            username=request.args['username'], 
                            u_id=request.args['u_id'])


#this is to load the manage_users json data
@app.route('/manage_users_json', methods=['POST'])
def manage_users_json():
    if request.method == 'POST':
        u_id = request.get_json()["u_id"]
        users_data = [["User_Id", "Role", "Username", "Password"]]

        ##fill the users_data from the DB
        users = User.query.all()
        for user in users:
            users_data.append([user.u_id, 
                              "Teacher" if user.admin else "Student", 
                              user.username,
                              user.password])

        #if all was ok
        return jsonify ({'Status' : 'ok',"msg":"","data":users_data})




@app.route('/edit_quiz.html', methods=['GET'])
def get_edit_quiz():
    return render_template('edit_quiz.html',
                            username=request.args['username'], 
                            u_id=request.args['u_id'],
                            qset_id=request.args['qset_id'])



# accept quiz edits and save to DB
@app.route('/submit_qset_edits_json', methods=['POST'])
def submit_qset_edits_json():
    if request.method == 'POST':
        qset_data = request.get_json()["qset_data"]

        #DB action required!!
        #write the contents of qset_data to the DB

        #if all was ok
        return jsonify ({'Status' : 'ok', "msg" : ""})






#for a student to actually do the quiz and make a submission
@app.route('/take_quiz.html', methods=['GET'])
def get_take_quiz():
    return render_template('take_quiz.html',
                            username=request.args['username'], 
                            u_id=request.args['u_id'],
                            qset_id=request.args['qset_id'])



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





#this is to load a qset via json
#this route is used by all the pages that need to load the question set data
@app.route('/load_qset_json', methods=['POST'])
def load_qset_json():
    if request.method == 'POST':
        u_id = request.get_json()["u_id"]
        username = request.get_json()["username"]
        qs_id = request.get_json()["qset_id"]
        #for the review submission by student case
        s_u_id = u_id
        #for marking submission
        if "s_u_id" in request.get_json():
            s_u_id = request.get_json()["s_u_id"]
        #for marking submission of a particular s_u_id
        include_submission = request.get_json()["include_submission"]
        #for the list of submissions to choose when marking
        include_submitters = request.get_json()["include_submitters"]
        qset_data = []
        submitters = []
        
        #get the data from the DB
        if include_submitters == "1":
            #get the list of submissions for this qs_id along with their status
            submitters = []
            statuses = ['Completed','Marked','Attempted']
            for status in statuses:
                s_users = Submission.query.filter_by(qs_id=qs_id,status=status).all()
                for s_user in s_users:
                    s_username = User.query.get(s_user.u_id).username
                    submitters.append(s_username + ' (' + str(s_user.u_id) + '), ' + status)

        #get the standard qset data json format to send to the user
        if include_submission == '1':
            if s_u_id == 'init':
                #find the next s_u_id to use
                statuses = ['Completed','Marked','Attempted']
                for status in statuses:
                    s_users = Submission.query.filter_by(qs_id=qs_id,status=status).all()
                    if len(s_users) > 0:
                        s_u_id = s_users.u_id
                        s_username = User.query.get(s_u_id).username
                        break
            #check if we have a suitable s_u_id
            if s_u_id == 'init':
                return jsonify ({'Status' : 'nok', "msg" : "no submissions yet for that question set"})
            #construct qset_data to return
            qset = query2list_of_dict(Question_Set.query.filter_by(qs_id=qs_id).all())
            if len(qset) == 0:
                return jsonify ({'Status' : 'nok', 'msg' : "question set doesn't exist"})
            qset = qset[0]
            #add s_u_id and s_unsername
            qset['s_u_id'] = s_u_id
            qset['s_username'] = s_username
            #add to qset_data
            qset_data.append(qset)
            #add the questions
            questions = Question.query.filter_by(qs_id=qs_id).all()
            if len(questions) == 0:
                return jsonify ({'Status' : 'nok', 'msg' : "no questions in that question set"})
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
                mark = -1
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
                return jsonify ({'Status' : 'nok', 'msg' : "question set doesn't exist"})
            qset = qset[0]
            #add to qset_data
            qset_data.append(qset)
            #add the questions
            questions = Question.query.filter_by(qs_id=qs_id).all()
            if len(questions) == 0:
                return jsonify ({'Status' : 'nok', 'msg' : "no questions in that question set"})
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
        return jsonify ({'Status' : 'ok', "msg" : "", "data" : qset_data, "submitters" : submitters})




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



# runs server
if __name__ == "__main__":
    # switch debug to false before assignment submission
    app.run(debug=True)