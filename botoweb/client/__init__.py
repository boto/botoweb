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
from botoweb.client.query import Query

import logging
log = logging.getLogger("botoweb.client")
class ClientObject(object):
	"""botoweb Client Object to interface via REST to our
	XML server
	"""
	_properties = []

	def __init__(self, env, id=None, **params):
		"""Initialize the Client Object with a given environment
		Additional arguments may be passed to set them immediately on the newly 
		created object

		:param env: The botoweb.environment.Environment object to use
		:type env: botoweb.environment.Environment

		:param id: The ID to use for this object
		:type id: str
		"""
		self._env = env
		self.id = id
		for k in params:
			setattr(self, k, params[k])

	@classmethod
	def all(cls, env):
		"""List all objects

		:param env: The botoweb.environment.Environment object to use
		:type env: botoweb.environment.Environment
		"""
		return cls.query(env, [])

	@classmethod
	def find(cls, env, **params):
		"""Simple search method.

		:param env: The botoweb.environment.Environment object to use
		:type env: botoweb.environment.Environment

		:param **params: Parameters to search for, passed in standard key=value pairs
		"""
		filters = []
		for k in params:
			filters.append((k, "=", params[k]))
		return cls.query(env, filters)

	@classmethod
	def query(cls, env, filters):
		"""Search for objects

		:param env: The botoweb.environment.Environment object to use
		:type env: botoweb.environment.Environment

		:param filters: Filters to apply to the search, formatted as [(key, op, value), (key, op, [value, value])]
			 values, if a list, are considered OR searches, whereas filters are normally AND operations.
		:type filters: [(key, op, value), (key2, op2, [value2, value3, ..])]
		"""
		return Query(cls, env, filters)

	@classmethod
	def get_by_id(cls, env, id):
		"""GET for object ID

		:param env: The botoweb.client.environment.Environment object to use
		:type env: botoweb.client.environment.Environment

		:param id: The ID of the object to get
		:type id: str
		"""
		return env.get_by_id(cls, id)

	def __call__(self):
		"""A little trick to make this object act as if it could be callable like a class"""
		return self.__class__(self._env)

	def put(self):
		"""PUT this object (save)"""
		return self._env.save(self)
