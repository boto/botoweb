# Author: Chris Moyer
from boto_web.exceptions import NotFound, Unauthorized
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

    def get(self, request, id=None ):
        """
        Get an object, or search for a list of objects
        """
        if id:
            return self.read(id=id)
        else:
            return self.search(params=request.GET.mixed())

    def post(self):
        """
        Save or update object to the DB
        """
        if not self.user:
            raise Unauthorized()
        obj = self.read()
        if obj:
            log.info("===== %s Update %s =====" % (self.user.username, self.db_class.__class__.__name__))
            obj = self.update(obj, self.request.POST)
            log.info("========================")
        else:
            log.info("===== %s Create %s =====" % (self.user.username, self.db_class.__class__.__name__))
            obj = self.create(self.request.POST)
            log.info("========================")
        return self.redirect("%s/%s" % (self.request.script_name, obj.id))

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
        objects = []
        query = self.db_class.find()
        for filter in set(params.keys()):
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
        for obj in query:
            objects.append(obj)
        return objects

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
