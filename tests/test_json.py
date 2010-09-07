# NOTE: these tests need to be executed from the root
# directory of an svn checkout using py.test

import boto
import time
import sys;sys.path.append("")
import botoweb;botoweb.set_env("example")

from botoweb.appserver.handlers.db import JSONWrapper
from botoweb.db.model import Model
from botoweb.db.property import StringProperty, ReferenceProperty, IntegerProperty
try:
	import json
except ImportError:
	import simplejson as json

class ExampleModel(Model):
	"""Test Model object"""
	# Test all the regular properties
	name = StringProperty(verbose_name="Name")
	parent = ReferenceProperty(Model, verbose_name="Parent Object")
	number = IntegerProperty(verbose_name="Integer Property")

	# This property is advertantly set to "None" by default,
	# and should come out as a null object, not a string
	some_null = StringProperty(verbose_name="Some Null property", default="None")


class TestJSON(object):
	"""Test the JSON Serialization through the DB Handler
	This doesn't actually launch a botoweb instance, instead
	it calls the JSONWrapper directly"""

	def setup_class(cls):
		"""Setup this class"""
		obj = ExampleModel()
		obj.id = "TEST"
		obj.name = "Some Name"
		obj.number = 1

		obj2 = ExampleModel()
		obj2.id = "TEST-PARENT"
		obj2.name = "Second Name"
		obj2.number = 2
		obj2.parent = obj

		obj.parent = obj2


		cls.objs = [obj, obj2]
		cls.wrapper = JSONWrapper(iter([obj, obj2]), user=None)

	def teardown_class(cls):
		"""Cleanup"""
		pass

	def test_fetch(self):
		"""Test Fetching one item"""
		obj = json.loads(self.wrapper.next())
		real_obj = self.objs[0]
		assert(obj['__id__'] == real_obj.id)
		assert(obj['__type__'] == real_obj.__class__.__name__)
		assert(obj['name'] == real_obj.name)
		assert(obj['number'] == real_obj.number)
		assert(obj['some_null'] == None)

		# Check the parent object
		obj2 = obj['parent']
		real_obj2 = self.objs[1]
		assert(obj2['__type__'] == real_obj2.__class__.__name__)
		assert(obj2['__id__'] == real_obj2.id)

	def test_fetch_again(self):
		"""Test fetching again"""
		obj = json.loads(self.wrapper.next())
		real_obj = self.objs[1]
		assert(obj['__id__'] == real_obj.id)

	def test_put_valid(self):
		"""Test putting an object via JSON"""
		pass
