# Copyright (c) 2008 Chris Moyer http://coredumped.org
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
from boto.utils import find_class
from botoweb.request import Request
from botoweb.response import Response
from botoweb.resources.user import User
from botoweb.exceptions import *

import traceback
import logging
log = logging.getLogger("botoweb.filter_mapper")

XSL_TEMPLATE = '<?xml-stylesheet href="%s" type="text/xsl" ?>'


from lxml import etree
from botoweb.appserver.filter_resolver import S3FilterResolver, PythonFilterResolver

import re
from StringIO import StringIO

from botoweb.appserver.wsgi_layer import WSGILayer
class FilterMapper(WSGILayer):
	"""
	Filter URL Mapper
	"""


	def update(self, env):
		"""
		On update, we have to re-build our entire filter list
		"""
		self.env = env
		self.filters = {}
		self.parser = etree.XMLParser()
		self.parser.resolvers.add(S3FilterResolver())
		self.parser.resolvers.add(PythonFilterResolver())
		self.external_functions = []
		if self.env.config.has_key("xsltfunctions"):
			for func_path in self.env.config['xsltfunctions']:
				__import__(func_path)
				funcset = find_class(func_path)
				ns = etree.FunctionNamespace(funcset.uri)
				for fname in funcset.functions:
					ns[fname] = funcset.functions[fname]

	def handle(self, req, response):
		"""
		Map to the correct filters
		"""
		variables = {}
		user = req.user
		headers = {}
		for key in req.headers:
			if not key.lower() in ["content-length", "authorization"]:
				headers[key] = req.headers[key]


		variables['host_url'] = etree.XSLT.strparam(req.host_url)
		if user:
			variables['user_id'] = etree.XSLT.strparam(str(user.id))
			variables['user_name'] = etree.XSLT.strparam(str(user.username))

		filter = self.get_filter(req.path,req.method, user)

		stylesheet = None
		if filter[0] and req.body:
			try:
				parsed_body = etree.parse(StringIO(req.body), self.parser)
			except:
				pass # Ignore if it's not XML
			else:
				req.body = str(filter[0](parsed_body, **variables))

		if self.app:
			response = self.app.handle(req, response)

		if response.content_type == "text/xml" and response.body:
			if filter[1]:
				try:
					response.body = str(filter[1](etree.parse(StringIO(response.body), self.parser), **variables))
				except:
					pass
			if filter[2]:
				response.body = "%s\r\n%s" % ("\r\n".join([XSL_TEMPLATE % f for f in filter[2]]), response.body)
		return response

	def get_filter(self, path, method, user):
		"""
		Get the filter for this URL and
		User

		@return: (input_filter, output_filter), either filter may also be None
		@rtype: 2-tuple
		"""
		log.debug("Get Stylesheet: %s %s" % (path, user))
		styledoc = None
		match = None
		for rule in self.env.config.get("botoweb", "filters", []):
			if rule.has_key("url"):
				if not re.match(rule['url'], path):
					continue
			if rule.has_key("method"):
				if rule['method'] != method:
					continue
			if rule.has_key("user"):
				if not user or rule['user'] != user.username:
					continue
			if rule.has_key("group"):
				if not user or not rule['group'] in user.groups:
					continue
			match = rule
			break

		input_filter = None
		output_filter = None
		client_filters = []
		if match:
			if rule.has_key('filters'):
				if rule['filters'].has_key("input"):
					input_filter = self._build_proc(rule['filters']['input'], user)
				if rule['filters'].has_key("output"):
					output_filter = self._build_proc(rule['filters']['output'], user)
			if rule.has_key("client_filters"):
				client_filters = rule['client_filters']

		return (input_filter, output_filter, client_filters)

	def _build_proc(self, uri, user):
		from botoweb import xslt_functions
		proc = None
		if uri:
			extensions = {}
			if user:
				extensions = {
					("python://botoweb/xslt_functions", "hasGroup"):  user.has_auth_group_ctx,
					("python://botoweb/xslt_functions", "hasAuth"):  user.has_auth_ctx,
					("python://botoweb/xslt_functions", "matches"):  user.matches_ctx,
					("http://www.w3.org/2005/xpath-functions", "ends-with"):  xslt_functions.ends_with,
					("http://www.w3.org/2005/xpath-functions", "starts-with"):  xslt_functions.starts_with
				}
			proc = etree.XSLT(etree.parse(uri, self.parser), extensions=extensions)
		return proc
