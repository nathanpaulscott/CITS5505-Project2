$(document).ready(function() {
	//GENERAL NOTES ON DYNAMIC CONTENT LOADING STRATEGY...
	//all the db sourced data is either:
	//1) sent in a hidden tag (faster as only need to send data once),
	//2) on page load we do a synchronous ajax request and recieve json, the page will bloack and will have to show some loading icon while it loads,
	//3) can build the page at the server and send it

	//I am leaning towards option 2 or 1



	//##########################3
	//Admin summary page
	//This will go to the admin_summary page which shows a summary table of all quizes
    //this page allows the admin to click on a quiz to edit it, or use the bulk import/export/delete buttons
	if (window.location.pathname.search(/\/admin_summary\.html$/i) != -1) {
		//this builds the table of quizes to administer

		//the user id comes form the previous page
		u_id = "some user_id";

		//Do the Ajax Request here to fetch the admin summary table data (qset_summary)
		$.ajax({
			type: 'POST',
			url: '/admin_summary_json',
			data: JSON.stringify(u_id),
			contentType: "application/json",
			data_type: "json",
			cache: false,
			processData: false,
			async: true,
			success: function(data) {
				//write this to the DOM and trigger the download, then delete from the DOM
				build_admin_summary(data["data"]);
			},
		});

		function build_admin_summary(qset_summary) {
			//this does the html table building				
			//does the table header
			var html_text = ""; 
			html_text = '<table class="table table-hover table-striped table-responsive" id="quiz-admin-table">' + '\n';
			html_text +='	<thead>' + '\n';
			html_text +='		<tr>' + '\n';
			html_text +='          <th scope="col">#</th>' + '\n';
			for (header_item of qset_summary[0]) {
				html_text +='          <th scope="col">'+ header_item +'</th>' + '\n';
			}
			html_text +='     	</tr>' + '\n';
			html_text +='   </thead>' + '\n';

			//does the table body
			html_text +='   <tbody>' + '\n';
			for (x = 1; x < qset_summary.length; x++){
				var ind = Number(x);
				html_text +='       <tr class="click-enable">' + '\n';
				html_text +='	       <td>' + ind + '</td>' + '\n';
				html_text +='	       <td id="qset-id">' + qset_summary[ind][0] + '</td>' + '\n';
				for (y = 1; y < qset_summary[ind].length; y++){
					var ind_inner = Number(y);
					html_text +='	       <td>' + qset_summary[ind][ind_inner] + '</td>' + '\n';
				}
				html_text +='       </tr>' + '\n';
			}
			html_text +='   </tbody>' + '\n';
			html_text += '</table>' + '\n';
			
			//append to the DOM
			$("#p-quiz-admin-table").append(html_text);

			//runs the datatable plugin on the table to make it sortable etc...
			$('#quiz-admin-table').DataTable({
				//"paging":true,"ordering":true,columnDefs: [{"orderable": false,"targets":0}],"order": [] 
			});
		
			//assigns a click listener to the table rows
			$("#quiz-admin-table tbody tr.click-enable").click(function() {
				var qset_id = $(this).find("td#qset-id").text();
				var user_id = $("#user_id").text();
				alert("we need to GET 'take_quiz.html' with params:\nqset_id: " + qset_id + "\nuser_id: " + user_id);
				window.location = "./edit_quiz.html?qset_id="+qset_id+"&user_id="+user_id;
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
			//Handles the delete button
			//#################################################################################
			$("#btn-delete-submit").on("click", function() {
				// here you need to request that the server deletes the given quiz ids
				//##############################################
				var qset_id = $.trim($("#delete-config-text").val()).split(",");
				//get the current set of qs_ids
				var qset_id_db = [];
				for (qset of qset_summary.slice(1,)) {
					qset_id_db.push(qset[0]);
				}
				//get the clean set of requested qs_ids
				var qset_id_req = [];
				for (qset of qset_id) {
					if (qset_id_db.includes(qset)){
						qset_id_req.push(qset);
					}
				}

				if (qset_id_req.length != 0) {
					//alert("ajax req to delete the given subset of the qs_ids from the DB:\n" + JSON.stringify(qs_id_req,null,2));
				}
				else{
					alert("no valid quiz ids were given")
					return
				}

				//Do the Ajax Request here to send the delte list to the server
				$.ajax({
					type: 'POST',
					url: '/delete_quiz',
					data: JSON.stringify(qset_id_req),
					contentType: "application/json",
					data_type: "json",
					cache: false,
					processData: false,
					async: true,
					success: function(data) {
						//for testing
						//alert(JSON.stringify(data,null,2));
						//give a status msg
						//$("#btn-delete-submit").after("<span>&nbsp&nbspStatus: " + JSON.stringify(data) + "</span>");
						$("#span-delete-submit").text("Status: " + data["Status"] + ", msg: " + data["msg"]);
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
				var qset_id = $.trim($("#export-config-text").val()).split(",");
				//get the current set of qs_ids
				var qset_id_db = [];
				for (qset of qset_summary.slice(1,)) {
					qset_id_db.push(qset[0]);
				}
				//get the clean set of requested qs_ids
				var qset_id_req = [];
				for (qset of qset_id) {
					if (qset_id_db.includes(qset)){
						qset_id_req.push(qset);
					}
				}

				if (qset_id[0].search(/all/i) != -1) {
					//alert("ajax req to export all quizes:\n" + JSON.stringify(qset_id_db,null,2));
					qset_id_req = qset_id_db;
				}
				else if (qset_id_req.length != 0) {
					//alert("ajax req to export the given subset of the qs_ids:\n" + JSON.stringify(qset_id_req,null,2));
				}
				else {
					alert("no valid quiz ids were given");
					return;
				}

				//Do the Ajax Request here to fetch the desired question sets
				$.ajax({
					type: 'POST',
					url: '/download_quiz',
					data: JSON.stringify(qset_id_req),
					contentType: "application/json",
					data_type: "json",
					cache: false,
					processData: false,
					async: true,
					success: function(data) {
						//for testing
						//give a status msg
						$("#span-export-submit").text("Status: " + data["Status"] + ", msg: " + data["msg"]);
						//write this to the DOM and trigger the download, then delete from the DOM
						var el = document.getElementById('a-export');
						var filename = "export.quiz";
						var href_text = "data:application/xml;charset=utf-8,";
						href_text += JSON.stringify(data["data"], null, 2);
						el.setAttribute("href", href_text);
						el.setAttribute("download", filename);
						el.click();
						el.setAttribute("href", "");
						el.setAttribute("download", "");
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
				$("#import-config").text("");
				document.getElementById("input-import").value = "";
				$('#import-config').collapse('show');
				document.getElementById('input-import').click();
			});
			//this is the onchange evenet handler for the hidden input file selection dialog
			$("#input-import").on("change", function() {
				//this code accepts multiple files, the quiz files should be .quiz and just be a text file of a json object with the correct format specifying the quiz text, answer types and images.  So we validate these files.  Any non .quiz files, are assumed to be associated image files and are just uploaded to the server, there is no crosschecking done locally, that can be done server-side later.  The quizes will still work with no image files, the images just will not render
				
				var files = this.files;
				for (f of files){
					//alert('you selected: ' + f["name"]);
					if (f["name"].search(/\.quiz/i) == -1) {
						//this is for images, upload them 

						//do som evalidation here if you want t avoid non-image files etc...
						if ( f["size"] > 1000000) {
							$("#import-config").append("Your file '" + f["name"] + "' is > 1MB, you should try to reduce it for usability fo the web app.  Not uploading it....<br/>");
							continue;
						}
						var img_allowed = ['image/gif', 'image/jpeg', 'image/png'];
						if (! img_allowed.includes(f["type"])) {
							$("#import-config").append("Your file '" + f["name"] + "' needs to be an image file (jpg, png, gif).  Not uploading it....<br/>");
							continue;
						}
						//alert(f["name"] + ' was accepted');

						//send to server
						var form_data = new FormData();
						form_data.append("file", f);
						$.ajax({
							type: 'POST',
							url: '/upload_image',
							data: form_data,
							async: true,
							contentType: false,
							cache: false,
							processData: false,
							success: function(data) {
								//testing
								//alert(JSON.stringify(status));
								$("#import-config").append(JSON.stringify(data,null,2) + "<br/>");
							}
						});

					}
					else {
						//this is for the .quiz files
						//this uses a closure to handle all the file read and to pass the filename in, I still do not understand how it works
						//this is for .quiz text files which contain quiz data in the specified json format.  we validate each one and reject if it fails (informing the user why)
						var reader = new FileReader();
						reader.onload = (function(e1,files_accept) {
							return function(e2) {
								var name = e1.name;
								var file_data = e2.target.result;
								//alert("file length is: " + file_data.length + " chars");
								try{
									var qs_data = JSON.parse(file_data);
								}
								catch(err) {
									$("#import-config").append("failed parsing '" + name + "' not uploading....<br/>");
									//alert('failed parsing ' + name + ' not uploading....');
									return;
								}
								//alert('parsing ' + name + ', then sending to the server');

								////////////////////////////////////////////////
								////////////////////////////////////////////////
								////////////////////////////////////////////////
								////////////////////////////////////////////////
								//NEED TO WRITE THE VALIDATION 
								////////////////////////////////////////////////
								////////////////////////////////////////////////
								////////////////////////////////////////////////
								////////////////////////////////////////////////

								//send to server
								$.ajax({
									type: 'POST',
									url: '/upload_quiz',
									data: JSON.stringify(qs_data),
									contentType: "application/json",
									data_type: "json",
									cache: false,
									processData: false,
									async: true,
									success: function(data) {
										//for testing
										//alert(JSON.stringify(status,null,2));
										data["msg"] = "Server received: '" + name + "'";
										$("#import-config").append(JSON.stringify(data,null,2) + "<br/>");
									},
								});

							};
						})(f);
						reader.readAsText(f);
					}
				}
			});
		} //end of the build_admin_summary function
	} //end of the admin_summary code



	//##########################3
	//edit_quiz page
	//This allows the admin to edit a quiz: adjust the order of text/image elements, set the answer type, add/delete text/image elements, import new .quiz spec to overwrite
	if (window.location.pathname.search(/\/edit_quiz\.html$/i) != -1) {
		//this is required for jquery-ui sortable to work
		//note I have to use the class selector first so it selects the multiple instances of #sortable
		//if I use #sortable only, it only selects the first one (you are not meant to duplicate ids)
		$(function() {
			$(".tab-pane ul#sortable").sortable();
			$(".tab-pane ul#sortable").disableSelection();
		});
	
		//user_id
		u_id = "admin123";
		// qset_id, that was chosen
		var qset_id = "QS435";
		// qset_id, that was chosen
		var qset_name = "Some Quiz Name";
		//q_ids in the selected qset, the index + 1 is the sequence of the question 
		var q_id = ["x243","y22","z43","x534","z115"];
		//the question specification has 2 possible fields per question, q_data and a_data if it is an multi-choice
		//q_data is a list of text and/or images, you can have as many as you like 
		//a_data is a list of multichoice answer options, you can have as many as you like
		//if the question requires a text answer, just do not specify a_data
		var qset_data = {
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
		//do the title
		html_text = qset_name + ' (qset_id: ' + qset_id + ')';
		//append to the DOM
		$("h5#title").append(html_text);

		var active_text = "active";
		var showactive_text = "show active";
		for (x in q_id) {
			var ind = Number(x)+1;
			//this is the actual question sequence, i.e. "Q1", "Q2", "Q3" etc... you need to build this list locally, it is basically "Q" + index+1
			var q_seq = "Q" + String(ind); 
			var html_text = ""; 
			
			//sets the first question to be selected initially and also the first of any multi-choices to be selected initially
			if (x > 0) {
				active_text = "";
				showactive_text = "";
			}
			
			//do the menu items
			html_text = '<li class="nav-item"><a class="nav-link ' + active_text + '" id="' + q_seq + '" data-toggle="pill" href="#' + q_seq + '-data" role="tab" aria-controls="' + q_seq + '-data" aria-selected="false">' + q_seq + '(' + q_id[x] + ')</a></li>';
			//append to the DOM
			$("#q_nav ul.nav").append(html_text);

			//question data
			//#######################################
			html_text = '<div class="tab-pane fade ' + showactive_text + '" id="' + q_seq + '-data" role="tabpanel" aria-labelledby="' + q_seq + '">' + '\n';
			html_text += '<h5>' + q_seq + ' (' + q_id[x] + ')</h5>' + '\n';
			html_text += '<button type="button" class="btn btn-success add-text-btn">Add Text</button>' + '\n';
			html_text += '<button type="button" class="btn btn-success add-image-btn">Add Image</button>' + '\n';
			//hidden input button to open the file selection dialog
			html_text += '<input type="file" id="select-image" hidden/>' + '\n';
			
			//this goes through the q_data list and adds text or image tags as specified
			//NOTE: im an using the textbox with class = "im" for images and "txt" for text sections.  I am hiding the textbox for images loaded from the server
			//I need the textboxes as I will use those on exit to determine the structure to upload to the server.
			html_text += '<ul id="sortable">' + '\n';
			for (y of qset_data[ind]["q_data"]) {
				html_text += '<li><p>' + '\n';
				html_text += '    <button type="button" class="btn btn-danger delete-btn">X</button>' + '\n';
				if (y.search(/^text:/) != -1) {
					html_text += '    <textarea class="form-control txt" rows="3">' + y.slice(5,) + '</textarea>' + '\n';
				}
				else if (y.search(/^image:/) != -1) {
					html_text += '    <img class="inline" src="./static/images/' + y.slice(6,) + '"/>' + '\n';
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

			//add the mc choices or a textbox
			var data = "";
			if ("a_data" in qset_data[ind]) {
				data = "mc:\n";
				//goes through the mc items
				for (y in qset_data[ind]["a_data"]) {
					data += qset_data[ind]["a_data"][y] + '\n';
				}
				html_text += 		'<textarea class="form-control" id="' + q_seq + '_A" rows="3">' + data + '</textarea>' + '\n';
			} else {  //the non-multichoice case
				data = "text";
				html_text += 		'<textarea class="form-control" id="' + q_seq + '_A" rows="3">text</textarea>' + '\n';
			}
			
			html_text += 	'</div>' + '\n';
			html_text += '</form>' + '\n';
			//#######################################
			html_text += '</div>';

			//append to the DOM
			$("#q_data").append(html_text);
		}
	
		
		//This assigns some listeners on the edit_quiz page
		//####################################################
		//add the handlers to the delete and add buttons
		//#######################################
		$(".add-image-btn").click(function (e) {
			$(e.target.parentNode).find("#select-image").trigger("click",e);
		});

		$(".add-text-btn").click(function (e) {
			add_text(e);
		});

		$(".delete-btn").click(function (e) {
			del_item(e);
		});

		function del_item(e) {
			//this deletes an element from the question
			var ul_parent = e.target.parentNode.parentNode.parentNode;
			var li_parent = e.target.parentNode.parentNode;
			ul_parent.removeChild(li_parent);
			$(ul_parent).sortable('refresh');	
		};

		function add_text(e) {
			//this adds an element to the question, either text or an image
			//build the html li object to add
			var data = "add text here";
			var html_text = "";
			html_text += '<p>' + '\n';
			html_text += '    <button type="button" class="btn btn-danger delete-btn">X</button>' + '\n';
			html_text += '    <textarea class="form-control txt" rows="3">' + data + '</textarea>' + '\n';
			html_text += '</p>' + '\n';
			var li_new = document.createElement("li");
			li_new.setAttribute('class','ui-sortable-handle');
			$(li_new).append(html_text);
			//add to DOM
			var parent = e.target.parentNode;
			$(parent).children("#sortable").prepend(li_new);
			$(parent).children("#sortable").sortable('refresh');	
			//add delete button listener
			$(li_new).find(".delete-btn").click(function (e) {
				del_item(e);
			});
		}

		//this is the onchange evenet handler for the hidden input file selection dialog
		$(".tab-pane #select-image").on("change", function(e) {			
			//selects the freshly added <img> tag for editing
			if (!(this.files && this.files[0])) {
				return;   //if no files were selected
			}
			//get the selected file object 
			var f = this.files[0];
			//############################################
			//do som evalidation here if you want t avoid non-image files etc...
			if ( f["size"] > 1000000) {
				alert("Your file is > 1MB, you should try to reduce it for usability fo the web app.");
				return;
			}
			var img_allowed = ['image/gif', 'image/jpeg', 'image/png'];
			if (! img_allowed.includes(f["type"])) {
				alert('File needs to be an image file (jpg, png, gif)');
				return;
			}
			//############################################

			//add the DOM element here
			add_image(e);

			//get the target DOM <img> element and update the src part
			var img_target = $($(this.parentNode).find("ul").children()[0]).find("img");
			//add some meta to the blob string
			var blob_str = URL.createObjectURL(f);
			//update DOM
			$(img_target).attr("src", blob_str);
			$(img_target).text("./static/images/" + f["name"]);
		});
		

		function add_image(e) {
			//this adds an image element to the question
			//build the html li object to add
			var data = "";
			var filename = "";   //this is a locally loaded file object

			var html_text = "";
			html_text += '<p>' + '\n';
			html_text += '    <button type="button" class="btn btn-danger delete-btn">X</button>' + '\n';
			//add the image textbox as hidden for the case we have the file 
			//html_text += '    <textarea class="form-control im" rows="3" hidden>' + filename + '</textarea>' + '\n';
			html_text += '    <img class="inline" src="./static/images/' + filename + '"/>' + '\n';
			html_text += '</p>' + '\n';

			var li_new = document.createElement("li");
			li_new.setAttribute('class','ui-sortable-handle');
			$(li_new).append(html_text);

			//add to DOM
			var parent = e.target.parentNode;
			$(parent).children("#sortable").prepend(li_new);
			$(parent).children("#sortable").sortable('refresh');	

			//add delete button listener
			$(li_new).find(".delete-btn").click(function (e) {
				del_item(e);
			});
		}
		//#######################################



		//assigns a click listener to the submit button as well as the finish and submit nav choice
		/*
		qset_data is a json object of the follwing format:
		qset_data = 
		{"qset_id":"XXXX",
		 "u_id":"XXXX,
		 1:{q_data:["text:some text","image:some_image.jpg","text:some text"...], 
		 	a_data=["option1","option2","option3"...]},
		 2:{q_data:["text:some text","image:some_image.jpg","text:some text"...]}
		 3:{q_data:["text:some text","image:some_image.jpg"...]},
		 4:{q_data:["text:some text","image:some_image.jpg","text:some text"...], 
		 	a_data=["option1","option2","option3"...]}}
		
		The blobs object just holds any details of added images
		blobs = {"blob string":"filename", "blob string":"filename"}
		*/
		$("#final-save").click(
				function() {
				var text_data = "";
				var qset_data = {"qset_id":qset_id,"u_id":u_id};
				var blobs = {};   // will hold the DOMstrings and filenames for any added images to upload
				//parses the quiz after edits
				//go through each q
				for (var i=0;i<q_id.length;i++) {
					var ind = Number(i)+1;
					//this is the actual question sequence, i.e. "Q1", "Q2", "Q3" etc... you need to build this list locally, it is basically "Q" + index+1
					var q_seq = "Q" + String(ind); 
					qset_data[ind]={"q_data":[]};
					var q_items = $("#" + q_seq + "-data ul").children();
					//go through each element of the question
					for (item of q_items) {
						text_data = $(item).find("textarea").val();
						if (text_data != undefined) {
							//the item is a textbox
							qset_data[ind]["q_data"].push("text:" + $.trim(text_data));
						} else {
							//the item is an image
							var target = $(item).find("img");
							if (target.attr("src").slice(0,5) == "blob:") {
								text_data = target.text();
								blobs[target.attr("src")] = text_data;
							} else {
								text_data = target.attr("src");
							}
							qset_data[ind]["q_data"].push("image:" + text_data);
						}
					}
					
					//reads the data from the answer textbox
					//do nothing if it is not "mc:...."
					text_data = $.trim($("#" + q_seq + "_A").val());
					if (text_data.slice(0,3) == "mc:") {
						qset_data[ind]["a_data"] = [];
						text_data = text_data.slice(3,).trim();
						for (mc_item of text_data.split(",")) {
							qset_data[ind]["a_data"].push(mc_item.trim());
						}
					}
				}

				//at this point qset_data holds all the data required for the particular quiz(question set), to stringify it => JSON.stringify(qset_data);
				//we also need to upload the images added.  We reference them by the DOMstrings in the blobs object.

				//temp for debugging
				text_data = "";
				text_data += "ajax update the server with the edited quiz data for qset_id: " + qset_id + "\n"; 
				text_data += JSON.stringify(qset_data, null, 2);
				console.log(text_data);
				console.log("the DOMstrings for added images are:\n" + JSON.stringify(blobs,null,2));
				alert("the DOMstrings for added images are:\n" + JSON.stringify(blobs,null,2) + "\n\n The question data is:\n" + text_data);
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

	} //end of the edit_quiz code



	//###########################################################################
	//###########################################################################
	//###########################################################################
	//###########################################################################
	//student_summary page
	//This will go to the student quiz summary page, the student can see the staus of the quizes and select a quiz t take
	if (window.location.pathname.search(/\/student_summary\.html$/i) != -1) {
		//this builds the table of quizes to take

		//the user id comes form the previous page
		u_id = "some user_id";

		//Do the Ajax Request here to fetch the student summary table data (qset_summary)
		$.ajax({
			type: 'POST',
			url: '/student_summary_json',
			data: JSON.stringify(u_id),
			contentType: "application/json",
			data_type: "json",
			cache: false,
			processData: false,
			async: true,
			success: function(data) {
				//write this to the DOM and trigger the download, then delete from the DOM
				build_student_summary(data["data"]);
			},
		});

		function build_student_summary(qset_summary) {
			//this does the html table building				
			//does the table header
			var html_text = ""; 
			html_text = '<table class="table table-hover table-striped table-responsive" id="quiz-selection-table">' + '\n';
			html_text +='	<thead>' + '\n';
			html_text +='		<tr>' + '\n';
			html_text +='          <th scope="col">#</th>' + '\n';
			for (header_item of qset_summary[0]) {
				html_text +='          <th scope="col">'+ header_item +'</th>' + '\n';
			}
			html_text +='     	</tr>' + '\n';
			html_text +='   </thead>' + '\n';

			//does the table body
			html_text +='   <tbody>' + '\n';
			for (x = 1; x < qset_summary.length; x++){
				var ind = Number(x);
				//enable selection only if the quiz has not been completed yet
				if (qset_summary[ind][5].search(/^(completed|marked)$/i) == -1) {
					html_text +='       <tr class="click-enable">' + '\n';
				}
				else {
					html_text +='       <tr>' + '\n';
				}
				html_text +='	       <th scope="row">' + ind + '</th>' + '\n';
				html_text +='	       <td id="qset-id">' + qset_summary[ind][0] + '</td>' + '\n';
				for (y = 1; y < qset_summary[ind].length; y++){
					var ind_inner = Number(y);
					html_text +='	       <td>' + qset_summary[ind][ind_inner] + '</td>' + '\n';
				}
				html_text +='       </tr>' + '\n';
			}
			html_text +='   </tbody>' + '\n';
			html_text += '</table>' + '\n';
			
			//append to the DOM
			$("#p-quiz-selection-table").append(html_text);

			//runs the datatable plugin on the table to make it sortable etc...
			$('#quiz-selection-table').DataTable();

			//assigns a click listener to the table rows
			$("#quiz-selection-table tbody tr.click-enable").click(function() {
				var qset_id = $(this).find("td#qset-id").text();
				var user_id = $("#user_id").text();
				alert("we need to GET 'take_quiz.html' with params:\nqset_id: " + qset_id + "\nuser_id: " + user_id);
				window.location = "./take_quiz.html?qset_id="+qset_id+"&user_id="+user_id;
			});
		}//end of the build_student_summary function
	} //end of the student_summary code


	//#######################################################
	//#######################################################
	//#######################################################
	//#######################################################
	//#######################################################
	//Take Quiz page
	//This loads the selected quiz and allows the student to answer the questions, the student can save as they go, the link for final commit is the top left nav bar
	if (window.location.pathname.search(/\/take_quiz\.html$/i) != -1) {
		//user_id
		u_id = "fred123";
		// qset_id, that was chosen
		var qset_id = "QS435";
		var qset_name = "Some Quiz Name";
		//q_ids in the selected qset, the index + 1 is the sequence of the question 
		var q_id = ["x243","y22","z43","x534","z115"];
		//the question specification has 2 possible fields per question, q_data and a_data if it is an multi-choice
		//q_data is a list of text and/or images, you can have as many as you like 
		//a_data is a list of multichoice answer options, you can have as many as you like
		//if the question requires a text answer, just do not specify a_data
		var qset_data = {
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
		//do the title
		html_text = qset_name;
		//append to the DOM
		$("h5#title").append(html_text);

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
			for (y of qset_data[ind]["q_data"]) {
				if (y.search(/^text:/) != -1) {
					html_text += '<p>' + y.slice(5,) + '</p>' + '\n';
				}
				else if (y.search(/^image:/) != -1) {
					html_text += '<p><img class="inline" src="./static/images/' + y.slice(6,) + '"/></p>' + '\n';
				}
    		}
			html_text += '<hr>' + '\n';

			//#######################################
			//answer data
			html_text += '<form>' + '\n';
			html_text += 	'<label for="form_group">Answer</label>' + '\n';
			html_text += 	'<div class="form-group" id="form_group">' + '\n';

			//add the mc choices or a textbox
			if ("a_data" in qset_data[ind]) {
				var checked_text = "checked";
				//goes through the mc items
				for (y in qset_data[ind]["a_data"]) {
					choice_ind = Number(y) + 1;
					var mc_id = 'mc_' + String(choice_ind);
					if (choice_ind > 1) checked_text = "";
					html_text += 		'<div class="form-check">' + '\n';
					html_text += 			'<input class="form-check-input" type="radio" name="' + q_seq + '_mc" id="' + mc_id + '" value="' + String(choice_ind) + '" ' + checked_text + '>' + '\n';
					html_text += 			'<label class="form-check-label" for="' + mc_id + '">' + qset_data[ind]["a_data"][y] + '</label>' + '\n';
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
	
		
		//This assigns some listeners on the take_quiz page
		//####################################################
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

	} //end of the take_quiz code

}); //end of the on_load section






