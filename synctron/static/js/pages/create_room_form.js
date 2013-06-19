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

$(document).ready(function()
{
	var validator = $("#create-room-form").validate({
		rules: {
			title: {
				required: true,
				minlength: 2,
				maxlength: 40,
			},
			slug: {
				required: true,
				maxlength: 40,
				pattern: /^[0-9A-Za-z\-\_]+$/,
			},
		},

		messages: {
			title: {
				required: "You must enter a title for the room.",
				minlength: jQuery.format("Your room's title must be at least {0} characters long."),
				maxlength: jQuery.format("Your room's title cannot be more than {0} characters long."),
			},
			slug: {
				required: "You must enter a slug for your room.",
				minlength: jQuery.format("Your room's slug must be at least {0} characters long."),
				maxlength: jQuery.format("Your room's slug cannot be more than {0} characters long."),
				pattern: "The slug can contain only alphanumerics, numbers, dashes, and underscores.",
				remote: jQuery.format("The slug {0} is already taken."),
			},
		},

		// errorPlacement: function(error, element)
		// {
		// 	if (element.is(""))
		// },
	});
});
