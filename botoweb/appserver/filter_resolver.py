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
from lxml import etree
from pkg_resources import resource_string
import re
import boto

class S3FilterResolver (etree.Resolver):
	"""Resolves the follwing URIs
	s3://bucket_name/key_name
	This resolver also caches files locally once it has been initialized
	"""
	prefix = "s3"

	def __init__(self):
		self.files = {}
		etree.Resolver.__init__(self)

	def resolve(self, url, pubid, context):
		ret = self.fetch_url(url)
		if ret:
			return self.resolve_string(ret, context)

	def fetch_url(self, url):
		if not self.files.has_key(url):
			match = re.match("^s3:\/\/([^\/]*)\/(.*)$", url)
			if match:
				s3 = boto.connect_s3()
				b = s3.get_bucket(match.group(1))
				k = b.get_key(match.group(2))
				if k:
					self.files[url] = k.get_contents_as_string()
		if self.files.has_key(url):
			return self.files[url]

class PythonFilterResolver(etree.Resolver):
	"""Resolves the follwing URIs
	python://module.name/file.name
	"""
	prefix = "python"

	def resolve(self, url, pubid, context):
		ret = self.fetch_url(url)
		if ret:
			return self.resolve_string(ret, context)

	def fetch_url(self, url):
		match = re.match("^python:\/\/([^\/]*)\/(.*)$", url)
		if match:
			module = match.group(1)
			name = match.group(2)
			return resource_string(module, name)
