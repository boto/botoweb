import webob
from boto_web import status

class Response(webob.Response):
    """
    Simple Adapter class for a WSGI response object
    to support GAE
    """

    def __init__(self, body="", **params):
        webob.Response.__init__(self, body=body, **params)

    def set_status(self, code, message=None):
        """
        Set the HTTP status of our response

        @param code: HTTP Status Code, should be one of the (appengine.webapp.status)s
        @type code: integer from status.HTTP_*
        """
        if not message:
            message = status.message[code]
        self.status = "%s %s" % (code, message)

    def clear(self):
        self.body = ""

    def wsgi_write(self, environ, start_response):
        return self.__call__(environ, start_response)


