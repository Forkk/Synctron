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
				password: $("#password").val(),
			}),
			dataType: "json",

			success: function(data, textStatus)
			{
				if (data.success)
				{
					// Logged in
					alert("Logged in with session ID " + data.sessid);
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