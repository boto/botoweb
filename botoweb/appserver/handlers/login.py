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
from botoweb.exceptions import TemporaryRedirect

import logging
log = logging.getLogger("botoweb.handlers.login")

class LoginHandler(RequestHandler):
	"""JanRain Login Handler"""

	def __init__(self, env, config):
		"""Set up and fetch the routes for the first time"""
		RequestHandler.__init__(self, env, config)

	def _post(self, request, response, id=None):
		"""Finish up the authentication process,
		fetching the user from the auth_token"""
		path = request.real_host_url
		if id:
			path += "/%s" % id
		raise TemporaryRedirect(path)

	def _get(self, request, response, id=None):
		return self._post(request, response, id)