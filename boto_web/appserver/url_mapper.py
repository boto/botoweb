# Author: Chris Moyer
import logging
import re
import sys
import traceback

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

class URLMapper(object):
    """
    Simple URL mapper
    """
    handlers = {}

    def __init__(self, boto_web_env):
        """
        Set up the environment for this system
        """
        self.boto_web_env = boto_web_env
        self.index_handler = IndexHandler(boto_web_env.config)

    def __call__(self, environ, start_response):
        """
        This needs to be callable as a function
        """
        request = Request(environ)
        response = Response()
        log.info("%s: %s" % (request.method, request.path_info))
        (handler, obj_id) = self.parse_path(request.path)
        if handler:
            response =  handler(request, response, obj_id)
        else:
            content = NotFound(url=request.path)
            log.error("Not Found: %s" % request.path)
            response.set_status(content.code)
            response.content_type = "text/xml"
            content.to_xml().writexml(response)
        return response.wsgi_write(environ, start_response)


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
        for handler_config in self.boto_web_env.config['handlers']:
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
                        conf = self.boto_web_env.config.copy()
                        conf.update(handler_config)
                        handler = handler_class(conf)

                    if handler:
                        self.handlers[handler_config['url']] = handler

                if handler:
                    return (handler, obj_id)
        return (None, None)
