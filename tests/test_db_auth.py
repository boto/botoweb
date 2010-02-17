# NOTE: these tests need to be executed from the root
# directory of an svn checkout using py.test

import boto
import time
from botoweb.resources.user import User
from botoweb.resources.authorization import Authorization

class TestDBAuth(object):
	"""Test DB-based authorization """

	def setup_class(cls):
		"""Setup this class"""
		cls.authorizations = []
		cls.user = User()
		cls.user.name = "Test User"
		cls.user.auth_groups = ['test_auth_group']

	def teardown_class(cls):
		"""Cleanup"""
		cls.user.delete()
		for auth in cls.authorizations:
			try:
				auth.delete()
			except:
				pass

	def test_no_auth(self):
		"""Test someone that shouldn't have any authorization to anything"""
		assert(self.user.has_auth() == False)

	def test_all_auth(self):
		"""Test someone that should have every authorization to everything"""
		auth = Authorization()
		auth.auth_group = "test_auth_group"
		auth.put()
		time.sleep(5)
		self.authorizations.append(auth)
		self.user.load_auths()
		assert(self.user.has_auth())
		assert(self.user.has_auth("GET"))
		assert(self.user.has_auth("POST"))
		assert(self.user.has_auth("PUT"))
		assert(self.user.has_auth("DELETE"))
		assert(self.user.has_auth("GET", "Foo"))
		assert(self.user.has_auth("GET", "Foo", "bar"))
		assert(self.user.has_auth("GET", "*", "bar"))
		auth.delete()

	def test_get_only_auth(self):
		"""Test someone that has only GET permissions on all objects"""
		auth = Authorization()
		auth.auth_group = "test_auth_group"
		auth.method = "GET"
		auth.put()
		time.sleep(5)
		self.authorizations.append(auth)
		self.user.load_auths()
		assert(self.user.has_auth("GET"))
		assert(self.user.has_auth("POST") == False)
		assert(self.user.has_auth("PUT") == False)
		assert(self.user.has_auth("DELETE") == False)
		assert(self.user.has_auth("DELETE", "Foo") == False)
		assert(self.user.has_auth("DELETE", "Foo", "bar") == False)
		assert(self.user.has_auth("DELETE", "*", "bar") == False)
		assert(self.user.has_auth("GET", "Foo"))
		assert(self.user.has_auth("GET", "Foo", "bar"))
		assert(self.user.has_auth("GET", "*", "bar"))
		auth.delete()

	def test_get_only_single_object_auth(self):
		"""Test someone that has only all permissions on a specific object"""
		auth = Authorization()
		auth.auth_group = "test_auth_group"
		auth.method = "GET"
		auth.obj_name = "Foo"
		auth.put()
		time.sleep(5)
		self.authorizations.append(auth)
		self.user.load_auths()
		assert(self.user.has_auth("GET") == False)
		assert(self.user.has_auth("GET", "Bar") == False)
		assert(self.user.has_auth("GET", "Bar", "bizzle") == False)
		assert(self.user.has_auth("GET", "Foo"))
		assert(self.user.has_auth("GET", "Foo", "bar"))
		auth.delete()

	def test_get_only_single_attr_auth(self):
		"""Test someone that has only all permissions on a specific object and single attribute"""
		auth = Authorization()
		auth.auth_group = "test_auth_group"
		auth.method = "GET"
		auth.obj_name = "Foo"
		auth.prop_name = "bar"
		auth.put()
		time.sleep(5)
		self.authorizations.append(auth)
		self.user.load_auths()
		assert(self.user.has_auth("GET") == False)
		assert(self.user.has_auth("GET", "Bar") == False)
		assert(self.user.has_auth("GET", "Bar", "bar") == False)
		assert(self.user.has_auth("GET", "*", "bar") == False)
		assert(self.user.has_auth("GET", "Foo") == False)
		assert(self.user.has_auth("GET", "Foo", "bar"))
		auth.delete()
