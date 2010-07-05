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
from botoweb.exceptions import *
from datetime import datetime

import traceback
import logging
log = logging.getLogger("botoweb.wsgi_layer")

import re


class WSGILayer(object):
	"""
	Base WSGI Layer. This simply gives us an additional
	few functions that allow this object to be called as a function,
	but also allows us to chain them together without having to re-build
	the request/response objects
	"""

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

		try:
			from arecibo import post
			self.arecibo = post()
			self.arecibo.server(url=boto.config.get("arecibo", "url"))
			self.arecibo.set("account", boto.config.get("arecibo", "public_key"))
		except:
			self.arecibo = None


	def __call__(self, environ, start_response):
		"""
		Handles basic one-time-only WSGI setup, and handles
		error catching.
		"""
		resp = Response()
		try:
			req = Request(environ)
		except:
			req = None
		try:
			resp = self.handle(req, resp)
		except HTTPRedirect, e:
			resp.set_status(e.code)
			resp.headers['Location'] = str(e.url)
			resp = self.format_exception(e, resp)
		except Unauthorized, e:
			resp.set_status(e.code)
			resp.headers.add("WWW-Authenticate", 'Basic realm="%s"' % self.env.config.get("app", "name", "Boto Web"))
			resp = self.format_exception(e, resp)
		except HTTPException, e:
			resp.set_status(e.code)
			resp = self.format_exception(e, resp)
			self.report_exception(e, req, priority=5)
		except Exception, e:
			content = InternalServerError(message=e.message)
			resp.set_status(content.code)
			log.critical(traceback.format_exc())
			resp = self.format_exception(content, resp)
			self.report_exception(content, req, priority=1)


		return resp(environ, start_response)

	def format_exception(self, e, resp):
		resp.clear()
		resp.set_status(e.code)
		resp.content_type = "text/xml"
		e.to_xml().writexml(resp)
		return resp

	def report_exception(self, e, req, priority=None):
		"""Report an exception, using arecibo if available"""
		if self.arecibo:
			try:
				self.arecibo.set("status", e.code)
				if priority:
					self.arecibo.set("priority", str(priority))
				self.arecibo.set("url", req.real_path_url)
				self.arecibo.set("msg", e.message)
				self.arecibo.set("type", e.__class__.__name__)
				self.arecibo.set("traceback", traceback.format_exc())
				self.arecibo.set("server", boto.config.get("Instance", "public-ipv4"))
				self.arecibo.set("timestamp", datetime.utcnow().isoformat());
				self.arecibo.set("request", req.body)
				if req and req.user:
					self.arecibo.set("username", req.user.username)
				if req.environ.has_key("HTTP_USER_AGENT"):
					self.arecibo.set("user_agent", req.environ['HTTP_USER_AGENT'])
				self.arecibo.send()
			except Exception, e:
				log.critical("Exception sending to arecibo: %s" % e)

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
