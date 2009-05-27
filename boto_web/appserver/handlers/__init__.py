# Author: Chris Moyer
import os
import os.path
import re
import urlparse
import StringIO
import traceback

import cgi
import wsgiref
import wsgiref.headers

import boto
import boto_web

from boto_web.exceptions import *
from boto.utils import find_class
import time
import mimetypes

import logging
log = logging.getLogger("boto_web.appserver.handlers")


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

    def __call__(self, request, response, obj_id):
        """
        Execute this handler based on the request passed in
        """
        if request.method == "GET":
            response = self._get(request, response, obj_id)
        elif request.method == "POST":
            response = self._post(request, response, obj_id)
        elif request.method == "HEAD":
            response = self._head(request, response, obj_id)
        elif request.method == "OPTIONS":
            response = self._options(request, response, obj_id)
        elif request.method == "PUT":
            response = self._put(request, response, obj_id)
        elif request.method == "DELETE":
            response = self._delete(request, response, obj_id)
        elif request.method == "TRACE":
            response = self._trace(request, response, obj_id)
        else:
            raise BadRequest(description="Unknown Method: %s" % request.method)
        return response

    def _get(self, request, response, id=None):
        return self._any(request, response, id)

    def _post(self, request, response, id=None):
        return self._any(request, response, id)
    
    def _head(self, request, response, id=None):
        return self._any(request, response, id)

    def _options(self, request, response, id=None):
        return self._any(request, response, id)

    def _put(self, request, response, id=None):
        return self._any(request, response, id)

    def _delete(self, request, response, id=None):
        return self._any(request, response, id)

    def _trace(self, request, response, id=None):
        return self._any(request, response, id)

    def _any(self, request, response, id=None):
        """
        Default handler for any request not specifically defined
        """
        raise MethodNotAllowed()
