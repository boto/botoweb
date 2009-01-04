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
import httplib

import boto
from boto_web.request import Request
from boto_web.response import Response
from boto_web.resources.user import User
from boto_web.resources.filter_rule import FilterRule
from boto_web.exceptions import *

import traceback
import logging
log = logging.getLogger("boto_web.url_mapper")

from Ft.Xml.Xslt import Processor
from Ft.Xml import InputSource

class URLMapper(object):
    """
    Filter URL Mapper
    """


    def __init__(self, proxy_host, proxy_port):
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
        variables = {}
        user = self.get_user(req)
        if not user:
            raise Unauthorized()
        response = Response()
        headers = {}
        for key in req.headers:
            if not key.lower() in ["content-length", "authorization"]:
                headers[key] = req.headers[key]

        conn = httplib.HTTPConnection(self.proxy_host, self.proxy_port)

        variables[u'user_id'] = user.id
        variables[u'user_name'] = user.username

        filter = self.get_filter(req.path,req.method, user)

        stylesheet = None
        if filter[0]:
            body = filter[0].run(InputSource.DefaultFactory.fromString(req.body, None), topLevelParams=variables)
        else:
            body = req.body

        conn.request(req.method, req.path_qs, body, headers)
        resp = conn.getresponse()


        resp_body = resp.read()
        response.set_status(resp.status)
        if resp.status == 200:
            response.content_type = "text/xml"

            if filter[1]:
                response.write(filter[1].run(InputSource.DefaultFactory.fromString(resp_body, None), topLevelParams=variables))
            else:
                response.write(resp_body)
        else:
            response.write(resp_body)
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
                try:
                    user = User.find(username=username).next()
                except:
                    user = None
                if user and user.password == password:
                    return user
        return None

    def get_filter(self, path, method, user):
        """
        Get the filter for this URL and
        User

        @return: [input_filter, output_filter], either filter may also be None
        @rtype: list
        """
        path = path.split('/')[1]
        log.info("Get Stylesheet: %s %s" % (path, user))
        styledoc = None
        query = FilterRule.find()
        #query.filter("user =", [user, None])
        query.filter("path =", [path, "*"])
        query.filter("method =", [method, "*"])
        try:
            filter = query.next()
        except:
            return [None, None]

        return [self._build_proc(filter.input_filter), self._build_proc(filter.output_filter)]

    def _build_proc(self, transform):
        proc = None
        if transform and str(transform):
            proc = Processor.Processor()
            style = InputSource.DefaultFactory.fromString(str(transform), None)
            proc.appendStylesheet(style)
        return proc
