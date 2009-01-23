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
from boto_web.exceptions import *

import traceback
import logging
log = logging.getLogger("boto_web.filter_mapper")

from Ft.Xml.Xslt import Processor
from Ft.Xml.InputSource import InputSourceFactory
from boto_web.appserver.filter_resolver import FilterResolver

import re

class FilterMapper(object):
    """
    Filter URL Mapper
    """


    def __init__(self, app, env):
        self.filters = {}
        self.app = app
        self.env = env
        self.resolver = FilterResolver()
        self.factory = InputSourceFactory(resolver=self.resolver)

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
        return response(environ, start_response)

    def handle(self, req):
        variables = {}
        user = self.get_user(req)
        if not user:
            raise Unauthorized()
        headers = {}
        for key in req.headers:
            if not key.lower() in ["content-length", "authorization"]:
                headers[key] = req.headers[key]


        variables[u'user_id'] = user.id
        variables[u'user_name'] = user.username

        filter = self.get_filter(req.path,req.method, user)

        stylesheet = None
        if filter[0] and req.body:
            req.body = filter[0].run(self.factory.fromString(req.body, None), topLevelParams=variables)

        response = req.get_response(self.app)

        if filter[1]:
            response.body = filter[1].run(self.factory.fromString(response.body, None), topLevelParams=variables)

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

        @return: (input_filter, output_filter), either filter may also be None
        @rtype: 2-tuple
        """
        log.info("Get Stylesheet: %s %s" % (path, user))
        styledoc = None
        match = None
        for rule in self.env.config['filters']:
            if rule.has_key("url"):
                if not re.match(rule['url'], path):
                    continue
            if rule.has_key("method"):
                if rule['method'] != method:
                    continue
            if rule.has_key("user"):
                if rule['user'] != user.username:
                    continue
            if rule.has_key("group"):
                if not rule['group'] in user.groups:
                    continue
            match = rule
            break

        input_filter = None
        output_filter = None
        if match:
            if rule['filters'].has_key("input"):
                input_filter = self._build_proc(rule['filters']['input'])
            if rule['filters'].has_key("output"):
                output_filter = self._build_proc(rule['filters']['output'])

        return (input_filter, output_filter)

    def _build_proc(self, uri):
        proc = None
        if uri:
            proc = Processor.Processor()
            style = self.factory.fromUri(uri)
            proc.appendStylesheet(style)
        return proc
