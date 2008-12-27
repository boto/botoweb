# Author: Chris Moyer
import logging
import re
import sys
import traceback

import boto_web
import mimetypes
from boto.utils import find_class
from boto_web.appserver.handlers import RequestHandler
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

    def __call__(self, environ, start_response):
        """
        This needs to be callable as a function
        """
        request = Request(environ)
        log.info("%s: %s" % (request.method, request.path_info))

        response = Response()
        content = self.handle(request, response)
        response.content_type = "text/xml"
        content.to_xml().writexml(response)
        return response.wsgi_write(environ, start_response)

    def handle(self, request, response):
        """
        Do the handling of the request
        and response.
        We split this out so it's easier to test
        """
        (handler, obj_id) = self.parse_path(request.path)
        try:
            if handler:
                try:
                    if request.method == "GET":
                        content = handler.get(request, obj_id)
                    elif request.method == "POST":
                        content = handler.post(request, obj_id)
                    elif request.method == "HEAD":
                        content = handler.head(request, obj_id)
                    elif request.method == "OPTIONS":
                        content = handler.options(request, obj_id)
                    elif request.method == "PUT":
                        content = handler.put(request, obj_id)
                    elif request.method == "DELETE":
                        content = handler.delete(request, obj_id)
                    elif request.method == "TRACE":
                        content = handler.trace(request, obj_id)
                    else:
                        raise BadRequest(description="Unknown Method: %s" % request.method)

                except HTTPRedirect, e:
                    response.clear()
                    response.set_status(e.code)
                    response.headers['Location'] = str(url)
                    content = e
                except HTTPException, e:
                    response.clear()
                    response.set_status(e.code)
                    content = e
                except Exception, e:
                    content = InternalServerError(message=e.message)
                    response.set_status(content.code)
                    log.critical(traceback.format_exc())
            else:
                content = NotFound(url=request.path)
                log.error("Not Found: %s" % request.path)
                response.set_status(content.code)
        except Exception, e:
            log.critical(traceback.format_exc())
            content = InternalServerError(message=e.message)
            response.set_status(content.code)

        return content

    def parse_path(self, path):
        """
        Get the handler and object id (if given) for this
        path request.

        @return: (Handler, obj_id)
        @rtype: tuple
        """
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
