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
