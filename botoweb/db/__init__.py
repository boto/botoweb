#
# Author: Chris Moyer http://coredumped.org/
#
# botoweb DB module overrides, this provides one simple
# location for users to pull in the DB modules from
# and adds a few new features on top of boto.sdb.db

import unicodedata
import re
def index_string(s):
	"""Generates an index of this string,
	stripping off all accents and making everything upper case"""
	if not isinstance(s, unicode):
		s = unicode(s, 'utf-8')
	s = re.sub(r'&#(x?)([^;]+);', lambda match: unichr(int(match.group(2), 16 if match.group(1) else 10)),s)
	return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').upper()
