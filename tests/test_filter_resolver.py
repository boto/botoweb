
from boto_web.appserver.filter_resolver import FilterResolver
from pkg_resources import resource_string
import boto

class TestFilterResolver(object):
    """
    Test the FilterResolver
    """

    def setup_class(cls):
        cls.filter_resolver = FilterResolver()
        cls.s3 = boto.connect_s3()
        cls.bucket = cls.s3.get_all_buckets()[0]


    def test_resolve_resource(self):
        """
        Try to resolve a python://
        """
        uri = "python://example/filters/blog.xsl"
        filter = self.filter_resolver.resolve(uri)
        filter_str = resource_string("example", "filters/blog.xsl")
        assert filter.read() == filter_str

    def test_resolve_s3(self):
        """
        Try to resolve an s3://
        """
        key = self.bucket.new_key("TestFoo.xsl")
        key.set_contents_from_string("<xml>TestFoo</xml>")
        uri = "s3://%s/%s" % (key.bucket.name, key.name)
        try:
            filter = self.filter_resolver.resolve(uri)
            assert key.read() == filter.read()
        finally:
            key.delete()
