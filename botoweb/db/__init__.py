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
	return unicodedata.normalize('NFKD', unicode(s)).encode('ASCII', 'ignore').upper()
