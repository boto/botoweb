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
import httplib

import boto
from botoweb.request import Request
from botoweb.response import Response
from botoweb.resources.user import User
from botoweb.exceptions import *

import traceback
import logging
log = logging.getLogger("botoweb.auth_layer")

import re

from botoweb.appserver.wsgi_layer import WSGILayer
class AuthLayer(WSGILayer):
	"""
	Authentication/Authorization layer
	This only handles authorization on a macro level, it 
	will prevent users from getting to specific paths based on 
	groups, or just simply limit a path to require you to be logged
	in to get to it.
	"""

	def handle(self, req, response):
		auth = self.get_auth_config(req.path)
		if auth and not auth.get("disable", False):
			log.debug("Checking auth: %s" % auth)
			if not req.user:
				raise Unauthorized()
			elif auth.has_key("group"):
				groups = auth['group']
				authed = False
				if not isinstance(groups, list):
					groups = [groups]
				for group in groups:
					if req.user.has_auth_group(group):
						authed = True
				if not authed:
					raise Forbidden()
		if req.user != None and req.user.auth_token != None:
			response.set_cookie('BW_AUTH_TOKEN', req.user.auth_token)
		if self.app:
			response = self.app.handle(req, response)
		return response

	def get_auth_config(self, path):
		"""
		Get the auth config for this path
		"""
		log.debug("Get Auth Config: %s" % (path))
		match = None
		if not self.env.config.has_key('botoweb'):
			return None
		for rule in self.env.config.get("botoweb", "auth", []):
			if rule.has_key("url"):
				if not re.match(rule['url'], path):
					continue
			if rule.has_key("method"):
				if rule['method'].lower().strip() != method.lower().strip():
					continue
			match = rule
			break
		return match


