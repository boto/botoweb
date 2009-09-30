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

import urllib
import urllib2
from lxml import etree
from xml.sax import make_parser
from botoweb.client.sax_handler import ObjectHandler
import logging
log = logging.getLogger("botoweb.client")
class Query(object):
	"""
	Query object iterator
	"""
	ALLOWED_EXPRESSIONS = ["=", "!=", ">", ">=", "<", "<=", "like", "not like", "between", "is null", "is not null"]

	def __init__(self, model_class, env, filters=[], limit=None, sort_by=None):
		self.model_class = model_class
		self.env = env
		self.filters = filters
		self.limit = limit
		self.sort_by = sort_by

	def filter(self, key, op, value):
		"""
		Add a filter to this query

		@param key: Key to filter on
		@param op: Operator to use
		@param value: Value, or list of values, to filter on
		"""
		assert op in self.ALLOWED_EXPRESSIONS
		self.filters.append((key, op, value))
		return self

	def order(self, key):
		"""
		Sort by this key
		"""
		self.sort_by = key
		return self

	def to_xml(self, doc=None):
		"""
		XML serialize this query
		"""
		if doc == None:
			doc = etree.Element("%sList" % self.model_class.__name__)
		for obj in self:
			obj.to_xml(doc)
		return doc

	def __iter__(self):
		self.env.register(self.model_class(self.env), self.model_class.__name__)
		return iter(self.env.find(self.model_class, self.filters, self.sort_by, self.limit))

	def __call__(self):
		"""Nifty little trick to allow this to be treaded like a class
		when we're being de-xmlized"""
		return self

	def next(self):
		return self.__iter__().next()

	def count(self):
		return 0
