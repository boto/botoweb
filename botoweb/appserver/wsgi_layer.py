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
import botoweb
from botoweb.request import Request
from botoweb.response import Response
from botoweb.exceptions import *
from datetime import datetime

import traceback
import logging
log = logging.getLogger("botoweb")

import re


class WSGILayer(object):
	"""
	Base WSGI Layer. This simply gives us an additional
	few functions that allow this object to be called as a function,
	but also allows us to chain them together without having to re-build
	the request/response objects
	"""
	threadpool = None
	maxthreads = None

	def __init__(self, env, app=None):
		"""
		Initialize this WSGI layer.

		@param env: A botoweb environment object that represents what we're running in
		@type env: botoweb.environment.Environment

		@param app: An optional WSGI layer that this layer is on top of.
		@type app: WSGILayer

		"""
		self.app = app
		self.update(env)

	def __call__(self, environ, start_response):
		"""
		Handles basic one-time-only WSGI setup, and handles
		error catching.
		"""
		resp = Response()
		req = Request(environ)
		try:
			# If there's too many threads already, just toss a
			# ServiceUnavailable to let the user know they should re-connect
			# later
			if self.maxthreads and self.threadpool:
				if len(self.threadpool.working) > self.maxthreads:
					raise ServiceUnavailable("Service Temporarily Overloaded")
			resp = self.handle(req, resp)
		except AssertionError, e:
			resp.set_status(400)
			resp.content_type = "text/plain"
			resp.body = str(e)
		except HTTPRedirect, e:
			resp.set_status(e.code)
			resp.headers['Location'] = str(e.url)
			resp = self.format_exception(e, resp, req)
		except Unauthorized, e:
			resp.set_status(e.code)
			if self.env.config.get("app", "basic_auth", True):
				resp.headers.add("WWW-Authenticate", 'Basic realm="%s"' % self.env.config.get("app", "name", "Boto Web"))
			resp = self.format_exception(e, resp, req)
		except HTTPException, e:
			resp.set_status(e.code)
			resp = self.format_exception(e, resp, req)
			log.debug(traceback.format_exc())
			botoweb.report_exception(e, req, priority=5)
		except Exception, e:
			log.exception(e)
			content = InternalServerError(message=e.message)
			resp.set_status(content.code)
			resp = self.format_exception(content, resp, req)
			botoweb.report_exception(content, req, priority=1)

		return resp(environ, start_response)

	def format_exception(self, e, resp, req):
		resp.set_status(e.code)
		if((req and req.file_extension == "json") or self.env.config.get("app", "format") == 'json'):
			resp.content_type = "application/json"
			resp.body = e.to_json()
		else:
			resp.content_type = "text/xml"
			e.to_xml().writexml(resp)
		return resp


	def update(self, env):
		"""
		Update this layer to use a new environment. Minimally
		this will set "self.env = env", but for specific layers
		you may have to undate or invalidate your cache
		"""
		self.env = env

	def handle(self, req, response):
		"""
		This is the function that is called when chainging WSGI layers
		together, it has the request and response objects passed
		into it so they are not re-created.
		"""
		return self.app.handle(req, response)

	def reload(self, *args, **params):
		"""Reload this application"""
		if self.app:
			return self.app.reload()
