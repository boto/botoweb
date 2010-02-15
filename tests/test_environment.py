# Tests for the "environment" stuff
# NOTE: these tests need to be executed from the root
# directory of an svn checkout using py.test

from pkg_resources import resource_exists, resource_stream
import yaml
from botoweb.environment import Environment

class TestEnvironment:
	"""
	Test all of the major functionality of the environment
	class. This test assumes that there is a module named "example" installed 
	in the python path and it has a "test.yaml" file in its conf/ directory
	and that there is a conf/env/test.yaml file too
	"""

	def test_module_exists(self):
		"""
		Make sure the example module exists
		and that it has a test.yaml
		"""
		assert resource_exists("example", "conf/test.yaml")

	def test_environment_load_regular(self):
		"""
		Test to make sure the tests file was loaded successfully
		"""
		test_conf = yaml.load(resource_stream("example", "conf/test.yaml"))
		env = Environment("example")
		assert env.config['test'] == test_conf

	def test_environment_load_special(self):
		"""
		Load up a special environment file
		and make sure the overrides apply
		"""
		env = Environment("example", "test")
		assert env.config['test']['test_bool'] == False
		assert env.config['app']['name'] == "Test App"

