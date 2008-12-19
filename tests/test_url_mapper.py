# NOTE: these tests need to be executed from the root
# directory of an svn checkout using py.test

from boto_web.appserver.url_mapper import URLMapper
from boto_web.appserver.handlers import RequestHandler
from boto_web.environment import Environment

class SimpleHandler(RequestHandler):
    """
    Simple test handler
    """

class TestURLMapper:
    """
    Test the URL Mapper for different configs
    """
    def setup_class(cls):
        """
        Setup this class
        """
        cls.env = Environment("example")
        cls.url_mapper = URLMapper(cls.env)

    def teardown_class(cls):
        """
        Cleanup
        """
        del(cls.url_mapper)
        del(cls.env)


    def test_simple_path_no_object(self):
        self.env.config['handlers'] = [ {"url": "/foo", "handler": "%s.SimpleHandler" % self.__module__} ]
        (handler, obj_id) = self.url_mapper.parse_path("/foo")
        assert(handler.__class__.__name__ == "SimpleHandler")
        assert(obj_id == None)

    def test_simple_path_with_object_id(self):
        my_obj_id = "2934823-423423432-asdf34AA-5498574298.avi"
        self.env.config['handlers'] = [ {"url": "/foo", "handler": "%s.SimpleHandler" % self.__module__} ]
        (handler, obj_id) = self.url_mapper.parse_path("/foo/%s" % my_obj_id)
        assert(handler.__class__.__name__ == "SimpleHandler")
        assert(obj_id == my_obj_id)

    def test_simple_path_with_trailing_slash(self):
        self.env.config['handlers'] = [ {"url": "/foo", "handler": "%s.SimpleHandler" % self.__module__} ]
        (handler, obj_id) = self.url_mapper.parse_path("/foo/")
        assert(handler.__class__.__name__ == "SimpleHandler")
        assert(obj_id == None)

    def test_simple_path_with_object_id_with_slash(self):
        my_obj_id = "bucket_name/key_name/foo.avi"
        self.env.config['handlers'] = [ {"url": "/foo", "handler": "%s.SimpleHandler" % self.__module__} ]
        (handler, obj_id) = self.url_mapper.parse_path("/foo/%s" % my_obj_id)
        assert(handler.__class__.__name__ == "SimpleHandler")
        assert(obj_id == my_obj_id)
