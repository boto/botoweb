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

# Description: Simple Encoders, dumps everything to 
# standard Python Data Types:
# - str
# - bool
# - list
# - dict
# - int

from botoweb.fixed_datetime import datetime
from datetime import datetime as datetime_type
from datetime import date

type_map = {}

def encode(value):
	"""Normalize this value to a standard python data type"""
	if value == None:
		return None
	prop_type = type(value)
	if prop_type in type_map:
		return type_map[prop_type](value)
	if isinstance(value, object):
		return encode_object(value)
	return encode_default(value)

def encode_default(value):
	"""Default encoding, just turn it into a string"""
	try:
		return str(value).replace("\r", "")
	except:
		return unicode(value).encode("ascii", "ignore").replace("\r", "")

def encode_str(value):
	return encode_default(value)

def encode_int(value):
	"""Integer is an acceptable type, so we just return it"""
	return value

def encode_bool(value):
	"""Bools are allowed types"""
	return value

def encode_list(value):
	"""Encode a list by encoding each property individually"""
	ret = []
	for val in value:
		ret.append(encode(val))
	return ret

def encode_dict(value):
	"""Dictionaries, like lists, are acceptable types, so we just
	encode each individual value"""
	ret = {}
	for k in value:
		ret[k] = encode(value[k])
	return ret

def encode_datetime(value):
	"""Encode a DATETIME into standard ISO 8601 Internet Format"""
	return value.isoformat().split(".")[0] + "Z"

def encode_object(value):
	"""Encode a generic object (must have an "id" attribute)"""
	from boto.sdb.db.query import Query
	from boto.sdb.db.blob import Blob
	from boto.s3.key import Key
	if isinstance(value, Query):
		return encode_query(value)
	elif isinstance(value, Blob):
		return encode_blob(value)
	elif isinstance(value, Key):
		return encode_key(value)
	elif hasattr(value, "id"):
		# If it has an ID, we return 
		# a dictionary with the class name
		# and the ID
		return {"__type__": value.__class__.__name__, "__id__": encode(value.id)}
	else:
		# As a generic fallback, we simply return the
		# stringified version of this object
		return encode_str(value)

def encode_query(value):
	"""Encode a query"""
	# TODO: Encode this as some sort of reference
	return None

def encode_blob(value):
	"""Encode a blob, this is sent as a reference"""
	# TODO: Encode this as some sort of reference
	return None

def encode_key(value):
	"""Encode an S3Key, this is the same as a blob for our
	purposes"""
	return encode_blob(value)


# Map out all of our encoders to their types
type_map = {
	str: encode_str,
	int: encode_int,
	unicode: encode_str,
	list: encode_list,
	dict: encode_dict,
	datetime: encode_datetime,
	datetime_type: encode_datetime,
	date: encode_datetime,
	object: encode_object,
	bool: encode_bool,
}

