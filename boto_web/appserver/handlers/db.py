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

    def _get(self, request, response, id=None ):
        """
        Get an object, or search for a list of objects
        """
        if id:
            content = self.read(id=id, user=request.user)
        else:
            content = self.search(params=request.GET.mixed(), user=request.user)
        response.content_type = "text/xml"
        content.to_xml().writexml(response)
        return response

    def _put(self, request, response, id=None):
        """
        Create/Update an object
        """
        #print request.body
        content = None
        obj = None
        if id:
            obj = self.db_class.get_by_ids(id)

        if obj:
            (cls, props, id) = self.xmlmanager.unmarshal_props(request.body_file, cls=self.db_class)
            content =  self.update(obj, props, request.user)
        else:
            new_obj = self.xmlmanager.unmarshal_object(request.body_file, cls=self.db_class)
            content =  self.create(new_obj, request.user)
            response.set_status(201)

        response.content_type = "text/xml"
        content.to_xml().writexml(response)
        return response


    def _delete(self, request, response, id=None):
        """
        Delete a given object
        """
        obj = self.read(id=id, user=request.user);
        content = self.delete(obj,user=request.user)
        response.content_type = "text/xml"
        content.to_xml().writexml(response)
        return response

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
    def search(self, params, user):
        """
        Search for given objects
        @param params: The Terms to search for
        @type params: Dictionary

        @param user: the user that is searching
        @type user: User
        """
        query_str = params.get("query", None)
        query = self.db_class.find()
        sort_by = params.get("sort_by", None)
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
                        m = re.match("^\'(.*)\' (=|>=|<=|<|>|!=|starts-with|ends-with|like) \'(.*)\'$", filter)
                        if m:
                            filter_name = m.group(1)
                            prop = self.db_class.find_property(filter_name)
                            values.append(self.db_class._manager.decode_value(prop, m.group(3)))
                            filter_cmp = m.group(2)
                    query.filter("%s %s" % (filter_name, filter_cmp), values)
        else:
            properties = [p.name for p in self.db_class.properties(hidden=False)]
            for filter in set(params.keys()):
                if filter == "sort_by":
                    continue
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
        if sort_by:
            query.order(sort_by)
        return query

    def create(self, obj, user):
        """
        Create an object in the DB
        @param obj: The object to create
        @type obj: self.db_class
        @param user: The user doing the creation
        @type user: User
        """
        obj.put()
        return obj

    def read(self, id, user):
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

    def update(self, obj, props, user):
        """
        Update our object

        @param obj: Object to update
        @type obj: self.db_class

        @param props: A has of properties to update
        @type props: hash

        @param user: The user making these changes
        @type user: User
        """
        boto.log.debug("===========================")
        boto.log.debug("Update %s" % obj.__class__.__name__)
        for prop_name in props:
            prop_val = props[prop_name]
            boto.log.debug("%s = %s" % (prop_name, prop_val))
            setattr(obj, prop_name, prop_val)
        boto.log.debug("===========================")
        obj.put()
        return obj

    def delete(self, obj, user):
        """
        Delete the object
        """
        log.info("Deleted object %s" % (obj.id))
        obj.delete()
        return obj
