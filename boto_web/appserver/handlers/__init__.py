# Author: Chris Moyer
import os
import os.path
import re
import urlparse
import StringIO
import traceback

import cgi
import webob
import wsgiref
import wsgiref.headers

import boto
import boto_web
from boto_web.exceptions import *
from boto.utils import find_class
from boto_web import status
import time
import mimetypes

import logging
log = logging.getLogger("boto_web.appserver.handlers")

class Request(webob.Request):
    """
    We like to add in session support here. Due to how the system must be distributable,
    all session information must be stored in the database.
    """
    file_extension = "html"

    def __init__(self, environ):
        charset = webob.NoDefault
        if environ.get('CONTENT_TYPE', '').find('charset') == -1:
            charset = 'utf-8'

        webob.Request.__init__(self, environ, charset=charset,
            unicode_errors= 'ignore', decode_param_names=True)

    def get(self, argument_name, default_value='', allow_multiple=False):
        param_value = self.get_all(argument_name)
        if allow_multiple:
            return param_value
        else:
            if len(param_value) > 0:
                return param_value[0]
            else:
                return default_value

    def get_all(self, argument_name):
        if self.charset:
            argument_name = argument_name.encode(self.charset)

        try:
            param_value = self.params.getall(argument_name)
        except KeyError:
            return default_value

        for i in range(len(param_value)):
            if isinstance(param_value[i], cgi.FieldStorage):
                param_value[i] = param_value[i].value

        return param_value

    def formDict(self):
        vals = {}
        if self.GET:
            for k in self.GET:
                vals[k] = self.GET[k]
        if self.POST:
            for k in self.POST:
                vals[k] = self.POST[k]
        return vals


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


class RequestHandler(object):
    """
    Simple Request Handler,
    The request handler is created only 
    once so we can handle caching.
    """

    def __init__(self, config):
        """
        Set up the global config for this
        handler
        """
        self.config = config

    def redirect(self, url, perminate=False):
        """
        HTTP Redirect
        @param perminate: Send a 301 (Perminate Redirect) instead of a 303 (Temporary Redirect) Default False
        @type perminate: boolean
        """
        self.response.clear()
        if perminate:
            self.response.set_status(301)
        else:
            self.response.set_status(303)
        self.response.headers['Location'] = str(url)

    def get(self, request, id=None):
        self.any(request, id)

    def post(self, request, id=None):
        self.any(request, id)
    
    def head(self, request, id=None):
        self.any(request, id)

    def options(self, request, id=None):
        self.any(request, id)

    def put(self, request, id=None):
        self.any(request, id)

    def delete(self, request, id=None):
        self.any(request, id)

    def trace(self, request, id=None):
        self.any(request, id)

    def any(self, request, id=None):
        """
        Default handler for any request not specifically defined
        """
        raise MethodNotAllowed()
