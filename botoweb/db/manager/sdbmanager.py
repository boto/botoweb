# Copyright (c) 2006,2007,2008 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010-2013 Chris Moyer http://coredumped.org/
# Copyright (c) 2014 Saikat DebRoy
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
import boto.sdb
import ssl
from boto.utils import find_class
import uuid
import re
from time import sleep
from botoweb.db.blob import Blob
from boto.exception import SDBPersistenceError, S3ResponseError
from botoweb.db.property import ListProperty
from botoweb.db.converter import StringConverter
from botoweb.db.manager import Manager

import logging
log = logging.getLogger('botoweb.db.manager.sdbmanager')

class SDBConverter(StringConverter):
	"""SDBConverter is just a StringConverter with special Blob property handling"""

	def encode_blob(self, value):
		if not value:
			return None
		if isinstance(value, str):
			return value

		if not value.id:
			bucket = self.manager.get_blob_bucket()
			key = bucket.new_key(str(uuid.uuid4()))
			value.id = 's3://%s/%s' % (key.bucket.name, key.name)
		else:
			match = re.match('^s3:\/\/([^\/]*)\/(.*)$', value.id)
			if match:
				s3 = self.manager.get_s3_connection()
				bucket = s3.get_bucket(match.group(1), validate=False)
				key = bucket.get_key(match.group(2))
			else:
				raise SDBPersistenceError('Invalid Blob ID: %s' % value.id)

		if value.value != None:
			key.set_contents_from_string(value.value)
		return value.id


	def decode_blob(self, value):
		if not value:
			return None
		match = re.match('^s3:\/\/([^\/]*)\/(.*)$', value)
		if match:
			s3 = self.manager.get_s3_connection()
			bucket = s3.get_bucket(match.group(1), validate=False)
			# Try to retrieve the blob up to five times
			error = None
			for attempt in range(0,5):
				try:
					key = bucket.get_key(match.group(2))
				except S3ResponseError, e:
					error = e
					log.exception(e)
					if e.reason != 'Forbidden':
						sleep(attempt**2)
						continue
					return None
				except Exception, e:
					log.exception(e)
					sleep(attempt**2)
					error = e
					continue
				else:
					error = None
					break
		else:
			return None
		if error:
			raise error
		if key:
			return Blob(file=key, id='s3://%s/%s' % (key.bucket.name, key.name))
		else:
			return None


class SDBManager(Manager):
	"""SimpleDB Manager"""
	_converter_class = SDBConverter
	
	def __init__(self, cls, db_name, db_user, db_passwd,
				 db_host, db_port, db_table, ddl_dir, enable_ssl, consistent=None):
		Manager.__init__(self, cls, db_name, db_user, db_passwd,
			db_host, db_port, db_table, ddl_dir, enable_ssl, consistent)
		self.s3 = None
		self.bucket = None
		self._sdb = None
		self._domain = None

	@property
	def sdb(self):
		if self._sdb is None:
			self._connect()
		return self._sdb

	@property
	def domain(self):
		if self._domain is None:
			self._connect()
		return self._domain

	def _connect(self):
		args = dict(aws_access_key_id=self.db_user,
					aws_secret_access_key=self.db_passwd,
					is_secure=self.enable_ssl)
		try:
			region = [x for x in boto.sdb.regions() if x.endpoint == self.db_host][0]
			args['region'] = region
		except IndexError:
			pass
		self._sdb = boto.connect_sdb(**args)
		self._sdb.http_exceptions = tuple(list(self._sdb.http_exceptions) + [ssl.SSLError])
		# This assumes that the domain has already been created
		# It's much more efficient to do it this way rather than
		# having this make a roundtrip each time to validate.
		# The downside is that if the domain doesn't exist, it breaks
		self._domain = self._sdb.lookup(self.db_name, validate=False)
		if not self._domain:
			self._domain = self._sdb.create_domain(self.db_name)

	def get_s3_connection(self):
		if not self.s3:
			self.s3 = boto.connect_s3(self.db_user, self.db_passwd)
			self.s3.http_exceptions = tuple(list(self.s3.http_exceptions) + [ssl.SSLError])
		return self.s3

	def get_blob_bucket(self, bucket_name=None):
		s3 = self.get_s3_connection()
		bucket_name = '%s-%s' % (boto.config.get('DB', 'blob_bucket_prefix', s3.aws_access_key_id), self.domain.name)
		bucket_name = bucket_name.lower()
		try:
			self.bucket = s3.get_bucket(bucket_name)
		except:
			self.bucket = s3.create_bucket(bucket_name)
		return self.bucket
			
	def load_object(self, obj):
		if not obj._loaded:
			obj._validate = False
			a = self.domain.get_attributes(obj.id,consistent_read=self.consistent)
			if a.has_key('__type__'):
				for prop in obj.properties(hidden=False):
					if a.has_key(prop.name):
						value = self.decode_value(prop, a[prop.name])
						value = prop.make_value_from_datastore(value)
						try:
							setattr(obj, prop.name, value)
						except Exception, e:
							log.exception(e)
			obj._loaded = True
			obj._validate = True
		
	def get_object(self, cls, id, a=None):
		obj = None
		if not a:
			a = self.domain.get_attributes(id,consistent_read=self.consistent)
		if a.has_key('__type__'):
			if not cls or a['__type__'] != cls.__name__:
				cls = find_class(a['__module__'], a['__type__'])
			if cls:
				params = {}
				for prop in cls.properties(hidden=False):
					if a.has_key(prop.name):
						value = self.decode_value(prop, a[prop.name])
						value = prop.make_value_from_datastore(value)
						params[prop.name] = value
				obj = cls(id, **params)
				obj._loaded = True
			else:
				s = '(%s) class %s.%s not found' % (id, a['__module__'], a['__type__'])
				log.info('sdbmanager: %s' % s)
		return obj
		
	def query(self, query):
		query_str = "select * from `%s` %s" % (self.domain.name, self._build_filter_part(query.model_class, query.filters, query.sort_by, query.select))
		if query.limit:
			query_str += " limit %s" % query.limit
		rs = self.domain.select(query_str, max_items=query.limit, next_token = query.next_token)
		query.rs = rs
		return self._object_lister(query.model_class, rs)

	def count(self, cls, filters, quick=True, sort_by=None, select=None):
		"""
		Get the number of results that would
		be returned in this query
		"""
		query = "select count(*) from `%s` %s" % (self.domain.name, self._build_filter_part(cls, filters, sort_by, select))
		count = 0
		for row in self.domain.select(query):
			count += int(row['Count'])
			if quick:
				return count
		return count


	def _build_filter(self, property, name, op, val):
		if name == "__id__":
			name = 'itemName()'
		if name != "itemName()":
			name = '`%s`' % name
		if val == None:
			if op in ('is','='):
				return "%(name)s is null" % {"name": name}
			elif op in ('is not', '!='):
				return "%s is not null" % name
			else:
				val = ""
		if property.__class__ == ListProperty:
			if op in ("is", "="):
				op = "like"
			elif op in ("!=", "not"):
				op = "not like"
			if not(op in ["like", "not like"] and val.startswith("%")):
				val = "%%:%s" % val
		return "%s %s '%s'" % (name, op, val.replace("'", "''"))

	def _build_filter_part(self, cls, filters, order_by=None, select=None):
		"""
		Build the filter part
		"""
		import types
		query_parts = []
		order_by_filtered = False

		if order_by:
			if order_by[0] == "-":
				order_by_method = "DESC";
				order_by = order_by[1:]
			else:
				order_by_method = "ASC";

		if select:
			if order_by and order_by in select:
				order_by_filtered = True
			query_parts.append("(%s)" % select)
		if isinstance(filters, str) or isinstance(filters, unicode):
			query = "WHERE %s AND `__type__` = '%s'" % (filters, cls.__name__)
			if order_by in ["__id__", "itemName()"]:
				query += " ORDER BY itemName() %s" % order_by_method
			elif order_by != None:
				query += " ORDER BY `%s` %s" % (order_by, order_by_method)
			return query

		for filter in filters:
			filter_parts = []
			filter_props = filter[0]
			if type(filter_props) != list:
				filter_props = [filter_props]
			for filter_prop in filter_props:
				(name, op) = filter_prop.strip().split(" ", 1)
				value = filter[1]
				property = cls.find_property(name)
				if name == order_by:
					order_by_filtered = True
				if types.TypeType(value) == types.ListType:
					filter_parts_sub = []
					for val in value:
						val = self.encode_value(property, val)
						if isinstance(val, list):
							for v in val:
								filter_parts_sub.append(self._build_filter(property, name, op, v))
						else:
							filter_parts_sub.append(self._build_filter(property, name, op, val))
					if op in ["not like", "not", "!="]:
						filter_parts.append("(%s)" % (" AND ".join(filter_parts_sub)))
					else:
						filter_parts.append("(%s)" % (" OR ".join(filter_parts_sub)))
				else:
					val = self.encode_value(property, value)
					if isinstance(val, list):
						for v in val:
							filter_parts.append(self._build_filter(property, name, op, v))
					else:
						filter_parts.append(self._build_filter(property, name, op, val))
			query_parts.append("(%s)" % (" or ".join(filter_parts)))


		type_query = "(`__type__` = '%s'" % cls.__name__
		for subclass in self.get_all_decendents(cls).keys():
			type_query += " or `__type__` = '%s'" % subclass
		type_query +=")"
		query_parts.append(type_query)

		order_by_query = ""

		if order_by:
			if not order_by_filtered:
				query_parts.append("`%s` LIKE '%%'" % order_by)
			if order_by in ["__id__", "itemName()"]:
				order_by_query = " ORDER BY itemName() %s" % order_by_method
			else:
				order_by_query = " ORDER BY `%s` %s" % (order_by, order_by_method)

		if len(query_parts) > 0:
			return "WHERE %s %s" % (" AND ".join(query_parts), order_by_query)
		else:
			return ""

	def save_object(self, obj, expected_value=None):
		if not obj.id:
			obj.id = str(uuid.uuid4())

		attrs = {'__type__' : obj.__class__.__name__,
				 '__module__' : obj.__class__.__module__,
				 '__lineage__' : obj.get_lineage()}
		del_attrs = []
		for property in obj.properties(hidden=False):
			if property.is_calculated:
				del_attrs.append(property.name)
				continue
			value = property.get_value_for_datastore(obj)
			if value is not None:
				value = self.encode_value(property, value)
			if value == []:
				value = None
			if value == None:
				del_attrs.append(property.name)
				continue
			attrs[property.name] = value
			if property.unique:
				try:
					args = {property.name: value}
					obj2 = obj.find(**args).next()
					if obj2.id != obj.id:
						raise SDBPersistenceError("Error: %s must be unique!" % property.name)
				except(StopIteration):
					pass
		# Convert the Expected value to SDB format
		if expected_value:
			prop = obj.find_property(expected_value[0])
			v = expected_value[1]
			if v is not None and not type(v) == bool:
				v = self.encode_value(prop, v)
			expected_value[1] = v
		self.domain.put_attributes(obj.id, attrs, replace=True, expected_value=expected_value)
		if len(del_attrs) > 0:
			self.domain.delete_attributes(obj.id, del_attrs)
		return obj

	def delete_object(self, obj):
		self.domain.delete_attributes(obj.id)

	def set_property(self, prop, obj, name, value):
		setattr(obj, name, value)
		value = prop.get_value_for_datastore(obj)
		value = self.encode_value(prop, value)
		if prop.unique:
			try:
				args = {prop.name: value}
				obj2 = obj.find(**args).next()
				if obj2.id != obj.id:
					raise SDBPersistenceError("Error: %s must be unique!" % prop.name)
			except(StopIteration):
				pass
		self.domain.put_attributes(obj.id, {name : value}, replace=True)

	def get_property(self, prop, obj, name):
		a = self.domain.get_attributes(obj.id,consistent_read=self.consistent)

		# try to get the attribute value from SDB
		if name in a:
			value = self.decode_value(prop, a[name])
			value = prop.make_value_from_datastore(value)
			setattr(obj, prop.name, value)
			return value
		raise AttributeError, '%s not found' % name

	def set_key_value(self, obj, name, value):
		self.domain.put_attributes(obj.id, {name : value}, replace=True)

	def delete_key_value(self, obj, name):
		self.domain.delete_attributes(obj.id, name)

	def get_key_value(self, obj, name):
		a = self.domain.get_attributes(obj.id, name,consistent_read=self.consistent)
		if a.has_key(name):
			return a[name]
		else:
			return None
	
	def get_raw_item(self, obj):
		return self.domain.get_item(obj.id)
		
