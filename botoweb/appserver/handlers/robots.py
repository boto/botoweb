# Copyright (c) 2009 Chris Moyer http://coredumped.org
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
from botoweb.appserver.handlers import RequestHandler

import logging
log = logging.getLogger("botoweb.handlers.robots")


class RobotsHandler(RequestHandler):
	"""Robots.txt handler"""

	def __init__(self, env, config):
		"""Set up and fetch the routes for the first time"""
		RequestHandler.__init__(self, env, config)

	def _get(self, request, response, id=None):
		"""Return "Disallow all" """
		response.content_type = 'text'
		response.write("User-agent: *\r\n")
		response.write("Disallow: /")
		return response
