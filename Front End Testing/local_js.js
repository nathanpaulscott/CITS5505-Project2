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
	//This will build the left question nav
	if (window.location.pathname.slice(-14) == 'take_quiz.html') {
		//this data is sent in json somehow, maybe in a hidden tag eg. 
		var q_list = ["Q1","Q2","Q3","Q4","Q5","Q6","Q7","Q8","Q9","Q10"];
		var q_type = ["text","text","text","text","text","text","text","text","text","text"];
		var q_data = ["data1","data2","data3","data4","data5","data6","data7","data8","data9","data10"]; 
		var q_active = ["active","","","","","","","","",""]
		var q_showactive = ["show active","","","","","","","","",""]
		
		for (x in q_list) {
			//do the menu items
			$("#q_nav ul.nav").append("<li><a class=\"nav-link " + q_active[x] + "\" id=\"" + q_list[x] + "\" data-toggle=\"pill\" href=\"#" + q_list[x] + "-data\" role=\"tab\" aria-controls=\"" + q_list[x] + "-data\" aria-selected=\"false\">" + q_list[x] + "</a></li>");

			//do the content items
			$("#q_data").append("<div class=\"tab-pane fade " + q_showactive[x] + "\" id=\"" + q_list[x] + "-data\" role=\"tabpanel\" aria-labelledby=\"" + q_list[x] + "\">" + 
			//#######################################
			//this is the actual inner content
			"<h5>"+q_list[x]+"</h5>" +
			"<p>" + q_data[x] + "    question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here, question text here,  </p>" + 
    		"<p><img class=\"inline\" src=\"./test_image.jpg\"/></p>" +
			//#######################################
			//answer area
			"<hr>" + 
			"<form>" + 
				"<div class=\"form-group\">" +
				  "<label for=\"" + q_list[x] + "_A\">Answer</label>" + 
				  "<textarea class=\"form-control\" id=\"" + q_list[x] + "_A\" rows=\"3\"></textarea>" + 
				"</div>" + 
				"<button type=\"submit\" class=\"btn btn-success\" formaction=\"javascript:save_answers(\'"+q_list[x]+"\')\">Submit</button>" +
			"</form>" +
			//#######################################
			"</div>");
		}
	}
});




//runs on user clikcing submit on an answer
function save_answers(q) {
	var answer_text = $.trim($("#" + q + "_A").val());
	alert("ajax update the server with the answer for q: " + q + ", or even all answers.\n" + 
	"answer text:\n" + answer_text);
}