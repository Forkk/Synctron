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

var ws;

// Stringifies the given object and sends it to the server.
function sendAction(data)
{
	var msg = JSON.stringify(data);
	console.log("Sending action: " + msg);
	ws.send(msg);
}

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
		var alertDiv = $("<div class='alert alert-error hide'>");
		alertDiv.html("<b>Error:</b> Lost connection to the synchronization server. Try refreshing the page in a few seconds.");
		$("#main-container").prepend(alertDiv);
		alertDiv.slideDown();
	}
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
				// if (event.data == YT.PlayerState.PLAYING && lastState != YT.PlayerState.PLAYING)
				// {
				// 	console.log("Sending play action...");
				// 	sendAction({ action: "play", time: vplayer.getCurrentTime() });
				// }
				// else if (event.data == YT.PlayerState.PAUSED && lastState != YT.PlayerState.PAUSED)
				// {
				// 	console.log("Sending pause action... ");
				// 	sendAction({ action: "pause", });
				// }

				// This breaks.
				// updateState(event.data);

				// When we finish buffering, we should sync.
				if (event.data != YT.PlayerState.BUFFERING && lastState == YT.PlayerState.BUFFERING)
				{
					console.log("Video stopped buffering. Requesting sync...");
					sendAction({ action: "sync", });
				}

				lastState = event.data;
			},

			onReady: function(event)
			{
				var session = $.cookie("session");

				console.log("Requesting init...");
				if (session === undefined)
					sendAction({ action: "init", room_id: room_id,  });
				else
					sendAction({ action: "init", room_id: room_id, session: session });

				// Start the update state timeout loop.
				updateStateTimeout();

				// Enable buttons.
				enableToolbarBtns();
			},
		}
	});

	initWebSocket();
};


/////////////////////////
//// USER LIST LOGIC ////
/////////////////////////

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
			sendAction({ action: "changevideo", index: clickedindex, });
		};

		var removeVideoClickFunc = function(evt)
		{
			evt.preventDefault();
			var clickedindex = evt.data;
			sendAction({ action: "removevideo", index: clickedindex, });
		};

		// Build the rows and columns of the table.
		var row = $("<tr id='plist-" + index + "'>");
		var titleCol = $("<td class='trunc-extra'>");
		var authorCol= $("<td class='trunc-extra'>" + entry.author + "</td>");
		var timeCol  = $("<td>" + getTimeStr(entry.duration) + "</td>");
		var idCol    = $("<td class='monospace'></td>");
		var closeCol = $("<td>");

		titleCol.attr("title", entry.title);
		authorCol.attr("title", entry.author);

		var titleLnk = $("<a href='#' class='trunc-extra'>" + entry.title + "</a>").click(index, changeVideoClickFunc);
		var closeBtn = $("<button type='button' class='close'>&times;</button>").click(index, removeVideoClickFunc);

		var idLnk    = $("<a href='http://youtu.be/" + entry.id + "' target='_blank'>" + entry.id + "</a>");
		idCol.append(idLnk);

		row.append(titleCol);
		row.append(authorCol);
		row.append(timeCol);
		row.append(idCol);
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
	var entry = {
		id: video.video_id,
		title: video.title,
		author: video.author,
		duration: video.duration,
	};
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
		sendAction({ action: "addvideo", video_id: vid });
	}
	else
	{
		sendAction({ action: "addvideo", video_id: vid, index: playlist_pos + 1 });
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
	sendAction({ action: "play" });
}

function sendSeek(time)
{
	sendAction({ action: "seek", time: time });
}

function sendPause()
{
	sendAction({ action: "pause" });
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
		// The state changed, assume the user paused.
		setPlaying(false);

		console.log("Sending pause");
		sendPause();
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
//// VIDEO PLAYER STUFF ////
////////////////////////////

actions = 
{
	error: function(data, sock)
	{
		console.log(JSON.stringify(data));
		alert(data.reason_msg);
	},

	// Handles the init action sent from the server.
	// Expects the following fields in data: video_id, playlist_pos
	// Doesn't return anything.
	setvideo: function(data, sock)
	{
		// Set the current video.
		vplayer.loadVideoById(data.video_id);
		changeCurrentIndex(data.playlist_pos);

		console.log("Requesting sync...");
		sendAction({ action: "sync", });

		// Request sync again in a bit to make sure the video is properly synchronized.
		setTimeout(function()
		{
			console.log("Requesting sync...");
			sendAction({ action: "sync", });
		}, (1*1000));

		// Update the playlist height to make sure the layout works.
		updatePlaylistHeight();
	},

	// Handles the sync action sent from the server.
	// Expects the following fields: video_time
	sync: function(data, sock)
	{
		changePlaying(data.is_playing);
		changeCurrentTime(data.video_time);
	},

	playlistupdate: function(data, sock)
	{
		// For now, we clear the playlist and reload info every time it changes.
		// In the future, we'll do this in a more efficient way, but for now I just want to get it working.
		playlistObj = [];

		data.playlist.forEach(function(video, index)
		{
			addPlaylistEntry(video, index);
		});

		playlist_pos = data.playlist_position;

		updatePlaylistElement();
	},

	userlistupdate: function(data, sock)
	{
		// Same as above in playlistupdate.
		userlistObj = [];

		data.userlist.forEach(function(user, index)
		{
			addUserListEntry(user);
		});
	},

	chatmsg: function(data, sock)
	{
		var chatbox = $("#chatbox-textarea");

		// Determine whether or not we're going to want to scroll to the bottom after we append the message.
		var distFromBottom = (chatbox[0].scrollHeight - chatbox.scrollTop()) - chatbox.outerHeight();
		var scrollToBottom = Math.abs(distFromBottom) <= 5;

		// First, we need to make sure any HTML tags are escaped.
		var escapedMsg = $("<div/>").text(data.message).html();

		// Now, we create a <p> element for the message and append it to the chat box.
		var msgElement = $("<p><b>" + data.sender + ":</b>&nbsp;" + escapedMsg + "</p>")
		chatbox.append(msgElement);

		// Finally, if the chatbox was scrolled to the bottom before,
		// we need to scroll it back to the bottom because we've added a new line.
		if (scrollToBottom)
			chatbox.scrollTop(chatbox[0].scrollHeight);
	},
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
		sendAction({ action: "sync", });
	});

	// Next/prev buttons.
	$("#next-btn").click(function(evt)
	{
		if (playlist_pos+1 < playlistObj.length)
			sendAction({ action: "changevideo", index: playlist_pos + 1, });
	});

	$("#prev-btn").click(function(evt)
	{
		if (playlist_pos > 0)
			sendAction({ action: "changevideo", index: playlist_pos - 1, });
	});

	// Chat input form
	$("#chat-input-form").submit(function(evt)
	{
		evt.preventDefault();
		sendAction({ action: "chatmsg", message: $("#chat-input").val(), })
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
