#
# Author: Chris Moyer http://coredumped.org/
#
# botoweb DB module overrides, this provides one simple
# location for users to pull in the DB modules from
# and adds a few new features on top of botoweb.db

def index_string(s):
	"""Generates an index of this string,
	stripping off all accents and making everything upper case"""
	import unicodedata
	import re
	if isinstance(s, list):
		s = " ".join(s)
	if not isinstance(s, unicode):
		s = str(s).decode('utf-8', 'replace')
	s = re.sub(r'&#(x?)([^;]+);', lambda match: unichr(int(match.group(2), 16 if match.group(1) else 10)),s)
	return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').upper()
