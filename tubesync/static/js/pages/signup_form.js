// Copyright (C) 2013 Screaming Cats

// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:

// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.

// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.

$(document).ready(function()
{
	var validator = $("#signup-form").validate({
		rules: {
			username: {
				required: true,
				minlength: 2,
				maxlength: 80,
			},
			email: {
				required: true,
				email: true,
				maxlength: 320,
			},
			password: {
				required: true,
				minlength: 6,
			},
			repeatpwd: {
				required: true,
				minlength: 6,
				equalTo: "#password",
			},
		},

		messages: {
			username: {
				required: "You must enter a username.",
				minlength: jQuery.format("Your username must be at least {0} characters long."),
				remote: jQuery.format("The username {0} is already taken."),
			},
			password: {
				required: "You must enter a password.",
				minlength: jQuery.format("Your password must be at least {0} characters long."),
			},
			repeatpwd: {
				required: "Passwords must match.",
				minlength: "Passwords must match.",
				equalTo: "Passwords must match."
			},
		},

		// errorPlacement: function(error, element)
		// {
		// 	if (element.is(""))
		// },

		submitHandler: function(form)
		{
			$.ajax({
				type: "POST",
				url: "/signup/ajax",
				data: $.param({
					username: $("#username").val(),
					password: $("#password").val(),
					email:    $("#email").val(),
				}),
				dataType: "json",

				success: function(data, textStatus)
				{
					if (data.success)
					{
						
					}
					else
					{
						// The server gave us an error.
						switch (data.error_id)
						{
						case "name_taken":
							alert("That username is already taken.");
							break;

						default:
							alert(data.error_msg);
							break;
						}
					}
				},

				error: function(jqXHR, jqError, httpError)
				{
					var errorMsg = "An unknown error occurred.";

					if (Math.floor(jqXHR.status / (Math.pow(10, 2)) % 10) !== 2)
					{
						errorMsg = getHTTPErrorMsg(jqXHR.status);
					}
					else
					{
						errorMsg = getJQErrorMsg(jqError);
					}

					alert(errorMsg);
				},
			});
		},
	});
});
