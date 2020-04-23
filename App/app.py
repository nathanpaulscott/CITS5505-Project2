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


@app.route('/take_quiz.html', methods=['GET'])
def get_take_quiz():
    return render_template('take_quiz.html',
                            username=request.args['username'], 
                            u_id=request.args['u_id'],
                            qset_id=request.args['qset_id'])


@app.route('/edit_quiz.html', methods=['GET'])
def get_edit_quiz():
    return render_template('edit_quiz.html',
                            username=request.args['username'], 
                            u_id=request.args['u_id'],
                            qset_id=request.args['qset_id'])



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
        qset_data = request.get_json()
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



#nathan...testing
##########################################################
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
    #for testing
    return jsonify ({ 'Status' : 'ok', 'msg':'Server recieved: ' + filename})
    #return jsonify ({ 'Status' : 'ok'})


#this is for the export quiz function in the admin_summary page
@app.route('/download_quiz', methods=['POST'])
def download_quiz():
    if request.method == 'POST':
        qset_req = request.get_json()
        #qs_req is a list of qset_ids that need to be returned in one list of qset objects
        #you need to build the qset json for each qset_id, i.e. select out the data from the qset table and q table
        #after this is done and it is saved to qset_data, we send it back
        #here is a sample output for 3 qsets, so it is a list of 3 qset objects
        qset_data = [{ "qset_id":"abc123", "u_id": "the id of the current admin user", "1":{"q_id":"xyz123","question":{"1":{"type":"text","data":"some text for Q1"}, "2":{"type":"image","data":"some_image.jpg"}, "3":{"type":"text","data":"some text"}}, "answer":{"type":"mc","data":["ans1","ans2","ans3","ans4"]}}, "2":{"q_id":"xyz123", "question":{"1":{"type":"text","data":"some text for Q2"}}}, "3":{"q_id":"xyz123", "question":{"1":{"type":"text","data":"some text for Q3"}, "2":{"type":"image","data":"some_image.jpg"}, "3":{"type":"image","data":"some_image.jpg"}, "4":{"type":"text","data":"some text"}, "5":{"type":"image","data":"some_image.jpg"}}, "answer":{"type":"mc","data":["ans1","ans2","ans3","ans4","ans5"]}}, "4":{"q_id":"xyz123", "question":{"1":{"type":"text","data":"some text for Q4"}}}, "5":{"q_id":"xyz123", "question":{"1":{"type":"text","data":"some text for Q5"}}}, "6":{"q_id":"xyz123", "question":{"1":{"type":"text","data":"some text for Q6"}}} }, {	 "qset_id":"aas3d45f", "u_id": "the id of the current admin user", "1":{"q_id":"xyz123", "question":{"1":{"type":"text","data":"some text for Q1"}, "2":{"type":"image","data":"some_image.jpg"}, "3":{"type":"text","data":"some text"}}, "answer":{"type":"mc","data":["ans1","ans2","ans3","ans4"]}}, "2":{"q_id":"xyz123", "question":{"1":{"type":"text","data":"some text for Q2"}}}, "3":{"q_id":"xyz123", "question":{"1":{"type":"text","data":"some text for Q3"}, "2":{"type":"image","data":"some_image.jpg"}, "3":{"type":"image","data":"some_image.jpg"}, "4":{"type":"text","data":"some text"}, "5":{"type":"image","data":"some_image.jpg"}}, "answer":{"type":"mc","data":["ans1","ans2","ans3","ans4","ans5"]}}, "4":{"q_id":"xyz123", "question":{"1":{"type":"text","data":"some text for Q4"}}}, "5":{"q_id":"xyz123", "question":{"1":{"type":"text","data":"some text for Q5"}}}, "6":{"q_id":"xyz123", "question":{"1":{"type":"text","data":"some text for Q6"}}} }, {	 "qset_id":"abc123456", "u_id": "the id of the current admin user", "1":{"q_id":"xyz123", "question":{"1":{"type":"text","data":"some text for Q1"}, "2":{"type":"image","data":"some_image.jpg"}, "3":{"type":"text","data":"some text"}}, "answer":{"type":"mc","data":["ans1","ans2","ans3","ans4"]}}, "2":{"q_id":"xyz123", "question":{"1":{"type":"text","data":"some text for Q2"}}}, "3":{"q_id":"xyz123", "question":{"1":{"type":"text","data":"some text for Q3"}, "2":{"type":"image","data":"some_image.jpg"}, "3":{"type":"image","data":"some_image.jpg"}, "4":{"type":"text","data":"some text"}, "5":{"type":"image","data":"some_image.jpg"}}, "answer":{"type":"mc","data":["ans1","ans2","ans3","ans4","ans5"]}}, "4":{"q_id":"xyz123", "question":{"1":{"type":"text","data":"some text for Q4"}}}, "5":{"q_id":"xyz123", "question":{"1":{"type":"text","data":"some text for Q5"}}}, "6":{"q_id":"xyz123", "question":{"1":{"type":"text","data":"some text for Q6"}}}}]
        #note you can see here an issue wiht using dictionaries, they do not preserve order
        #I am leaning more to using my format option 3 which used more lists
        return jsonify ({'Status' : 'ok','msg':qset_req,'data':qset_data})



#this is for the delete quiz function in the admin_summary page
@app.route('/delete_quiz', methods=['POST'])
def delete_quiz():
    if request.method == 'POST':
        qset_req = request.get_json()
        #qs_req is a list of qset_ids that need to be deleted from the qset table and q table
        #so you just need to do the sql work here
        
        #if all was ok
        return jsonify ({'Status' : 'ok',"msg":qset_req})


#this is to load the admin_summary json data
@app.route('/admin_summary_json', methods=['POST'])
def admin_summary_json():
    if request.method == 'POST':
        u_id = request.get_json()
        #u_id will have the user_id that is asking for the page, right now do nothing, but later we can do something
        #you need to extract the admin summary table json, you will have to get some basic stats also, so need to access more tables here

        #ttemp
        qset_summary =  \
        [
        ["Quiz Id","Topic","Tot Qs","MC Qs","Time(mins)","Owner","Status","Img.Missing","Attempted","Completed","Marked","Score Mean","Score SD"],
        ["x453","Topic A",10,5,50,"u_id","Active",0,4,25,9,59.3,13.4],
        ["y987","Topic B",20,10,100,"u_id","Active",0,8,45,33,68.3,8.4],
        ["x365","Topic A",30,20,150,"u_id","Active",0,3,35,32,62.3,7.4],
        ["d13","Topic A",10,5,30,"u_id","Active",0,0,65,0,-1,-1],
        ["s4","Topic C",15,7,70,"u_id","Active",0,5,25,3,90.3,20.1],
        ["c476","Topic C",12,8,60,"u_id","Pending",4,0,0,0,-1,-1],
        ["x893","Topic A",20,10,80,"u_id","Active",0,2,35,22,70.3,12],
        ["f453","Topic D",20,15,90,"u_id","Closed",0,7,45,45,67.2,8.3],
        ["b323","Topic B",15,10,65,"u_id","Active",0,4,65,60,60.3,9.2],
        ["z43","Topic B",10,5,40,"u_id","Active",0,3,45,30,63.3,11.1],
        ["x443","Topic A",5,5,25,"u_id","Active",0,0,25,2,80.3,22.7]
        ]

        #if all was ok
        return jsonify ({'Status' : 'ok',"msg":"","data":qset_summary})


#this is to load the student_summary json data
@app.route('/student_summary_json', methods=['POST'])
def student_summary_json():
    if request.method == 'POST':
        u_id = request.get_json()
        #u_id will have the user_id that is asking for the page, right now do nothing, but later we can do something
        #you need to extract the student summary table json, you will have to get some basic stats also, so need to access more tables here

        #temp
		#NOTE: the status here is different to the admin status, here it can be : [not attempted, not complete, complete, marked]
        qset_summary =  \
        [
        ["Quiz Id","Topic","Tot Qs","MC Qs","Time(mins)","Status","Score","Score Mean","Score SD"],
        ["x453","Topic A",10,5,50,"Not Attempted",-1,59.3,13.4],
        ["y987","Topic B",20,10,100,"Completed",-1,68.3,8.4],
        ["x365","Topic A",30,20,150,"Marked",85.7,62.3,7.4],
        ["d13","Topic A",10,5,30,"Attempted",-1,-1,-1],
        ["s4","Topic C",15,7,70,"Not Attempted",-1,90.3,20.1],
        ["c476","Topic C",12,8,60,"Marked",65.3,-1,-1],
        ["x893","Topic A",20,10,80,"Completed",-1,70.3,12],
        ["f453","Topic D",20,15,90,"Marked",88.1,67.2,8.3],
        ["b323","Topic B",15,10,65,"Not Atttempted",-1,60.3,9.2],
        ["z43","Topic B",10,5,40,"Marked",46.2,63.3,11.1],
        ["x443","Topic A",5,5,25,"Completed",-1,80.3,22.7]
        ]

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
	{"qset_id":"some alpha-numeric string"},

	{"question":[{"q_id":""},
				 {"type":"text","data":"some text for Q1"},
		  		 {"type":"image","data":"some_image.jpg"},
				 {"type":"text","data":"some text"}], 
	 "answer":{"type":"mc","data":["ans1","ans2","ans3","ans4"]}},
	
	{"question":[{"q_id":""},
				 {"type":"text","data":"some text for Q2"}]},
	
	{"question":[{"q_id":""},
			     {"type":"text","data":"some text for Q3"},
				 {"type":"image","data":"some_image.jpg"},
				 {"type":"image","data":"some_image.jpg"},
				 {"type":"text","data":"some text"}, 
				 {"type":"image","data":"some_image.jpg"}],
	 "answer":{"type":"mc","data":["ans1","ans2","ans3","ans4","ans5"]}},
	
	{"question":[{"q_id":""},
				 {"type":"text","data":"some text for Q4"}]},
	
	{"question":[{"q_id":""},
				 {"type":"text","data":"some text for Q5"}]},
	
	{"question":[{"q_id":""},
				 {"type":"text","data":"some text for Q6"}]}
]
////////////////////////////////////////
NOTE: The browser will add object["user_id"]="the user id" to the incoming json object before upg to the server
NOTE: if the qset_id is missing, then the browser adds this field to the json object using the next available qset_id (say qset_ids are "qs" + a number)
NOTE: the browser will also add the q_id parameter to object[q_seq]["q_id"]="some question id".  Where maybe question id = qset_id + "_" + q_seq, eg. qs456_3
//////////////////////////////////////////////////////
So what gets sent to the server is:
//////////////////////////////////////////////////////
[	
	{"qset_id":"some alpha-numeric string",
    "u_id": "the id of the current admin user"},

	{"question":[{"q_id":""},
				 {"type":"text","data":"some text for Q1"},
		  		 {"type":"image","data":"some_image.jpg"},
				 {"type":"text","data":"some text"}], 
	 "answer":{"type":"mc","data":["ans1","ans2","ans3","ans4"]}},
	
	{"question":[{"q_id":""},
				 {"type":"text","data":"some text for Q2"}]},
	
	{"question":[{"q_id":""},
			     {"type":"text","data":"some text for Q3"},
				 {"type":"image","data":"some_image.jpg"},
				 {"type":"image","data":"some_image.jpg"},
				 {"type":"text","data":"some text"}, 
				 {"type":"image","data":"some_image.jpg"}],
	 "answer":{"type":"mc","data":["ans1","ans2","ans3","ans4","ans5"]}},
	
	{"question":[{"q_id":""},
				 {"type":"text","data":"some text for Q4"}]},
	
	{"question":[{"q_id":""},
				 {"type":"text","data":"some text for Q5"}]},
	
	{"question":[{"q_id":""},
				 {"type":"text","data":"some text for Q6"}]}
]

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
    object_name[3]["question"][1:]

/////////////////////////////////////////////////////
Then at the server this json object needs to go in the question_set table and the question table as so:
/////////////////////////////////////////////////////
table: question_set, one row per question set
col(PK): qset_id => gets the object["qset_id"]
col: qset_name => maybe add a name field to the import for text names, object["qset_name"]
col: owner => object["u_id"]
col: status => give it an initial status of "not active"
col: q_list => write a list of the q_ids, 
    i.e. something like..... json.dumps([object[x]["question"][0]["q_id"] for x in object if x > 0])

table: questions, one row per question
for q_seq in range(1,len(object):
    col(PK): q_id => object[q_seq]["question"]["q_id"]
    col: q_seq => q_seq (numeric)
    col: a_type: object[q_seq]["answer"]["type"]
    col: a_data: json.dumps(object[q_seq]["answer"]["data"])
    col: q_data: object[q_seq]["question"][1:]


 """


#########################################################







# runs server
if __name__ == "__main__":
    # switch debug to false before assignment submission
    app.run(debug=True)