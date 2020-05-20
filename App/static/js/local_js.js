/////////////////////////////////////////////////////////////////////////////////
 //this runs a token protected ajax get request, used for each page request
 /////////////////////////////////////////////////////////////////////////////////
 function ajax_authorized_get(target, target_fn, args) {
	//this does a jwt authorized get for the given target
	// and passes control to the html building function (target_fn)

	//note on args
	//args["sesssion_data"] has the token and some other info
	//args also contains parameters to send in the get request(any key that is not session_data or data)
	//args["data"] is added with the json from the get request

	//this changes the address in the address bar of the browser, it is purely cosmetic
	//if the user presses reload, they will get an error as no token is sent
	//comment out to just show the login address (the real address) the whole time
	window.history.replaceState({}, "", target);

	//the response here is to call the calling function with args if status==ok
	//goes back to login.html if status == error
	//goes to student_summary or admin summary if the status is cancel

	//get the list of get params to send (not the session_data)
	let get_params = {};
	for (key in args) {
		if (! ["session_data"].includes(key)) {
			get_params[key] = args[key];
		}
	}

	//this does the ajax get request
	$.ajax({
		type: 'GET',
		url: target,
		data: get_params,
		headers: {'Authorization':args["session_data"]["token"]},
		contentType: 'application/json',
		dataType: 'json',
		success: function (data) {
			if (data["status"] == "ok"){
				if (data["msg"] != "") {
					alert(data["msg"]);
				}
				//load new base template page
				load_new_html(target, data["html"]);
				//add data to args
				args["data"] = data["data"];
				//pass to the target_fn to build the page
				target_fn(args);
			}
			else if (data["status"] == "error") {
				alert(data["msg"]);
				if ('target' in data) {
					window.location = data['target'];
				}
			}
			else if (data["status"] == "cancel") {
				alert(data["msg"]);
				let args_new = {};args_new["session_data"] = args["session_data"];
				if (data["target"] == '/admin_summary.html')
					ajax_authorized_get(data['target'], build_admin_summary, args_new);
				else
					ajax_authorized_get(data['target'], build_student_summary, args_new);
			}
			else if (data["status"] == "pass") {
				alert(data["msg"]);
			}
		}
	});
}


/////////////////////////////////////////////////////////////////////////////////
 //this runs a token protected ajax post request, used to typically send data
 /////////////////////////////////////////////////////////////////////////////////
function ajax_authorized_post(target, target_fn, req_args, target_fn_args) {
	//get the list of get params to send (not the session_data)
	let post_params = {};
	for (key in req_args) {
		if (! ["session_data"].includes(key)) 
			post_params[key] = req_args[key];
	}

	$.ajax({
		type: 'POST',
		url: target,
		data: JSON.stringify(post_params),
		headers: {'Authorization':req_args["session_data"]["token"]},
		contentType: "application/json",
		data_type: "json",
		cache: false,
		processData: false,
		async: true,
		success: function(data) {
			if (data["status"] == "ok") {
				//alert(data["msg"]);
				//reload page
				ajax_authorized_get(data["target"], target_fn, target_fn_args);
			} else {
				alert(data["msg"]);
				if ('target' in data) {
					window.location = data['target'];
				}
			}
		},
	});
}



/////////////////////////////////////////////////////////////////////////////////
 //this runs specific code on the login/register page load, this basically starts off the app
 /////////////////////////////////////////////////////////////////////////////////
 $(document).ready(function() {

	///////////////////////////////////////////////////////////////////
	//handles the registration
	if (window.location.pathname.search(/register\.html$/) != -1) {
		//this sets up the listeners for the form submit and sends the ajax req
		$("#submit").click(function() {
			let username = $("#username").val();
			let password = $("#password").val();
			let admin = $("#admin").val();

			//validation
			result = input_validation({"username":{"value":username}, 
										"password":{"value":password}});
			if (! result) return;

			form_data  = new FormData();
			form_data.append("username", username);
			form_data.append("password", password);
			form_data.append("admin", admin);
			let target = "/register.html";
			$.ajax({
				type: 'POST',
				url: target,
				data: form_data,
				contentType: false,
				cache: false,
				processData: false,
				async: true,
				success: function(data) {
					if (data["status"] == "error") {
						alert(data["msg"]);
						//only reload if it's another page
						if (data["target"].search(/register\.html$/) == -1) {
							window.location = data['target'];
						}
					} else {
						alert('Registration Success')
						window.location = '/login.html';
					}
				}
			});	
		}); 
	}


	//////////////////////////////////////////////////////////////////
	//handles the login and the returned token, then routes to admin or student area
	if (window.location.pathname.search(/login\.html$/) != -1) {
		//this sets up the listeners for the form submit and sends the ajax req
		$("#submit").click(function() {
			let username = $("#username").val();
			let password = $("#password").val();

			//validation
			//result = input_validation({"username":{"value":username}, "password":{"value":password}});
			//if (! result) return;

			form_data  = new FormData();
			form_data.append("username", username);
			form_data.append("password", password);
			let target = "/login.html";
			$.ajax({
				type: 'POST',
				url: target,
				data: form_data,
				contentType: false,
				cache: false,
				processData: false,
				async: true,
				success: function(data) {
					if (data["status"] == "ok") {
						let session_data = data['data'];
						//calls the summary page for admin or student
						let args = {"session_data":session_data};
						if (data["target"] == '/admin_summary.html')
							ajax_authorized_get(data["target"], build_admin_summary, args);
						else
							ajax_authorized_get(data["target"], build_student_summary, args);
					} 
					else {
						alert(data["msg"]);
						//only reload if it's another page
						if (data["target"].search(/login\.html$/) == -1) 
							window.location = data['target'];
					} 
				}
			});	
		}); 
	}
}); //end of the on_load section




//this has all the registration and login validation code
function input_validation(form) {
	username = form.username.value;
	password = form.password.value;

	success = true;
	msg = "";
	if (username.search(/[A-Za-z0-9]{1,30}/) == -1) {
		msg +="!!Username needs to be between 1 and 30 characters and be comprised of alphabetcial and numeric characters only\n\n";
		success = false;
	}
	if (password.search(/.{8,30}/) == -1 ||
		password.search(/[A-Z]{1,30}/) == -1 ||
		password.search(/[a-z]{1,30}/) == -1 ||
		password.search(/[0-9]{1,30}/) == -1 ||
		password.search(/[!@#$%^&*]{1,30}/) == -1) {
			msg +="!!Password needs to be between 8 and 30 characters and be comprised of at least one capital letter, one lower case letter, one number and one special character from (!@#$%^&*)\nThis non conformant password will now be accepted as long as it is not blank, but msg was just to show that validation could be enabled\n\n";
			//disable actual blocking of non conformant passwords for testing as it is too painful to enter in long passwords
			//success = false;
	}

	if (msg.length > 0) alert(msg);
	return success;
}


//validation for the quiz import
function validate_import(qset_data, name) {
	if (! Array.isArray(qset_data)) 
		return {"status":"error","msg":"!!! outer object should be an array '" + name + "', not uploading....<br/>"};

	let keys = ["enabled","qs_id","time","topic","u_id"]
	for (key of keys){
		if (! key in qset_data[0])
			return {"status":"error","msg":key + " doesn't exist in the first element of the array: '" + name + "', not uploading....<br/>"};
	}
	
	for (q of qset_data.slice(1,)){
		if (! "question" in q)
			return {"status":"error","msg":"A question key needs to be in each array element except first one: '" + name + "', not uploading....<br/>"};

		if (! "answer" in q)
			return {"status":"error","msg":"An answer key needs to be in each array element except first one: '" + name + "', not uploading....<br/>"};

		if (! "correct" in q["answer"])
			return {"status":"error","msg":"The answer object needs to have a key: 'correct' with the correct answer: '" + name + "', not uploading....<br/>"};

		if (! "type" in q["answer"])
			return {"status":"error","msg":"The answer object needs to have a key: 'type' with the answer type ('mc' or 'text'): '" + name + "', not uploading....<br/>"};

		if (! ["text","mc"].includes(q["answer"]["type"]))
			return {"status":"error","msg":"The answer object type element needs to be either 'text' or 'mc': '" + name + "', not uploading....<br/>"};

		if (q["answer"]["type"] == "mc" && 
			! "data" in q["answer"])
			return {"status":"error","msg":"The answer object needs to have a data element with a list of multi choice options if the answer type is 'mc': '" + name + "', not uploading....<br/>"};

		if (q["answer"]["type"] == "mc" && 
			! q["answer"]["data"].includes(q["answer"]["correct"]))
			return {"status":"error","msg":"The mc correct answer needs to be one of the given options: '" + name + "', not uploading....<br/>"};

		/*
		//this is when we specify mc correct as the index (,2,3,4,5 etc)
		if (q["answer"]["type"] == "mc" && 
			Number.isNaN(parseInt(q["answer"]["correct"])))
			return {"status":"error","msg":"As the answer is multi-choice, the correct element needs to parse to an integer: '" + name + "', not uploading....<br/>"};

		if (q["answer"]["type"] == "mc" && 
			parseInt(q["answer"]["correct"]) >= 1 && 
			parseInt(q["answer"]["correct"]) <= q["answer"]["data"].length )
			return {"status":"error","msg":"As the answer is multi-choice, the correct element needs to be a relevant integer mapping to a given option: '" + name + "', not uploading....<br/>"};
		*/
		
		if (q["answer"]["type"] == "text" && 
			String(q["answer"]["correct"]).length == 0)
			return {"status":"error","msg":"The answer object needs to have a correct answer in the correct element, not just blank: '" + name + "', not uploading....<br/>"};

		if (! Array.isArray(q["question"])) 
			return {"status":"error","msg":"!!! the question element needs to contain an array [header, part1...partn]: '" + name + "', not uploading....<br/>"};

		if (! "marks" in q["question"][0])
			return {"status":"error","msg":"The question needs to have a marks element with the available marks for the question: '" + name + "', not uploading....<br/>"};

		//if (! "q_id" in q["question"][0])
		//	return {"status":"error","msg":"The question needs to have a q_id element: '" + name + "', not uploading....<br/>"};

		for (q_part of q["question"].slice(1,)){
			if (! "type" in q_part || 
				! ["text","image"].includes(q_part["type"]))
				return {"status":"error","msg":"Each question part of a question needs to have a type element valued 'text' or 'image' depending on the part type: '" + name + "', not uploading....<br/>"};

			if (! "data" in q_part ||
				q_part["data"].length == 0)
				return {"status":"error","msg":"Each question part of a question needs to have a data element with the text data or the image filename and it can not be blank: '" + name + "', not uploading....<br/>"};
		}
	}
	return {"status":"ok"}
}


/////////////////////////////////////////////////////////////////////////////////
//utility functions
/////////////////////////////////////////////////////////////////////////////////
function encodeQueryData(data) {
	//encodes a dict to an HTTP GET string
	const ret = [];
	for (let d in data)
		ret.push(encodeURIComponent(d) + '=' + encodeURIComponent(data[d]));
	return ret.join('&');
}

 function findGetParameter(param) {
	let url = new URL(window.location.href);
	let result = url.searchParams.get(param);
    return result;
}

function fix_header(username){
	//update the username in the header
	$("#username").text(username);

	//change the home link because of fontawsome screwup
	//$("#home i").removeAttr("class"); 
	//$("#home i").text("exit");
}

function load_new_html(url, html) {
	//this loads a new html document from an html string
	//you have 2 options 
	//1) reload the js, it wipes the document, loose local lets, some say its bad
	//all I know is that chrome and edge give a bunch of warnings
	//document.open();
	//document.write(html);
	//document.close();
	
	//2) this doesn't load js after the login page, just replaces the document structure
	//doesn't give warnings, works fine
	let newdoc = document.implementation.createHTMLDocument();   //or this
	newdoc.documentElement.innerHTML = html;
	document.replaceChild(newdoc.documentElement, document.documentElement);
}



//////////////////////////////////////////////////////////////////////////////////
//HTML building code
//////////////////////////////////////////////////////////////////////////////////
//all the functions after this point are used to build the dynamic content of each page
//the most complex being the admin_summary due to the various buttons and add-on functions
///////////////////////////////////////////////////////////////////////////////////
//admin_summary => longest and most complex
//student_summary => medium length
//take_quiz => medium length
//review_quiz => short
//mark_quiz => medium length
//edit_quiz => quite long and complex
//manage_users => short
//student_stats => short
//admin_stats => short
//////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////
function build_admin_summary(args) {
	//this does the html table building				
	let qset_summary = args["data"]["data"];
	let session_data = args['session_data'];
	let username = session_data["username"];
	let u_id = 	session_data["u_id"];

	//fix the header
	fix_header(username);
	//disable the manage users href
	$("#manage-users").attr("href","javascript:;"); 
	//disable the admin stats href
	$("#admin-stats").attr("href","javascript:;"); 

	//does the table header
	let html_text = ""; 
	html_text = '<table class="table table-hover table-striped table-responsive" id="quiz-admin-table">' + '\n';
	html_text +='	<thead>' + '\n';
	html_text +='		<tr>' + '\n';
	html_text +='          <th scope="col"></th>' + '\n';
	html_text +='          <th scope="col"></th>' + '\n';
	for (header_item of qset_summary[0]) {
		html_text +='          <th scope="col">'+ header_item +'</th>' + '\n';
	}
	html_text +='     	</tr>' + '\n';
	html_text +='   </thead>' + '\n';

	//does the table body
	html_text +='   <tbody>' + '\n';
	for (i = 1; i < qset_summary.length; i++){
		html_text +='       <tr class="click-enable">' + '\n';
		html_text +='	       <td class="edit-quiz">Edit</td>' + '\n';
		html_text +='	       <td class="mark-quiz">Mark</td>' + '\n';
		html_text +='	       <td id="qs-id">' + qset_summary[i][0] + '</td>' + '\n';
		for (j = 1; j < qset_summary[i].length; j++){
			html_text +='	       <td>' + qset_summary[i][j] + '</td>' + '\n';
		}
		html_text +='       </tr>' + '\n';
	}
	html_text +='   </tbody>' + '\n';
	html_text += '</table>' + '\n';
	
	//append to the DOM
	$("#p-quiz-admin-table").append(html_text);

	//assigns a click listener to the mark cells for marking and review
	$("#quiz-admin-table tbody tr.click-enable td.mark-quiz").click(function() {
		let qs_id = $(this).parent().find("td#qs-id").text();
		//gets the total submissions available from the next 3 elements in the table
		//if there are no submissions, do not proceed
		let qs_avail = Number($(this).parent().find("td#qs-id").next().text()) +
						Number($(this).parent().find("td#qs-id").next().next().text()) +
						Number($(this).parent().find("td#qs-id").next().next().next().text());

		if (qs_avail > 0) {						
			let args = {"session_data":session_data,
						"qs_id":qs_id,
						"s_u_id":"init",
						"include_submission":"1",
						"include_submitters":"1"};
			ajax_authorized_get("./mark_quiz.html", build_mark_quiz, args);
		}	
	});

	//assigns a click listener to the edit cells for editing the qset
	$("#quiz-admin-table tbody tr.click-enable td.edit-quiz").click(function() {
		let qs_id = $(this).parent().find("td#qs-id").text();
		let args = {"session_data":session_data,
					"qs_id":qs_id,
					"include_submission":"0",
					"include_submitters":"0"};
		ajax_authorized_get("./edit_quiz.html", build_edit_quiz, args);
	});

	//assigns a click listener to the manage-users link
	$("#manage-users").click(function() {
		let args = {"session_data":session_data} 
		ajax_authorized_get("./manage_users.html", build_manage_users, args);
	});
	
	//assigns a click listener to the admin-stats link
	$("#admin-stats").click(function() {
		let args = {"session_data":session_data, "qs_id":"init"} 
		ajax_authorized_get("./admin_stats.html", build_admin_stats, args);
	});

	//###############################
	//This controls the export and delete collapse areas so only one is showing at a time
	//#################################################################################
	$("#btn-delete").on("click", function() {
		$('#import-config').collapse('hide');
		$('#export-config').collapse('hide');
	});

	$("#btn-export").on("click", function() {
		$('#import-config').collapse('hide');
		$('#delete-config').collapse('hide');
	});


	//###############################
	//Handles the refresh button
	//#################################################################################
	$("#btn-refresh").on("click", function() {
		ajax_authorized_get('/admin_summary.html', build_admin_summary, {"session_data":session_data});
	});


	//###############################
	//Handles the delete button
	//#################################################################################
	$("#btn-delete-submit").on("click", function() {
		// here you need to request that the server deletes the given quiz ids
		//##############################################
		let qs_id_text = $.trim($("#delete-config-text").val()).split(",");
		
		//get the current set of qs_ids
		let qs_id_db = [];
		for (qset of qset_summary.slice(1,)) {
			qs_id_db.push(String(qset[0]));
		}

		//get the clean set of requested qs_ids
		let qs_id_req = [];
		for (qset of qs_id_text) {
			if (qs_id_db.includes(qset)){
				qs_id_req.push(qset);
			}
		}

		if (qs_id_req.length != 0) {
			//alert("ajax req to delete the given subset of the qs_ids from the DB:\n" + JSON.stringify(qs_id_req,null,2));
		}
		else{
			alert("no valid quiz ids were given")
			return
		}

		//Do the Ajax Request here to send the delete list to the server
		$.ajax({
			type: 'POST',
			url: '/delete_quiz',
			data: JSON.stringify({"qs_id_req":qs_id_req}),
			headers: {'Authorization':session_data["token"]},
			contentType: "application/json",
			data_type: "json",
			cache: false,
			processData: false,
			async: true,
			success: function(data) {
				if (data["status"] == 'ok') {
					$("#span-delete-submit").text("Status: " + data["status"] + ", msg: " + data["msg"]);
				}
				else {
					alert(data["msg"]);
					if ('target' in data) {
						window.location = data['target'];
					}
				}
			},
		});
		
	});
	

	//###############################
	//Handles the export button
	//#################################################################################
	$("#btn-export-submit").on("click", function() {
		// here you need to request the quiz data in json format from the server
		//it is using qset_summary whihc is the json object coming in to populate the table in this page
		//##############################################33
		let qs_id_text = $.trim($("#export-config-text").val()).split(",");

		//get the current set of qs_ids
		let qs_id_db = [];
		for (qset of qset_summary.slice(1,)) {
			qs_id_db.push(String(qset[0]));
		}

		//get the clean set of requested qs_ids
		let qs_id_req = [];
		for (qset of qs_id_text) {
			if (qs_id_db.includes(qset)){
				qs_id_req.push(qset);
			}
		}

		if (qs_id_text[0].search(/all/i) != -1) {
			//alert("ajax req to export all quizes:\n" + JSON.stringify(qs_id_db,null,2));
			qs_id_req = qs_id_db;
		}
		else if (qs_id_req.length == 0) {
			alert("no valid quiz ids were given");
			return;
		}

		//Do the Ajax Request here to fetch the desired question sets
		$.ajax({
			type: 'POST',
			url: '/download_quiz',
			data: JSON.stringify({"qs_id_req":qs_id_req}),
			headers: {'Authorization':session_data["token"]},
			contentType: "application/json",
			data_type: "json",
			cache: false,
			processData: false,
			async: true,
			success: function(data) {
				if (data["status"] == 'ok') {
					//give a status msg
					$("#span-export-submit").text("Status: " + data["status"] + ", msg: " + data["msg"]);
					//write this to the DOM and trigger the download, then delete from the DOM
					for (qset of data["data"]) {
						let filename = "export_qs_id_" + String(qset[0]["qs_id"]) + ".quiz";
						let el = document.getElementById('a-export');
						let href_text = "data:application/xml;charset=utf-8,";
						href_text += JSON.stringify(qset, null, 2);
						el.setAttribute("href", href_text);
						el.setAttribute("download", filename);
						el.click();
						el.setAttribute("href", "");
						el.setAttribute("download", "");
					}
				}
				else {
					alert(data["msg"]);
					if ('target' in data) {
						window.location = data['target'];
					}
				}
			},
		});
	});


	//###############################
	//Handles the import button
	//#################################################################################
	//assign the onclick event listener to the import button whihc in turn triggers a click on the hidden input button to launch the file dialog
	$("#btn-import").on("click", function() {
		$('#export-config').collapse('hide');
		$('#delete-config').collapse('hide');
		$('#import-config').collapse('show');

		//this resets the control (VIP)
		document.getElementById("input-import").value = "";

		$("#import-config").text("");
		document.getElementById('input-import').click();
	});

	//this is the onchange evenet handler for the hidden input file selection dialog
	$("#input-import").on("change", function() {
		//this code accepts multiple files, the quiz files should be .quiz and just be a text file of a json object with the correct format specifying the quiz text, answer types and images.  So we validate these files.  Any non .quiz files, are assumed to be associated image files and are just uploaded to the server, there is no crosschecking done locally, that can be done server-side later.  The quizes will still work with no image files, the images just will not render
		
		let files = this.files;
		let upload_data = [];
		let cancel_upload = true;
		let cnt = 0;
		for (f of files) 
			if (f["name"].search(/\.quiz/i) > -1) 
				cnt = cnt + 1;

		for (f of files){
			if (f["name"].search(/\.quiz/i) == -1) {
				//this is for images

				//do some validation here if you want t avoid non-image files etc...
				let img_allowed = ['image/gif', 'image/jpeg', 'image/png'];
				if (! img_allowed.includes(f["type"])) {
					$("#import-config").append("Your file '" + f["name"] + "' needs to be an image file (jpg, png, gif).  Not uploading it....<br/>");
					continue;
				}
				if ( f["size"] > 1000000) {
					$("#import-config").append("Your file '" + f["name"] + "' is > 1MB, you should try to reduce it for usability fo the web app.  Not uploading it....<br/>");
					continue;
				}

				//send to server
				let form_data = new FormData();
				form_data.append("file", f);
				$.ajax({
					type: 'POST',
					url: '/upload_image',
					headers: {'Authorization':session_data["token"]},
					data: form_data,
					async: true,
					contentType: false,
					cache: false,
					processData: false,
					success: function(data) {
						if (data["status"] == 'ok') {
							$("#import-config").append(data["msg"] + "<br/>");
						}
						else {
							alert(data["msg"]);
							if ('target' in data) {
								window.location = data['target'];
							}
						}
					}
				});
			}
			else {
				//this is for the .quiz files
				//this uses a closure to handle all the file read and to pass the filename in, I still do not understand how it works
				//this is for .quiz text files which contain quiz data in the specified json format.  we validate each one and reject if it fails (informing the user why)
				let reader = new FileReader();
				reader.onload = (function(e1) {
					return function(e2) {
						cnt = cnt-1;
						let error_msg = "";
						let name = e1.name;
						let file_data = e2.target.result;
						let qset_data = [];
						try{
							//parse data, this can throw
							qset_data = JSON.parse(file_data);
							//validate data
							result = validate_import(qset_data, name);
							if (result["status"] == "ok") {
								upload_data.push(qset_data);
								cancel_upload = false;   //need just one good quiz to not cancel the upload
								$("#import-config").append(name + ":  validation success<br/>");
							}
							else 
								$("#import-config").append(result["msg"]);							
						}
						catch(err) {
							$("#import-config").append("!!! bad json format '" + name + "', not uploading....<br/>");
						}

						//check we are done and can do the upload
						//need to upload all quizes in one array to avoid qs_id issues
						//cnt == 0 means we are at the last quiz file
						if (cnt == 0 && ! cancel_upload){
							//send to server
							$.ajax({
								type: 'POST',
								url: '/upload_quiz',
								data: JSON.stringify({"upload_data":upload_data,
													  "import_flag":true}),
								headers: {'Authorization':session_data["token"]},
								contentType: "application/json",
								data_type: "json",
								cache: false,
								processData: false,
								async: true,
								success: function(data) {
									if (data["status"] == 'ok') {
										$("#import-config").append(data["msg"] + "<br/>");
									}
									else {
										alert(data["msg"]);
										if ('target' in data) {
											window.location = data['target'];
										}
									}
								},
							});
						}
					};
				})(f);
				reader.readAsText(f);
			}
		}
	});

	//runs the datatable plugin on the table to make it sortable etc...
	$('#quiz-admin-table').DataTable({
		"paging":true,
		"ordering":true,
		columnDefs: [{"orderable": false,"targets":[0,1]}],"order": [] 
	});
} //end of the build_admin_summary function


///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
function build_student_summary(args) {
	//this does the html table building				
	let qset_summary = args["data"]["data"];
	let session_data = args['session_data'];
	let username = session_data["username"];
	let u_id = 	session_data["u_id"];

	//fix the header
	fix_header(username);
	//disable the admin stats href
	$("#student-stats").attr("href","javascript:;"); 

	//does the table header
	let html_text = ""; 
	html_text = '<table class="table table-hover table-striped table-responsive" id="quiz-selection-table">' + '\n';
	html_text +='	<thead>' + '\n';
	html_text +='		<tr>' + '\n';
	//html_text +='          <th scope="col">#</th>' + '\n';
	for (header_item of qset_summary[0]) {
		html_text +='          <th scope="col">'+ header_item +'</th>' + '\n';
	}
	html_text +='     	</tr>' + '\n';
	html_text +='   </thead>' + '\n';

	//does the table body
	html_text +='   <tbody>' + '\n';
	for (let i = 1; i < qset_summary.length; i++){
		html_text +='       <tr class="click-enable">' + '\n';
		
		//html_text +='	       <td id="qs_id">' + String(i) + '</td>' + '\n';
		html_text +='	       <td id="qset-status">' + qset_summary[i][0] + '</td>' + '\n';
		html_text +='	       <td id="qs-id">' + qset_summary[i][1] + '</td>' + '\n';
		for (let j = 2; j < qset_summary[i].length; j++){
			html_text +='	       <td>' + qset_summary[i][j] + '</td>' + '\n';
		}
		html_text +='       </tr>' + '\n';
	}
	html_text +='   </tbody>' + '\n';
	html_text += '</table>' + '\n';
	
	//append to the DOM
	$("#p-quiz-selection-table").append(html_text);

	//assigns a click listener to the student-stats link
	$("#student-stats").click(function() {
		let args = {"session_data":session_data, "qs_id":"init"} 
		ajax_authorized_get("./student_stats.html", build_student_stats, args);
	});
	
	//assigns a click listener to the table rows
	$("#quiz-selection-table tbody tr.click-enable").click(function() {
		let status = $(this).find("td#qset-status").text();
		let qs_id = $(this).find("td#qs-id").text();

		if (["Completed","Marked"].includes(status)) {
			//review the quiz sumbission and/or marks		
			let args = {"session_data":session_data, 
						"qs_id":qs_id, 
						"include_submission":"1",
						"include_submitters":"0"};
			ajax_authorized_get("./review_quiz.html", build_review_quiz, args);
		} else {
			//take the quiz 
			let args = {"session_data":session_data, 
						"qs_id":qs_id, 
						"preview_flag":false,
						"include_submission":"0",
						"include_submitters":"0"};
			ajax_authorized_get("./take_quiz.html", build_take_quiz, args);
		}
	});

	//runs the datatable plugin on the table to make it sortable etc...
	$('#quiz-selection-table').DataTable();
}//end of the build_student_summary function




///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
function build_take_quiz(args) { 
	//this does the html building				
	let qset_data = args["data"]["data"];
	let session_data = args["session_data"];
	let username = session_data["username"];
	let u_id = 	session_data["u_id"];
	let preview_flag = args["preview_flag"];
	let quiz_time = qset_data[0]["time"]

	let qs_id = qset_data[0]["qs_id"];
	let s_username = qset_data[0]["s_username"];
	let s_u_id = qset_data[0]["s_u_id"];

	//fix the header
	fix_header(username);
	//disable the final save href
	$("#final-save").attr("href","javascript:;"); 
	//disable the cancel-test href
	$("#cancel-test").attr("href","javascript:;"); 

	//do the title
	html_text = qset_data[0]["topic"] + " (" + String(qs_id) + ")";
	//append to the DOM
	$("h5#title").append(html_text);

	let active_text = "active";
	let showactive_text = "show active";
	//go through the questions, from index 1 to end of array
	for (let i=1; i < qset_data.length; i++) {
		//this is the actual question sequence, i.e. "Q1", "Q2", "Q3" etc... you need to build this list locally, it is basically "Q" + index+1
		let q_seq = "Q" + String(i); 
		let html_text = ""; 
		
		//sets the first question to be selected initially and also the first of any multi-choices to be selected initially
		if (i > 1) {
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
		
		//this goes through the question part list and adds text or image tags as specified
		//the first index of the list is the q_id, so ignore that
		let question_parts = qset_data[i]["question"].slice(1,);
		for (q_part of question_parts) {
			if (q_part["type"] == "text") {
				html_text += '<p>' + q_part["data"] + '</p>' + '\n';
			}
			else if (q_part["type"] == "image") {
				html_text += '<p><img class="inline" src="./static/images/' + q_part["data"] + '"/></p>' + '\n';
			}
		}
		html_text += '<hr>' + '\n';

		//#######################################
		//answer data
		html_text += '<form>' + '\n';
		html_text += 	'<label for="form_group">Answer:</label>' + '\n';
		html_text += 	'<div class="form-group" id="form_group">' + '\n';

		//add the mc choices or a textbox
		if ("answer" in qset_data[i] && qset_data[i]["answer"]["type"] == "mc") {
			let checked_text = "checked";
			//goes through the mc items
			//add a blank element ot the start of array to make the indicies 1 based
			let mc_options = qset_data[i]["answer"]["data"];
			mc_options.unshift("");
			for (let j=1; j < mc_options.length; j++) {
				let mc_id = q_seq + "_mc_" + String(j);
				if (j > 1) checked_text = "";
				html_text += 		'<div class="form-check">' + '\n';
				html_text += 			'<input class="form-check-input" type="radio" name="' + q_seq + '_mc" id="' + mc_id + '" value="' + String(j) + '" ' + checked_text + '>' + '\n';
				html_text += 			'<label class="form-check-label" for="' + mc_id + '">' + mc_options[j] + '</label>' + '\n';
				html_text += 		'</div>' + '\n';
			}
		} else {  //the non-multichoice case
			html_text += 		'<textarea class="form-control" id="' + q_seq + '_A" rows="3"></textarea>' + '\n';
		}
		html_text += 	'</div>' + '\n';
		html_text += 	'<button type="button" class="btn btn-success save-continue">Submit</button>' + '\n';
		html_text += '</form>' + '\n';
		//#######################################
		html_text += '</div>';

		//append to the DOM
		$("#q_data").append(html_text);
	}

	//makes some DOM changes for the preview case
	if (preview_flag) {
		$("#final-save").attr("id","back2edit"); 		
		$("#back2edit").attr("href","javascript:;"); 
		$("#back2edit").text("Back to Edit Quiz");
		$("#cancel-test").remove();
		$(".save-continue").prop("disabled",true);

		//assigns a click listener to the back to edit link (preview case)
		$("#back2edit").click(function() {
			//go back to the edit quiz page
			let args = {"session_data":session_data,
						"qs_id":qs_id,
						"include_submission":"0",
						"include_submitters":"0"};
			ajax_authorized_get("./edit_quiz.html", build_edit_quiz, args);
		});
	}
	

	//this adds the countdown timer for the quiz, the server will actually determine the end time by the way
	$('#countdown').collapse("show")
	let t_start = new Date().getTime();
	let t_end = t_start + quiz_time*60*1000;
	let x = setInterval(function() {
		let t_remain = t_end - new Date().getTime();
		let h = Math.floor((t_remain % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)).toString().padStart(2,"0");
		let m = Math.floor((t_remain % (1000 * 60 * 60)) / (1000 * 60)).toString().padStart(2,"0");
		let s = Math.floor((t_remain % (1000 * 60)) / 1000).toString().padStart(2,"0");
		$("#countdown").text("Time remaining => " + h + ":" + m + ":" + s);
		if (t_remain < 0) {
			clearInterval(x);
			$("#countdown").text("Times Up  ");
		}
	}, 1000);
		
		
	//This assigns some listeners on the take_quiz page
	//####################################################
	//assigns a click listener to the question selection links so they hide on question selection when in smalll screen mode
	$("#q_nav li.nav-item").click(
		function() {
			let x = document.getElementById("q_nav");
			if (x.classList.contains("show")){
				x.classList.remove("show");
			}
		}
	);

	//assigns a click listener to the submit button as well as the finish and submit nav choice
	$(".save-continue, #final-save, #cancel-test").click(function() {
		//sets the final_submit flag to indicate the user closed off the quiz, otherwise the attmpt is not complete even though interim results are saved
		let final_flag = $(this).is("#final-save");
		let cancel_flag = $(this).is("#cancel-test");
		if (cancel_flag) 
			final_flag = false;

		let a_data = [];
		//get the answers
		for (let i=1; i < qset_data.length; i++) {
			//this is the actual question sequence, i.e. "Q1", "Q2", "Q3" etc... you need to build this list locally, it is basically "Q" + index+1
			let q_seq = "Q" + String(i);
			//read both for the mc case and the text case, the correct one will not be undefined
			let mc_choice = $("input[name=" + q_seq + "_mc]:checked").val();
			let text_field = $.trim($("#" + q_seq + "_A").val());
			if (mc_choice != undefined) 
				a_data.push(mc_choice);
			else 
				a_data.push(text_field);
		}

		$.ajax({
			type: 'POST',
			url: '/submit_answers_json',
			data: JSON.stringify({"qs_id":qs_id,
								"final_flag":final_flag,
								"a_data":a_data}),
			headers: {'Authorization':session_data["token"]},
			contentType: "application/json",
			data_type: "json",
			cache: false,
			processData: false,
			async: true,
			success: function(data) {
				if (data["status"] == "ok") {
					alert("Your answers were submitted with status: ok");
					if (final_flag || cancel_flag) {
						//go back to the student_summary page
						let args = {"session_data":session_data};
						ajax_authorized_get("./student_summary.html", build_student_summary, args);
					}
				} 
				else {
					alert(data["msg"]);
					if ('target' in data) {
						window.location = data['target'];
					}
				}
			},
		});
	});  //end of submit answers code
} //end of the build_take_quiz function


///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
function build_review_quiz(args) {
	//this does the html building				
	let qset_data = args["data"]["data"];
	let submission_status = args["data"]["submission_status"];
	let session_data = args["session_data"];
	let username = session_data["username"];
	let u_id = session_data["u_id"];
	
	let qs_id = qset_data[0]["qs_id"];
	let s_username = qset_data[0]["s_username"];
	let s_u_id = qset_data[0]["s_u_id"];

	//fix the header
	fix_header(username);
	//disable the final save href
	$("#final-save").attr("href","javascript:;"); 

	//do the title
	html_text = qset_data[0]["topic"] + " (" + String(qs_id) + ")" + '<br/> <span class="submitter">username: ' + s_username + '<br/>user_id: ' + s_u_id + '<br/>status: ' + submission_status + '</span>';
	//append to the DOM
	$("h5#title").append(html_text);

	let active_text = "active";
	let showactive_text = "show active";
	//go through the questions, from index 1 to end of array
	for (let i=1; i < qset_data.length; i++) {
		//this is the actual question sequence, i.e. "Q1", "Q2", "Q3" etc... you need to build this list locally, it is basically "Q" + index+1
		let q_seq = "Q" + String(i); 
		let html_text = ""; 
		
		//sets the first question to be selected initially and also the first of any multi-choices to be selected initially
		if (i > 1) {
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
		//set the grade text in the title
		let mark_text = "Not Yet Marked";
		if (qset_data[i]["answer"]["grade"] != "-1") 
			mark_text = qset_data[i]["answer"]["grade"] + '/' + qset_data[i]["question"][0]["marks"];
		html_text += '<h5>' + q_seq + '&nbsp&nbsp&nbsp&nbsp(' + mark_text + ')</h5>' + '\n';
		
		//this goes through the question part list and adds text or image tags as specified
		//the first index of the list is the q_id, so ignore that
		let question_parts = qset_data[i]["question"].slice(1,);
		for (q_part of question_parts) {
			if (q_part["type"] == "text") {
				html_text += '<p>' + q_part["data"] + '</p>' + '\n';
			}
			else if (q_part["type"] == "image") {
				html_text += '<p><img class="inline" src="./static/images/' + q_part["data"] + '"/></p>' + '\n';
			}
		}
		html_text += '<hr>' + '\n';

		//#######################################
		//answer data
		html_text += '<form>' + '\n';
		html_text += 	'<label for="form_group">Answer:</label>' + '\n';
		html_text += 	'<div class="form-group" id="form_group">' + '\n';

		//disable inputs
		let disabled_text = "disabled";
		//add the mc choices or a textbox
		if ("answer" in qset_data[i] && qset_data[i]["answer"]["type"] == "mc") {
			//goes through the mc items
			//add a blank element ot the start of array to make the indicies 1 based
			let mc_options = qset_data[i]["answer"]["data"];
			mc_options.unshift("");
			for (let j = 1; j < mc_options.length; j++) {
				let mc_id = q_seq + "_mc_" + String(j);
				//this sets the submitted radio button selection
				let checked_text = "";
				if (j == Number(qset_data[i]["answer"]["answer"])) 
					checked_text = "checked";
				
				html_text += 		'<div class="form-check">' + '\n';
				html_text += 			'<input class="form-check-input" type="radio" name="' + q_seq + '_mc" id="' + mc_id + '" value="' + String(j) + '" ' + checked_text + ' ' + disabled_text + '>' + '\n';
				html_text += 			'<label class="form-check-label" for="' + mc_id + '">' + mc_options[j] + '</label>' + '\n';
				html_text += 		'</div>' + '\n';
			}
		} else {  //the non-multichoice case
			html_text += 		'<textarea class="form-control" id="' + q_seq + '_A" rows="3" ' + disabled_text + '>' + qset_data[i]["answer"]["answer"] + '</textarea>' + '\n';
		}
		html_text += 	'</div>' + '\n';

		//add the assessor comments text
		html_text += 	'<label for="form_group2">Assessor Comments:</label>' + '\n';
		html_text += 	'<div class="form-group" id="form_group2">' + '\n';
		html_text += 		'<textarea class="form-control" id="' + q_seq + '_C" rows="3" ' + disabled_text + '>' + qset_data[i]["answer"]["comment"] + '</textarea>' + '\n';
		html_text += 	'</div>' + '\n';
		html_text += '</form>' + '\n';
		//#######################################
		html_text += '</div>';

		//append to the DOM
		$("#q_data").append(html_text);
	}

	//This assigns some listeners on the take_quiz page
	//####################################################
	//assigns a click listener to the question selection links so they hide on question selection when in smalll screen mode
	$("#q_nav li.nav-item").click(
		function() {
			let x = document.getElementById("q_nav");
			if (x.classList.contains("show")){
				x.classList.remove("show");
			}
		}
	);

	//assigns a click listener to the finish link
	$("#final-save").click(function() {
		//go back to the student_summary page
		let args = {"session_data":session_data};
		ajax_authorized_get("./student_summary.html", build_student_summary, args);
	});
} //end of the build_review_quiz function


///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
function build_mark_quiz(args) { 
	//this does the html building				
	let qset_data = args["data"]["data"];
	let submitters = args["data"]["submitters"];
	let submission_status = args["data"]["submission_status"];
	let session_data = args["session_data"];
	let username = session_data["username"];
	let u_id = session_data["u_id"];

	let qs_id = qset_data[0]["qs_id"];
	let s_u_id = qset_data[0]["s_u_id"];
	let s_username = qset_data[0]["s_username"];

	//fix the header
	fix_header(username);
	//disable the final-save link
	$("#final-save").attr("href","javascript:;"); 

	//do the title
	html_text = qset_data[0]["topic"] + " (" + String(qs_id) + ")" + '<br/> <span class="submitter">username: ' + s_username + '<br/>user_id: ' + qset_data[0]["s_u_id"] + '<br/>status: ' + submission_status + '</span>';
	//append to the DOM
	$("h5#title").append(html_text);

	let active_text = "active";
	let showactive_text = "show active";
	//go through the questions, from index 1 to end of array
	for (let i=1; i < qset_data.length; i++) {
		//this is the actual question sequence, i.e. "Q1", "Q2", "Q3" etc... you need to build this list locally, it is basically "Q" + index+1
		let q_seq = "Q" + String(i); 
		let html_text = ""; 
		
		//sets the first question to be selected initially and also the first of any multi-choices to be selected initially
		if (i > 1) {
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
		
		//this goes through the question part list and adds text or image tags as specified
		//the first index of the list is the q_id, so ignore that
		let question_parts = qset_data[i]["question"].slice(1,);
		for (q_part of question_parts) {
			if (q_part["type"] == "text") {
				html_text += '<p>' + q_part["data"] + '</p>' + '\n';
			}
			else if (q_part["type"] == "image") {
				html_text += '<p><img class="inline" src="./static/images/' + q_part["data"] + '"/></p>' + '\n';
			}
		}
		html_text += '<hr>' + '\n';

		//#######################################
		//answer data
		html_text += '<form>' + '\n';
		html_text += 	'<label for="form_group">Answer:</label>' + '\n';
		html_text += 	'<div class="form-group" id="form_group">' + '\n';

		//disable inputs
		let disabled_text = "disabled";
		//add the mc choices or a textbox
		if ("answer" in qset_data[i] && qset_data[i]["answer"]["type"] == "mc") {
			//goes through the mc items
			//add a blank element ot the start of array to make the indicies 1 based
			let mc_options = qset_data[i]["answer"]["data"];
			mc_options.unshift("");
			for (let j = 1; j < mc_options.length; j++) {
				let mc_id = q_seq + "_mc_" + String(j);
				//this sets the submitted radio button selection
				let checked_text = "";
				if (j == Number(qset_data[i]["answer"]["answer"])) 
					checked_text = "checked";
				
				html_text += 		'<div class="form-check">' + '\n';
				html_text += 			'<input class="form-check-input" type="radio" name="' + q_seq + '_mc" id="' + mc_id + '" value="' + String(j) + '" ' + checked_text + ' ' + disabled_text + '>' + '\n';
				html_text += 			'<label class="form-check-label" for="' + mc_id + '">' + mc_options[j] + '</label>' + '\n';
				html_text += 		'</div>' + '\n';
			}
		} else {  //the non-multichoice case
			html_text += 		'<textarea class="form-control" id="' + q_seq + '_A" rows="3" ' + disabled_text + '>' + qset_data[i]["answer"]["answer"] + '</textarea>' + '\n';
		}
		html_text += 	'</div>' + '\n';

		//add assessor grade field
		let mark_text = "";
		let mark_max = qset_data[i]["question"][0]["marks"];
		if (qset_data[i]["answer"]["grade"] != undefined) {
			mark_text = qset_data[i]["answer"]["grade"];
			if (Number(mark_text) > Number(mark_max))
				mark_text = mark_max;
			if (Number(mark_text) < -1)
				mark_text = "-1";
		} else
			mark_text = "-1";

		html_text += 	'<label for="form_group2">Mark (out of ' + qset_data[i]["question"][0]["marks"] + '):</label>' + '\n';
		html_text += 	'<div class="form-group" id="form_group2">' + '\n';
		html_text += 	'	<input type="number" style="max-width:80px;" class="form-control"  id="' + q_seq + '_M" value=' + mark_text + ' max="' + mark_max + '" min="0">' + '\n';
		html_text += 	'</div>' + '\n';
		
		//add the assessor comments text
		let comment_text = "";
		if (qset_data[i]["answer"]["comment"] != undefined)
			comment_text = qset_data[i]["answer"]["comment"];
		html_text += 	'<label for="form_group3">Assessor Comments:</label>' + '\n';
		html_text += 	'<div class="form-group" id="form_group3">' + '\n';
		html_text += 		'<textarea class="form-control" id="' + q_seq + '_C" rows="3">' + comment_text + '</textarea>' + '\n';
		html_text += 	'</div>' + '\n';
		html_text += 	'<button type="button" class="btn btn-success save-continue">Submit</button>' + '\n';
		html_text += '</form>' + '\n';
		//#######################################
		html_text += '</div>';

		//append to the DOM
		$("#q_data").append(html_text);
	}

	//does the change submitter list
	//this resets the control
	document.getElementById("submitters").value = "";

	html_text = "";
	for (sub of submitters)
		html_text += '		<option value="' + sub + '"></option>' + '\n';
	$("#submitters").append(html_text);


	//This assigns some listeners on the take_quiz page
	//####################################################
	//assigns a click listener to the question selection links so they hide on question selection when in smalll screen mode
	$("#q_nav li.nav-item").click(
		function() {
			let x = document.getElementById("q_nav");
			if (x.classList.contains("show")){
				x.classList.remove("show");
			}
		}
	);

	//assigns a click listener to the submit button as well as the finish and submit nav choice
	$(".save-continue, \
		#final-save, \
		#btn-load-submitter").click(function() {
		//set the change s_u_id flag for the case the user want to change
		let change_flag = $(this).is("#btn-load-submitter");

		let final_flag = $(this).is("#final-save");

		let marking_data = [{"qs_id":qs_id,"u_id":u_id,"s_u_id":s_u_id}];
		//get the marking data
		for (let i = 1; i < qset_data.length; i++) {
			//this is the actual question sequence, i.e. "Q1", "Q2", "Q3" etc... you need to build this list locally, it is basically "Q" + index+1
			let q_seq = "Q" + String(i);
			let mark_text = $("#" + q_seq + "_M").val();
			let comment_text = $.trim($("#" + q_seq + "_C").val());
			
			//validation
			let mark_max = qset_data[i]["question"][0]["marks"];
			if (mark_text == "")
				mark_text = "0";
			else {
				if (Number(mark_text) > Number(mark_max)) 
					mark_text = mark_max;
				if (Number(mark_text) < 0)
					mark_text = "0";
			}
			$("#" + q_seq + "_M").val(mark_text);
			marking_data.push({"mark":mark_text,"comment":comment_text});
		}

		$.ajax({
			type: 'POST',
			url: '/submit_marks_json',
			data: JSON.stringify({"data":marking_data}),
			headers: {'Authorization':session_data["token"]},
			contentType: "application/json",
			data_type: "json",
			cache: false,
			processData: false,
			async: true,
			success: function(data) {
				if (data["status"] == 'ok') {
					alert("Your marks were submitted with status: " + data["status"]);
					if (final_flag) {
						let args = {"session_data":session_data};
						ajax_authorized_get("./admin_summary.html", build_admin_summary, args);
					}

					if (change_flag) {
						//change the s_u_id
						let new_user = $('[name="input-submitter"]').val();
						s_u_id = new_user.slice(new_user.search("\\(")+1,new_user.search("\\)")).trim();
						//go to the chosen user mark page
						let args = {"session_data":session_data,
									"qs_id":qs_id,
									"s_u_id":s_u_id,
									"include_submission":"1",
									"include_submitters":"1"};
						ajax_authorized_get("./mark_quiz.html", build_mark_quiz, args);
					}
				}
				else {
					alert(data["msg"]);
					if ('target' in data) {
						window.location = data['target'];
					}
				}
			},
		});
	});  //end of submit marks code
} //end of the build_mark_quiz function


///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
function build_edit_quiz(args) {
	let qset_data = args["data"]["data"];
	let session_data = args["session_data"];
	let username = session_data["username"];
	let u_id = session_data["u_id"];

	let newfiles = [];
	
	//this does the html building				
	let qs_id = qset_data[0]["qs_id"];

	//fix the header
	fix_header(username);
	//disable the preview link
	$("#preview").attr("href","javascript:;"); 
	//disable the final save href
	$("#final-save").attr("href","javascript:;"); 

	//do the title
	html_text = qset_data[0]["topic"] + " (" + String(qs_id) + ")";
	//append to the DOM
	$("h5#title").append(html_text);

	let active_text = "active";
	let showactive_text = "show active";

	for (let i=1; i < qset_data.length; i++) {
		//this is the actual question sequence, i.e. "Q1", "Q2", "Q3" etc... you need to build this list locally, it is basically "Q" + index+1
		let q_seq = "Q" + String(i); 
		let html_text = ""; 
		
		//sets the first question to be selected initially and also the first of any multi-choices to be selected initially
		if (i > 1) {
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
		html_text += '<button type="button" class="btn btn-success add-text-btn">Add Text</button>' + '\n';
		html_text += '<button type="button" class="btn btn-success add-image-btn">Add Image</button>' + '\n';
		//hidden input button to open the file selection dialog
		html_text += '<input type="file" class="select-image" hidden/>' + '\n';
		
		//this goes through the q_data list and adds text or image tags as specified
		//NOTE: im an using the textbox with class = "im" for images and "txt" for text sections.  I am hiding the textbox for images loaded from the server
		//I need the textboxes as I will use those on exit to determine the structure to upload to the server.
		html_text += '<ul id="sortable">' + '\n';
		let question_parts = qset_data[i]["question"].slice(1,);
		for (q_part of question_parts) {
		//for (y of qset_data[ind]["q_data"]) {
			html_text += '<li><p>' + '\n';
			html_text += '    <button type="button" class="btn btn-danger delete-btn">X</button>' + '\n';
			if (q_part["type"] == "text") {
				html_text += '    <textarea class="form-control txt" rows="3">' + q_part["data"] + '</textarea>' + '\n';
			}
			else if (q_part["type"] == "image") {
				html_text += '    <img class="inline" src="./static/images/' + q_part["data"] + '"/>' + '\n';
			}
			html_text += '</p></li>' + '\n';
		}
		html_text += '</ul>' + '\n';
		html_text += '<hr>' + '\n';

		//#######################################
		//answer data
		html_text += '<form>' + '\n';
		html_text += 	'<label for="form_group">Answer</label>' + '\n';
		html_text += 	'<div class="form-group" id="form_group">' + '\n';
		//add the answer specification
		let text = "";
		if (qset_data[i]["answer"]["type"] == "mc") {
			text = "mc\n";
			text += "correct: " + qset_data[i]["answer"]["correct"].trim() + "\n";
			let mc_options = qset_data[i]["answer"]["data"];
			//add a blacnk item at the start of the array to get the indicies correct
			for (let j=0; j < mc_options.length; j++) 
				text += mc_options[j].trim() + '\n';
			text  = text.slice(0,-1);
		}
		else {
			text = "text\n";
			text += "correct: " + qset_data[i]["answer"]["correct"].trim();
		}
		html_text += 		'<textarea class="form-control" id="' + q_seq + '_A" rows="3">' + text + '</textarea>' + '\n';
		html_text += 	'</div>' + '\n';
		html_text += 	'<button type="button" class="btn btn-success save-continue">Submit</button>' + '\n';
		html_text += '</form>' + '\n';
		//#######################################
		html_text += '</div>';

		//append to the DOM
		$("#q_data").append(html_text);

		//this is required for jquery-ui sortable to work
		//you have to do it here AFTER the DOM has been built!!!!
		//note I have to use the class selector first so it selects the multiple instances of #sortable
		//if I use #sortable only, it only selects the first one (you are not meant to duplicate ids)
		$(function() {
			$(".tab-pane ul#sortable").sortable();
			$(".tab-pane ul#sortable").disableSelection();
		});
	}


	
	//This assigns some listeners on the edit_quiz page
	//####################################################
	//assigns a click listener to the question selection links so they hide on question selection when in smalll screen mode
	$("#q_nav li.nav-item").click(
		function() {
			let x = document.getElementById("q_nav");
			if (x.classList.contains("show")){
				x.classList.remove("show");
			}
		}
	);
	
	//add the handlers to the delete and add buttons
	//#######################################
	$(".add-image-btn").click(function (e) {
		//this resets the input control (important)
		for (el of document.getElementsByClassName("select-image")) 
			el.value = "";
		$(e.target.parentNode).find(".select-image").trigger("click",e);
	});

	$(".add-text-btn").click(function (e) {
		add_text(e);
	});

	$(".delete-btn").click(function (e) {
		del_item(e);
	});

	function del_item(e) {
		//this deletes an element from the question
		let ul_parent = e.target.parentNode.parentNode.parentNode;
		let li_parent = e.target.parentNode.parentNode;
		ul_parent.removeChild(li_parent);
		$(ul_parent).sortable('refresh');	
	};

	function add_text(e) {
		//this adds an element to the question, either text or an image
		//build the html li object to add
		let text = "add text here";
		let html_text = "";
		html_text += '<p>' + '\n';
		html_text += '    <button type="button" class="btn btn-danger delete-btn">X</button>' + '\n';
		html_text += '    <textarea class="form-control txt" rows="3">' + text + '</textarea>' + '\n';
		html_text += '</p>' + '\n';
		let li_new = document.createElement("li");
		li_new.setAttribute('class','ui-sortable-handle');
		$(li_new).append(html_text);
		//add to DOM
		let parent = e.target.parentNode;
		$(parent).children("#sortable").prepend(li_new);
		$(parent).children("#sortable").sortable('refresh');	
		//add delete button listener
		$(li_new).find(".delete-btn").click(function (e) {
			del_item(e);
		});
	}

	//this is the onchange evenet handler for the hidden input file selection dialog
	$(".tab-pane .select-image").on("change", function(e) {			
		//selects the freshly added <img> tag for editing
		if (!(this.files && this.files[0])) {
			return;   //if no files were selected
		}
		//get the selected file object 
		let f = this.files[0];
		//############################################
		//do some validation here if you want t avoid non-image files etc...
		if ( f["size"] > 1000000) {
			alert("Your file is > 1MB, you should try to reduce it for usability fo the web app.");
			return;
		}
		let img_allowed = ['image/gif', 'image/jpeg', 'image/png'];
		if (! img_allowed.includes(f["type"])) {
			alert('File needs to be an image file (jpg, png, gif)');
			return;
		}
		//############################################

		newfiles.push(f);

		//add the image part to the question
		add_image_part(e);
		//show the image in the new part
		let img_target = $($(this.parentNode).find("ul").children()[0]).find("img");
		//add some meta to the blob string
		let blob_str = URL.createObjectURL(f);
		//update DOM
		$(img_target).attr("src", blob_str);
		$(img_target).text("./static/images/" + f["name"]);
	});
	

	function add_image_part(e) {
		//this adds an image element to the question
		//build the html li object to add
		let data = "";
		let filename = "";   //this is a locally loaded file object

		let html_text = "";
		html_text += '<p>' + '\n';
		html_text += '    <button type="button" class="btn btn-danger delete-btn">X</button>' + '\n';
		//add the image textbox as hidden for the case we have the file 
		//html_text += '    <textarea class="form-control im" rows="3" hidden>' + filename + '</textarea>' + '\n';
		html_text += '    <img class="inline" src="./static/images/' + filename + '"/>' + '\n';
		html_text += '</p>' + '\n';

		let li_new = document.createElement("li");
		li_new.setAttribute('class','ui-sortable-handle');
		$(li_new).append(html_text);

		//add to DOM
		let parent = e.target.parentNode;
		$(parent).children("#sortable").prepend(li_new);
		$(parent).children("#sortable").sortable('refresh');	

		//add delete button listener
		$(li_new).find(".delete-btn").click(function (e) {
			del_item(e);
		});
	}
	//#######################################



	//assigns a click listener to the submit button as well as the finish and submit nav choice
	$(".save-continue, #final-save, #preview").click(function() {
		//so basically here you need to build the whole qset_data object to send
		let qset_data_new = [qset_data[0]];
		let text_data = "";
		let blobs = {};   // will hold the DOMstrings and filenames for any added images to upload

		//sets the final_flag and preview_flag
		let final_flag = false;
		if ($(this).is('#final-save'))  
			final_flag = true;
		let preview_flag = false;
		if ($(this).is('#preview'))  
			preview_flag = true;

		//parses the quiz after edits
		//go through each q
		let questions = $("#q_data").children("div");
		let i = 1;
		for (q of questions) {
			//this is the actual question sequence, i.e. "Q1", "Q2", "Q3" etc... you need to build this list locally, it is basically "Q" + index+1
			let q_seq = "Q" + String(i); 
			//copies the question header from qset_data as this was not changed
			let q_data = {"question":[qset_data[i]["question"][0]]};
			//go through each element of the question
			let q_parts = $(q).children("ul").children("li");
			for (q_part of q_parts) {
				if ($(q_part).find("textarea").length > 0) {
					//the item is a textbox
					text_data = $(q_part).find("textarea").val();
					q_data["question"].push({"type":"text","data":$.trim(text_data)});
				} 
				else if ($(q_part).find("img").length > 0) {
					//the item is an image
					let target = $(q_part).find("img");
					if (target.attr("src").slice(0,5) == "blob:") {
						//target is a new image					
						text_data = target.text();
						//extract just the filename
						text_data = text_data.substring(text_data.lastIndexOf('/')+1);
						blobs[target.attr("src")] = text_data;
					} 
					else {
						text_data = target.attr("src");    //target is an old image
						//extract just the filename
						text_data = text_data.substring(text_data.lastIndexOf('/')+1);
					}
					
					q_data["question"].push({"type":"image","data":text_data});
				}
			}
		
			//reads the data from the answer textbox
			q_data["answer"] = {};
			let header_flag = false;
			let correct_flag = false;
			let mc_option_flag = true;
			text_data = $.trim($("#" + q_seq + "_A").val());
			items = text_data.split("\n");

			if (items[0].trim() == "mc") {
				q_data["answer"]["type"] = "mc";
				q_data["answer"]["data"] = [];
				//#reject if it doesnt have at least 3 elements
				if (items.length >= 3)
					header_flag = true;
					mc_option_flag = false;
					for (item of items.slice(1,)) {
						if (item.trim().slice(0,8) == "correct:") {
							q_data["answer"]["correct"] = item.trim().slice(8,);
							correct_flag = true;
						} else {
							q_data["answer"]["data"].push(item.trim());
							mc_option_flag = true;
						}
					}
			} else if (items[0].trim() == "text") {
				q_data["answer"]["type"] = "text";
				//#reject if it doesnt have at least 2 elements
				if (items.length >= 2)
					header_flag = true;
					//join the elements in case they have newlines
					let temp = items.slice(1,).join(' ').trim();
					if (temp.slice(0,8) == "correct:") {
						q_data["answer"]["correct"] = temp.slice(8,).trim();
						correct_flag = true;
				}
			}

			//check for bad input
			if (! header_flag || ! correct_flag || ! mc_option_flag) {
				alert("The answer specification for " + q_seq + " is not acceptable, see instructions for specification, edits not committed =>\n" + text_data);
				return;
			}

			//write the question and answer sepcification
			qset_data_new.push(q_data);
			i += 1;
		}
		
		$.ajax({
			type: 'POST',
			url: '/upload_quiz',
			data: JSON.stringify({"upload_data":[qset_data_new],
								"import_flag":false}),
			headers: {'Authorization':session_data["token"]},
			contentType: "application/json",
			data_type: "json",
			cache: false,
			processData: false,
			async: true,
			success: function(data) {
				if (data["status"] == "ok") {
					alert("Your edits were submitted with status: ok");
					if (preview_flag) {
						let args = {"session_data":session_data, 
									"qs_id":qs_id, 
									"preview_flag":true,
									"include_submission":"0",
									"include_submitters":"0"};
						ajax_authorized_get("./take_quiz.html", build_take_quiz, args);
					} 
					else if (final_flag) {
						//back to the admin page if there were no issues on final commit
						let args = {"session_data":session_data};
						ajax_authorized_get("./admin_summary.html", build_admin_summary, args);
					}
				}
				else {
					alert(data["msg"]);
					if ('target' in data) {
						window.location = data['target'];
					}
				}
			},
		});

		//upload the new images
		for (f of newfiles) {
			//send to server
			let form_data = new FormData();
			form_data.append("file", f);
			$.ajax({
				type: 'POST',
				url: '/upload_image',
				headers: {'Authorization':session_data["token"]},
				data: form_data,
				async: true,
				contentType: false,
				cache: false,
				processData: false,
				success: function(data) {
					if (data["status"] == 'ok') {
						console.log(JSON.stringify(data,null,2));
					}
					else {
						alert(data["msg"]);
						if ('target' in data) {
							window.location = data['target'];
						}
					}
				}
			});
		}
	});
}


///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
function build_student_stats(args) {
	//this does the html table building				
	let stats_data = args["data"]["data"];
	let session_data = args['session_data'];
	let username = session_data["username"];
	let u_id = 	session_data["u_id"];

	//fix the header
	fix_header(username);
	//disable the finish href
	$("#finish").attr("href","javascript:;"); 

	//to be done

	$("#finish").click(function() {
		let args = {"session_data":session_data};
		ajax_authorized_get("./student_summary.html", build_student_summary, args);
	});
}//end of the build_student_stats function


///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
function build_admin_stats(args) {
	//this does the html table building				
	let stats_data = args["data"]["data"];
	let session_data = args['session_data'];
	let username = session_data["username"];
	let u_id = 	session_data["u_id"];

	//fix the header
	fix_header(username);
	//disable the finish href
	$("#finish").attr("href","javascript:;"); 

	//to be done

	$("#finish").click(function() {
		let args = {"session_data":session_data};
		ajax_authorized_get("./admin_summary.html", build_admin_summary, args);
	});
}//end of the build_admin_stats function


///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
function build_manage_users(args) {
	//this does the html table building				
	let users_data = args["data"]["data"];
	let session_data = args['session_data'];
	let username = session_data["username"];
	let u_id = 	session_data["u_id"];

	//fix the header
	fix_header(username);
	//disable the finish href
	$("#finish").attr("href","javascript:;"); 

	//does the table header
	let html_text = ""; 
	html_text = '<table class="table table-hover table-striped table-responsive" id="user-admin-table">' + '\n';
	html_text +='	<thead>' + '\n';
	html_text +='		<tr>' + '\n';
	html_text +='          <th scope="col"></th>' + '\n';
	html_text +='          <th scope="col"></th>' + '\n';
	for (header_item of users_data[0]) {
		html_text +='          <th scope="col">'+ header_item +'</th>' + '\n';
	}
	html_text +='     	</tr>' + '\n';
	html_text +='   </thead>' + '\n';

	//does the table body
	html_text +='   <tbody>' + '\n';
	for (i = 1; i < users_data.length; i++){
		html_text +='       <tr class="click-enable">' + '\n';
		html_text +='	       <td class="del-user">Del</td>' + '\n';
		html_text +='	       <td class="edit-user">Edit</td>' + '\n';
		html_text +='	       <td class="tab-uid">' + users_data[i][0] + '</td>' + '\n';
		html_text +='	       <td class="tab-admin">' + users_data[i][1] + '</td>' + '\n';
		html_text +='	       <td class="tab-username">' + users_data[i][2] + '</td>' + '\n';
		html_text +='	       <td class="tab-password">' + users_data[i][3] + '</td>' + '\n';
		html_text +='       </tr>' + '\n';
	}
	html_text +='   </tbody>' + '\n';
	html_text += '</table>' + '\n';
	
	//append to the DOM
	$("#p-user-admin-table").append(html_text);

	//assigns a click listener to the edit user cell of the table
	$(".edit-user").click(function (e) {handle_edit_user(e)});
	//assigns a click listener to the delete user cell of the table
	$(".del-user").click(function (e) {handle_delete_user(e)});

	function handle_edit_user(e) {
		$('#add-user').collapse('hide');
		$('#mod-user').collapse('show');

		$("#mod-uid").val($(e.target).parent().find(".tab-uid").text());
		$("#mod-username").val($(e.target).parent().find(".tab-username").text());
		if ($(e.target).parent().find(".tab-admin").text()=="Teacher") 
			$("#mod-admin").val(1); 
		else 
			$("#mod-admin").val(0);
	}

	function handle_delete_user(e) {
		$('#add-user').collapse('hide');
		$('#mod-user').collapse('hide');

		let u_id_edit = $(e.target).parent().find(".tab-uid").text();
		//for this request
		let args = {"session_data":session_data,
					"u_id":u_id_edit,
					"username":"",
					"password":"",
					"admin":""};
		//for the next request
		let args2 = {"session_data":session_data};
		ajax_authorized_post("./edit_user", build_manage_users, args, args2);
	}

	//assigns a click listener to the add user btn to handle the correct operation of the collaspsing elements
	$("#btn-add-user").click(function() {
		$('#add-user').collapse('show');
		$('#mod-user').collapse('hide');
	});

	//assigns a click listener to the add user submit button
	$("#add-submit").click(function() {
		let username_new = $("#add-username").val();
		let password_new = $("#add-password").val();
		let admin_new = $("#add-admin").val();

		//validation
		result = input_validation({"username":{"value":username_new}, "password":{"value":password_new}});
		if (! result) return;

		//for this request
		let args = {"session_data":session_data,
					"u_id":"",
					"username":username_new,
					"password":password_new,
					"admin":admin_new};
		//for the next request
		let args2 = {"session_data":session_data};
		ajax_authorized_post("./edit_user", build_manage_users, args, args2);
	});

	//assigns a click listener to the edit submit button
	$("#mod-submit").click(function() {
		let username_new = $("#mod-username").val();
		let password_new = $("#mod-password").val();
		let admin_new = $("#mod-admin").val();

		//validation
		result = input_validation({"username":{"value":username_new}, "password":{"value":password_new}});
		if (! result) return;

		//for this request
		let args = {"session_data":session_data,
					"u_id":$("#mod-uid").val(),
					"username":username_new,
					"password":password_new,
					"admin":admin_new};
		//for the next request
		let args2 = {"session_data":session_data};
		ajax_authorized_post("./edit_user", build_manage_users, args, args2);
	});

	$("#finish").click(function() {
		let args = {"session_data":session_data};
		ajax_authorized_get("./admin_summary.html", build_admin_summary, args);
	});
	
	//runs the datatable plugin on the table to make it sortable etc...
	//do this last as it meesses up listeners if not
	$('#user-admin-table').DataTable({
		"paging":true,
		"ordering":true,
		columnDefs: [{"orderable": false,"targets":[0,1]}],"order": [] 
	});
} //end of the build_manage_users function





///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
function build_student_stats(args) {
	//this does the html table building				
	let chart_data = args["data"]["data"];
	let session_data = args['session_data'];
	let username = session_data["username"];
	let u_id = 	session_data["u_id"];
	let qsets = args["data"]["qsets"];
	let qs_id = args["data"]["qs_id"];
	let mark_u_id = args["data"]["mark_u_id"];

	//fix the header
	fix_header(username);
	//add the qs_id to the subheaderr
	$("#title").text("Quiz: " + qs_id + ", your mark: " + mark_u_id);
	//disable the finish href
	$("#finish").attr("href","javascript:;"); 
	//add listener to the finish link
	$("#finish").click(function() {
		let args = {"session_data":session_data};
		ajax_authorized_get("./student_summary.html", build_student_summary, args);
	});

	//code for the change qs_id selection
	//this resets the control change qs_id list control
	document.getElementById("qs").value = "";
	//writes the list
	html_text = "";
	for (qs of qsets)
		html_text += '		<option value="' + qs + '"></option>' + '\n';
	$("#qs").append(html_text);
	//sets up the listener for the change qs_id button
	$("#btn-load-qs").click(function() {
		let new_qs_id = $('[name="input-qs"]').val();
		//load the stats page with the new qs_id
		let args = {"session_data":session_data,
					"qs_id":new_qs_id};
		ajax_authorized_get("./student_stats.html", build_student_stats, args);
	});

	//draw the chart
	if (chart_data.length < 3) {
		//there is only 1 data point, so the histogram is meaningless, so do not draw it, google charts will throw also
		$("#chart").text("There is only one datapoint, so charting is meaningless, wait for more people to do the quiz and get marked...");
	} else {
		//load the chart data
		$.ajax({
			url: "https://www.gstatic.com/charts/loader.js",
			dataType: "script",
			success: function() {
				google.charts.load("current", {packages:["corechart"]});
				google.charts.setOnLoadCallback(drawChart);
				function drawChart() {
				let data = google.visualization.arrayToDataTable(chart_data);
				let options = {
					title: 'Results for ' + username + ' vs the rest',
					legend: { position: 'none' },
					colors: ['#4285F4'],
					chartArea: { width: 401 },
					hAxis: {
					//ticks: [-1, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1]
					},
					bar: { gap: 0 },
					histogram: {
					bucketSize: 1,
					maxNumBuckets: 50,
					//minValue: -1,
					//maxValue: 1
					}
				};
				let chart = new google.visualization.Histogram(document.getElementById('chart'));
				chart.draw(data, options);
				}
			}
		});
	}
}





///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
function build_admin_stats(args) {
	//this does the html table building				
	let chart_data = args["data"]["data"];
	let session_data = args['session_data'];
	let username = session_data["username"];
	let u_id = 	session_data["u_id"];
	let qsets = args["data"]["qsets"];
	let qs_id = args["data"]["qs_id"];

	//fix the header
	fix_header(username);
	//add the qs_id to the subheaderr
	$("#title").text("Quiz: " + qs_id);
	//disable the finish href
	$("#finish").attr("href","javascript:;"); 
	//add listener to the finish link
	$("#finish").click(function() {
		let args = {"session_data":session_data};
		ajax_authorized_get("./admin_summary.html", build_admin_summary, args);
	});

	//code for the change qs_id selection
	//this resets the control for the change as_id selector list
	document.getElementById("qs").value = "";
	//writes the list
	html_text = "";
	for (qs of qsets)
		html_text += '		<option value="' + qs + '"></option>' + '\n';
	$("#qs").append(html_text);
	//sets up the listener for the change qs button
	$("#btn-load-qs").click(function() {
		let new_qs_id = $('[name="input-qs"]').val();
		//get the stats for the new qs_id
		let args = {"session_data":session_data,
					"qs_id":new_qs_id};
		ajax_authorized_get("./admin_stats.html", build_admin_stats, args);
	});

	//draw the chart
	if (chart_data.length < 3) {
		//there is only 1 data point, so the histogram is meaningless, so do not draw it, google charts will throw also
		$("#chart").text("There is only one datapoint, so charting is meaningless, wait for more people to do the quiz and get marked...");
	} else {
		$.ajax({
			url: "https://www.gstatic.com/charts/loader.js",
			dataType: "script",
			success: function() {
				google.charts.load("current", {packages:["corechart"]});
				google.charts.setOnLoadCallback(drawChart);
				function drawChart() {
				let data = google.visualization.arrayToDataTable(chart_data);
				let options = {
					title: 'Quiz results',
					legend: { position: 'none' },
					colors: ['#4285F4'],
					chartArea: { width: 401 },
					hAxis: {
					//ticks: [-1, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1]
					},
					bar: { gap: 0 },
					histogram: {
					bucketSize: 1,
					maxNumBuckets: 50
					}
				};
				let chart = new google.visualization.Histogram(document.getElementById('chart'));
				chart.draw(data, options);
				}
			}
		});
	}
}


