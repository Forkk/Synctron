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


/////////////////////////
//// WEBSOCKET STUFF ////
/////////////////////////

var WEB_SOCKET_SWF_LOCATION = "/static/js/socketio/WebSocketMain.swf";

var iframeApiReady = false;
var socketReady = false;

var socket;

function stuffReady()
{
	if (socketReady && iframeApiReady) 
	{
		console.log("Joining room...");
		socket.emit("join", room_slug);

		// Start the update state timeout loop.
		updateStateTimeout();

		// Enable buttons.
		enableToolbarBtns();
	}
}

var alertShowing = false;

function alertBox(msg, alertClass, hideTimeout)
{
	if ($("#alert-div").hasClass("hide"))
		$("#alert-div").slideDown();

	if (alertClass !== undefined)
	{
		$("#alert-div").removeClass("alert-error");
		$("#alert-div").removeClass("alert-success");
		$("#alert-div").removeClass("alert-info");
		$("#alert-div").addClass("alert-" + alertClass);
	}

	if (msg !== undefined)
		$("#alert-div").text(msg);

	if (hideTimeout !== undefined)
		setTimeout(function() { $("#alert-div").slideUp(); }, hideTimeout);
}

function initWebSocket()
{
	if (socket !== undefined)
		return;
	
    socket = io.connect("/room");

	socket.on("connect", function()
	{
		console.log("Socket connected.");
		socketReady = true;
		stuffReady();
	});

	socket.on("connecting", function(type)
	{
		console.log("Trying to connect via " + type + "...");
	});

	socket.on("connect_failed", function()
	{
		console.log("Failed to connect to the server.");
		alertBox("Failed to connect to the server.");
	});

	socket.on("disconnect", function()
	{
		console.log("Lost connection to server.");
		alertBox("Lost connection to the server.", "error");
	});

	socket.on("reconnecting", function()
	{
		console.log("Reconnecting to the server.");
		alertBox("Lost connection to the server. Attempting to reconnect.", "warning");
	});

	socket.on("reconnect", function()
	{
		console.log("Reconnected to the server.");
		alertBox("Reconnected to the server.", "success", 2000);
	});

	socket.on("reconnect_failed", function()
	{
		console.log("Failed to reconnect.");
		alertBox("Failed to reconnect to the server.", "error");
	});

	socket.on("error", function(reason)
	{
		console.error("Error: " + reason);
		alertBox("Error: " + reason, "error");
	});

	socket.on("room_not_found", function()
	{
		$("#room-not-found-modal").modal({
			keyboard: false,
			backdrop: "static",
		});
	});

	socket.on("sync", function(video_time, is_playing)
	{
		changePlaying(is_playing);
		changeCurrentTime(video_time);
	});

	socket.on("video_changed", function(playlist_position, video_id)
	{
		console.log("Video changed to " + video_id);

		// Set the current video.
		changeCurrentIndex(playlist_position);
		vplayer.loadVideoById(video_id === undefined || video_id === null ? "" : video_id);

		console.log("Requesting sync...");
		socket.emit("sync");

		// Request sync again in a bit to make sure the video is properly synchronized.
		setTimeout(function()
		{
			console.log("Requesting sync...");
			socket.emit("sync");
		}, (1*1000));

		// Update the playlist height to make sure the layout works.
		updatePlaylistHeight();
	});

	socket.on("playlist_update", function(entries)
	{
		playlistObj = [];
		entries.forEach(function(video, index)
		{
			addPlaylistEntry(video, index);
		});
		updatePlaylistElement();
	});

	socket.on("video_added", function(entry, index)
	{
		// Videos were added. Add them to the playlist.
		// data.entries.forEach(function(video, index)
		// {
			// The index for each entry added should be the index of the first one 
			// plus the index of the entry in the entries list.
			addPlaylistEntry(entry, index);
		// });
		updatePlaylistElement();
	});

	socket.on("videos_removed", function(indices)
	{
		// Videos were removed. Remove them from the playlist.
		// This is a bit complicated, because if we just start removing indices,
		// the index of everything after what we've just removed will change.
		// To get around this issue, we need to remove the highest indices first.
		indices.sort(function(a, b)
		{
			// If a is greater, a comes first.
			if (a > b)
				return -1;
			// If b is greater, b comes first.
			else if (a < b)
				return 1;
			// If they're equal, return 0.
			else
				return 0;
		});

		// Now that the list of indices is sorted with greater indices first,
		// we can just go through it and remove everything.
		indices.forEach(function(index)
		{
			removePlaylistEntry(index, false);

			// If the index we're removing is less than the index of the currently playing video, 
			// we'll need to decrement playlist_pos too.
			playlist_pos--;
		});
		updatePlaylistElement();
	});

	socket.on("video_moved", function(old_index, new_index)
	{
		// TODO: Implement video moved.
		socket.emit("reload_playlist");
	});

	socket.on("userlist_update", function(userlist)
	{
		userlistObj = [];

		userlist.forEach(function(user, index)
		{
			addUserListEntry(user, index, false);
		});
		updateUserListTable();
	});

	socket.on("chat_message", function(message, from_user)
	{
		var chatbox = $("#chatbox-textarea");

		// Determine whether or not we're going to want to scroll to the bottom after we append the message.
		var distFromBottom = (chatbox[0].scrollHeight - chatbox.scrollTop()) - chatbox.outerHeight();
		var scrollToBottom = Math.abs(distFromBottom) <= 5;

		// First, we need to make sure any HTML tags are escaped.
		var escapedMsg = $("<div/>").text(message).html();

		// Now, we create a <p> element for the message and append it to the chat box.
		var msgElement = $("<p><b>" + from_user + ":</b>&nbsp;" + escapedMsg + "</p>")
		chatbox.append(msgElement);

		// Finally, if the chatbox was scrolled to the bottom before,
		// we need to scroll it back to the bottom because we've added a new line.
		if (scrollToBottom)
			chatbox.scrollTop(chatbox[0].scrollHeight);
	});

	socket.on("error_occurred", function(errid, message)
	{
		alert("Error: " + message);
	});
}

function onYouTubeIframeAPIReady()
{
	// Set up player
	var lastState = -2;
	vplayer = new YT.Player("player", {
		width: "592",
		height: "333",
		videoId: "",
		playerVars: { enablejsapi: 1, wmode: "opaque", },
		events: {
			onStateChange: function(event)
			{
				// When we finish buffering, we should sync.
				if (event.data != YT.PlayerState.BUFFERING && lastState == YT.PlayerState.BUFFERING)
				{
					console.log("Video stopped buffering. Requesting sync...");
					socket.emit("sync");
				}

				lastState = event.data;
			},

			onReady: function(event)
			{
				console.log("YouTube iframe API loaded.");
				iframeApiReady = true;
				stuffReady();
			},
		}
	});

	initWebSocket();
};


/////////////////////////
//// USER LIST LOGIC ////
/////////////////////////

// Regular expression for matching a guest's username.
var guestRegex = /Guest \d+/;

var userlistObj = [];

function updateUserListTable()
{
	$("#userlist-body").html("");
	userlistObj.forEach(function(entry, index)
	{
		var row = $("<tr id='ulist-" + index + "'>")
		var typeCol = $("<td>");
		var usernameCol = $("<td class='expand'>" + entry.name + "</td>")


		if (entry.isyou) row.addClass("info");
		if (entry.isguest) row.addClass("italic");


		typeColIcon = $("<i>");

		if (entry.isowner)
		{
			typeColIcon.addClass("icon-star");
			typeCol.attr("title", "Room Owner");
		}
		else if (entry.isadmin)
		{
			typeColIcon.addClass("icon-star-empty");
			typeCol.attr("title", "Room Admin");
		}
		else
		{
			typeColIcon.addClass("icon-user");
			typeCol.attr("title", " Normal User");
		}

		typeCol.append(typeColIcon);
		typeCol.tooltip({
			placement: "left",
			container: "#userlist-scroll",
			trigger: "hover",
		});

		row.append(typeCol);
		row.append(usernameCol);
		$("#userlist-body").append(row);
	});
	$("#userlist-title").text(userlistObj.length.toString() + " Users");
}

function addUserListEntry(data, index, shouldUpdateUserList)
{
	var entry = {
		name: data.username,
		isyou: data.isyou,
		isguest: data.isguest,
		isadmin: data.isadmin,
		isowner: data.isowner,
	};
	userlistObj.splice(index, 0, entry);

	if (shouldUpdateUserList === undefined || shouldUpdateUserList === true)
		updateUserListTable();
}


////////////////////////
//// PLAYLIST LOGIC ////
////////////////////////

// Array for storing the playlist in.
var playlistObj = [];

// Index of the currently playing video in the playlist.
var playlist_pos = -1;

// Re-builds the playlist table body element.
function updatePlaylistElement()
{
	$("#playlist-body").html("");
	playlistObj.forEach(function(entry, index)
	{
		var changeVideoClickFunc = function(evt)
		{
			evt.preventDefault();
			var clickedindex = evt.data;
			socket.emit("change_video", clickedindex);
		};

		var removeVideoClickFunc = function(evt)
		{
			evt.preventDefault();
			var clickedindex = evt.data;
			socket.emit("remove_video", clickedindex);
		};

		// Build the rows and columns of the table.
		var row = $("<tr id='plist-" + index + "'>");
		var titleCol = $("<td class='trunc-extra'>");
		var authorCol= $("<td class='trunc-extra'>" + entry.author + "</td>");
		var timeCol  = $("<td class='text-right'>" + getTimeStr(entry.duration) + "</td>");
		var idCol    = $("<td class='monospace'></td>");
		var byCol    = $("<td class='trunc-extra'>");
		var closeCol = $("<td>");

		titleCol.attr("title", entry.title);
		authorCol.attr("title", entry.author);

		var titleLnk = $("<a href='#' class='trunc-extra'>" + entry.title + "</a>").click(index, changeVideoClickFunc);
		var closeBtn = $("<button type='button' class='close'>&times;</button>").click(index, removeVideoClickFunc);

		var idLnk    = $("<a href='http://youtu.be/" + entry.id + "' target='_blank'>" + entry.id + "</a>");
		idCol.append(idLnk);

		if (entry.added_by === null)
		{
			byCol.text("Unknown");
			byCol.addClass("italic");
		}
		else
		{
			byCol.text(entry.added_by);
			if (entry.added_by.match(guestRegex))
				byCol.addClass("italic");
		}

		row.append(titleCol);
		row.append(authorCol);
		row.append(timeCol);
		row.append(idCol);
		row.append(byCol);
		row.append(closeCol);

		titleCol.append($("<div class='trunc-extra'></div>").append(titleLnk));
		closeCol.append(closeBtn);

		if (index === playlist_pos)
		{
			row.addClass("info");
		}

		$("#playlist-body").append(row);
	});

	updateSkipButtonsState();
}

// Adds a new playlist entry for the given video ID.
// If shouldUpdatePlaylist is true or unspecified, updatePlaylistElement will be called.
function addPlaylistEntry(video, index, shouldUpdatePlaylist)
{
	if (video === undefined || video === null)
		return;

	var entry = {
		id: video.video_id,
		title: video.title,
		author: video.author,
		duration: video.duration,
		added_by: video.added_by,
	};
	console.log(video)
	playlistObj.splice(index, 0, entry);

	if (shouldUpdatePlaylist === undefined || shouldUpdatePlaylist === true)
		updatePlaylistElement();

	// $.ajax({
	// 	url: "http://gdata.youtube.com/feeds/api/videos/" + vid + "?v=2&alt=json",
	// 	dataType: "json",
	// 	success: function(data)
	// 	{
	// 		entry.title = data.entry.title.$t;
	// 		entry.duration = data.entry.media$group.yt$duration.seconds;
	// 		updatePlaylistElement();
	// 	},
	// });
}

function removePlaylistEntry(index, shouldUpdatePlaylist)
{
	playlistObj.splice(index, 1);

	if (shouldUpdatePlaylist === undefined || shouldUpdatePlaylist === true)
		updatePlaylistElement();
}


// Adds the given video ID or URL to the playlist. Shows an error if it isn't valid.
// This is for when a user adds a video via the UI.
function addVideoToPlaylist(video, index)
{
	vid = getVIDFromURL(video);

	if (vid === undefined)
	{
		alert("That's not a valid YouTube video URL or ID.");
		return;
	}

	if (index === undefined)
	{
		socket.emit("add_video", vid);
	}
	else
	{
		socket.emit("add_video", vid, playlist_pos + 1);
	}

	showAddVideoForm(false);
}

// Determines the given URL's video ID.
function getVIDFromURL(video)
{
	if (video.length == 11 && /[A-Za-z_\-]/.test(video))
	{
		// Assume it's a valid video ID.
		return video;
	}

	// If it isn't a video ID, we need to parse it.
	urlData = parseURL(video);

	// Check if the URL is YouTube. If it's youtu.be, we need to parse it differently.
	if (urlData.host.toLowerCase().indexOf("youtube") != -1)
	{
		// For standard YouTube URLs, the video ID is the "v" URL parameter.

		// If there is no "v" parameter, this isn't a valid video URL.
		if (urlData.params.v === undefined)
			return undefined;
		else
			return urlData.params.v;
	}
	else if (urlData.host.toLowerCase().indexOf("youtu.be") != -1)
	{
		// For youtu.be URLs, the video ID is the path (without leading or trailing spaces).
		return urlData.file;
	}

	// If we get here, it's not a YouTube video URL.
	return undefined;
}



//////////////////////
//// PLAYER LOGIC ////
//////////////////////

/////////////
// ACTIONS //
/////////////

function sendPlay()
{
	socket.emit("play");
}

function sendSeek(time)
{
	socket.emit("seek", time);
}

function sendPause()
{
	socket.emit("pause");
}


////////////////////////////
// PLAYBACK CONTROL STUFF //
////////////////////////////

// Whether or not the video should be playing.
var is_playing = false;

// Whether or not the video should be set to playing on the next updateState().
var set_new_is_playing = false;
var new_is_playing = is_playing;

var set_new_current_time = false;
var new_current_time = -1;

// The time the video was last paused at.
// When the user plays the video, if this differs from the video's current time, a seek is done.
var time_paused = -1;


function changeCurrentIndex(index)
{
	playlist_pos = index;
	updatePlaylistElement();
}


function changePlaying(playing)
{
	new_is_playing = playing;
	set_new_is_playing = true;
}

function changeCurrentTime(time)
{
	new_current_time = time;
	set_new_current_time = true;
}

// Sets is_playing and plays or pauses the video.
function setPlaying(playing)
{
	state_changing = true;
	if (typeof playing !== "undefined")
		is_playing = playing;

	if (is_playing)
	{
		console.log("Playing");
		vplayer.playVideo();
	}
	else
	{
		console.log("Pausing");
		vplayer.pauseVideo();
		time_paused = vplayer.getCurrentTime();
	}
}

// Checks if is_playing differs from whether or not the video is playing.
// If the video is playing and is_playing is false, assumes the user has played the video.
// The opposite is true for pausing.
function updateState(state)
{
	if (typeof state === "undefined") state = vplayer.getPlayerState();

	if (set_new_is_playing)
	{
		console.log("Script changed is playing to " + new_is_playing);
		setPlaying(new_is_playing);
		set_new_is_playing = false;
	}
	else if (set_new_current_time)
	{
		console.log("Script seeked to " + new_current_time);
		vplayer.seekTo(new_current_time);
		time_current = new_current_time;
		set_new_current_time = false;
	}
	else if (is_playing && state == YT.PlayerState.PAUSED)
	{
		// Even though you'd *think* that when the video ended, the state would be
		// PlayerState.ENDED, like the documentation says, sometimes it's not.
		// Because of this, we need to make sure it's actually paused and not simply ended...
		if (vplayer.getCurrentTime() < vplayer.getDuration())
		{
			// The state changed, assume the user paused.
			setPlaying(false);

			console.log("Sending pause");
			sendPause();
		}
	}
	else if (!is_playing && state == YT.PlayerState.PLAYING)
	{
		// The state changed, assume the user played.
		setPlaying(true);

		// Figure out if we need to do a seek.
		// If the current time and the time paused are more than a few seconds apart, seek.
		var time_current = vplayer.getCurrentTime();
		var pause_current_diff = Math.abs(time_paused - time_current);
		console.log("Pause time and current time are " + pause_current_diff + " seconds apart.");
		if (pause_current_diff > 3)
		{
			// Seek
			console.log("Sending seek");
			sendSeek(time_current);
		}

		console.log("Sending play");
		sendPlay();
	}
}

function updateStateTimeout()
{
	updateState();
	setTimeout(updateStateTimeout, 100);
}


////////////////////////////
////// DOCUMENT READY //////
////////////////////////////

$(document).ready(function()
{
	//// Initialize toolbar buttons. ////

	// Set tooltips.
	$("#room-toolbar button").tooltip({
		placement: "top",
		container: "#room-toolbar",
	});

	// Add video popover.
	$("#addvideo-btn").popover({
		html: true,
		placement: "right",
		trigger: "manual",
		title: "Add Video",
		content: $("#add-video-popover").html(),
		container: "#room-toolbar",
	});
	$("#add-video-popover").remove(); // At this point, we don't need this anymore.

	// Handlers
	$("#addvideo-btn").click(function(evt)
	{
		var show = !$("#addvideo-btn").hasClass("active");
		showAddVideoForm(show);
	});

	$("#resync-btn").click(function(evt)
	{
		console.log("Requesting sync...");
		socket.emit("sync");
	});

	// Next/prev buttons.
	$("#next-btn").click(function(evt)
	{
		if (playlist_pos+1 < playlistObj.length)
			socket.emit("change_video", playlist_pos + 1);
	});

	$("#prev-btn").click(function(evt)
	{
		if (playlist_pos > 0)
			socket.emit("change_video", playlist_pos - 1);
	});

	// Reload playlist button
	$("#reload-plist-btn").click(function(evt)
	{
		socket.emit("reload_playlist");
	});

	// Star button
	$("#star-btn").click(function(evt)
	{
		$.ajax({
			url: room_slug + "/star",
			data: $.param({ action: $("#star-btn").hasClass("active") ? "unstar" : "star" }),
			dataType: "json",
			success: function(data)
			{
				setStarred(data.starred, true);
			},
		});
	});
	updateStarButton();


	// Chat input form
	$("#chat-input-form").submit(function(evt)
	{
		evt.preventDefault();
		socket.emit("chat_message", $("#chat-input").val());
		$("#chat-input").val("");
	});

	// Handle window resize
	$(window).resize(function(evt)
	{
		updatePlaylistHeight();
	});
});

function showAddVideoForm(show)
{
	if (show === undefined || show)
	{
		$("#addvideo-btn").addClass("active");
		$("#addvideo-btn").popover("show");

		var addEndFunc = function(evt)
		{
			var videoId = $("input#video_id").val();
			console.log("Adding video " + videoId + " to the end of the playlist.");
			addVideoToPlaylist(videoId);
			evt.preventDefault();
		}

		var addNextFunc = function(evt)
		{
			var videoId = $("input#video_id").val();
			console.log("Adding video " + videoId + " after the current video (" + playlist_pos + ") in the playlist.");
			addVideoToPlaylist(videoId, playlist_pos + 1);
			evt.preventDefault();
		}

		$("#btn-add-end").click(addEndFunc);
		$("#menu-add-end").click(addEndFunc);
		$("#menu-add-next").click(addNextFunc);
		$("#videoform").submit(addEndFunc);
		$("#videoform #video_id").focus();
	}
	else
	{
		$("#addvideo-btn").removeClass("active");
		$("#addvideo-btn").popover("hide");
	}
}

var toolbarBtnsEnabled = false;

function enableToolbarBtns(enable)
{
	toolbarBtnsEnabled = enable === undefined || enable;
	updateToolbarState();
}

// Updates the state of all the toolbar buttons.
function updateToolbarState()
{
	// Enable / disable all buttons except those that need exra processing.
	var btns = $("#room-toolbar button:not(#next-btn):not(#prev-btn)");
	setElementEnabled(btns, toolbarBtnsEnabled);

	// Now, do extra processing for special cases such as buttons that need
	// to be enabled/disabled based on other factors.
	updateSkipButtonsState();
}

// Updates the state of the skip to next and skip to previous buttons.
function updateSkipButtonsState()
{
	if (toolbarBtnsEnabled)
	{
		// If we're at or past the end of the playlist, disable the "next video" button.
		 setElementEnabled($("#next-btn"), (playlist_pos+1 < playlistObj.length));

		 // If we're at or past the beginning of the playlist, disable the "previous video" button.
		 setElementEnabled($("#prev-btn"), (playlist_pos > 0));
	}
	else
	{
		// If toolbar buttons aren't enabled, just disable them.
		setElementEnabled($("#next-btn,#prev-btn"), false);
	}
}

function updatePlaylistHeight()
{
	var plistScroll = $("#playlist-scroll");
	var minHeight = plistScroll.css("min-height");

	// Simply resize the playlist's scroll div to fit the available screen space.
	var availableSpace = $(window).height() - plistScroll.offset().top - 20;

	// If the space available is greater than the minimum size of the div, resize it to fit the space.
	if (availableSpace <= minHeight)
		plistScroll.height(minHeight);
	else
		plistScroll.height(availableSpace);
}

// Does an AJAX request to <room_slug>/star to check if the user starred the room and updates the star button.
function updateStarButton()
{
	$.ajax({
		url: room_slug + "/star",
		dataType: "json",
		success: function(data)
		{
			setStarred(data.starred);
		},
	});
}

function setStarred(starred, reshowTooltip)
{
	var tiptext;
	if (starred == true)
	{
		$("#star-btn").addClass("active");
		tiptext = "Un-star this room";
	}
	else
	{
		$("#star-btn").removeClass("active");
		tiptext = "Star this room";
	}
	$("#star-btn").attr("data-original-title", tiptext).tooltip("fixTitle");
	if (reshowTooltip === true)
		$("#star-btn").tooltip("show");
}
