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
