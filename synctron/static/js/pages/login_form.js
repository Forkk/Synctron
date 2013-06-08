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
	$("#login-form").submit(function(evt)
	{
		evt.preventDefault();

		$.ajax({
			type: "POST",
			url: "/login/ajax",
			data: $.param({
				username: $("#username").val(),
				password: CryptoJS.SHA384($("#password").val()).toString(),
			}),
			dataType: "json",

			success: function(data, textStatus)
			{
				if (data.success)
				{
					// Logged in. Store session ID in a cookie and redirect to the home page.
					if (loginSuccessHref !== undefined)
						window.location.href = loginSuccessHref;
					else
						window.location.href = "/";
				}
				else
				{
					switch (data.error_id)
					{
					case "bad_login":
						alert("Wrong username or password.");
						break;

					default:
						alert("An unknown error occurred: " + data.error_msg);
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
	});
});
