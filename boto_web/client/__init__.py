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
from boto_web.client.query import Query

import logging
log = logging.getLogger("boto_web.client")
class ClientObject(object):
    """
    boto_web Client Object to interface via REST to our
    XML server
    """
    _properties = []

    def __init__(self, env, id=None, **params):
        """
        Initialize the Client Object with a given environment
        Additional arguments may be passed to set them immediately on the newly 
        created object

        @param env: The boto_web.environment.Environment object to use
        @type env: boto_web.environment.Environment

        @param id: The ID to use for this object
        @type id: str
        """
        self._env = env
        self.id = id
        for k in params:
            setattr(self, k, params[k])

    @classmethod
    def _get_base_url(cls, env):
        """
        Get the base URL based on this environment
        """
        host_url = env.config.get("client", "base_url", "")
        path = env.config.get("client", cls.__name__, {}).get("path", "/%s" % cls.__name__.lower())
        return "%s%s" % (host_url, path)

    @classmethod
    def all(cls, env):
        """
        List all objects

        @param env: The boto_web.environment.Environment object to use
        @type env: boto_web.environment.Environment
        """
        return cls.query(env, [])

    @classmethod
    def find(cls, env, **params):
        """
        Simple search method.

        @param env: The boto_web.environment.Environment object to use
        @type env: boto_web.environment.Environment

        @param **params: Parameters to search for, passed in standard key=value pairs
        """
        filters = []
        for k in params:
            filters.append((k, "=", params[k]))
        return cls.query(env, filters)

    @classmethod
    def query(cls, env, filters):
        """
        Search for objects

        @param env: The boto_web.environment.Environment object to use
        @type env: boto_web.environment.Environment

        @param filters: Filters to apply to the search, formatted as [(key, op, value), (key, op, [value, value])]
             values, if a list, are considered OR searches, whereas filters are normally AND operations.
        @type filters: [(key, op, value), (key2, op2, [value2, value3, ..])]
        """
        return Query(cls, env, filters)

    @classmethod
    def get_by_id(cls, env, id):
        """
        GET for object ID

        @param env: The boto_web.environment.Environment object to use
        @type env: boto_web.environment.Environment

        @param id: The ID of the object to get
        @type id: str
        """
        assert len(id) > 0
        url = "%s/%s" % (cls._get_base_url(env), id)
        log.debug("Fetching from URL: %s" % url)
        params = {}
        return cls(env, id=id, **params)

    def _get_url(self):
        """Get the URL for this specific object"""
        base_url = self.__class__._get_base_url(self._env)
        if self.id:
            return "%s/%s" % (base_url, self.id)
        else:
            return base_url

    def encode_value(self, prop_node, value):
        """Encode a property and store it in this doc"""
        from lxml import etree
        if type(value) == list:
            for item in value:
                item_node = etree.SubElement(prop_node, "item", type=str(type(item).__name__))
                self.encode_value(item_node, item)
        elif type(value) == dict:
            for k in value:
                v = value[k]
                item_node = etree.SubElement(prop_node, "item", type=str(type(item).__name__), id=str(k))
                self.encode_value(item_node, v)
        else:
            prop_node.text = str(value)

    def to_xml(self, doc=None):
        """Turn this object into XML"""
        from lxml import etree
        if doc:
            root = etree.SubElement(doc, "object", id=self.id)
        else:
            root = etree.Element("object", id=self.id)
            doc = root
        for prop_name in self._properties:
            value = getattr(self, prop_name)
            prop_node = etree.SubElement(doc, "property", name=prop_name, type=str(type(value).__name__))
            self.encode_value(prop_node, getattr(self, prop_name))
        return doc

    def put(self):
        """PUT this object (save)"""
        from lxml import etree
        url = self._get_base_url(self._env)
        if self.id != None:
            url+= "/%s" % self.id
            method = "PUT"
        else:
            method = "POST"
        log.debug("Putting object to URL: %s" % url)
        body = etree.tostring(self.to_xml(), xml_declaration=True, pretty_print=True, encoding="utf-8")
        url = self._get_url()
        conn = self._env.connect_client()
        return conn.request(method, url, body=body, headers={"Content-Type": "text/xml"})
