# Author: Chris Moyer
import logging
import re
import sys
import traceback
import urllib

import botoweb
import mimetypes
from boto.utils import find_class

from botoweb.appserver.handlers import RequestHandler
from botoweb.appserver.handlers.index import IndexHandler
from botoweb.appserver.handlers.robots import RobotsHandler

from botoweb.request import Request
from botoweb.response import Response
from botoweb import status
from botoweb.exceptions import *

log = logging.getLogger("botoweb.url_mapper")

from botoweb.appserver.wsgi_layer import WSGILayer
class URLMapper(WSGILayer):
	"""
	Simple URL mapper
	"""
	handlers = {}
	index_handler = None
	robot_handler = None

	def update(self, env):
		"""
		On an update, we have to remove all of our handlers and re-build 
		our index handler
		"""
		self.env = env
		self.index_handler = IndexHandler(self.env, {})
		self.robot_handler = RobotsHandler(self.env, {})
		self.handlers = {}
		# Load up and verify all the handlers
		for route in self.env.config.get("botoweb", "handlers"):
			handler = find_class(route.get("handler"))
			if not handler:
				raise Exception("Handler not found: %s" % route.get('handler'))
			if route.get("db_class"):
				model_class = find_class(route.get("db_class").strip())
				if model_class is None:
					raise Exception("DB Class not found: '%s'" % route.get('db_class'))

	def handle(self, req, response):
		"""
		Basic URL mapper
		"""
		if req.user:
			log.info("[%s] %s: %s" % (req.user.username, req.method, req.path_info))
		else:
			log.info("%s: %s" % (req.method, req.path_info))
		(handler, obj_id) = self.parse_path(req)
		if not handler:
			raise NotFound(url=req.path)
		return handler(req, response, obj_id)


	def parse_path(self, req):
		"""
		Get the handler and object id (if given) for this
		path request.

		@return: (Handler, obj_id)
		@rtype: tuple
		"""
		path = req.path
		handler = None
		obj_id = None
		for handler_config in self.env.config.get("botoweb", "handlers"):
			match = re.match("^(%s)(\.xml|\.json|\.csv)?(\/(.*))?$" % handler_config['url'], path)

			if match:
				# Allow for setting a custom content-type by URL
				if match.group(2):
					req.file_extension = match.group(2)[1:]
				else:
					req.file_extension = self.env.config.get("app", "format")
				log.debug("URL Mapping: %s" % handler_config)
				obj_id = match.group(4)
				if obj_id == "":
					obj_id = None

				if self.handlers.has_key(handler_config['url']):
					handler = self.handlers.get(handler_config['url'])
				else:
					if handler_config.has_key("handler"):
						class_name = handler_config['handler']
						handler_class = find_class(class_name)
						handler = handler_class(self.env, handler_config)

					if handler:
						self.handlers[handler_config['url']] = handler

				if handler:
					req.script_name = match.group(1)
					if obj_id:
						obj_id = urllib.unquote(obj_id)
					return (handler, obj_id)
		if path == "/":
			return (self.index_handler, None)
		elif path == "/robots.txt":
			return (self.robot_handler, None)
		else:
			return (None, None)

	def reload(self, *args, **params):
		"""Reload all the handlers"""
		from threading import Thread
		log.info("Reloading handlers")
		for handler in self.handlers.values():
			try:
				t = Thread(target=handler.reload)
				t.start()
			except Exception, e:
				log.exception("Exception reloading handler: %s" % handler)
