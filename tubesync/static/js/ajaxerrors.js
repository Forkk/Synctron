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