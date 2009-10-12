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

import datetime
import pytz
from botoweb import xmlize

class ObjectTest(object):
	"""Test Object to dump/load from XML"""
	pass

TEST_XML = """<?xml version="1.0" ?>
<Test>
	<test_simple>Simple String</test_simple>
	<test_string type="string">Another String</test_string>
	<test_datetime type="dateTime">2009-09-09T09:09:09-05</test_datetime>
	<test_multi type="string">Value A</test_multi>
	<test_multi type="string">Value B</test_multi>
	<test_multi type="string">Value C</test_multi>
</Test>
"""

class TestXMLize(object):
	"""Test the xmlize package serializing and de-serializing XML"""

	def test_str(self):
		"""Test encoding a string"""
		xmlize.register(ObjectTest)
		obj = ObjectTest()
		obj.foo = "bar"
		obj.name = "Bizzle"
		obj.id = "12345"
		sr = xmlize.dumps(obj)
		obj2 = xmlize.loads(sr)


		assert obj2.foo == obj.foo
		assert obj2.name == obj.name
		assert obj2.__id__ == obj.id

	def test_datetime(self):
		"""Try encoding and decoding a datetime"""
		xmlize.register(ObjectTest)
		obj = ObjectTest()
		obj.d = datetime.datetime(year=2009, month=9, day=9, hour=9, minute=9, second=9, tzinfo=pytz.utc)
		sr = xmlize.dumps(obj)
		obj2 = xmlize.loads(sr)

		print obj2.d.tzinfo
		assert obj2.d == obj.d


	def test_loads(self):
		"""Test loading a string that we know should work"""
		obj = xmlize.loads(TEST_XML)
		assert obj.test_simple == "Simple String"
		assert obj.test_string == "Another String"
		assert obj.test_datetime.year == 2009
		assert obj.test_datetime.month == 9
		assert obj.test_datetime.day == 9
		assert obj.test_datetime.hour == 9
		assert obj.test_datetime.minute == 9
		assert obj.test_datetime.second == 9
		assert obj.test_datetime.tzinfo.utcoffset(obj.test_datetime) == datetime.timedelta(hours = -5)
