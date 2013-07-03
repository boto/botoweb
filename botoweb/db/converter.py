# Copyright (c) 2013 Chris Moyer http://coredumped.org/
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
from botoweb.db.key import Key
from botoweb.db.coremodel import Model
from botoweb.db.blob import Blob
from botoweb.db.property import ListProperty, MapProperty
from datetime import datetime, date, time
from botoweb.exceptions import TimeDecodeError
from botoweb import ISO8601

import logging
log = logging.getLogger('botoweb.db.converter')

class Converter(object):
	"""
	Responsible for converting base Python types to format compatible with underlying
	database. This is a base implementation which does no conversions.

	To convert a value, pass it to the encode or decode method.  The encode method
	will take a Python native value and convert to DB format.  The decode method will
	take a DB format value and convert it to Python native format.  To find the appropriate
	method to call, the generic encode/decode methods will look for the type-specific
	method by searching for a method called 'encode_<type name>' or 'decode_<type name>'.
	"""
	def __init__(self, manager):
		self.manager = manager
		self.type_map = { bool : (self.encode_bool, self.decode_bool),
						int : (self.encode_int, self.decode_int),
						long : (self.encode_long, self.decode_long),
						float : (self.encode_float, self.decode_float),
						Model : (self.encode_reference, self.decode_reference),
						Key : (self.encode_reference, self.decode_reference),
						datetime : (self.encode_datetime, self.decode_datetime),
						date : (self.encode_date, self.decode_date),
						time : (self.encode_time, self.decode_time),
						Blob: (self.encode_blob, self.decode_blob),
						str: (self.encode_string, self.decode_string),
					}

	def encode(self, item_type, value):
		try:
			if Model in item_type.mro():
				item_type = Model
		except:
			pass
		if item_type in self.type_map:
			encode = self.type_map[item_type][0]
			return encode(value)
		return value

	def decode(self, item_type, value):
		if item_type in self.type_map:
			decode = self.type_map[item_type][1]
			return decode(value)
		return value

	def encode_list(self, prop, value):
		if value in (None, []):
			return []
		if not isinstance(value, list):
			# This is a little trick to avoid encoding when it's just a single value,
			# since that most likely means it's from a query
			item_type = getattr(prop, 'item_type')
			return self.encode(item_type, value)
		# Just enumerate(value) won't work here because
		# we need to add in some zero padding
		# We support lists up to 1,000 attributes, since
		# SDB technically only supports 1024 attributes anyway
		values = {}
		for k,v in enumerate(value):
			values['%03d' % k] = v
		return self.encode_map(prop, values)

	def encode_map(self, prop, value):
		import urllib
		if value == None:
			return None
		if not isinstance(value, dict):
			raise ValueError, 'Expected a dict value, got %s' % type(value)
		new_value = []
		for key in value:
			item_type = getattr(prop, 'item_type')
			if Model in item_type.mro():
				item_type = Model
			encoded_value = self.encode(item_type, value[key])
			if encoded_value != None:
				new_value.append('%s:%s' % (urllib.quote(key), encoded_value))
		return new_value

	def encode_prop(self, prop, value):
		if isinstance(prop, ListProperty):
			return self.encode_list(prop, value)
		elif isinstance(prop, MapProperty):
			return self.encode_map(prop, value)
		else:
			return self.encode(prop.data_type, value)

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

	def decode_map(self, prop, value):
		if not isinstance(value, list):
			value = [value]
		ret_value = {}
		item_type = getattr(prop, 'item_type')
		for val in value:
			k,v = self.decode_map_element(item_type, val)
			ret_value[k] = v
		return ret_value

	def decode_map_element(self, item_type, value):
		"""Decode a single element for a map"""
		import urllib
		key = value
		if ':' in value:
			key, value = value.split(':',1)
			key = urllib.unquote(key)
		if Model in item_type.mro():
			value = item_type(id=value)
		else:
			value = self.decode(item_type, value)
		return (key, value)

	def decode_prop(self, prop, value):
		if isinstance(prop, ListProperty):
			return self.decode_list(prop, value)
		elif isinstance(prop, MapProperty):
			return self.decode_map(prop, value)
		else:
			return self.decode(prop.data_type, value)

	def encode_int(self, value):
		value = int(value)
		value += 2147483648
		return '%010d' % value

	def decode_int(self, value):
		try:
			value = int(value)
		except:
			log.error('Error, %s is not an integer' % value)
			value = 0
		value = int(value)
		value -= 2147483648
		return int(value)

	def encode_long(self, value):
		value = long(value)
		value += 9223372036854775808
		return '%020d' % value

	def decode_long(self, value):
		value = long(value)
		value -= 9223372036854775808
		return value

	def encode_bool(self, value):
		if value == True or str(value).lower() in ('true', 'yes'):
			return 'true'
		else:
			return 'false'

	def decode_bool(self, value):
		if isinstance(value, basestring):
			if value.lower() == 'true':
				return True
			else:
				return False
		else:
			return bool(value)

	def encode_float(self, value):
		"""
		See http://tools.ietf.org/html/draft-wood-ldapext-float-00.
		"""
		s = '%e' % value
		l = s.split('e')
		mantissa = l[0].ljust(18, '0')
		exponent = l[1]
		if value == 0.0:
			case = '3'
			exponent = '000'
		elif mantissa[0] != '-' and exponent[0] == '+':
			case = '5'
			exponent = exponent[1:].rjust(3, '0')
		elif mantissa[0] != '-' and exponent[0] == '-':
			case = '4'
			exponent = 999 + int(exponent)
			exponent = '%03d' % exponent
		elif mantissa[0] == '-' and exponent[0] == '-':
			case = '2'
			mantissa = '%f' % (10 + float(mantissa))
			mantissa = mantissa.ljust(18, '0')
			exponent = exponent[1:].rjust(3, '0')
		else:
			case = '1'
			mantissa = '%f' % (10 + float(mantissa))
			mantissa = mantissa.ljust(18, '0')
			exponent = 999 - int(exponent)
			exponent = '%03d' % exponent
		return '%s %s %s' % (case, exponent, mantissa)

	def decode_float(self, value):
		case = value[0]
		exponent = value[2:5]
		mantissa = value[6:]
		if case == '3':
			return 0.0
		elif case == '5':
			pass
		elif case == '4':
			exponent = '%03d' % (int(exponent) - 999)
		elif case == '2':
			mantissa = '%f' % (float(mantissa) - 10)
			exponent = '-' + exponent
		else:
			mantissa = '%f' % (float(mantissa) - 10)
			exponent = '%03d' % abs((int(exponent) - 999))
		return float(mantissa + 'e' + exponent)

	def encode_datetime(self, value):
		if isinstance(value, str) or isinstance(value, unicode):
			return value
		if isinstance(value, datetime):
			return value.strftime(ISO8601)
		else:
			return value.isoformat()

	def decode_datetime(self, value):
		"""Handles both Dates and DateTime objects"""
		if value is None:
			return value
		try:
			if 'T' in value:
				if '.' in value:
					# Handle true 'isoformat()' dates, which may have a microsecond on at the end of them
					return datetime.strptime(value.split('.')[0], ISO8601)
				else:
					return datetime.strptime(value, ISO8601)
			else:
				value = value.split('-')
				return date(int(value[0]), int(value[1]), int(value[2]))
		except Exception, e:
			return None

	def encode_date(self, value):
		return value

	def decode_date(self, value):
		if isinstance(value, basestring):
			try:
				value = value.split('-')
				return date(int(value[0]), int(value[1]), int(value[2]))
			except:
				log.exception('Could not decode date: %s' % value)
				return None

	def encode_time(self, value):
		return self.encode_date(value)

	def decode_time(self, value):
		""" converts strings in the form of HH:MM:SS.mmmmmm
			(created by datetime.time.isoformat()) to
			datetime.time objects.

			Timzone-aware strings ('HH:MM:SS.mmmmmm+HH:MM') won't
			be handled right now and will raise TimeDecodeError.
		"""
		if '-' in value or '+' in value:
			# TODO: Handle tzinfo
			raise TimeDecodeError("Can't handle timezone aware objects: %r" % value)
		tmp = value.split('.')
		arg = map(int, tmp[0].split(':'))
		if len(tmp) == 2:
			arg.append(int(tmp[1]))
		return time(*arg)

	def encode_reference(self, value):
		return value

	def decode_reference(self, value):
		if not value or value == 'None':
			return None
		return value

	def encode_blob(self, value):
		return value

	def decode_blob(self, value):
		if isinstance(value, basestring):
			return Blob(value)
		return value

	def encode_string(self, value):
		"""Convert ASCII, Latin-1 or UTF-8 to pure Unicode"""
		if not isinstance(value, str): return value
		try:
			return unicode(value, 'utf-8')
		except: # really, this should throw an exception.
				# in the interest of not breaking current
				# systems, however:
			arr = []
			for ch in value:
				arr.append(unichr(ord(ch)))
			return u''.join(arr)

	def decode_string(self, value):
		"""Decoding a string is really nothing, just
		return the value as-is"""
		return value

class StringConverter(Converter):
	"""Converts all values to Strings"""

	def encode_blob(self, value):
		if not value or isinstance(value, basestring):
			return value
		return str(value)

	def encode_reference(self, value):
		if value in (None, 'None', '', ' '):
			return None
		if isinstance(value, str) or isinstance(value, unicode):
			return value
		else:
			return value.id

	def encode_date(self, value):
		if isinstance(value, str) or isinstance(value, unicode):
			return value
		return value.isoformat()

