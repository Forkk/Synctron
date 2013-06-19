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

function updateRoomList(rooms)
{
	var body = $(".roomlist tbody");
	body.html("");

	rooms.forEach(function(room, index)
	{
		var row = $("<tr>");

		var nameCol = $("<td>").append($("<a>").attr("href", "/room/" + room.slug).text(room.title));
		var slugCol = $("<td>").append($("<a>").attr("href", "/room/" + room.slug).text(room.slug));
		var userCountCol = $("<td>").addClass("text-right").text(room.usercount);

		row.append(nameCol);
		row.append(slugCol);
		row.append(userCountCol);

		body.append(row);
	});
}

$(document).ready(function()
{
	socket = io.connect("/roomlist");

	socket.on("connect", function()
	{
		console.log("Socket connected. Requesting list update.");
		socket.emit("list_update");
	});

	socket.on("room_list_users", function(rooms)
	{
		console.log("Got user count room list update.");
		updateRoomList(rooms);
	});
});
