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
from base64 import b32decode, b32encode

import logging
log = logging.getLogger('botoweb.db.dynamo')

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
	# Supports CloudSearch
	_cs_search_endpoint = None
	_cs_document_endpoint = None

	def __init__(self, *args, **kwargs):
		"""Create a new DynamoDB model
		This supports both:
		>>> DynamoModel(table, 'hash_key', 'range_key', attrs)
		>>> DynamoModel('hash_key', 'range_key')

		as well as using keyword args:
		>>> DynamoModel(table=table, hash_key='hash_key', range_key='range_key')
		>>> DynamoModel(hash_key='hash_key', range_key='range_key')
		>>> DynamoModel(table, hash_key='hash_key', range_key='range_key')

		This could be coming from Layer2, or it could be just called
		directly by us."""
		if len(args) > 0:
			first_arg = args[0]
		else:
			first_arg = kwargs.get('table')
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
			value = value.strftime('%Y-%m-%dT%H:%M:%S')
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
		assert(cls._table), 'Table not created for %s' % cls.__name__
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
				log.exception('Could not retrieve item')
				cls._table = None
				attempt += 1
				time.sleep(attempt**2)
				last_error = e
			except BotoServerError, e:
				log.error('Boto Server Error: %s' % e)
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
				log.exception('Dynamo Response Error: %s' % e)
				cls._table = None
				attempt += 1
				last_error = e
				time.sleep(attempt**2)
			except BotoServerError, e:
				log.error('Boto Server Error: %s' % e)
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
	def search(cls, q=None, bq=None, rank=None, start=0, **kwargs):
		"""Search using CloudSearch. This requires a _cs_search_endpoint property to be set
		:param q: The optional TEXT search query
		:type q: str
		:param bq: The optional BOOLEAN search query
		:type bq: str
		:param rank: The optional Search rank
		:type rank: str
		:param start: The optional start point to begin the search
		:type start: int
		:param: Other KW args are supported and used as direct matches in the Boolean Query"""
		from boto.cloudsearch.search import SearchConnection
		if not cls._cs_search_endpoint:
			raise NotImplemented('No CloudSearch Domain Set')

		# Converts all the keyword arguments to a boolaen query
		if kwargs:
			query_parts = []
			if bq:
				query_parts.append(bq)

			# Build all the query parts
			for arg in kwargs:
				query_parts.append('%s:\'%s\'' % (arg, kwargs[arg]))

			# Reduce the query back to a single string
			bq = '(and %s)' % ' '.join(query_parts)

		# Build the search args
		args = {}
		if q:
			args['q'] = q
		if bq:
			args['bq'] = bq
		if rank:
			args['rank'] = rank
		if start:
			args['start'] = start

		conn = SearchConnection(endpoint=cls._cs_search_endpoint)
		return BatchItemFetcher(conn.search(**args), cls)


	@classmethod
	def properties(cls, hidden=True):
		"""Returns a list of property objects, for compatibility with SDB Model objects"""
		if not cls._prop_cache:
			cls._prop_cache = []
			cursor = cls
			while cursor:
				if hasattr(cursor, '_properties') and cursor._properties:
					for key in cursor._properties.keys():
						prop = cursor._properties[key]
						if isinstance(prop, basestring):
							from botoweb.db.property import StringProperty
							prop = StringProperty(verbose_name=prop, name=key)
						if not prop.name:
							prop.name = key
						if hidden or not prop.__class__.__name__.startswith('_'):
							cls._prop_cache.append(prop)
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
		from datetime import datetime
		ret = self.get(name)
		# Handle none and empty values
		if not ret:
			return ret
		# Handle Unicode
		if isinstance(ret, unicode):
			ret = ret.encode('utf-8')
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
					# Decode Objects
					elif hasattr(prop, 'reference_class'):
						ret = prop.reference_class(ret)
					# Decode Datetimes
					elif prop.data_type == datetime:
						ret = datetime.utcfromtimestamp(ret)
					# Decode everything else
					else:
						ret = prop.data_type(ret)
			except Exception:
				log.exception('Could not decode %s: %s', prop.data_type, ret)

		return ret

	def get_id(self):
		if self._range_key_name:
			return '/'.join([self[self._hash_key_name], self[self._range_key_name]])
		else:
			return self[self._hash_key_name]

	def set_id(self, val):
		"""Allows for setting the ID"""
		if self._range_key_name:
			(self[self._hash_key_name], self[self._range_key_name]) = val.split('/', 1)
		else:
			self[self._hash_key_name] = val

	id = property(get_id, set_id)

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
		if self._cs_document_endpoint:
			self.save_to_cloudsearch()
		Item.put(self, *args, **kwargs)
		self.after_save_or_update()

	def save(self, *args, **kwargs):
		self.on_save_or_update()
		if self._cs_document_endpoint:
			self.save_to_cloudsearch()
		Item.save(self, *args, **kwargs)
		self.after_save_or_update()

	def save_to_cloudsearch(self, conn=None):
		"""Save/Update this item in CloudSearch"""
		from boto.cloudsearch.document import DocumentServiceConnection
		if conn is None:
			conn = DocumentServiceConnection(endpoint=self._cs_document_endpoint)
		# Build the document ID
		doc_id = self.id
		doc_id = b32encode(doc_id).lower().replace('=', '_')
		conn.add(doc_id, int(time.time()), fields=self.get_sdf())
		conn.commit()

	def get_sdf(self):
		"""GET a SDF (Search Data Format) for use in CloudSearch"""
		data = self.to_dict()
		# Adds a "Model" field if one doesn't already exist
		if not data.has_key('model'):
			data['model'] =  self.__class__.__name__

		# Remove all null values
		for key in data.keys():
			val = data[key]
			if key.startswith('_') or val in (' ', '  ',  [''], [' '], ['  ']) or (not val and not isinstance(val, bool) and not isinstance(val, int)):
				del(data[key])
			elif isinstance(val, list) or isinstance(val, tuple):
				val = list(set(val))
				for item in val:
					if isinstance(item, basestring):
						item = item.strip()
					if not item:
						val.remove(item)
				if not val and not isinstance(val, bool) and not isinstance(val, int):
					del(data[key])
				else:
					data[key] = val
			elif isinstance(val, basestring):
				# Prevents rouge empty strings
				data[key] = val.strip()
				if not data[key]:
					del(data[key])
		return data

	def delete(self, *args, **kwargs):
		"""Intercept the delete function to also remove this record from CloudSearch
		if it is indexed"""
		if self._cs_document_endpoint:
			from boto.cloudsearch.document import DocumentServiceConnection
			conn = DocumentServiceConnection(endpoint=self._cs_document_endpoint)
			doc_id = self.id
			doc_id = b32encode(doc_id).lower().replace('=', '_')
			conn.delete(doc_id, int(time.time()))
			conn.commit()
		return Item.delete(self, *args, **kwargs)



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
				log.exception('could not execute scan')
				self.model_class._table = None
				attempt += 1
				last_error = e
		if last_error:
			raise last_error

	def count(self, quick=True):
		"""Can't get counts from DynamoDB"""
		return -1


class SetEncoder(json.JSONEncoder):
	"""Custom JSON encoder for converting sets to lists."""

	def default(self, obj):
		if isinstance(obj, set):
			obj = list(obj)
		return json.JSONEncoder.default(self, obj)

class BatchItemFetcher(object):
	"""Fetches items in bulk, instead of individually"""

	def __init__(self, items, model_class, count=-1, limit=None):
		from boto.cloudsearch.search import SearchResults
		# Handle SearchResults from CloudSearch
		if isinstance(items, SearchResults):
			self.items = []
			for item in items:
				obj_id = b32decode(item['id'].upper().replace('_', '='))
				if model_class.get_table().schema.range_key_name:
					obj_id = obj_id.split('/')
				self.items.append(obj_id)
			count = items.hits
		else:
			self.items = items

		self._count = count
		# Aliased because some things use 'total' instead of count()
		self.total = count
		self.limit = limit
		self.next_token = None
		self.model_class = model_class
		self.results = {}

		# If there are items to be fetched, do the batch lookup
		if self.items:
			for result in model_class.get_table().batch_get_item(self.items):
				obj_id = result[model_class.get_table().schema.hash_key_name]
				if model_class.get_table().schema.range_key_name:
					obj_id =  '/'.join([obj_id, result[model_class.get_table().schema.range_key_name]])
				self.results[obj_id] = self.get_obj(result)

	def __iter__(self):
		for item in self.items:
			if isinstance(item, list):
				item_id = '/'.join(item)
			else:
				item_id = item
			if self.results.has_key(item_id):
				yield self.results[item_id]
			else:
				yield self.model_class.lookup(item)

	def get_obj(self, item):
		"""Turns a DynamoDB result into an object"""
		item = dict(item)

		# Convert sets back to lists
		for key in item.keys():
			val = item[key]
			if isinstance(val, set):
				item[key] = list(val)
		# Get it as an object
		obj = self.model_class.from_dict(item)
		return obj

	def count(self, *args, **kwargs):
		return self._count
