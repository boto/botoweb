
from botoweb.appserver.filter_resolver import S3FilterResolver, PythonFilterResolver
from pkg_resources import resource_string
import boto

class TestFilterResolver(object):
	"""Test the FilterResolver"""

	def setup_class(cls):
		cls.s3_filter_resolver = S3FilterResolver()
		cls.python_filter_resolver = PythonFilterResolver()
		cls.s3 = boto.connect_s3()
		cls.bucket = cls.s3.get_all_buckets()[0]


	def test_resolve_resource(self):
		"""Try to resolve a python://"""
		uri = "python://botoweb/filters/base.xsl"
		filter = self.python_filter_resolver.fetch_url(uri)
		filter_str = resource_string("botoweb", "filters/base.xsl")
		assert filter == filter_str

	def test_resolve_s3(self):
		"""Try to resolve an s3://"""
		key = self.bucket.new_key("TestFoo.xsl")
		key.set_contents_from_string("<xml>TestFoo</xml>")
		uri = "s3://%s/%s" % (key.bucket.name, key.name)
		try:
			filter = self.s3_filter_resolver.fetch_url(uri)
			assert key.get_contents_as_string() == filter
		finally:
			key.delete()
