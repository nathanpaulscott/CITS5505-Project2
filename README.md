# CITS5505-Project2
 Quiz System

---
## Status Comments  
Right now, the main functionality of the app is working as decribed below

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
 
 * refactor backend - 2 days  (Jack).  Can be done near the end.  The sample project has a more modular format, ie. breaking up the app.py file into routes, models, controllers etc.
 * refactor front-end - 3 days  (Nathan).  Clean up the code and move some of the basic page building to jinja, but I suggest staying with the current structure, just cleaning up some things and doing the basic stuff in the server to show we can do it.  Like putting the username in the template, we can do in the backend, but the looping, just do in javascript.
 * write testing code, I do not know how to do that, how can you write testing code for a gui based tool?!?!?  Really needs human testing, but this is a major requirement in the project spec
 * writing README (mainly Jack, revising by Nathan)
 

Extras:
* forgotten password email feature => no idea how t do this without email
* visualisation of performance across users (eg graph showing spread of marks) => maybe

Done
-------------
* quizzes written to database with images => done
* student reading + taking quizzes => done
* other quiz types besides MCQ => text answers is done
* admin updating/deleting quizzes => done
* admin viewing submissions => done
* admin writing feedback => done
* timing code => the token will expire after 30mins (settable in app.py).  The next server request from the user after token expiry will cause them to be kicked out to the login screen.  If the request was to submit quiz edits, or marking data, that data will be lost (I can change it, but how long to give them, better to just give them a submit button so they can submit regularly along the way.  In the case of taking a quiz, the token expiry is set to the allotted test time after the test has started, so that the user can submit their answers as long as they do so within the test time + a 2 minute buffer.  If they try to submit answers 2 mins after the test close, the answers will be lost and the user kicked out to the login page.  This adjusted token expiry time only applies to answer submissions, the next request to load the student summary page will use the normal token expiry time, thus if the normal token has expired at the point of submission, the user will then (after results being accepted) be redirected to the login page as with every other expiry case.  No page memory was implemented, i.e. a user gets kicked out to the login page as the token has expired and on re-login, they go back to the last page they were at.  This was not implemented as the app page structure is too simple, it is more clear just to go back to the summary page on login.


README of project
---
Running the application:
1. Open a terminal.
2. Navigate to the "app" folder of the application.
3. Type "python app.py".
4. Click the link in the terminal to open "http://127.0.0.1:5000/".

Using the application as an administrator:
Administrators have various privileges not available to students including managing users, modifying quizzes and marking quizzes.

Admin summary:
On the admin summary page, administrator accounts may import new quizzes using the .quiz format, export quizzes from the database for local download or delete quizzes using the coloured buttons above the quiz table. Administrators can also edit or mark quizzes by selecting the relevant buttons in the table. 

*include image of admin_summary

Editing quizzes:
Administrators can access the edit quiz page by clicking "edit" on a quiz in the admin summary. On the edit quiz page, administrators can add additional question text or images, change the response type ("text" for short answer or "mc" for multiple choice) and change the options for multiple choice questions.

*include image of edit quiz page

Managing users:

*include screenshot of manage users page


Using the application as a student:
Student accounts have limited privileges allowing them to take quizzes and view results.

Student summary:
The student summary page shows information about available quizzes including their completion status and awarded mark. Students can click on completed quizzes to view feedback or click on other quizzes to complete them. Students have a limited amount of time to complete a quiz and may submit at any time. If time runs out, the quiz will automatically be submitted with the student's answers. Quizzes may contain multiple choice questions, short answer questions and images.

*include screenshot of student summary
