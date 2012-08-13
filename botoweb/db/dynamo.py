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
import boto
from boto.dynamodb.item import Item
from boto.dynamodb.table import Table
from boto.dynamodb import exceptions
from boto.exception import DynamoDBResponseError, BotoServerError

import logging
log = logging.getLogger("botoweb.db.dynamo")

class DynamoModel(Item):
	"""DynamoDB Model.
	This is just a wrapper around
	boto.dynamodb.item.Item
	"""
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
		from datetime import datetime
		if isinstance(value, datetime):
			value = value.strftime("%Y-%m-%dT%H:%M:%S")
		elif isinstance(value, list):
			value = set(value)
		return Item.__setitem__(self, key, value)
	
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
		attempts = 0
		while attempts < 5:
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
			except DynamoDBResponseError:
				log.exception("Could not retrieve item")
				cls._table = None
				attempts += 1

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
		while attempt < 5:
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
			except BotoServerError, e:
				log.error("Boto Server Error: %s" % e)
				cls._table = None
				attempt += 1

	find = query

	@classmethod
	def all(cls):
		"""Uses Scan to return all of this type of object"""
		attempt = 0
		while attempt < 5:
			try:
				for item in cls.get_table().scan(item_class=cls):
					yield item
				return
			except DynamoDBResponseError:
				log.exception("could not execute scan")
				cls._table = None
				attempt += 1

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
