README of project
---
### Running the application:
1. Open a terminal.
2. Navigate to the "app" folder of the application.
3. Type "python app.py".
4. Click the link in the terminal to open "http://127.0.0.1:5000/".

### Using the application as an teacher:
Teachers have various privileges not available to students including managing users, modifying quizzes and marking quizzes.

##### Quiz Administration:
On the quiz administration page, teacher accounts may import new quizzes using the .quiz format (a JSON file with a specific format), upload images, export quizzes from the database for local download or delete quizzes using the coloured buttons above the quiz table. Teachers can also edit or mark quizzes by selecting the relevant buttons in the table. 

##### Viewing statistics:
The statistics page displays the results of each quiz graphically. Simply provide the quiz ID to change quiz.

##### Editing quizzes:
Teachers can access the edit quiz page by clicking "edit" on a quiz in the admin summary. On the edit quiz page, teachers can add additional question text or images, change the response type ("text" for short answer or "mc" for multiple choice) and change the options for multiple choice questions.

##### Marking quizzes:
By selecting 'mark' on a quiz in the quiz administration page, teachers may view each student's submission. The mark quiz page allows teachers to see the student's submission and the correct answer. A mark may be provided and comments written in the textbox. Once all questions have been marked, clicking 'Finish and Submit' in the header will submit the marks and feedback for students to view.

##### Managing users:
Teacher accounts have permission to change usernames, passwords and roles of other accounts on the manage users page. Additionally, users can be added or deleted.


### Using the application as a student:
Student accounts have limited privileges allowing them to take quizzes and view results.

##### Student summary:
The student summary page shows information about available quizzes including their completion status and awarded mark. Students can click on completed quizzes to view feedback or click on other quizzes to complete them. Students have a limited amount of time to complete a quiz and may submit at any time. If time runs out, the quiz will automatically be submitted with the student's answers. Quizzes may contain multiple choice questions, short answer questions and images.

*include screenshot of student summary
