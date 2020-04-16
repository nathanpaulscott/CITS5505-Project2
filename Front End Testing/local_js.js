$(document).ready(function() {


	//##########################3
	//Quiz page
	//This will go to the take_quiz page with the parameter to fetch the selected question set for hte particular user
    //select on field text ....$("#quiz-selection-table tbody tr:contains('no attempts')").click(function() {
	if (window.location.pathname.slice(-9) == 'quiz.html') {
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
	if (window.location.pathname.slice(-14) == 'take_quiz.html') {
		//all the db sourced data is sent in json somehow, maybe in a hidden tag eg.  
		//Otherwise, we can just build the page at the server and send it, but it is not hard to build it locally. 
		var qset_id = "QS435";   // this comes from the db
		var q_id = ["Q243","Q22","Q43","Q534","Q115","Q26","Q7","Q28","Q49","Q410"];   //these are Q_ids from the db
		var q_data = {
			1:{"text":"text data1"},
			2:{"text":"text data2",
				"mc":{	1:"option1",
						2:"option2",
						3:"option3"}},
			3:{"text":"text data3"},
			4:{"text":"text data4"},
			5:{"text":"text data5"},
			6:{"text":"text data6",
				"mc":{	1:"option1",
						2:"option2",
						3:"option3"}},
			7:{"text":"text data7"},
			8:{"text":"text data8"},
			9:{"text":"text data9"},
			10:{"text":"text data10"}
		};
		//this is the actual question sequence, i.e. "Q1", "Q2", "Q3" etc... you need to build this list locally, it is basically "Q" + index+1
		//var q_seq = [];

		var active_text = "active";
		var showactive_text = "show active";
		for (x in q_id) {
			var ind = Number(x)+1;
			var q_seq = "Q" + String(ind); 
			//sets the multi-choice flag
			
			var html_text = ""; 
			
			//sets the first question to be selected initially and also the first of any multi-choices to be selected initially
			if (x>0) {
				active_text = "";
				showactive_text = "";
			}

			//add the value for the question sequence
			//q_seq.push("Q" + String(ind));
			
			//do the menu items
			html_text = '<li class="nav-item"><a class="nav-link ' + active_text + '" id="' + q_seq + '" data-toggle="pill" href="#' + q_seq + '-data" role="tab" aria-controls="' + q_seq + '-data" aria-selected="false">' + q_seq + '</a></li>';
			//append to the DOM
			$("#q_nav ul.nav").append(html_text);

			//do the content items
			html_text = '<div class="tab-pane fade ' + showactive_text + '" id="' + q_seq + '-data" role="tabpanel" aria-labelledby="' + q_seq + '">' + '\n';
			html_text += '<h5>' + q_seq + '</h5>' + '\n';
			html_text += '<p>' + q_data[ind]["text"] + '    question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here,  </p>' + '\n';
    		//add an image in certain cases just for demo
    		if (x in [0,1,2]) {
    			html_text += '<p><img class="inline" src="./test_image.jpg"/></p>' + '\n';
    		}
			html_text += '<hr>' + '\n';
			//#######################################
			//answer area
			html_text += '<form>' + '\n';
			html_text += 	'<label for="form_group">Answer</label>' + '\n';
			html_text += 	'<div class="form-group" id="form_group">' + '\n';

			if ("mc" in q_data[ind]) {
				var checked_text = "checked";
				//goes through the mc items, keys are always 1,2,3...
				for (item in q_data[ind]["mc"]) {
					var mc_id = 'mc_' + String(item);
					if (item>1) checked_text = "";
					html_text += 		'<div class="form-check">' + '\n';
					html_text += 			'<input class="form-check-input" type="radio" name="' + q_seq + '_mc" id="' + mc_id + '" value="' + String(item) + '" ' + checked_text + '>' + '\n';
					html_text += 			'<label class="form-check-label" for="' + mc_id + '">' + q_data[ind]["mc"][item] + '</label>' + '\n';
					html_text += 		'</div>' + '\n';
				}
			} else {
				html_text += 		'<textarea class="form-control" id="' + q_seq + '_A" rows="3"></textarea>' + '\n';
			}
			
			html_text += 	'</div>' + '\n';
			html_text += 	'<button type="submit" class="btn btn-success" formaction="javascript:save_answers(\'' + q_seq + '\',\'' + q_id[x] + '\',\'' + qset_id + '\',' + ("mc" in q_data[ind]) + ')">Submit</button>' + '\n';
			html_text += '</form>' + '\n';
			//#######################################
			html_text += '</div>';

			//append to the DOM
			$("#q_data").append(html_text);
		}
	

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




//runs on user clikcing submit on an answer
function save_answers(q_seq,q_id,qset_id,is_mc) {
	var text = "";
	text += "ajax update the server with the answer for question: " + q_seq + ", or even all answers.\n"; 
	text += "q_seq: " + q_seq + "\n";
	text += "q_id: " + q_id + "\n";
	text += "qset_id: " + qset_id + "\n";
	if (is_mc) {
		var answer_val = $("input[name=" + q_seq + "_mc]:checked").val()
		text += "answer choice:\n" + answer_val;
	} else {
		var answer_text = $.trim($("#" + q_seq + "_A").val());
		text += "answer text:\n" + answer_text;
	}	

	alert(text);
}
