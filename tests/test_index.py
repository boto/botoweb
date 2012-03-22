#
# Author: Chris Moyer http://coredumped.org/
#
from botoweb.db.index import Index

class TestIndex(object):
	"""Test our index system"""
	
	@classmethod
	def setup_class(cls):
		cls.index = Index("test-index")

	@classmethod
	def teardown_class(cls):
		cls.index.delete()

	def test_simple_index(self):
		"""Test a simple index operation"""
		self.index.add("Little Food Garden", "1")
		self.index.add("Large Food Kitchen", "2")

		# Search just for one word
		items = [ item['id'] for item in self.index.search("food", True)]
		assert("1" in items)
		assert("2" in items)

		# Search for multiple words
		items = [item['id'] for item in self.index.search("food garden", True)]
		assert(items == ["1"])
		items = [item['id'] for item in self.index.search("little food", True)]
		assert(items == ["1"])
		items = [item['id'] for item in self.index.search("little food garden", True)]
		assert(items == ["1"])

	def test_split_word_index(self):
		"""A more complicated search, we make sure that FoodStuffs.com 
		gets matched with a search for Food Stuffs"""
		self.index.add("FoodStuffs.com", "fs.com")
		items = [item['id'] for item in self.index.search("Food Stuffs", True)]
		assert("fs.com" in items)
		items = [item['id'] for item in self.index.search("FoodStuffs.com", True)]
		assert("fs.com" in items)

	def test_tuples(self):
		"""Tests the tuple generator"""
		name = "Little Food Garden"
		tuples = self.index.get_tuples(name, stem=False)
		for name in name.split(" "):
			assert(name.upper() in tuples)

		# Also make sure the combinations exist
		assert("LITTLE FOOD" in tuples)
		assert("FOOD GARDEN" in tuples)
