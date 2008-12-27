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
