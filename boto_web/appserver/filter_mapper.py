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

from boto_web.appserver.wsgi_layer import WSGILayer
class FilterMapper(WSGILayer):
    """
    Filter URL Mapper
    """


    def update(self, env):
        """
        On update, we have to re-build our entire filter list
        """
        self.env = env
        self.filters = {}
        self.resolver = FilterResolver()
        self.factory = InputSourceFactory(resolver=self.resolver)
        try:
            self.external_functions = self.env.config['xsltfunctions']
        except:
            self.external_functions = []

    def handle(self, req, response):
        """
        Map to the correct filters
        """
        variables = {}
        user = req.user
        headers = {}
        for key in req.headers:
            if not key.lower() in ["content-length", "authorization"]:
                headers[key] = req.headers[key]


        if user:
            variables[u'user'] = user
            variables[u'user_id'] = user.id
            variables[u'user_name'] = user.username

        filter = self.get_filter(req.path,req.method, user)

        stylesheet = None
        if filter[0] and req.body:
            req.body = filter[0].run(self.factory.fromString(req.body, None), topLevelParams=variables)

        if self.app:
            response = self.app.handle(req, response)

        if filter[1]:
            response.body = filter[1].run(self.factory.fromString(response.body, None), topLevelParams=variables)

        return response

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
        if not self.env.config.has_section('filters'):
            return (None, None)
        for rule in self.env.config['filters']:
            if rule.has_key("url"):
                if not re.match(rule['url'], path):
                    continue
            if rule.has_key("method"):
                if rule['method'] != method:
                    continue
            if rule.has_key("user"):
                if not user or rule['user'] != user.username:
                    continue
            if rule.has_key("group"):
                if not user or not rule['group'] in user.groups:
                    continue
            match = rule
            break

        input_filter = None
        output_filter = None
        if match and rule.has_key('filters'):
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
            proc.registerExtensionModules(self.external_functions)
        return proc
