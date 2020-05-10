# CITS5505-Project2
 Quiz System


To run the server: 
1. In a terminal, navigate to Back End
2. Type "python app.py"
3. Click the link that appears in the terminal

---
## Status Comments  
All DB integration has been done.   
The login and session management is mostly done.
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
 
 * add / delete / modify user code needs to be written ~ 1/2 day (Nathan)
 * timing code, need to time the user when taking a quiz and auto submit if they time-out and redirect to student summary
 * refactor backend - 2 days  (Jack).  Can be done near the end.  The sample project has a more modular format, ie. breaking up the app.py file into routes, models, controllers etc.
 * refactor front-end - 3 days  (Nathan).  Clean up the code and move some of the basic page building to jinja, but I suggest staying with the current structure, just cleaning up some things and doing the basic stuff in the server to show we can do it.  Like putting the username in the template, we can do in the backend, but the looping, just do in javascript.
 * writing all quizzes and adding to database - 1 day (Jack)
 * write testing code, I do not know how to do that, how can you write testing code for a gui based tool?!?!?  Really needs human testing, but this is a major requirement in the project spec
 * minor fixes: when a quiz is submitted, show "success" popup and redirect to student summary
 

Extras:
* forgotten password email feature => no idea how t do this without email
* visualisation of performance across users (eg graph showing spread of marks) => maybe

Done
-------------
* student reading + taking quizzes => done
* other quiz types besides MCQ => text answers is done
* admin updating/deleting quizzes => done
* admin viewing submissions => done
* admin writing feedback => done

