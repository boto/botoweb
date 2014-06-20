# Copyright (c) 2013 Chris Moyer http://coredumped.org/
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

import uuid
import time
import boto.dynamodb
from botoweb.db.converter import StringConverter
from botoweb.db.manager import Manager
import botoweb.exceptions
import boto.exception
import boto.dynamodb.exceptions

import logging
log = logging.getLogger('botoweb.db.manager.dynamo')

class DDBConverter(StringConverter):
	"""We have to also convert Lists to Sets"""

	def encode_list(self, prop, value):
		ret = StringConverter.encode_list(self, prop, value)
		if ret and isinstance(ret, list):
			ret = set(ret)
		return ret

	def encode_map(self, prop, value):
		ret = StringConverter.encode_map(self, prop, value)
		if ret and isinstance(ret, list):
			ret = set(ret)
		return ret

	def decode_list(self, prop, value):
		if not isinstance(value, list) and not isinstance(value, set):
			value = [value]
		if hasattr(prop, 'item_type'):
			item_type = getattr(prop, 'item_type')
			dec_val = {}
			for val in value:
				if val != None:
					k,v = self.decode_map_element(item_type, val)
					try:
						k = int(k)
					except:
						k = v
					dec_val[k] = v
			value = dec_val.values()
		return value



class DynamoDBManager(Manager):
	"""DynamoDB + CloudSearch"""
	_converter_class = DDBConverter

	def __init__(self, cls, db_name, db_user, db_passwd,
				 db_host, db_port, db_table, ddl_dir, enable_ssl, consistent=None):
		Manager.__init__(self, cls, db_name, db_user, db_passwd,
			db_host, db_port, db_table, ddl_dir, enable_ssl, consistent)
		self._dynamodb = None
		self._table = None

	@property
	def dynamodb(self):
		if self._dynamodb is None:
			self._connect()
		return self._dynamodb

	@property
	def table(self):
		if self._table is None:
			self._connect()
		return self._table

	def _connect(self):
		args = dict(aws_access_key_id=self.db_user,
					aws_secret_access_key=self.db_passwd,
					is_secure=self.enable_ssl)
		try:
			region = [x for x in boto.dynamodb.regions() if x.endpoint == self.db_host][0]
			args['region'] = region
		except IndexError:
			pass
		self._dynamodb = boto.connect_dynamodb(**args)
		# Look up or create a new table for this item
		try:
			self._table = self._dynamodb.lookup(self.db_name)
		except boto.exception.DynamoDBResponseError:
			self._table = None
		if not self._table:
			from boto.dynamodb.schema import Schema
			self._table = self._dynamodb.create_table(
				name=self.db_name,
				schema=Schema.create(hash_key=('__id__', 'S')),
				read_units=1,
				write_units=1)
			while self._table.status == 'CREATING':
				time.sleep(1)
				self._table.refresh()

	def save_object(self, obj, expected_value=None):
		if not obj.id:
			obj.id = str(uuid.uuid4())
			obj._loaded = True

		raw_item = self.get_raw_item(obj)
		obj._raw_item = raw_item

		# Set/delete all the properties
		for property in obj.properties(hidden=False):
			delete_item = property.is_calculated
			if not delete_item:
				value = property.get_value_for_datastore(obj)
				if value is not None:
					value = self.encode_value(property, value)
				if value == []:
					value = None
				delete_item = value == None
			if delete_item:
				if raw_item.has_key(property.name):
					del(raw_item[property.name])
			else:
				raw_item[property.name] = value

		# Convert the Expected value to DynamoDB
		if expected_value:
			prop = obj.find_property(expected_value[0])
			v = expected_value[1]
			if v is not None and not type(v) == bool:
				v = self.encode_value(prop, v)
			expected_value[1] = v

		# Save
		raw_item.put(expected_value=expected_value)
		return obj

	def get_raw_item(self, obj):
		try:
			return self.table.lookup(obj.id)
		except boto.dynamodb.exceptions.DynamoDBKeyNotFoundError:
			return self.table.new_item(obj.id)

	def load_object(self, obj):
		if not obj._loaded:
			try:
				raw_item = self.get_raw_item(obj)
			except boto.dynamodb.exceptions.DynamoDBKeyNotFoundError:
				return
			for prop in obj.properties(hidden=False):
				if raw_item.has_key(prop.name):
					value = self.decode_value(prop, raw_item[prop.name])
					value = prop.make_value_from_datastore(value)
					try:
						setattr(obj, prop.name, value)
					except Exception, e:
						log.exception(e)
			obj._loaded = True
		return obj

	def get_object(self, cls, id, a=None):
		try:
			raw_item = self.table.lookup(id)
		except boto.dynamodb.exceptions.DynamoDBKeyNotFoundError:
			raise botoweb.exceptions.NotFound('Could not find %s "%s"' % (cls.__name__, id))

		params = {}
		for prop in cls.properties(hidden=False):
			if raw_item.has_key(prop.name):
				value = self.decode_value(prop, raw_item[prop.name])
				value = prop.make_value_from_datastore(value)
				params[prop.name] = value
		obj = cls(id, **params)
		obj._loaded = True
		return obj

	#
	# Searching and querying come out of CloudSearch
	# 
	def count(self, cls, filters, quick=True, sort_by=None, select=None):
		return 0
