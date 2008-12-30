# Author: Chris Moyer
from boto_web.exceptions import NotFound, Unauthorized, BadRequest
from boto_web.appserver.handlers import RequestHandler

import boto
from boto.utils import find_class, Password
from boto.sdb.db.model import Model
from boto.sdb.db.key import Key

import re
from datetime import datetime

import logging
log = logging.getLogger("boto_web.handlers.db")

class DBHandler(RequestHandler):
    """
    DB Handler Base class
    this provides a simple CRUD interface to 
    any DB object

    The simplest use of this handler would be calling it directly as such::
        - url: /blog
          handler: boto_web.appserver.handlers.db.DBHandler
          db_class: resources.post.Post

    You may also pass in the follwoing custom fields:
    * db_class: Required, the class to use for this interface
    """
    db_class = None

    def __init__(self, config):
        RequestHandler.__init__(self, config)
        db_class_name = self.config.get('db_class', None)
        if db_class_name:
            self.db_class = find_class(db_class_name)
        self.xmlmanager = self.db_class.get_xmlmanager()

    def get(self, request, id=None ):
        """
        Get an object, or search for a list of objects
        """
        if id:
            return self.read(id=id)
        else:
            return self.search(params=request.GET.mixed())

    def put(self, request, id=None):
        """
        Create an object
        """
        obj = self.xmlmanager.unmarshal_object(request.body_file)
        obj.put()
        return obj


    def decode(self, type, value):
        """
        Decode a string value sent by the user into actual things
        """
        if value:
            if Model in type.mro():
                return type.get_by_ids(value)
            elif type == bool:
                if value.lower() == 'true':
                    return True
                else:
                    return False
            elif type == datetime:
                return datetime.strptime(value, "%m/%d/%y %H:%M:%S")
            elif type == Password:
                return value
            else:
                return type(value)
        return value

    ###
    # The CRUD interface, this is
    # all you should override if you need to
    ##
    def search(self, params):
        """
        Search for given objects
        @param params: The Terms to search for
        @type params: Dictionary
        """
        query_str = params.get("query", None)
        query = self.db_class.find()
        if query_str:
            parts = query_str.split(" intersection ")
            for part in parts:
                matches = re.match("^\[(.*)\]$", part)
                if matches:
                    match = matches.group(1)
                    filters = match.split(" OR ")
                    filter_name = None
                    filter_cmp = None
                    values = []
                    for filter in filters:
                        m = re.match("^\'(.*)\' (=|>=|<=|<|>|starts-with|ends-with) \'(.*)\'$", filter)
                        if m:
                            values.append(m.group(3))
                            filter_name = m.group(1)
                            filter_cmp = m.group(2)
                    query.filter("%s %s" % (filter_name, filter_cmp), values)
        else:
            properties = [p.name for p in self.db_class.properties(hidden=False)]
            for filter in set(params.keys()):
                if not filter in properties:
                    raise BadRequest("Property not found: '%s'" % filter)
                filter_value = params[filter]
                filter_args = filter.split(".")
                if len(filter_args) > 1:
                    filter_cmp = filter_args[1]
                else:
                    filter_cmp = "="
                filter = filter_args[0]
                if len(filter_value) == 1:
                    filter_value = filter_value[0]
                if filter_value:
                    query.filter("%s %s " % (filter, filter_cmp), filter_value)
        return query

    def create(self, params):
        """
        Create an object in the DB
        @param params: Dictionary of params to set on this object
        @type params: dict
        """
        obj = self.db_class()
        return self.update(obj, params)

    def read(self, id):
        """
        Get the object that this URI points to, or None if they don't point to one
        If we point to a URI that doesn't exist, we toss a NotFound error
        """
        obj = None
        try:
            obj = self.db_class.get_by_ids(id)
        except:
            raise NotFound()
        if not obj:
            raise NotFound()
        return obj

    def update(self, obj, params):
        """
        Update our object
        @param params: Dictionary of params to set on this object
        @type params: dict
        """
        props = {}
        for p in obj.properties():
            props[p.name] = p
        for param in params.keys():
            if props.has_key(param):
                prop = props[param]
                if prop.data_type == list:
                    p_list = params.get(param)
                    if len(p_list) <= 1:
                        p_list = p_list[0].split("\r\n")
                    val = []
                    for v in p_list:
                        if v:
                            val.append(self.decode(prop.item_type, v))
                elif prop.data_type == Key:
                    val = self.decode(prop.reference_class, params.get(param))
                else:
                    val = self.decode(prop.data_type, params.get(param))
                if val:
                    log.info("%s: %s" % (param, str(val)))
                    setattr(obj, param, val)
        obj.save()
        return obj

    def delete(self, request=None, id=None):
        """
        Delete a given object
        """
        obj = self.read(id=id);
        obj.delete()
        log.info("Deleted object %s" % (obj.id))
        return obj
