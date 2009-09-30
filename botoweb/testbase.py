#
# Copyright (C) 2009 Chris Moyer http://coredumped.org/
# 
import sys
sys.path.append(".")

from lxml import etree
from StringIO import StringIO

class TestBase(object):
	"""
	Testing base class, this provides some 
	simple shared functionality for all
	classes to use.

	This emulates what would actually happen if
	you connected via the HTTP server without actually
	running the HTTP server.
	"""
	application="botoweb"
	user = None

	def __init__(self):
		"""
		Setup this class to handle testing
		"""
		import boto
		from botoweb.environment import Environment
		e = Environment(self.application)
		self.env = e
		boto.config = self.env.config

		from botoweb.appserver.url_mapper import URLMapper
		from botoweb.appserver.filter_mapper import FilterMapper
		from botoweb.appserver.auth_layer import AuthLayer

		self.mapper = AuthLayer( app=FilterMapper( app=URLMapper(e), env=e), env=e)



	def make_request(self, resource, method="GET", body=None, params={}, headers={}):
		"""
		Make a request to a given resource

		@param resource: The resource URI to fetch from (ex. /users)
		@type resource: str

		@param method: The HTTP/1.1 Method to use, (GET/PUT/DELETE/POST/HEAD)
		@type method: str

		@param body: Optional body text to send
		@type body: str

		@param params: Optional additional GET/POST parameters to send (GET if GET, POST if POST)
		@type params: dict

		@param headers: Optional extra headers to send
		@type headers: dict
		"""
		from botoweb.request import Request
		from botoweb.response import Response
		import urllib

		query_params = []
		for k in params:
			query_params.append("%s=%s" % (k, urllib.quote_plus(params[k])))

		if method == "POST":
			req = Request.blank(resource)
			if query_params:
				body = "&".join(query_params)
				req.environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
		else:
			if query_params:
				resource = "%s?%s" % (resource, "&".join(query_params))
			req = Request.blank(resource)

		if body:
			req.body = body
			req.environ['CONTENT_LENGTH'] = str(len(req.body))

		for k in headers:
			req.headers[k] = headers[k]

		req.method = method

		if self.user:
			req._user = self.user

		from pprint import pprint
		pprint(req.GET)
		return self.mapper.handle(req, Response())

	def validate_schema(self, xml, schema):
		"""
		Validate value against schema
		@param xml: The XML document to verify
		@type xml: str

		@param schema: The Schema file to validate against
		@type schema: file
		"""

		xmlschema_doc = etree.parse(schema)
		xmlschema = etree.XMLSchema(xmlschema_doc)
		return xmlschema.assertValid(etree.parse(StringIO(xml)))
