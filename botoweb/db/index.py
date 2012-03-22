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
# Description: DynamoDB based "index" system
# This does a lot of work with stemming and other
# simple operations to allow us to search for several
# different variations of a string in order to 
# get out a value. Most commonly this would be used
# to index an object (by reference)
import time

class Index(object):
	"""Index item, which actually more or less represents a
	Table within DynamoDB.
	Usage:
	>>> index = Index('my-index')
	>>> index.add("the foo object", "1234")
	>>> # Search for a specific item
	>>> results = index.search("Foo")
	>>> for result in results:
	>>> 	print result
	"""

	def __init__(self, name):
		"""Initialize an index"""
		self.name = name
		self._table = None
		self._stemmer = None

	@property
	def table(self):
		if not self._table and self.name is not None:
			import boto
			conn = boto.connect_dynamodb()
			try:
				table = conn.lookup(self.name)
			except:
				table = None
			if not table:
				schema = conn.create_schema(
					"name", "str",
					"id", "str"
				)
				table = conn.create_table(self.name, schema, 5, 5)
				while table.status != "ACTIVE":
					table.refresh()
					time.sleep(5)
			self._table = table
		return self._table

	@property
	def stemmer(self):
		"""Allow the use of the Stemmer module"""
		if self._stemmer is None:
			try:
				import Stemmer
			except ImportError:
				self._stemmer = False
				return self._stemmer
			self._stemmer = Stemmer.Stemmer('english')
		return self._stemmer

	def stem(self, name):
		"""Stem the name into its root form, if the Stemmer module is installed"""
		if self.stemmer is False:
			return name
		return self.stemmer.stemWord(name)

	def get_tuples(self, name, stem=True):
		"""Split the given name into it's mutliple values to be indexed"""
		name = self.clean(name)
		tuples = []
		words = name.split(" ")
		# Loop over each value from the
		# maximum length down to one, each
		# time grabbing all the tuples of that length
		# from the list
		max_len = len(words) + 1
		cur_size = max_len + 1
		while cur_size > 0:
			cursor = 0
			while (cursor + cur_size) < max_len:
				tuples.append(words[cursor:cursor + cur_size])
				cursor += 1
			cur_size -= 1

		names = []
		for tuple in tuples:
			names.append(" ".join(tuple).upper())
			if stem:
				names.append(" ".join([self.stem(n) for n in tuple]).upper())

		return set(names)


	def add(self, name, value, stem=True, **extra):
		"""Index a specific name to a given value (with optional extra attributes)
		:param name: The name to index
		:type name: str
		:param value: The value to return for any matches
		:type value: str
		:param stem: Should the name be stemmed? (Default True), if set to False,
			the name will only be split into tuples, not stemmed
		:type stem: bool
		:param **extra: optional extra attributes to store in the resource record
		"""
		names = self.get_tuples(self.clean(name), stem)
		for name in names:
			item = self.table.new_item(name, value, attrs=extra)
			item['ts'] = time.time()
			item.save(return_values="ALL_NEW")

	def delete(self):
		"""Delete this index table"""
		self.table.delete()

	def search(self, name, consistent_read=False):
		"""Search for the given name, returning the matching value(s) as a generator"""
		name = self.clean(name)
		search_vals = []
		for sv in [
				name.upper(),
				" ".join([self.stem(n) for n in name.split(" ")]).upper(),
				"".join([self.stem(n) for n in name.split(" ")]).upper(),
				name.replace(" ", "").upper()
			]:
			if not sv in search_vals:
				search_vals.append(sv)

		results = False
		for name in search_vals:
			for item in self.table.query(name, consistent_read=consistent_read):
				results = True
				yield item
			if results:
				break

	def clean(self, name):
		"""Clean input, which may be in UTF-8 or Unicode"""
		import re
		if isinstance(name, unicode):
			name = name.encode("utf-8", "ignore")
		name = name.replace(".", " ")
		name = re.sub("[^a-zA-Z0-9\ \-]", "", name)
		return name
