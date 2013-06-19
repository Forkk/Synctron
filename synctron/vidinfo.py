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

from synctron import app

from apiclient.discovery import build
from apiclient.errors import HttpError

from isodate import parse_duration

yt_service = build("youtube", "v3", developerKey=app.config.get("YT_API_KEY"))

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

	if vid is None:
		app.logger.error("Video ID passed to get_video_info is None.")
		return None

	response = None
	try:
		response = yt_service.videos().list(id=vid, 
			part="id,snippet,contentDetails",
			fields="items(id,snippet/title,snippet/channelTitle,contentDetails/duration)").execute()
	except HttpError:
		app.logger.error("HttpError occurred when trying to get video info for video ID %s." % vid, exc_info=True)
		raise

	# If items are returned, the video doesn't exist. We should return None.
	if len(response["items"]) == 0:
		return None

	# Otherwise, get some info from the response.
	else:
		item = response["items"][0]

		video_info_cache[vid] = {
			"video_id": item["id"],
			"title": item["snippet"]["title"],
			"author": item["snippet"]["channelTitle"],
			"duration": parse_duration(item["contentDetails"]["duration"]).total_seconds(),
		}
		return video_info_cache[vid]

