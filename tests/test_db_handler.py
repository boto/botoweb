# NOTE: these tests need to be executed from the root
# directory of an svn checkout using py.test

import boto
import time
from botoweb.appserver.handlers.db import DBHandler
from botoweb.db.coremodel import Model
from botoweb.db.property import StringProperty
from botoweb.environment import Environment
from botoweb.xmlize import ProxyObject

class SimpleObject(Model):
	"""Simple test object"""
	name = StringProperty()


class TestDBHandler(object):
	"""Test the DBHandler"""

	def setup_class(cls):
		"""Setup this class"""
		import sys
		sys.path.append(".")
		sys.path.append("../")
		env = Environment("example")
		cls.handler = DBHandler(env, config={"db_class": "%s.SimpleObject" % SimpleObject.__module__})

	def teardown_class(cls):
		"""Cleanup"""
		for obj in SimpleObject.all():
			obj.delete()
		del(cls.handler)

	def test_create(self):
		"""Test creating something"""
		proxy_obj = ProxyObject()
		proxy_obj.__name__ = "SimpleObject"
		proxy_obj.name = "TestObject"
		obj = self.handler.create(proxy_obj, None, None)
		assert(obj.name == "TestObject")
		assert(obj.__class__ == SimpleObject)
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
		obj2 = self.handler.read(obj.id, None)
		assert(obj2.name == obj.name)
		assert(obj2.id == obj.id)
		obj2.delete()

	def test_update(self):
		obj = SimpleObject()
		obj.name = "TestObject"
		obj.put()
		time.sleep(1)
		obj2 = self.handler.update(obj, {"name": "FooObject"}, None, None)
		time.sleep(1)
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
		obj2 = self.handler.delete(obj, None)
		assert(obj2.id == obj.id)
		time.sleep(2)
		obj3 = SimpleObject.get_by_ids(obj.id)
		assert(obj3 == None)
