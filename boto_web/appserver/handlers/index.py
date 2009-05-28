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
from boto_web.appserver.handlers import RequestHandler
from xml.dom.minidom import getDOMImplementation, Node
import copy

import logging
log = logging.getLogger("boto_web.handlers.db")

class Index(object):
    """
    Index object which shows routes based on a config
    and turns that into XML
    """
    
    def __init__(self, config):
        """
        @param config: The routing config from this app
        @type config: array of dicts
        """
        self.config = config
        self.impl = getDOMImplementation()
        self.doc = self.impl.createDocument(None, 'Index', None)
        self.doc.documentElement.setAttribute("name", self.config.get("app", "name", "boto_web application"))
        self.doc = self.to_xml(self.doc)


    def to_xml(self, doc=None):
        if not doc:
            return self.doc
        else:
            # Populate the document
            for route in self.config['handlers']:
                route_node = self.doc.createElement("route")
                route_node.setAttribute("href", route['url'])
                for k in route.keys():
                    if k != "url":
                        attr_node = self.doc.createElement(k)
                        attr_node.appendChild(self.doc.createTextNode(str(route[k])))
                        route_node.appendChild(attr_node)
                self.doc.documentElement.appendChild(route_node)
            return doc


class IndexHandler(RequestHandler):
    """
    Simple Index Handler which helps to show what
    URLs we have and what objects they provide
    """
    def __init__(self, config):
        RequestHandler.__init__(self,config)
        self._index = None

    def _get(self, request, response, id=None):
        """
        List all our routes
        """
        if not self._index:
            self._index = Index(self.config)
        response.content_type = 'text/xml'
        doc = copy.deepcopy(self._index.to_xml())
        if request.user:
            request.user.to_xml(doc)

        doc.writexml(response)
        return response
