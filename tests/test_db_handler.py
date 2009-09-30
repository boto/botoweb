# NOTE: these tests need to be executed from the root
# directory of an svn checkout using py.test

import boto
import time
from botoweb.appserver.handlers.db import DBHandler
from boto.sdb.db.model import Model
from boto.sdb.db.property import StringProperty

class SimpleObject(Model):
	"""
	Simple test object
	"""
	name = StringProperty()


class TestDBHandler:
	"""
	Test the DBHandler
	"""
	def setup_class(cls):
		"""
		Setup this class
		"""
		cls.handler = DBHandler(config={"db_class": "%s.SimpleObject" % SimpleObject.__module__})

	def teardown_class(cls):
		"""
		Cleanup
		"""
		for obj in SimpleObject.all():
			obj.delete()
		del(cls.handler)

	def test_create(self):
		"""
		Test creating something
		"""
		obj = self.handler.create(params={"name": "TestObject"})
		assert(obj.name == "TestObject")
		time.sleep(1)
		obj2 = SimpleObject.get_by_ids(obj.id)
		assert(obj2)
		assert(obj2.name == "TestObject")
		obj.delete()

	def test_read(self):
		obj = SimpleObject()
		obj.name = "TestObject"
		obj.put()
		time.sleep(1)
		obj2 = self.handler.read(id=obj.id)
		assert(obj2.name == obj.name)
		assert(obj2.id == obj.id)
		obj2.delete()

	def test_update(self):
		obj = SimpleObject()
		obj.name = "TestObject"
		obj.put()
		time.sleep(1)
		obj2 = self.handler.update(obj=obj, params={"name": "FooObject"})
		assert(obj2.id == obj.id)
		assert(obj2.name == "FooObject")
		obj = SimpleObject.get_by_ids(obj.id)
		assert(obj.name == "FooObject")
		obj.delete()

	def test_delete(self):
		obj = SimpleObject()
		obj.name="DelObject"
		obj.put()
		time.sleep(1)
		obj2 = self.handler.delete(id=obj.id)
		assert(obj2.id == obj.id)
		time.sleep(2)
		obj3 = SimpleObject.get_by_ids(obj.id)
		assert(obj3 == None)
