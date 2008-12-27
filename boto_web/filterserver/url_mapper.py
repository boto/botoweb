# Copyright (c) 2008 Chris Moyer http://coredumped.org
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
import libxml2
import libxslt

import httplib

import boto
from boto_web.request import Request
from boto_web.response import Response
from boto_web.resources.user import User
from boto_web.exceptions import *

import traceback
import logging
log = logging.getLogger("boto_web.url_mapper")

class URLMapper(object):
    """
    Filter URL Mapper
    """


    def __init__(self, proxy_host, proxy_port, bucket):
        self.bucket = bucket
        self.filters = {}
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    def __call__(self, environ, start_response):
        """
        Map to the correct filters
        """
        try:
            req = Request(environ)
            response = self.handle(req)
        except HTTPRedirect, e:
            response = Response()
            response.set_status(e.code)
            response.headers['Location'] = str(url)
            content = e
        except Unauthorized, e:
            response = Response()
            response.set_status(e.code)
            response.headers.add("WWW-Authenticate", 'Basic realm="%s"' % boto.config.get("boto_web", "application", "Boto Web"))
        except HTTPException, e:
            response = Response()
            response.set_status(e.code)
            response.write(e.message)
        except Exception, e:
            response = Response()
            content = InternalServerError(message=e.message)
            response.set_status(content.code)
            log.critical(traceback.format_exc())
        return response.wsgi_write(environ, start_response)

    def handle(self, req):
        user = self.get_user(req)
        if not user:
            raise Unauthorized()
        response = Response()
        conn = httplib.HTTPConnection(self.proxy_host, self.proxy_port)
        conn.request(req.method, req.path)
        resp = conn.getresponse()

        response.write(resp.read())
        response.set_status(resp.status)
        response.content_type = resp.getheader('Content-type', 'text/html')

        return response


    def get_user(self, req):
        """
        Get the user from this request object
        @return: User object, or None
        @rtype: User or None
        """
        auth_header =  req.environ.get("HTTP_AUTHORIZATION")
        if auth_header:
            auth_type, encoded_info = auth_header.split(None, 1)
            if auth_type.lower() == "basic":
                unencoded_info = encoded_info.decode('base64')
                username, password = unencoded_info.split(':', 1)
                user = User.find(username=username).next()
                if user and user.password == password:
                    return user
        return None

    def filter(self, stylesheet, input):
        """
        Do the actual filtering
        """
        styledoc = libxml2.parseFile(stylesheet)
        style = libxslt.parseStylesheetDoc(styledoc)
        doc = libxml2.parseFile(input)
        result = style.applyStylesheet(doc, None)
        style.saveResultToFilename("foo", result, 0)
        style.freeStylesheet()
        doc.freeDoc()
        result.freeDoc()

