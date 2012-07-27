# Author: Chris Moyer
import os
import os.path
import re
import urlparse
import StringIO
import traceback

import cgi
import wsgiref
import wsgiref.headers

import boto
import botoweb

from botoweb.exceptions import *
from boto.utils import find_class
import time
import mimetypes

import logging

class RequestHandler(object):
	"""
	Simple Request Handler,
	The request handler is created only 
	once so we can handle caching.
	"""
	allowed_methods = ['get', 'post', 'head','put', 'delete', 'options']

	def __init__(self, env, config={}):
		"""Set up the environment and local config"""
		self.env = env
		self.config = config
		self.log = logging.getLogger(self.__module__)

	def __call__(self, request, response, obj_id):
		"""Execute this handler based on the request passed in"""
		method = request.method.lower()
		# CORS support if configured
		if self.env.config.get("app", "allow_origin"):
			response.headers['Access-Control-Allow-Origin'] = str(self.env.config.get('app', 'allow_origin'))
		if self.config.has_key("allow_origin"):
			response.headers['Access-Control-Allow-Origin'] = str(self.config.get('allow_origin'))
		if self.env.config.get("app", "expose_headers"):
			response.headers['Access-Control-Expose-Headers'] = str(self.env.config.get('app', 'expose_headers'))
		if self.config.has_key("expose_headers"):
			response.headers['Access-Control-Expose-Headers'] = str(self.config.get('expose_headers'))
		if self.env.config.get("app", "allow_headers"):
			response.headers['Access-Control-Allow-Headers'] = str(self.env.config.get('app', 'allow_headers'))
		if self.config.has_key("allow_headers"):
			response.headers['Access-Control-Allow-Headers'] = str(self.config.get('allow_headers'))

		if method in self.allowed_methods:
			method = getattr(self, "_%s" % method)
			return method(request, response, obj_id)
		else:
			raise BadRequest(description="Unknown Method: %s" % request.method)

	def _options(self, request, response, id=None):
		"""OPTIONS as per the RFC2616 specification, requires that we send any and all allowed methods in an allow header"""
		response.headers['Allow'] = ", ".join(map(str.upper, self.allowed_methods))
		response.content_length = 0
		response.set_status(200)
		return response

	def _get(self, request, response, id=None):
		raise NotImplemented()

	def _post(self, request, response, id=None):
		raise NotImplemented()
	
	def _head(self, request, response, id=None):
		raise NotImplemented()

	def _put(self, request, response, id=None):
		raise NotImplemented()

	def _delete(self, request, response, id=None):
		raise NotImplemented()

	def reload(self):
		"""Reload any caches in this handler"""
		pass