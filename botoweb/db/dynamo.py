# Copyright (c) 2012 Chris Moyer http://coredumped.org
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
#
# Author: Chris Moyer http://coredumped.org/
# Description: DynamoDB related objects.
# This is a lighter weight ORM for DynamoDB

import ssl
import json
import boto
import time
from boto.dynamodb.item import Item
from boto.dynamodb.table import Table
from boto.dynamodb import exceptions
from boto.exception import DynamoDBResponseError, BotoServerError

import logging
log = logging.getLogger("botoweb.db.dynamo")

MAX_RETRIES = 10

class DynamoModel(Item):
	"""DynamoDB Model.
	This is just a wrapper around
	boto.dynamodb.item.Item
	"""
	_manager = None # SDB Model Compatibility
	_table = None
	_table_name = None
	_properties = None
	_prop_cache = None

	def __init__(self, *args, **kwargs):
		"""Create a new DynamoDB model
		This supports both:
		>>> DynamoModel(table, "hash_key", "range_key", attrs)
		>>> DynamoModel("hash_key", "range_key")

		as well as using keyword args:
		>>> DynamoModel(table=table, hash_key="hash_key", range_key="range_key")
		>>> DynamoModel(hash_key="hash_key", range_key="range_key")
		>>> DynamoModel(table, hash_key="hash_key", range_key="range_key")

		This could be coming from Layer2, or it could be just called
		directly by us."""
		if len(args) > 0:
			first_arg = args[0]
		else:
			first_arg = kwargs.get("table")
		if first_arg and isinstance(first_arg, Table):
			# If the first argment is a Table, then
			# we assume this came from Layer2, so just pass this
			# on up the chain
			return Item.__init__(self, *args, **kwargs)
		else:
			# Otherwise, we're probably being called directly
			# so we should auto-set the table
			return Item.__init__(self, self.get_table(), *args, **kwargs)

	def __setitem__(self, key, value):
		"""Overwrite the setter to automatically
		convert types to DynamoDB supported types"""
		return Item.__setitem__(self, key, self.convert(key, value))

	def convert(self, key, value):
		"""Convert the value, this is called from __setitem__ but also called
		recursively when Lists are passed in"""
		from botoweb.db.model import Model
		from datetime import datetime
		# Allow null or empty values
		if not value:
			return value
		if isinstance(value, datetime):
			value = value.strftime("%Y-%m-%dT%H:%M:%S")
		elif isinstance(value, list):
			# Make sure to convert all the items in the list first
			for x, item in enumerate(value):
				value[x] = self.convert(key, item)
			value = set(value)
		elif isinstance(value, DynamoModel):
			value = value.id
		elif isinstance(value, Model):
			value = value.id
			
		return value
	
	@classmethod
	def get_table(cls):
		"""Get the table object for the given class"""
		if cls._table is None:
			conn = boto.connect_dynamodb()
			tbl_name = cls._table_name
			if not tbl_name:
				tbl_name = cls.__name__
			cls._table = conn.lookup(tbl_name)
		assert(cls._table), "Table not created for %s" % cls.__name__
		return cls._table

	@classmethod
	def get_by_id(cls, hash_key, range_key=None, consistent_read=False):
		"""Get this type of item by a given ID"""
		attempt = 0
		last_error = None
		while attempt < MAX_RETRIES:
			table = cls.get_table()
			try:
				return table.lookup(
					hash_key=hash_key,
					range_key=range_key,
					consistent_read=consistent_read,
					item_class=cls
				)
			except exceptions.DynamoDBKeyNotFoundError:
				return None
			except DynamoDBResponseError, e:
				log.exception("Could not retrieve item")
				cls._table = None
				attempt += 1
				time.sleep(attempt**2)
				last_error = e
			except BotoServerError, e:
				log.error("Boto Server Error: %s" % e)
				cls._table = None
				attempt += 1
				last_error = e
				time.sleep(attempt**2)

		if last_error:
			raise e

	lookup = get_by_id

	@classmethod
	def query(cls, hash_key, range_key_condition=None,
				request_limit=None, consistent_read=False,
				scan_index_forward=True):
		"""Query under a given hash_key

		:type range_key_condition: dict
		:param range_key_condition: A dict where the key is either
			a scalar value appropriate for the RangeKey in the schema
			of the database or a tuple of such values.  The value-
			associated with this key in the dict will be one of the
			following conditions:

			'EQ'|'LE'|'LT'|'GE'|'GT'|'BEGINS_WITH'|'BETWEEN'

			The only condition which expects or will accept a tuple
			of values is 'BETWEEN', otherwise a scalar value should
			be used as the key in the dict.

		:type request_limit: int
		:param request_limit: The maximum number of items to request from DynamoDB
			in one request. This limit helps with preventing over usage of your
			read quota.

		:type consistent_read: bool
		:param consistent_read: If True, a consistent read
			request is issued.  Otherwise, an eventually consistent
			request is issued.

		:type scan_index_forward: bool
		:param scan_index_forward: Specified forward or backward
			traversal of the index.  Default is forward (True).
		"""

		attempt = 0
		last_error = None
		while attempt < MAX_RETRIES:
			try:
				for item in  cls.get_table().query(hash_key=hash_key,
					range_key_condition=range_key_condition,
					request_limit=request_limit,
					consistent_read=consistent_read,
					scan_index_forward=scan_index_forward,item_class=cls):
					yield item
				return
			except DynamoDBResponseError, e:
				log.exception("Dynamo Response Error: %s" % e)
				cls._table = None
				attempt += 1
				last_error = e
				time.sleep(attempt**2)
			except BotoServerError, e:
				log.error("Boto Server Error: %s" % e)
				cls._table = None
				attempt += 1
				last_error = e
				time.sleep(attempt**2)
		if last_error:
			raise last_error

	find = query

	@classmethod
	def all(cls, request_limit=None):
		"""Uses Scan to return all of this type of object"""
		return DynamoQuery(cls, request_limit=request_limit)

	@classmethod
	def properties(cls, hidden=True):
		"""Returns a list of property objects, for compatibility with SDB Model objects"""
		if not cls._prop_cache:
			cls._prop_cache = []
			cursor = cls
			while cursor:
				if hasattr(cursor, "_properties") and cursor._properties:
					for key in cursor._properties.keys():
						prop = cursor._properties[key]
						if isinstance(prop, basestring):
							from botoweb.db.property import StringProperty
							prop = StringProperty(verbose_name=prop, name=key)
						if not prop.name:
							prop.name = key
						if hidden or not prop.__class__.__name__.startswith('_'):
							cursor._prop_cache.append(prop)
				if len(cursor.__bases__) > 0:
					cursor = cursor.__bases__[0]
				else:
					cursor = None
		return cls._prop_cache

	@classmethod
	def find_property(cls, prop_name):
		for prop in cls.properties():
			if prop.name == prop_name:
				return prop
		return None

	def __getattr__(self, name):
		ret = self.get(name)
		# Decode
		prop = self.find_property(name)
		if prop:
			try:
				if hasattr(prop, 'data_type'):
					# Decode lists
					if prop.data_type == list:
						# Singular values sometimes don't come out as lists, but as their
						# base value, like a String instead of a String Set
						if not isinstance(ret, set) and not isinstance(ret, list):
							ret = [ret]
						# Sets aren't modifyable, so we need to convert it to a list instead
						if isinstance(ret, set):
							ret = list(ret)
						if hasattr(prop, 'item_type'):
							for x, val in enumerate(ret):
								ret[x] = prop.item_type(val)
					# Decode everything else
					else:
							ret = prop.data_type(ret)
			except Exception:
				log.exception('Could not decode %s: %s', prop.data_type, ret)

		return ret

	@property
	def id(self):
		if self._range_key_name:
			return "-".join([self[self._hash_key_name], self[self._range_key_name]])
		else:
			return self[self._hash_key_name]

	#
	# Converters
	#
	def to_json(self):
		return json.dumps(self, cls=SetEncoder)

	def to_dict(self, recursive=True, include_hidden=True):
		"""Returns a copy of this item, converting all sets into lists"""

		d = {}
		for key, value in self.items():
			if not include_hidden and key.startswith('_'):
				continue
			if isinstance(value, set):
				value = list(value)
			d[key] = value
		# Auto set the __type__ and __id__ properties
		# if they aren't already specified
		if not self.has_key('__type__'):
			d['__type__'] = self.__class__.__name__
		if not self.has_key('__id__'):
			d['__id__'] = self.id
		return d

	@classmethod
	def from_dict(cls, data):
		"""Takes a normal dict, and returns this object"""
		table = cls.get_table()
		assert(data.has_key(table.schema.hash_key_name)), 'Missing %s' % table.schema.hash_key_name
		if table.schema.range_key_name:
			assert(data.has_key(table.schema.range_key_name)), 'Missing %s' % table.schema.range_key_name
		return cls(attrs=data)

	def put_attributes(self, attrs, expected_value=None, return_values=None):
		"""Put multiple attributes, really just calls
		put_attribute for each key/value pair, then 
		calls save"""
		updates = self._updates
		self._updates = {}
		for key, val in attrs.items():
			self.put_attribute(key, val)
		self.save(expected_value=expected_value, return_values=return_values)
		self._updates = updates

	#
	# Override the save and put methods
	# to auto-set some properties
	#
	def on_save_or_update(self):
		"""Automatically set properties, to be called
		from put() and save()"""
		if not self.has_key('created_at'):
			self['created_at'] = int(time.time())
		self['modified_at'] = int(time.time())

	def after_save_or_update(self):
		"""Automatically called *after* any save or update
		has been performed"""
		pass

	def put(self, *args, **kwargs):
		self.on_save_or_update()
		Item.put(self, *args, **kwargs)
		self.after_save_or_update()

	def save(self, *args, **kwargs):
		self.on_save_or_update()
		Item.save(self, *args, **kwargs)
		self.after_save_or_update()

from botoweb.db.query import Query
class DynamoQuery(Query):
	"""Query iterator for Dynamo-based objects"""

	def __init__(self, *args, **kwargs):
		if kwargs.has_key('request_limit'):
			self.request_limit = kwargs['request_limit']
			del(kwargs['request_limit'])
		Query.__init__(self, *args, **kwargs)

	def __iter__(self):
		"""Override this to change how we query this
		model"""
		attempt = 0
		last_error = None
		while attempt < MAX_RETRIES:
			try:
				for item in self.model_class.get_table().scan(item_class=self.model_class, request_limit=self.request_limit):
					yield item
				return
			except DynamoDBResponseError, e:
				log.exception("could not execute scan")
				self.model_class._table = None
				attempt += 1
				last_error = e
		if last_error:
			raise last_error

	def count(self, quick=True):
		"""Can't get counts from DynamoDB"""
		return self.model_class.get_table().item_count


class SetEncoder(json.JSONEncoder):
	"""Custom JSON encoder for converting sets to lists."""

	def default(self, obj):
		if isinstance(obj, set):
			obj = list(obj)
		return json.JSONEncoder.default(self, obj)
