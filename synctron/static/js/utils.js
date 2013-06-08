// This function creates a new anchor element and uses location
// properties (inherent) to get the desired URL data. Some String
// operations are used (to normalize results across browsers).
function parseURL(url)
{
	var a =  document.createElement('a');
	a.href = url;

	return {
		source: url,
		protocol: a.protocol.replace(':',''),
		host: a.hostname,
		port: a.port,
		query: a.search,
		params: (function()
		{
			var ret = {},
				seg = a.search.replace(/^\?/,'').split('&'),
				len = seg.length, i = 0, s;

			for (; i < len; i++)
			{
				if (!seg[i]) { continue; }
				s = seg[i].split('=');
				ret[s[0]] = s[1];
			}
			return ret;
		})(),
		file: (a.pathname.match(/\/([^\/?#]+)$/i) || [,''])[1],
		hash: a.hash.replace('#',''),
		path: a.pathname.replace(/^([^\/])/,'/$1'),
		relative: (a.href.match(/tps?:\/\/[^\/]+(.+)/) || [,''])[1],
		segments: a.pathname.replace(/^\//,'').split('/')
	};
}


// Returns a time string in the format HH:MM:SS or MM:SS for the given seconds.
// If forceHrs is false or undefined, MM:SS will be used unless the given time is more than an hour.
function getTimeStr(timeSecs, forceHrs)
{
	if (typeof forceHrs === "undefined")
		forceHrs = false;

	var hours = Math.floor(timeSecs / 3600);
	var minutes = Math.floor((timeSecs - (hours * 3600)) / 60);
	var seconds = timeSecs - (hours * 3600) - (minutes * 60);

	if (hours < 10) {hours = "0" + hours;}
	if (minutes < 10) {minutes = "0" + minutes;}
	if (seconds < 10) {seconds = "0" + seconds;}
	var time = "";
	if (hours > 0 || forceHrs) time += hours + ":";
	time += minutes + ":" + seconds;
	return time;
}

// Returns a human readable error message for the given jQuery error.
function getJQErrorMsg(jqError)
{
	switch (jqError)
	{
	case "timeout":
		return "The operation timed out.";

	case "abort":
		return "The operation was aborted.";

	case "parsererror":
		return "The server returned an invalid response.";

	default:
		return "An unknown error occurred.";
	}
}

// Returns a human readable error message for the given HTTP status code.
function getHTTPErrorMsg(httpCode)
{
	switch (httpCode)
	{
	case 400:
		return "Status code: " + httpCode + " - The server got a bad request. This is likely an error with the application.";

	case 400:
		return "Status code: " + httpCode + " - The requested page was not found. This is likely an error with the application.";

	case 500:
		return "Status code: " + httpCode + " - The server encountered an error processing the request. Try again later.";

	case 502:
		return "Status code: " + httpCode + " - Bad gateway. The server is probably down. Try again later.";

	case 504:
		return "Status code: " + httpCode + " - Gateway timeout. The server timed out. Try again later.";

	default:
		return "Got an unknown HTTP error " + httpCode + ".";
	}
}


// Enables/disables the given element(s). Enabling/disabling is done by adding/removing the "disabled" class.
function setElementEnabled(element, enabled)
{
	if (enabled) element.removeClass("disabled");
	else element.addClass("disabled");
}
