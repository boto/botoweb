# Copyright (c) 2010-2013 Chris Moyer http://coredumped.org/
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
from botoweb.db.property import ListProperty
from botoweb.db.model import Model
import time

class SimpleListModel(Model):
	"""Test the List Property"""
	nums = ListProperty(int)
	strs = ListProperty(str)

class TestLists(object):
	"""Test the List property"""
	_test_cls = SimpleListModel

	def setup_class(cls):
		"""Setup this class"""
		cls.objs = []

	def teardown_class(cls):
		"""Remove our objects"""
		for o in cls.objs:
			try:
				o.delete()
			except:
				pass

	def test_list_order(self):
		"""Testing the order of lists"""
		t = self._test_cls()
		t.nums = [5, 4, 1, 3, 2]
		t.strs = ["B", "C", "A", "D", "Foo"]
		t.put()
		self.objs.append(t)
		time.sleep(3)
		t = self._test_cls.get_by_id(t.id)
		assert(t.nums == [5, 4, 1, 3, 2])
		assert(t.strs == ["B", "C", "A", "D", "Foo"])

	def test_query_equals(self):
		"""We noticed a slight problem with querying, since the query uses the same encoder,
		it was asserting that the value was at the same position in the list, not just "in" the list"""
		t = self._test_cls()
		t.strs = ["Bizzle", "Bar"]
		t.put()
		self.objs.append(t)
		time.sleep(3)
		assert(self._test_cls.find(strs="Bizzle").count() == 1)
		assert(self._test_cls.find(strs="Bar").count() == 1)
		assert(self._test_cls.find(strs=["Bar", "Bizzle"]).count() == 1)

	def test_query_not_equals(self):
		"""Test a not equal filter"""
		t = self._test_cls()
		t.strs = ["Fizzle"]
		t.put()
		self.objs.append(t)
		time.sleep(3)
		print self._test_cls.all().filter("strs !=", "Fizzle").get_query()
		for tt in self._test_cls.all().filter("strs !=", "Fizzle"):
			print tt.strs
			assert("Fizzle" not in tt.strs)
