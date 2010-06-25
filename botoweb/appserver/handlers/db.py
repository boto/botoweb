# Author: Chris Moyer
from botoweb.exceptions import NotFound, Forbidden, BadRequest, Conflict, Gone
from botoweb.appserver.handlers import RequestHandler

import boto
from boto.utils import find_class, Password
from boto.sdb.db.blob import Blob
from boto.sdb.db.model import Model

import urllib

from datetime import datetime

import logging
log = logging.getLogger("botoweb.handlers.db")

from botoweb import xmlize


try:
	import json
	json.loads("[]")
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
	page_size = 50

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
				return self.get_property(request, response, obj, property)
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
		response.headers['X-Result-Count'] = str(objs.count())
		return response


	def _post(self, request, response, id=None):
		"""Create a new resource, or update a single property on an object"""
		if id:
			vals = id.split("/",1)
			if len(vals) > 1:
				obj = self.db_class.get_by_id(vals[0])
				return self.update_property(request, response, obj, vals[1])
			else:
				obj = self.db_class.get_by_id(id)
				if obj:
					raise Conflict("Object %s already exists" % id)

		new_obj = xmlize.loads(request.body)
		new_obj.__id__ = id
		obj = self.create(new_obj, request.user, request)
		response.set_status(201)
		response.content_type = "text/xml"
		response.write(xmlize.dumps(obj))
		return response


	def _put(self, request, response, id=None):
		"""Update an existing resource"""
		content = None
		obj = None
		if id:
			obj = self.db_class.get_by_id(id)

		if not obj:
			raise NotFound()

		new_obj = xmlize.loads(request.body)
		props = {}
		for prop in new_obj.__dict__:
			prop_value = getattr(new_obj, prop)
			if not prop.startswith("_"):
				props[prop] = prop_value
		content =  self.update(obj, props, request.user, request)

		response.content_type = "text/xml"
		response.write(xmlize.dumps(content))
		return response


	def _delete(self, request, response, id=None):
		"""
		Delete a given object
		"""
		obj = self.read(id=id, user=request.user);
		content = self.delete(obj,user=request.user)
		response.content_type = "text/xml"
		response.write(xmlize.dumps(content))
		return response

	def decode(self, type, value):
		"""
		Decode a string value sent by the user into actual things
		"""
		if value:
			if Model in type.mro():
				return type.get_by_id(value)
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

	def build_query(self, params, query, user=None, show_deleted=False):
		"""Build the query based on the parameters specified here,
		You must pass in the base query object to start with
		"""
		query_str = params.get("query", None)
		sort_by = params.get("sort_by", None)
		next_token = params.get("next_token", None)
		if query_str:
			try:
				filters = json.loads(query_str)
			except:
				raise BadRequest("Bad query string")
			for filter in filters:
				param_name = filter[0]
				prop_value = filter[2]
				if hasattr(self.db_class, "_indexed_%s" % param_name):
					param_name = "_indexed_%s" % param_name
					prop_value = prop_value.upper()
				# Allows a ['prop_name', 'sort', 'desc|asc']
				if filter[1] == "sort":
					if filter[2] == "desc":
						param_name = "-%s" % param_name
					query.sort_by = param_name
				else:
					query.filter("%s %s" % (param_name, filter[1]), prop_value)
		else:
			properties = [p.name for p in query.model_class.properties(hidden=False)]
			for filter in set(params.keys()):
				if filter in ["sort_by", "next_token"]:
					continue
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
			query.next_token = urllib.unquote(next_token.strip()).replace(" ", "+")
		if not show_deleted:
			query.filter("deleted =", [False, None]) # Allow deleted to be either not set or set to false
		return query


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
		return self.build_query(params, query=self.db_class.find(), user=user)

	def create(self, obj, user, request):
		"""Create an object in the DB
		:param obj: an object with all the properties to create
		:type obj: botoweb.xmlize.ProxyObject
		:param user: The user doing the creation
		:type user: User
		"""
		now = datetime.utcnow()
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


				# Set an index, if it exists
				if hasattr(newobj, "_indexed_%s" % prop) and prop_value:
					setattr(newobj, "_indexed_%s" % prop, prop_value.upper())
		newobj.created_at = now
		newobj.modified_at = now
		newobj.created_by = user
		newobj.modified_by = user
		newobj.put()
		boto.log.info("%s Created %s %s" % (user, newobj.__class__.__name__, newobj.id))
		return newobj

	def read(self, id, user):
		"""
		Get the object that this URI points to, or None if they don't point to one
		If we point to a URI that doesn't exist, we toss a NotFound error
		"""
		obj = None
		try:
			obj = self.db_class.get_by_id(id)
		except:
			raise NotFound()
		if not obj:
			raise NotFound()
		# Insurance to make sure this is actually an instance of
		# what they're allowed to request from this handler
		if not isinstance(obj, self.db_class):
			raise NotFound()
		# If the object was marked as "deleted", then
		# we need to raise a "Gone" exception, which is defined as:
		# "The 410 response is primarily intended to assist the 
		# task of web maintenance by notifying the recipient that 
		# the resource is intentionally unavailable and that the 
		# server owners desire that remote links to that resource 
		# be removed."
		if hasattr(obj, "deleted") and obj.deleted:
			raise Gone("Object has been deleted", "The object %s no longer exists" % obj.id)
		return obj

	def update(self, obj, props, user, request):
		"""
		Update our object

		:param obj: Object to update
		:type obj: self.db_class

		:param props: A hash of properties to update
		:type props: hash

		:param user: The user making these changes
		:type user: User

		:param request: The request object
		:type request: botoweb.request.Request

		"""
		boto.log.debug("===========================")
		boto.log.info("Update %s" % obj.__class__.__name__)
		for prop_name in props:
			prop_val = props[prop_name]
			boto.log.debug("%s = %s" % (prop_name, prop_val))
			try:
				setattr(obj, prop_name, prop_val)
			except Exception, e:
				if prop_val != "": # If it was a nothing request, we ignore it
					raise BadRequest("Bad value for %s: %s" % (prop_name, e))

			if hasattr(obj, "_indexed_%s" % prop_name) and prop_val:
				setattr(obj, "_indexed_%s" % prop_name, prop_val.upper())
				boto.log.debug("Indexed: %s" % prop_name)
		boto.log.debug("===========================")
		obj.modified_by = user
		obj.modified_at = datetime.utcnow()
		obj.put()
		return obj

	def delete(self, obj, user):
		"""
		Delete the object
		"""
		log.info("Deleted object %s" % (obj.id))

		if hasattr(obj, "deleted"):
			# Don't actually remove it from the DB, just set it
			# to "deleted" and flag who did it and when
			# TODO: Allow them to be purged if it was just created?
			obj.deleted = True
			obj.deleted_at = datetime.utcnow()
			obj.deleted_by = user
			obj.put()
		else:
			obj.delete()
		return obj

	def get_property(self, request, response, obj, property):
		"""Return just a single property"""
		from boto.sdb.db.query import Query
		if not hasattr(obj, property):
			raise BadRequest("%s has no attribute %s" % (obj.__class__.__name__, property))

		# Some leakage here of authorizations, but 
		# I'm not quite sure how to handle this elsewhere
		if request.user and not request.user.has_auth('GET', obj.__class__.__name__, property):
			raise Forbidden()

		val = getattr(obj, property)
		if type(val) in (str, unicode) or isinstance(val, Blob):
			response.content_type = "text/plain"
			response.write(str(val))
		elif isinstance(val, Query):
			objs = self.build_query(request.GET.mixed(), query=val, user=request.user)
			response.headers['X-Result-Count'] = str(objs.count())
			response.write("<%s>" % property)

			objs.limit = self.page_size
			for o in objs:
				response.write(xmlize.dumps(o))
			params = request.GET.mixed()
			if objs.next_token:
				if params.has_key("next_token"):
					del(params['next_token'])
				self_link = '%s%s%s/%s/%s?%s' % (request.real_host_url, request.base_url, request.script_name, obj.id, property, urllib.urlencode(params).replace("&", "&amp;"))
				params['next_token'] = objs.next_token
				next_link = '%s%s%s/%s/%s?%s' % (request.real_host_url, request.base_url, request.script_name, obj.id, property, urllib.urlencode(params).replace("&", "&amp;"))
				response.write('<link type="text/xml" rel="next" href="%s"/>' % (next_link))
				response.write('<link type="text/xml" rel="self" href="%s"/>' % (self_link))
			response.write("</%s>" % property)
		elif val:
			response.write("<response>%s</response>" % xmlize.dumps(val, property))
		else:
			response.set_status(204)
		return response

	def update_property(self, request, response, obj, property):
		"""Update the property via a POST to the specific property,
		Typically this means we're putting up a BLOB"""
		if not hasattr(obj, property):
			raise BadRequest("%s has no attribute %s" % (obj.__class__.__name__, property))
		val = request.POST.get(property)
		if hasattr(val, "file"):
			val = val.file.read()
		setattr(obj, property, val)

		if hasattr(obj, "_indexed_%s" % property) and val:
			setattr(obj, "_indexed_%s" % property, val.upper())
			boto.log.debug("Indexed: %s" % property)

		obj.modified_by = request.user
		obj.modified_at = datetime.utcnow()
		obj.put()
		log.info("Updated %s<%s>.%s" % (obj.__class__.__name__, obj.id, property))
		# 204 is the proper status code but it does not allow the onload event
		# to fire in the browser, which expects a 200. Without the onload event
		# we cannot determine when an upload is complete.
		#response.set_status(204)
		return response
