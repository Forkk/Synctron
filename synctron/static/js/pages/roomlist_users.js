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

function initWebSocket()
{
	if (!window.WebSocket)
	{
		if (window.MozWebSocket)
		{
			window.WebSocket = window.MozWebSocket;
		}
		else
		{
			alert("Your browser doesn't support WebSockets.");
		}
	}

	ws = new WebSocket(wsapi_url);

	ws.onopen = function(evt)
	{
		sendAction({ action: "roomlist", listen: true })
	}

	ws.onmessage = function(evt)
	{
		console.log("Message from server: " + evt.data);

		var data;
		var action;

		try
		{
			data = JSON.parse(evt.data);
			action = data.action;
		}
		catch (SyntaxError) { }

		if (action === undefined)
		{
			alert("Server sent invalid message. Not good.");
			console.log("Server sent invalid message:");
			console.log(evt.data);
			ws.close();
		}

		var actionFunc = actions[action]
		if (actionFunc === undefined)
		{
			console.log("Server sent unknown action '" + actionFunc + "'. Ignoring.");
		}
		else
		{
			actionFunc(data, ws);
		}
	}

	ws.onclose = function(evt)
	{
		console.log("WebSocket closed.");
		// var alertDiv = $("<div class='alert alert-error hide'>");
		// alertDiv.html("<b>Error:</b> Lost connection to the synchronization server. Try refreshing the page in a few seconds.");
		// $("#main-container").prepend(alertDiv);
		// alertDiv.slideDown();
	}
}

function sendAction(data)
{
	var msg = JSON.stringify(data);
	console.log("Sending action: " + msg);
	ws.send(msg);
}

var actions = 
{
	roomlist: function(data)
	{
		updateRoomList(data.rooms)
	},
};

function updateRoomList(rooms)
{
	var body = $(".roomlist tbody");
	body.html("");

	rooms.forEach(function(room, index)
	{
		var row = $("<tr>");

		var nameCol = $("<td>").append($("<a>").attr("href", "/room/" + room.name).text(room.name));
		var userCountCol = $("<td>").text(room.usercount);

		row.append(nameCol);
		row.append(userCountCol);

		body.append(row);
	});
}

$(document).ready(function()
{
	initWebSocket();
});
