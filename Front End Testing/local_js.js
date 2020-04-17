$(document).ready(function() {
	//##########################3
	//Admin page
	//This will go to the edit_quiz page with the parameter to fetch the selected question set for the particular user
    //select on field text ....$("#quiz-selection-table tbody tr:contains('no attempts')").click(function() {
	if (window.location.pathname.search(/\/admin\.html$/i) != -1) {
		$("#quiz-selection-table tbody tr").click(function() {
			var qset_id = $(this).find("td#qset-id").text();
			var user_id = $("#user_id").text();
			alert("we need to GET 'take_quiz.html' with params:\nqset_id: " + qset_id + "\nuser_id: " + user_id);
			window.location = "./take_quiz.html?qset_id="+qset_id+"&user_id="+user_id;
		});
	}



	//##########################3
	//Quiz page
	//This will go to the take_quiz page with the parameter to fetch the selected question set for the particular user
    //select on field text ....$("#quiz-selection-table tbody tr:contains('no attempts')").click(function() {
	if (window.location.pathname.search(/\/quiz\.html$/i) != -1) {
		$("#quiz-selection-table tbody tr").click(function() {
			var qset_id = $(this).find("td#qset-id").text();
			var user_id = $("#user_id").text();
			alert("we need to GET 'take_quiz.html' with params:\nqset_id: " + qset_id + "\nuser_id: " + user_id);
			window.location = "./take_quiz.html?qset_id="+qset_id+"&user_id="+user_id;
		});
	}


	//##########################3
	//Take Quiz page
	//This will build the left question nav and the panels with the questions and answers
	if (window.location.pathname.search(/\/take_quiz\.html$/i) != -1) {
		//all the db sourced data is sent in json somehow, maybe in a hidden tag eg.  
		//Otherwise, we can just build the page at the server and send it, but it is not hard to build it locally. 
		
		//user_id
		u_id = "fred123";
		// qset_id, that was chosen
		var qset_id = "QS435";
		//q_ids in the selected qset, the index + 1 is the sequence of the question 
		var q_id = ["x243","y22","z43","x534","z115"];
		//the question specification has 2 possible fields per question, q_data and a_data if it is an multi-choice
		//q_data is a list of text and/or images, you can have as many as you like 
		//a_data is a list of multichoice answer options, you can have as many as you like
		//if the question requires a text answer, just do not specify a_data
		var q_spec = {
			1:{	"q_data":["text:question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here.",
						"image:test_image4.jfif",
						"text:question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here, question 1 text here.",
						"image:test_image3.jfif",
						"image:test_image.jpg"]},
			2:{	"q_data":["text:question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here, question 2 text here,",
						"image:test_image1.jfif",
						"text:question 2 text here, question 2 text here, question 2 text here."],
				"a_data":["option1",
						"option2",
						"option3",
						"option4"]},
			3:{	"q_data":["text:question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here, question 3 text here."]},
			4:{	"q_data":["text:question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here, question 4 text here."],
				"a_data":["option1",
						"option2",
						"option3",
						"option4",
						"option5"]},
			5:{	"q_data":["text:question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here, question 5 text here,",
						"image:test_image2.jfif"]}
			};
				
				
		//this does the html building				
		var active_text = "active";
		var showactive_text = "show active";
		for (x in q_id) {
			var ind = Number(x)+1;
			//this is the actual question sequence, i.e. "Q1", "Q2", "Q3" etc... you need to build this list locally, it is basically "Q" + index+1
			var q_seq = "Q" + String(ind); 
			var html_text = ""; 
			
			//sets the first question to be selected initially and also the first of any multi-choices to be selected initially
			if (x>0) {
				active_text = "";
				showactive_text = "";
			}
			
			//do the menu items
			html_text = '<li class="nav-item"><a class="nav-link ' + active_text + '" id="' + q_seq + '" data-toggle="pill" href="#' + q_seq + '-data" role="tab" aria-controls="' + q_seq + '-data" aria-selected="false">' + q_seq + '</a></li>';
			//append to the DOM
			$("#q_nav ul.nav").append(html_text);

			//question data
			//#######################################
			html_text = '<div class="tab-pane fade ' + showactive_text + '" id="' + q_seq + '-data" role="tabpanel" aria-labelledby="' + q_seq + '">' + '\n';
			html_text += '<h5>' + q_seq + '</h5>' + '\n';
			
			//this goes through the q_data list and adds text or image tags as specified
			for (y of q_spec[ind]["q_data"]) {
				if (y.search(/^text:/) != -1) {
					html_text += '<p>' + y.slice(5,) + '</p>' + '\n';
				}
				else if (y.search(/^image:/) != -1) {
	    			html_text += '<p><img class="inline" src="./' + y.slice(6,) + '"/></p>' + '\n';
				}
    		}
			html_text += '<hr>' + '\n';

			//#######################################
			//answer data
			html_text += '<form>' + '\n';
			html_text += 	'<label for="form_group">Answer</label>' + '\n';
			html_text += 	'<div class="form-group" id="form_group">' + '\n';

			//add the mc choices or a textbox
			if ("a_data" in q_spec[ind]) {
				var checked_text = "checked";
				//goes through the mc items
				for (y in q_spec[ind]["a_data"]) {
					choice_ind = Number(y) + 1;
					var mc_id = 'mc_' + String(choice_ind);
					if (choice_ind > 1) checked_text = "";
					html_text += 		'<div class="form-check">' + '\n';
					html_text += 			'<input class="form-check-input" type="radio" name="' + q_seq + '_mc" id="' + mc_id + '" value="' + String(choice_ind) + '" ' + checked_text + '>' + '\n';
					html_text += 			'<label class="form-check-label" for="' + mc_id + '">' + q_spec[ind]["a_data"][y] + '</label>' + '\n';
					html_text += 		'</div>' + '\n';
				}
			} else {  //the non-multichoice case
				html_text += 		'<textarea class="form-control" id="' + q_seq + '_A" rows="3"></textarea>' + '\n';
			}
			
			html_text += 	'</div>' + '\n';
			html_text += 	'<button type="button" id="save" class="btn btn-success">Submit</button>' + '\n';
			html_text += '</form>' + '\n';
			//#######################################
			html_text += '</div>';

			//append to the DOM
			$("#q_data").append(html_text);
		}
	
		
		//assigns a click listener to the submit button as well as the finish and submit nav choice
		$("#save, #final-save").click(
			function() {
				var a_data = {"qset_id":qset_id,"u_id":u_id};
				//sets the final_submit flag to indicate the user closed off the quiz, otherwise the attmpt is not complete even though interim results are saved
				a_data["final_submit"] = 0;
				if ($(this).is('#final-save')) { 
					a_data["final_submit"] = 1;
				}
				//get the answers
				for (x in q_id) {
					var ind = Number(x)+1;
					//this is the actual question sequence, i.e. "Q1", "Q2", "Q3" etc... you need to build this list locally, it is basically "Q" + index+1
					var q_seq = "Q" + String(ind); 
					//read both for the mc case and the text case, the correct one will not be undefined
					var mc_choice = $("input[name=" + q_seq + "_mc]:checked").val();
					var text_field = $.trim($("#" + q_seq + "_A").val());
					if (mc_choice != undefined) {
						a_data[q_id[x]] = Number(mc_choice);
					} 
					else {
						a_data[q_id[x]] = text_field;
					}	
				}

				//temp
				var text = "";
				text += "ajax update the server with the current answers for qset_id: " + qset_id + "\n"; 
				text += JSON.stringify(a_data, null, 4);
				alert(text);
			}
		);


		
		//assigns a click listener to the question selection links so they hide on question selection when in smalll screen mode
		$("#q_nav li.nav-item").click(
			function() {
				var x = document.getElementById("q_nav");
				if (x.classList.contains("show")){
					x.classList.remove("show");
				}
			}
		);

	}
});






