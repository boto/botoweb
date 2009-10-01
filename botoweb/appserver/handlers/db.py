# Author: Chris Moyer
from botoweb.exceptions import NotFound, Unauthorized, BadRequest
from botoweb.appserver.handlers import RequestHandler

import boto
from boto.utils import find_class, Password
from boto.sdb.db.model import Model
from boto.sdb.db.key import Key

import urllib

import re
from datetime import datetime

import logging
log = logging.getLogger("botoweb.handlers.db")

from lxml import etree
from botoweb import xmlize


try:
	import json
except ImportError:
	import simplejson as json

class DBHandler(RequestHandler):
	"""
	DB Handler Base class
	this provides a simple CRUD interface to 
	any DB object

	The simplest use of this handler would be calling it directly as such::
		- url: /blog
		  handler: botoweb.appserver.handlers.db.DBHandler
		  db_class: resources.post.Post

	You may also pass in the follwoing custom fields:
	* db_class: Required, the class to use for this interface
	"""
	db_class = None
	page_size = 15

	def __init__(self, env, config):
		RequestHandler.__init__(self, env, config)
		db_class_name = self.config.get('db_class', None)
		if db_class_name:
			self.db_class = find_class(db_class_name)
		xmlize.register(self.db_class)

	def _get(self, request, response, id=None ):
		"""Get an object, or search for a list of objects"""
		response.content_type = "text/xml"
		if id:
			vals = id.split("/",1)
			property = None
			if len(vals) > 1:
				(id, property) = vals
			obj = self.read(id=id, user=request.user)
			if property:
				return self.get_property(response, obj, property)
			else:
				response.write(xmlize.dumps(obj))
		else:
			# Add the count to the header
			response = self._head(request, response)
			objs = self.search(params=request.GET.mixed(), user=request.user)
			objs.limit = self.page_size
			response.write("<%sList>" % self.db_class.__name__)
			for obj in objs:
				response.write(xmlize.dumps(obj))
			params = request.GET.mixed()
			if objs.next_token:
				if params.has_key("next_token"):
					del(params['next_token'])
				self_link = '%s%s%s?%s' % (request.real_host_url, request.base_url, request.script_name, urllib.urlencode(params).replace("&", "&amp;"))
				params['next_token'] = objs.next_token
				next_link = '%s%s%s?%s' % (request.real_host_url, request.base_url, request.script_name, urllib.urlencode(params).replace("&", "&amp;"))
				response.write('<link type="text/xml" rel="next" href="%s"/>' % (next_link))
				response.write('<link type="text/xml" rel="self" href="%s"/>' % (self_link))
			response.write("</%sList>" % self.db_class.__name__)
		return response

	def _head(self, request, response, id=None):
		"""Get the headers for this response, realisticaly this
		just means they want to know the count of how many results would be
		returned if they'd run this query"""
		objs = self.search(params=request.GET.mixed(), user=request.user)
		response.headers['Count'] = objs.count()
		return response


	def _post(self, request, response, id=None):
		"""Create a new resource"""
		if id:
			obj = self.db_class.get_by_ids(id)
			if obj:
				raise Conflict("Object %s already exists" % id)

		new_obj = xmlize.loads(request.body)
		new_obj.__id__ = id
		obj = self.create(new_obj, request.user)
		response.set_status(201)
		response.headers['Location'] = obj.id
		return response


	def _put(self, request, response, id=None):
		"""Update an existing resource"""
		content = None
		obj = None
		if id:
			obj = self.db_class.get_by_ids(id)

		if not obj:
			raise NotFound()

		new_obj = xmlize.loads(request.body)
		props = {}
		for prop in new_obj.__dict__:
			prop_value = getattr(new_obj, prop)
			if not prop.startswith("_"):
				props[prop] = prop_value
		content =  self.update(obj, props, request.user)

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
		next_token = params.get("next_token", None)
		if query_str:
			try:
				filters = json.loads(query_str)
			except:
				raise BadRequest("Bad query string")
			for filter in filters:
				query.filter("%s %s" % (filter[0], filter[1]), filter[2])
		else:
			properties = [p.name for p in self.db_class.properties(hidden=False)]
			for filter in set(params.keys()):
				if filter in ["sort_by", "next_token"]:
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
		if next_token:
			query.next_token = next_token
		return query

	def create(self, obj, user):
		"""Create an object in the DB
		:param obj: an object with all the properties to create
		:type obj: botoweb.xmlize.ProxyObject
		:param user: The user doing the creation
		:type user: User
		"""
		if obj.__model_class__:
			newobj = obj.__model_class__()
		else:
			newobj = self.db_class()
		if not isinstance(newobj, self.db_class):
			raise BadRequest("Object you passed in isn't of a type this handler understands!")
		for prop in obj.__dict__:
			if not prop.startswith("_"):
				prop_value = getattr(obj, prop)
				try:
					setattr(newobj, prop, prop_value)
				except Exception, e:
					raise BadRequest("Invalid value for %s" % prop)
		return newobj

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
		boto.log.info("Update %s" % obj.__class__.__name__)
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

	def get_property(self, response, obj, property):
		"""Return just a single property"""
		response.content_type = "text/plain"
		val = getattr(obj, property)
		if type(val) == list:
			for v in val:
				response.write(str(v))
		else:
			response.write(str(val))
		return response
