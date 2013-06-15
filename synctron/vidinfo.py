# Copyright (C) 2013 Screaming Cats

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import requests

"""
A set of functions for getting (and caching) information about YouTube videos.
"""

# Cache of video info. Dictionary maps video info to video ID.
video_info_cache = {}

def get_video_info(vid):
	"""
	Does a YouTube API request and returns a dict containing information about the video.
	If the given video ID is not a valid YouTube video ID, returns None.
	"""

	if vid in video_info_cache:
		return video_info_cache[vid]

	req = requests.get("http://gdata.youtube.com/feeds/api/videos/%s?v=2&alt=json" % vid)

	try:
		response = req.json()
	except ValueError:
		# If it's not valid JSON, this isn't a valid video ID.
		return None

	author = None
	if len(response["entry"]["author"]) > 0:
		author = response["entry"]["author"][0]["name"]["$t"]

	video_info_cache[vid] = {
		"video_id": vid,
		"title": response["entry"]["title"]["$t"],
		"author": author,
		"duration": int(response["entry"]["media$group"]["yt$duration"]["seconds"]),
	}
	
	return video_info_cache[vid]

