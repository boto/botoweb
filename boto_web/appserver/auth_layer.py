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
from boto_web.resources.user import User
from boto_web.exceptions import *

import traceback
import logging
log = logging.getLogger("boto_web.auth_layer")

import re

class AuthLayer(object):
    """
    Authentication/Authorization layer
    This only handles authorization on a macro level, it 
    will prevent users from getting to specific paths based on 
    groups, or just simply limit a path to require you to be logged
    in to get to it.
    """

    def __init__(self, app, env):
        self.app = app
        self.env = env

    def __call__(self, environ, start_response):
        """
        Based on the authorization file, require
        users to be logged in per path.
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
            response.headers.add("WWW-Authenticate", 'Basic realm="%s"' % self.env.config.get("app", "name", "Boto Web"))
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
        auth = self.get_auth_config(req.path)
        if auth:
            log.info("Checking auth: %s" % auth)
            if not req.user:
                raise Unauthorized()
            elif auth.has_key("group") and not req.user.has_auth_group(auth['group']):
                raise Unauthorized()
        return self.app.handle(req)

    def get_auth_config(self, path):
        """
        Get the auth config for this path
        """
        log.info("Get Auth Config: %s" % (path))
        match = None
        if not self.env.config.has_key('auth'):
            return None
        for rule in self.env.config['auth']:
            if rule.has_key("url"):
                if not re.match(rule['url'], path):
                    continue
            if rule.has_key("method"):
                if rule['method'] != method:
                    continue
            match = rule
            break
        return match


