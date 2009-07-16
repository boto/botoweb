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

import urllib
import urllib2
from lxml import etree
from xml.sax import make_parser
from boto_web.client.sax_handler import ObjectHandler
import logging
log = logging.getLogger("boto_web.client")
class Query(object):
    """
    Query object iterator
    """
    ALLOWED_EXPRESSIONS = ["=", "!=", ">", ">=", "<", "<=", "like", "not like", "intersection", "between", "is null", "is not null"]

    def __init__(self, model_class, env, filters=[], limit=None, sort_by=None):
        self.model_class = model_class
        self.env = env
        self.filters = filters
        self.limit = limit
        self.sort_by = sort_by

    def filter(self, key, op, value):
        """
        Add a filter to this query

        @param key: Key to filter on
        @param op: Operator to use
        @param value: Value, or list of values, to filter on
        """
        assert op in self.ALLOWED_EXPRESSIONS
        self.filters.append((key, op, value))
        return self

    def order(self, key):
        """
        Sort by this key
        """
        self.sort_by = key
        return self

    def to_xml(self, doc=None):
        """
        XML serialize this query
        """
        if doc == None:
            doc = etree.Element("%sList" % self.model_class.__name__)
        for obj in self:
            obj.to_xml(doc)
        return doc

    def __iter__(self):
        url = self.build_url()
        log.debug("Query: %s" % url)
        conn = self.env.connect_client()
        resp = conn.request("GET", url)
        handler = ObjectHandler(self.model_class)
        parser = make_parser()
        parser.setContentHandler(handler)
        try:
            parser.parse(resp)
        except:
            raise Exception("Error Parsing Response: %s" % resp.read())
        return iter(handler.objs)

    def build_url(self):
        """
        Generate the query URL
        """
        import types
        if len(self.filters) > 4:
            raise Exception('Too many filters, max is 4')
        params = {}
        parts = []
        for name, op, value in self.filters:
            if types.TypeType(value) == types.ListType:
                filter_parts = []
                for val in value:
                    val = self.encode_value(property, val)
                    filter_parts.append("'%s' %s '%s'" % (name, op, val))
                parts.append("[%s]" % " OR ".join(filter_parts))
            else:
                value = self.encode_value(property, value)
                parts.append("['%s' %s '%s']" % (name, op, value))
        query = ' intersection '.join(parts)
        if query:
            params['query'] = query
        if self.sort_by:
            params['sort_by'] = self.sort_by
        if self.limit:
            params['limit'] = self.limit
        url = self.model_class._get_base_url(self.env)
        if len(params) > 0:
            query = urllib.urlencode(params)
            url += ("?"+query)
        base_path = self.env.config.get("client", "base_path", "")
        return "%s%s" % (base_path, url)

    def encode_value(self, property, value):
        return str(value)

    def next(self):
        return self.__iter__().next()

    def count(self):
        return 0
