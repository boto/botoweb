# Author: Chris Moyer
import logging
import re
import sys
import traceback
import urllib

import boto_web
import mimetypes
from boto.utils import find_class
from boto_web.appserver.handlers import RequestHandler
from boto_web.appserver.handlers.index import IndexHandler
from boto_web.request import Request
from boto_web.response import Response
from boto_web import status
from boto_web.exceptions import *

log = logging.getLogger("boto_web.url_mapper")

from boto_web.appserver.wsgi_layer import WSGILayer
class URLMapper(WSGILayer):
    """
    Simple URL mapper
    """
    handlers = {}
    index_handler = None

    def update(self, env):
        """
        On an update, we have to remove all of our handlers and re-build 
        our index handler
        """
        self.env = env
        self.index_handler = IndexHandler(self.env.config)
        self.handlers = {}

    def handle(self, req, response):
        """
        Basic URL mapper
        """
        log.info("%s: %s" % (req.method, req.path_info))
        (handler, obj_id) = self.parse_path(req.path)
        if not handler:
            raise NotFound(url=req.path)
        return handler(req, response, obj_id)


    def parse_path(self, path):
        """
        Get the handler and object id (if given) for this
        path request.

        @return: (Handler, obj_id)
        @rtype: tuple
        """
        if path == "/":
            return (self.index_handler, None)
        handler = None
        obj_id = None
        for handler_config in self.env.config['handlers']:
            match = re.match("^%s(\/(.*))?$" % handler_config['url'], path)

            if match:
                log.debug("URL Mapping: %s" % handler_config)
                obj_id = match.group(2)
                if obj_id == "":
                    obj_id = None

                if self.handlers.has_key(handler_config['url']):
                    handler = self.handlers.get(handler_config['url'])
                else:
                    if handler_config.has_key("handler"):
                        class_name = handler_config['handler']
                        handler_class = find_class(class_name)
                        conf = self.env.config.copy()
                        conf.update(handler_config)
                        handler = handler_class(conf)

                    if handler:
                        self.handlers[handler_config['url']] = handler

                if handler:
                    if obj_id:
                        obj_id = urllib.unquote(obj_id)
                    return (handler, obj_id)
        return (None, None)
