# CITS5505-Project2
 Quiz System


To run the server: 
1. In a terminal, navigate to Back End
2. Type "python app.py"
3. Click the link that appears in the terminal

---
## Nathan's Comments  
Right now, I have the main functionality of the front end of the tool working as decribed below.  

### Landing  
You can register, then login wiht yoru username and password.  You go to the student area if you are a student, go to the teacher area if you are a teacher.

### Student  

* you get the summary of quizes available to you and your status with them, you can click on one and it will either take you to take the quiz if it has not been completed yet, or to review your submission if it has been completed.
 + The review submission will show you any teacher marks and comments and doesn't allow you to change anything.
 + The take quiz part allows you to submit answers, it only considers it compelte if you answer all questions.

### Teacher  

* you get the summary of all quizes and their status and stats, you can either edit a quiz, mark a quiz, manage uers or use the bulk quiz import,export, delete buttons.
 + The edit quiz section allows you to edit the selected quiz, you can add/remove text/image sections and move their order.  Yuo can also change the answer type and the multi-choice options.
 + The mark quiz, brings up the first unmarked submission of the selected quiz_id that the DB finds.  The teacher can choose another submission to mark from a list of all submissions (ranked by unmarked first) or just press the next button to move on to the next unmarked submission.  Clicking submit saves the marking along the way.
 + The manage users page brings up a list of the users in the system (user_id, username, role) and the admin can add/remove users or modify roles.
 
 ---
 
 ## Outstanding work  
 The following are outstanding items that are required for the project to be submittable:  
 
 * add / delete / modify user code needs to be written ~ 1/2 day (Nathan)
 * add a next button to the marking page ~ 1/2 day (Nathan)
 * DB integration, all DB tables and DB interaction logic/code needs to be done ~ 1 week (Jack, I will help needed).  This is in the critical path right now.  Currently all front-end data is sent to the server or recieved from the server via ajax requests successfully, however the DB function is not there yet.
 (student reading + taking quizzes, other quiz types besides MCQ, admin updating/deleting quizzes, admin viewing submissions, admin writing feedback/ automatic marking)
 * login and password, this needs to be secure and redone ~ 3 days (Jack).  This is super critical to get right before submission.  Users need to not be able to just enter a url and get to protected pages (CSRF attacks), we have to implement something like flask-wtf forms to do this, we can basically get the structure from the sample project on github (group-up).  This may require some screwing around with the routing and the front end code.
 * refactor backend - 2 days  (Jack).  Can be done near the end.  The sample project has a more modular format, ie. breaking up the app.py file into routes, models, controllers etc.
 * refactor front-end - 3 days  (Nathan).  Clean up the code and move some of the basic page building to jinja, but I suggest staying with the current structure, just cleaning up some things and doing the basic stuff in the server to show we can do it.  Like putting the username in the template, we can do in the backend, but the looping, just do in javascript.
 * writing all quizzes and adding to database - 1 day (Jack)
 

Extras:
* forgotten password email feature
* visualisation of performance across users (eg graph showing spread of marks)
* action log
