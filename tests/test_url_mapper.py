# NOTE: these tests need to be executed from the root
# directory of an svn checkout using py.test

from boto_web.appserver.url_mapper import URLMapper
from boto_web.appserver.handlers import RequestHandler
from boto_web.request import Request
from boto_web.response import Response
from boto_web.environment import Environment


class XMLString(object):
    """
    String that can be turned into xml
    """
    def __init__(self, val):
        self.val = val

    def to_xml(self):
        return "<string>%s</string>" % val

class SimpleHandler(RequestHandler):
    """
    Simple test handler
    """

    def get(self, req, id=None):
        if id == None:
            return XMLString("GET")
        else:
            return XMLString("GET: %s" % id)

    def post(self, req, id=None):
        if id == None:
            return XMLString("POST")
        else:
            return XMLString("POST: %s" % id)


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
        cls.env.config['handlers'] = [ {"url": "/foo", "handler": "%s.SimpleHandler" % cls.__module__} ]

    def teardown_class(cls):
        """
        Cleanup
        """
        del(cls.url_mapper)
        del(cls.env)


    def test_path_no_object(self):
        (handler, obj_id) = self.url_mapper.parse_path("/foo")
        assert(handler.__class__.__name__ == "SimpleHandler")
        assert(obj_id == None)

    def test_path_with_object_id(self):
        my_obj_id = "2934823-423423432-asdf34AA-5498574298.avi"
        (handler, obj_id) = self.url_mapper.parse_path("/foo/%s" % my_obj_id)
        assert(handler.__class__.__name__ == "SimpleHandler")
        assert(obj_id == my_obj_id)

    def test_path_with_trailing_slash(self):
        (handler, obj_id) = self.url_mapper.parse_path("/foo/")
        assert(handler.__class__.__name__ == "SimpleHandler")
        assert(obj_id == None)

    def test_path_with_object_id_with_slash(self):
        my_obj_id = "bucket_name/key_name/foo.avi"
        (handler, obj_id) = self.url_mapper.parse_path("/foo/%s" % my_obj_id)
        assert(handler.__class__.__name__ == "SimpleHandler")
        assert(obj_id == my_obj_id)


    def test_handle_get_noargs(self):
        """
        Test handing a GET request
        """
        r = Request.blank("/foo")
        r.method = "GET"
        content = self.url_mapper.handle(r, Response())
        print content
        assert(content.val == "GET")

    def test_handle_get_with_args(self):
        """
        Test handing a GET request
        """
        r = Request.blank("/foo?bar=biz&diz=dazzle")
        r.method = "GET"
        content = self.url_mapper.handle(r, Response())
        assert(content.val == "GET")

    def test_handle_get_with_args_and_id(self):
        """
        Test handing a GET request
        """
        r = Request.blank("/foo/my_object_id?bar=biz&diz=dazzle")
        r.method = "GET"
        content = self.url_mapper.handle(r, Response())
        assert(content.val == "GET: my_object_id")

    def test_handle_post_with_args_and_id(self):
        r = Request.blank("/foo/my_object_id?bar=biz&diz=dazzle")
        r.method = "POST"
        content = self.url_mapper.handle(r, Response())
        assert(content.val == "POST: my_object_id")
