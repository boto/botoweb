#
# Author: Chris Moyer http://coredumped.org/
#
# botoweb DB module overrides, this provides one simple
# location for users to pull in the DB modules from
# and adds a few new features on top of boto.sdb.db

import unicodedata
def index_string(s):
	"""Generates an index of this string,
	stripping off all accents and making everything upper case"""
	return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')).upper()
