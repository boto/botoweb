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
log = logging.getLogger("botoweb.cache_layer")

import re

from botoweb.appserver.wsgi_layer import WSGILayer
class CacheLayer(WSGILayer):
	"""
	Memcached layer on top of botoweb, this helps to 
	speed up frequent querys

	To Enable caching you must have python-memcached or libmemcached 
	installed (both providing the same interface), and then add a 
	config file under conf/cache.yaml like such:
		servers:
		  - host: hostname or ip
			port: port number

		  - host: another_hostname
			port: port number

	Optionaly you can have more control by adding a urls section:
		urls:
		  - url: /url_pattern_to_exclude*
			cache_time: 0

		  - url: /special_url_to_cache_long
			cache_time: 60000

	Note that these URLs are matched against the full query string, so 
	you will have to specify if that is or isn't allowed
	"""


	def update(self, env):
		"""
		When updating our environment, we're essentially re-creating our
		entire server pool
		"""
		self.env = env
		servers = []
		if env.config.has_section("cache"):
			import memcache
			for server in env.config['cache']['servers']:
				servers.append("%s:%s" % (server['host'], server['port']))
			self.memc = memcache.Client(servers)
		else:
			self.memc = None

	def handle(self, req, response):
		"""
		Cache layer with timeouts
		"""
		path_key = req.path_qs
		if req.method == "GET" and self.memc:
			try:
				cached_response = self.memc.get(path_key)
			except:
				cached_response = None
		else:
			cached_response = None
		if not cached_response:
			if self.app:
				response = self.app.handle(req, response)
			if req.method == "GET" and self.memc:
				cache_time = 60
				if self.env.config['cache'].has_key("urls"):
					for pattern in self.env.config['cache']['urls']:
						if re.match(pattern['url'], path_key):
							cache_time = pattern['cache_time']
							break
				if cache_time > 0:
					try:
						self.memc.set(path_key, response, cache_time)
					except:
						pass
		else:
			response = cached_response
		return response
