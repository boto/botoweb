# Copyright (c) 2009 Chris Moyer http://coredumped.org
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
from boto_web.exceptions import *

import traceback
import logging
log = logging.getLogger("boto_web.wsgi_layer")

import re

class WSGILayer(object):
    """
    Base WSGI Layer. This simply gives us an additional
    few functions that allow this object to be called as a function,
    but also allows us to chain them together without having to re-build
    the request/response objects
    """

    def __init__(self, env, app=None):
        """
        Initialize this WSGI layer.

        @param env: A boto_web environment object that represents what we're running in
        @type env: boto_web.environment.Environment

        @param app: An optional WSGI layer that this layer is on top of.
        @type app: WSGILayer

        """
        self.app = app
        self.update(env)

    def __call__(self, environ, start_response):
        """
        Handles basic one-time-only WSGI setup, and handles
        error catching.
        """
        resp = Response()
        try:
            req = Request(environ)
            resp = self.handle(req, resp)
        except HTTPRedirect, e:
            resp.set_status(e.code)
            resp.headers['Location'] = str(url)
            content = e
        except Unauthorized, e:
            resp.set_status(e.code)
            resp.headers.add("WWW-Authenticate", 'Basic realm="%s"' % self.env.config.get("app", "name", "Boto Web"))
        except HTTPException, e:
            resp.set_status(e.code)
            resp.write(e.message)
        except Exception, e:
            content = InternalServerError(message=e.message)
            resp.set_status(content.code)
            log.critical(traceback.format_exc())
        return resp(environ, start_response)

    def update(self, env):
        """
        Update this layer to use a new environment. Minimally
        this will set "self.env = env", but for specific layers
        you may have to undate or invalidate your cache
        """
        self.env = env

    def handle(self, req, response):
        """
        This is the function that is called when chainging WSGI layers
        together, it has the request and response objects passed
        into it so they are not re-created.
        """
        return self.app.handle(req, response)
