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
from lxml import etree
from botoweb import xmlize
import time
import logging
log = logging.getLogger("botoweb.client.Environment")

try:
	import json
except ImportError:
	import simplejson as json

class Environment(object):
	"""Client Environment Object
	This operates off of the "Index" XML information 
	passed by the botoweb index handler
	"""
	max_tries = 10

	def __init__(self, host, port, enable_ssl=False):
		"""Initialize this environment from the URL specified

		@param host: The host to connect to
		@type host: str

		@param port: The port on the host to connect to
		@type port: int

		@param enable_ssl: True if we should use HTTPS, otherwise False
		@type enable_ssl: bool
		"""
		if enable_ssl:
			from httplib import HTTPSConnection as Connection
		else:
			from httplib import HTTPConnection as Connection
		self.conn = Connection(host, port)
		self.host = host
		self.port = port
		self.enable_ssl = enable_ssl
		self.auth_header = None

		# Try to fetch the pre-set username/password for this server
		import commands
		import re
		output = commands.getstatusoutput("security find-internet-password -gs %s" % self.host)
		if output[0] == 0:
			for l in output[1].split("\n"):
				matches = re.match("password: \"(.+?)\"", str(l))
				if matches:
					password = matches.group(1)
				matches = re.match("\s+?\"acct\"<blob>=\"(.+?)\"", str(l))
				if matches:
					username = matches.group(1)
			self.set_basic_auth(username, password)
		self._generate_routes()

	def _generate_routes(self):
		"""Generate the route table"""
		self.routes = {}
		resp = self.request("GET", "/")
		assert resp.status == 200
		tree = etree.parse(resp)
		root = tree.getroot()
		assert root.tag == "Index"
		self.app_name = root.get("name")
		for node in root:
			if node.tag == "api":
				self.routes[node.get("name")] = node.xpath("href/text()")[0]
		
	def request(self, method, path, post_data=None, body=None, headers={}):
		"""
		@param method: the HTTP Method to use
		@type method: str

		@param path: the path to access
		@type path: str

		@param post_data: Optional POST data to send (as form encoded body)
		@type post_data: dict

		@param body: Optional body text to send
		@type body: str
		"""
		tries = 0
		if body and not headers.has_key("Content-Length"):
			headers['Content-Length'] = len(body)
		while tries < self.max_tries:
			tries += 1
			self.connect()
			if self.auth_header:
				headers['Authorization'] = self.auth_header
			self.conn.request(method, path, body, headers)
			resp = self.conn.getresponse()
			if resp.status == 401:
				self.close()
				self.get_basic_auth()
				continue
			elif resp.status >= 500 or resp.status == 408:
				log.info("Got %s: Retrying in %s second(s)" % (resp.status, (tries**2)))
				time.sleep(tries**2)
				continue
			else:
				return resp
		if resp.status == 400:
			log.exception(resp.read())
		return resp

	def close(self):
		try:
			self.conn.close()
		except:
			pass

	def connect(self):
		self.close()
		self.conn.connect()

	def set_basic_auth(self, username, password):
		import base64
		base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
		self.auth_header =  "Basic %s" % base64string


	def get_basic_auth(self):
		"""
		Prompt for basic auth
		"""
		from getpass import getpass
		username = raw_input("Username: ")
		password = getpass("Password: ")
		self.set_basic_auth(username, password)


	def register(self, cls, name=None):
		"""Register this class with an optional name
		@param cls: Class to register
		@type cls: class

		@param name: Optional name to use for this class
		@type name: str
		"""
		xmlize.register(cls, name)

	def save(self, obj):
		"""Save this object"""
		assert obj.__class__.__name__ in self.routes
		url = self.routes[obj.__class__.__name__]
		body = xmlize.dumps(obj)
		if obj.id:
			# PUT to update
			self.request(method="PUT", path="/%s/%s" % (url, obj.id), body=body)
		else:
			# POST to create
			self.request(method="POST", path="/%s"%url, body=body)

	def get_by_id(self, cls, id):
		"""Get an object by ID

		@param cls: The class of the object to fetch
		@type cls: class or str

		@param id: The ID of the object to fetch
		@type id: str
		"""
		assert len(id) > 0
		if type(cls) == str:
			class_name = cls
			cls = xmlize.get_class(class_name)
		else:
			class_name = cls.__name__
		
		url = "%s/%s" % (self.routes[class_name], id)
		resp = self.request("GET", url)
		return xmlize.loads(resp.read())

	def find(self, cls, filters=None, sort=None, limit=None):
		"""Find objects by filters

		@param cls: The class of the object to search for
		@type cls: class or str

		@param filters: An Optional array of tuples for the filters like [["description", "!=", "foo"], ['name', '=', ['bar', 'biz', 'fizzle']]]
		@type filters: list

		@param sort: Optional param to sort on
		@type sort: str
		
		@param limit: Optional limit to how many results are fetched
		@type limit: int
		"""
		if type(cls) == str:
			class_name = cls
			cls = xmlize.get_class(class_name)
		else:
			class_name = cls.__name__
		
		url = "/%s%s" % (self.routes[class_name], self._build_query(filters, sort, limit))
		resp = self.request("GET", url)
		return xmlize.loads(resp.read())

	def _build_query(self, filters=None, sort_by=None, limit=None):
		"""Generate the query string"""
		import urllib
		if len(filters) > 4:
			raise Exception('Too many filters, max is 4')
		params = {}
		url = ""
		if filters:
			params['query'] = json.dumps(filters)
		if sort_by:
			params['sort_by'] = sort_by
		if limit:
			params['limit'] = str(limit)
		if len(params) > 0:
			query = urllib.urlencode(params)
			url += ("?"+query)
		return url


