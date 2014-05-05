# Author: Chris Moyer
from botoweb.exceptions import NotFound, Forbidden, BadRequest, Conflict, Gone
from boto.exception import SDBPersistenceError, SDBResponseError
from botoweb.appserver.handlers import RequestHandler
from botoweb.db.dynamo import BatchItemFetcher

from boto.utils import find_class, Password
from botoweb.db.blob import Blob
from botoweb.db.coremodel import Model

import urllib

from datetime import datetime
from time import time

from botoweb import xmlize
from botoweb.db import index_string
from botoweb.db.dynamo import DynamoModel

try:
	import simplejson as json
except:
	import json

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

	def __call__(self, *params, **keywords):
		"""Override to replace the SDBResponseError 
		with a BadRequest error"""
		try:
			return RequestHandler.__call__(self, *params, **keywords)
		except SDBResponseError, e:
			raise BadRequest("Invalid Query", description=str(e))

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
				if request.file_extension == "json" or request.accept.best_match(['application/xml', 'application/json']) == "application/json":
					response.content_type = "application/json"
					response.app_iter = JSONWrapper(iter([obj]), request.user)
				else:
					response.write(xmlize.dumps(obj))
					
		else:
			params = request.GET.mixed()
			objs = self.search(params=params, user=request.user)
			# Add the count to the header
			try:
				response.headers['X-Result-Count'] = str(objs.count())
			except:
				raise BadRequest('Invalid Query')
			if params.has_key("next_token"):
				del(params['next_token'])
			base_url = '%s%s%s' % (request.real_host_url, request.base_url, request.script_name)
			#objs.limit = self.page_size
			if request.file_extension == "json" or request.accept.best_match(['application/xml', 'application/json']) == "application/json":
				response.content_type = "application/json"
				response.app_iter = JSONWrapper(objs, request.user, "%s.json" % base_url, params)
			elif request.file_extension == "csv":
				response.content_type = "text/csv"
				response.headers['Content-Disposition'] = 'attachment;filename=%s.csv' % self.db_class.__name__
				response.app_iter = CSVWrapper(objs, request.user, self.db_class)
			else:
				page = False
				if(objs.limit == None):
					objs.limit = self.page_size
					page = True
				response.write("<%sList>" % self.db_class.__name__)
				for obj in objs:
					dataStr = xmlize.dumps(obj)
					if '\x80' in dataStr or '\x1d' in dataStr:
						dataStr.replace('\x80','').replace('\x1d','')
					response.write(dataStr)
				if page and objs.next_token:
					if params.has_key("next_token"):
						del(params['next_token'])
					self_link = '%s?%s' % (base_url, urllib.urlencode(params).replace("&", "&amp;"))
					params['next_token'] = objs.next_token
					next_link = '%s?%s' % (base_url, urllib.urlencode(params).replace("&", "&amp;"))
					response.write('<link type="text/xml" rel="next" href="%s"/>' % (next_link))
					response.write('<link type="text/xml" rel="self" href="%s"/>' % (self_link))
				response.write("</%sList>" % self.db_class.__name__)
		return response

	def _head(self, request, response, id=None):
		"""Get the headers for this response, realisticaly this
		just means they want to know the count of how many results would be
		returned if they'd run this query

		NOTE: This is an ESTIMATE, it's not the full count, since
		that may take way too long to generate. This only returns the
		total records that could be counted in 5 seconds
		"""
		objs = self.search(params=request.GET.mixed(), user=request.user)
		try:
			response.headers['X-Result-Count'] = str(objs.count())
		except:
			raise BadRequest("Invalid Query")
		return response


	def _post(self, request, response, id=None):
		"""Create a new resource, or update a single property on an object"""
		if id:
			vals = id.split("/",1)
			if len(vals) > 1:
				obj = self.db_class.lookup(vals[0])
				return self.update_property(request, response, obj, vals[1])
			else:
				obj = self.db_class.lookup(id)
				if obj:
					raise Conflict("Object %s already exists" % id)

		if request.file_extension == "json" or request.accept.best_match(['application/xml', 'application/json']) == "application/json":
			new_obj = json.loads(request.body)
			new_obj['__id__'] = id
		else:
			new_obj = xmlize.loads(request.body)
			new_obj.__id__ = id
		obj = self.create(new_obj, request.user, request)
		response.set_status(201)
		if request.file_extension == "json" or request.accept.best_match(['application/xml', 'application/json']) == "application/json":
			response.content_type = "application/json"
			response.app_iter = JSONWrapper(iter([obj]), request.user)
		else:
			response.content_type = "text/xml"
			response.write(xmlize.dumps(obj))
		return response


	def _put(self, request, response, id=None):
		"""Update an existing resource"""
		obj = None
		if id:
			obj = self.db_class.lookup(id)

		if not obj:
			raise NotFound()

		props = {}
		if "json" in request.content_type:
			props = json.loads(request.body)
		elif request.content_type == "application/x-www-form-urlencoded" and not request.body.startswith("<"):
			props = request.POST.mixed()
		else:
			request.content_type = "text/xml"
			# By default we assume it's XML
			new_obj = xmlize.loads(request.body)
			for prop in new_obj.__dict__:
				prop_value = getattr(new_obj, prop)
				if not prop.startswith("_"):
					props[prop] = prop_value
		obj =  self.update(obj, props, request.user, request)

		if request.file_extension == "json" or request.accept.best_match(['application/xml', 'application/json']) == "application/json":
			response.content_type = "application/json"
			response.app_iter = JSONWrapper(iter([obj]), request.user)
		else:
			response.content_type = "text/xml"
			response.write(xmlize.dumps(obj))
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
				return type.lookup(value)
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
		simple_query = params.get('q', None)
		properties = [p.name for p in query.model_class.properties(hidden=False)]
		if query_str:
			if query_str.startswith("["):
				try:
					filters = json.loads(query_str)
				except:
					raise BadRequest("Bad query string")
				for filter in filters:
					param_names = filter[0]
					prop_value = filter[2]
					if not isinstance(param_names, list):
						param_names = [param_names]
					for pnum, param_name in enumerate(param_names):
						# Handle the "auto indexing"
						# to make SDB searching case-insensitive
						if hasattr(self.db_class, "_indexed_%s" % param_name):
							param_name = "_indexed_%s" % param_name
							# Make sure the uppercased version is
							# also in the prop_value array
							# we have to add this to the accepted values,
							# not just replace, since they may have
							# multiple param_names in the list, and
							# not all of them may be indexed
							if isinstance(prop_value, list):
								for pv in prop_value:
									pv = index_string(pv)
									if not pv in prop_value:
										prop_value.append(pv)
							else:
								prop_value = [prop_value, index_string(prop_value)]
						param_names[pnum] = param_name
					# Allows a ['prop_name', 'sort', 'desc|asc']
					if filter[1] == "sort":
						if filter[2] == "desc":
							param_names[0] = "-%s" % param_names[0]
						query.sort_by = param_names[0]
					# Allows a ['', 'limit', '1']
					elif filter[1] == "limit":
						query.limit = int(filter[2])
					# Allows a ['', 'offset', '25']
					elif filter[1] == "offset":
						query.offset = int(filter[2])
					else:
						param_filters = []
						for param_name in param_names:
							param_filters.append("%s %s" % (param_name, filter[1]))
						query.filter(param_filters, prop_value)
			else:
				pass
		elif simple_query:
			if hasattr(self.db_class, '_indexed_name'):
				query.filter('_indexed_name like', '%%%s%%' % index_string(simple_query))
			else:
				query.filter('name like', '%%%s%%' % simple_query)
		else:
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
		if not show_deleted and "deleted" in properties:
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
		if DynamoModel in self.db_class.mro():
			return self.build_query(params, query=self.db_class.all(), user=user)
		else:
			return self.build_query(params, query=self.db_class.find(), user=user)

	def create(self, obj, user, request):
		"""Create an object in the DB
		:param obj: an object with all the properties to create
		:type obj: botoweb.xmlize.ProxyObject OR dict
		:param user: The user doing the creation
		:type user: User
		"""
		now = datetime.utcnow()
		if isinstance(obj, dict):
			model_class = obj.get('__type__')
			prop_dict = obj
		else:
			model_class = obj.__model_class__
			prop_dict = obj.__dict__
		id = prop_dict.get("__id__")
		if model_class:
			newobj = model_class(id)
		else:
			newobj = self.db_class(id)
		# Make sure the user is auth'd to "POST" (aka. create) this type of object
		if not request.user or not request.user.has_auth('POST', newobj.__class__.__name__):
			raise Forbidden("You may not create new %ss!" % newobj.__class__.__name__)
		if not isinstance(newobj, self.db_class):
			raise BadRequest("Object you passed in isn't of a type this handler understands!")
		for prop in prop_dict:
			# Only allow them to set public properties,
			# and verify that they're allowed to set each one
			# Anything else they try to send is ignored
			if not prop.startswith("_") and (user.has_auth('PUT', newobj.__class__.__name__, prop) or user.has_auth('POST', newobj.__class__.__name__, prop)):
				prop_value = prop_dict[prop]
				if isinstance(newobj, DynamoModel):
					# DynamoDB Objects get set as dict-values
					# Check to make sure the value isn't empty
					if prop_value:
						# Check to make sure it's a valid property
						if newobj._properties.has_key(prop):
							newobj[prop] = prop_value
						else:
							self.log.error('Ignoring invalid property %s for object %s' % (prop, newobj.__class__.__name__))
				else:
					# SimpleDB objects get set as attributes
					try:
						setattr(newobj, prop, prop_value)
					except Exception, e:
						raise BadRequest("Invalid value for %s" % prop)

				# Set an index, if it exists
				if hasattr(newobj, "_indexed_%s" % prop) and prop_value:
					setattr(newobj, "_indexed_%s" % prop, index_string(prop_value))
		# Only set these properties for non-dynamo models
		if not isinstance(newobj, DynamoModel):
			newobj.created_at = now
			newobj.modified_at = now
			newobj.created_by = user
			newobj.modified_by = user
		try:
			newobj.put()
		except SDBPersistenceError, e:
			raise BadRequest(e.message)
		self.log.info("%s Created %s %s" % (user, newobj.__class__.__name__, newobj.id))
		return newobj

	def read(self, id, user):
		"""
		Get the object that this URI points to, or None if they don't point to one
		If we point to a URI that doesn't exist, we toss a NotFound error
		"""
		obj = None
		try:
			obj = self.db_class.lookup(id)
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
		# Be sure they can acutally update this object
		if not request.user or not request.user.has_auth('PUT', obj.__class__.__name__):
			raise Forbidden("You may not update %ss!" % obj.__class__.__name__)
		self.log.debug("===========================")
		self.log.info("Update %s" % obj.__class__.__name__)
		for prop_name in props:
			# Make sure it's not a hidden prop and that
			# this user is allowed to write to it
			if not prop_name.startswith("_") and user.has_auth('PUT', obj.__class__.__name__, prop_name):
				prop_val = props[prop_name]
				self.log.debug("%s = %s" % (prop_name, prop_val))
				if isinstance(obj, DynamoModel):
					# DynamoDB Objects get set as dict-values
					# Check to make sure the value isn't empty
					if prop_val:
						# Check to make sure it's a valid property
						if obj.find_property(prop_name):
							obj[prop_name] = prop_val
						else:
							self.log.error('Ignoring invalid property %s for object %s' % (prop_name, obj.__class__.__name__))
					else:
						# If it's not there, we delete it
						del obj[prop_name]
				else:
					try:
						setattr(obj, prop_name, prop_val)
					except Exception, e:
						if prop_val != "": # If it was a nothing request, we ignore it
							self.log.exception(e)
							raise BadRequest("Bad value for %s: %s" % (prop_name, e))

				if hasattr(obj, "_indexed_%s" % prop_name) and prop_val:
					setattr(obj, "_indexed_%s" % prop_name, index_string(prop_val))
					self.log.debug("Indexed: %s" % prop_name)
		self.log.debug("===========================")
		obj.modified_by = user
		obj.modified_at = datetime.utcnow()
		obj.put()
		return obj

	def delete(self, obj, user):
		"""
		Delete the object
		"""
		self.log.info('Deleted object %s' % (obj.id))
		# Handle DynamoModels
		if isinstance(obj, DynamoModel):
			if obj._properties.has_key('deleted'):
				obj['deleted'] = True
				obj['deleted_at'] = datetime.utcnow()
				obj['deleted_by'] = user.id
				obj.put()
			else:
				try:
					obj.delete()
				except:
					self.log.exception('Could not delete %s' % obj)
					raise
		else:
			if hasattr(obj, 'deleted'):
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
		from botoweb.db.query import Query
		from boto.s3.key import Key

		# Figure out what format to send
		format = None
		if "." in property:
			property,format = property.split(".")
		else:
			format = request.accept.best_match(['application/xml', 'application/json']).split('/')[-1]


		# Some leakage here of authorizations, but 
		# I'm not quite sure how to handle this elsewhere
		if request.user and not request.user.has_auth('GET', obj.__class__.__name__, property):
			self.log.warn("User: %s does not have read access to %s.%s" %  (request.user.username, obj.__class__.__name__, property))
			raise Forbidden()

		try:
			val = getattr(obj, property)
		except AttributeError, e:
			raise BadRequest("%s has no attribute %s" % (obj.__class__.__name__, property))
		except Exception, e:
			raise BadRequest(str(e))
		if type(val) in (str, unicode):
			if format is None or format == 'txt':
				response.content_type = "text/plain"
			elif format == 'xml':
				response.content_type = 'text/xml'
			response.write(str(val))
		elif isinstance(val, Blob):
			response.content_type = 'text/plain'
			#if format == 'xml':
			#	response.content_type = 'text/xml'
			try:
				response.write(str(val))
			except:
				response.write(val.read())
		elif isinstance(val, Key):
			response.content_type = val.content_type
			response.write(val.get_contents_as_string())
		elif isinstance(val, Query) or isinstance(val, BatchItemFetcher):
			objs = self.build_query(request.GET.mixed(), query=val, user=request.user)
			response.headers['X-Result-Count'] = str(objs.count())
			response.write("<%s>" % property)

			page = False
			if(objs.limit == None):
				objs.limit = self.page_size
				page = True
			for o in objs:
				response.write(xmlize.dumps(o))
			params = request.GET.mixed()
			if page and objs.next_token:
				if params.has_key("next_token"):
					del(params['next_token'])
				self_link = '%s%s%s/%s/%s?%s' % (request.real_host_url, request.base_url, request.script_name, obj.id, property, urllib.urlencode(params).replace("&", "&amp;"))
				params['next_token'] = objs.next_token
				next_link = '%s%s%s/%s/%s?%s' % (request.real_host_url, request.base_url, request.script_name, obj.id, property, urllib.urlencode(params).replace("&", "&amp;"))
				response.write('<link type="text/xml" rel="next" href="%s"/>' % (next_link))
				response.write('<link type="text/xml" rel="self" href="%s"/>' % (self_link))
			response.write("</%s>" % property)
		elif val:
			if format in [None, "xml"]:
				response.content_type = "text/xml"
				if hasattr(val, "to_xml"):
					response.write(val.to_xml())
				else:
					response.write("<response>%s</response>" % xmlize.dumps(val, property))
			elif format == "json":
				response.content_type = "application/json"
				if hasattr(val, "to_json"):
					response.write(val.to_json())
				elif hasattr(val, "to_dict"):
					response.write(json.dumps(val.to_dict()))
				else:
					response.write(json.dumps(val))
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
			setattr(obj, "_indexed_%s" % property, index_string(val.upper))
			self.log.debug("Indexed: %s" % property)

		obj.modified_by = request.user
		obj.modified_at = datetime.utcnow()
		obj.put()
		self.log.info("Updated %s<%s>.%s" % (obj.__class__.__name__, obj.id, property))
		# 204 is the proper status code but it does not allow the onload event
		# to fire in the browser, which expects a 200. Without the onload event
		# we cannot determine when an upload is complete.
		#response.set_status(204)
		return response

NO_SEND_PROPS = [ "CalculatedProperty" ]
class JSONWrapper(object):
	"""JSON Wrapper"""

	def __init__(self, objs, user, base_url=None, params=None):
		"""Create this JSON wrapper"""
		self.objs = objs
		self.user = user
		self.start_time = time()
		self.next_token = None
		self.base_url = base_url
		self.params = params
		self.closed = False

	def __iter__(self):
		return self

	def next(self):
		"""Get the next item in this JSON array"""
		if self.closed:
			raise StopIteration()
		ret = ""
		if hasattr(self.objs, "next_token") and self.objs.next_token and self.objs.next_token != self.next_token:
			self.next_token = self.objs.next_token
			ret += json.dumps({"__type__": "__meta__", "next_token": self.next_token, "next_url": self.generate_url(self.next_token)}) + "\r\n"
		try:
			obj = self.objs.next()
			cls_name = obj.__class__.__name__
			s = {
				"__type__": cls_name,
				"__id__": obj.id
			}
			for prop in obj.properties():
				# Check for user authorizations before saving it to the array
				if prop.name and not prop.name.startswith("_")  and not prop.__class__.__name__ in NO_SEND_PROPS and (not self.user or self.user.has_auth("GET", cls_name, prop.name)):
					s[prop.name] = self.encode(getattr(obj, prop.name), prop)
			ret += json.dumps(s) + "\r\n"
			return ret
		except StopIteration:
			self.closed = True
			return json.dumps({"__type__": "__meta__", "next_token": "", "next_url": ""}) + "\r\n\r\n"

	def encode(self, val, prop):
		"""Encode a property to a JSON serializable type"""
		from botoweb.encoder import encode
		return encode(val)

	def generate_url(self, next_token=None):
		"""Generate a URL for more results"""
		params = self.params
		if next_token != None:
			self.params['next_token'] = next_token
		return "%s?%s" % (self.base_url, urllib.urlencode(params))

class CSVWrapper(object):
	"""CSV Wrapper"""

	def __init__(self, objs, user, db_class):
		"""Create this JSON wrapper"""
		self.objs = objs
		self.user = user
		self.db_class = db_class
		self.start_time = time()
		self.headers = None
		self.props = {}

	def __iter__(self):
		return self

	def next(self):
		"""Get the next item in this CSV"""
		from StringIO import StringIO
		import csv
		ret = StringIO()
		output = csv.writer(ret)
		# If we haven't yet set the headers, lets initialize them
		try:
			obj = self.objs.next()
			cls_name = obj.__class__.__name__
			if self.headers == None:
				self.headers = {"__class__": "Model", "id": "ID"}
				for prop in self.db_class.properties():
					# Check for user authorizations before saving it to the array
					if prop.name and not prop.name.startswith("_")  and not prop.__class__.__name__ in NO_SEND_PROPS and self.user.has_auth("GET", cls_name, prop.name):
						self.headers[prop.name] = prop.verbose_name
						self.props[prop.name] = prop
				output.writerow(self.headers.values())
			s = [self.encode(getattr(obj, h), h) for h in self.headers.keys()]
			output.writerow(s)
			return ret.getvalue()
		except StopIteration:
			self.log.info("Rendered in: %.02f seconds" % (time() - self.start_time))
			raise

	def encode(self, val, prop_name):
		"""Encode a property to a CSV serializable type"""
		if prop_name == "__class__":
			return val.__name__
		try:
			return str(val)
		except:
			return unicode(val).encode("ascii", "ignore")
