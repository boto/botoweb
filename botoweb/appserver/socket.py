"""
Author: Chris Moyer <cmoyer@newstex.com>
SocketIO Basic functionality
"""

from botoweb.request import Request
from botoweb.response import Response
from botoweb.appserver.wsgi_layer import WSGILayer
from botoweb.exceptions import HTTPException
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
import logging
log = logging.getLogger('botoweb.appserver.socketio')

import json
import urllib

from gevent.coros import Semaphore

class BWNamespace(BaseNamespace):
	"""Simple BotoWeb Namespace which routes requests directly
	to the application object"""

	def initialize(self, *args, **kwargs):
		self.headers = {}
		self.cache_lock = Semaphore()
		return BaseNamespace.initialize(self, *args, **kwargs)

	def _request(self, method, args, path='/'):
		"""Generic Request
		All request args must contain at least:
		:msg_id: The message ID to correspond back when returning a response
		:model: The name of the model corresponding to this request
			(this corresponds to the "name" attribtute in handlers.yaml)

		Requests may also contain:
		:id: ID of the object to request
		:params: Any GET/POST parameters to pass in. The proper parameters are always
			used determined by what request type this is
		:post: POST parameters to send (ignores request method)
		:get: GET parameters to send (ignores request method)
		"""
		try:
			# Sanity Checking
			if args:
				msg_id = args.get('msg_id')
				if not args.has_key('msg_id'):
					self.emit('err', {'code': 400, 'msg': 'No msg_id provided'})
					return
				if not args.has_key('model'):
					self.emit('err', {'code': 400, 'msg': 'No model provided'})
					return

				path = self.request['routes'].get(args['model'], args['model'])
				log.info('%s: %s => %s' % (method, args['model'], path))
			else:
				log.info('%s %s' % (method, path))
				msg_id = 0

			# Add in any GET/POST parameters
			post_params = None
			get_params = None
			if args:
				if method == 'POST':
					post_params = args.get('params')
				else:
					get_params = args.get('params')
				if args.has_key('get'):
					get_params = args.get('get')
				if args.has_key('post'):
					post_params = args.get('post')

			# Set up the Request and Response
			# objects
			resp = Response()
			environ = self.environ.copy()
			environ['REQUEST_METHOD'] = method.upper()
			if args:
				# If an ID is specified, add that to the path
				if args.has_key('id'):
					path += '/' + args['id']
				# Also allow a parameter
				if args.has_key('param'):
					path += '/' + args['param']

			# Set the path
			environ['PATH_INFO'] = path
			# Add in any GET paramters
			if get_params:
				environ['QUERY_STRING'] = urllib.urlencode(get_params)

			# Set up authorization
			if self.request.has_key('AUTH'):
				username = self.request['AUTH'].get('username')
				password = self.request['AUTH'].get('password')
				auth_header = ':'.join([username, password])
				auth_header = 'BASIC %s' % auth_header.encode('base64')
				environ['HTTP_AUTHORIZATION'] = auth_header
			req = Request(environ)
			req.accept = self.headers.get('accept', req.headers.get('X-Application-Accept', 'application/json'))
			# Add in any POST params
			if post_params:
				req.content_type = 'application/x-www-form-urlencoded'
				req.body = urllib.urlencode(post_params)
				
			for header in self.headers:
				# We already handled the accept header above
				if header == 'accept':
					continue
				req.headers[header] = self.headers[header]

			# Add in any cached items
			with self.cache_lock:
				req.cache = self.session
				if self.session.has_key('user'):
					req._user = self.session['user']

			# Execute the application
			try:
				# Run the request
				self.request['app'].handle(req, resp)

				# Handle any caching
				with self.cache_lock:
					if req.user:
						self.session['user'] = req.user
					for item in req.cache:
						self.session[item] = req.cache[item]

				# Return the response
				if 'json' in resp.content_type:
					for line in resp.app_iter:
						if not self.socket.connected:
							log.error('Client unexpectedly disconnected')
							return
						if line:
							for item in line.split('\r\n'):
								if item:
									data = json.loads(item)
									self.emit('data', {'msg_id': msg_id, 'msg': data})
				else:
					self.emit('data', {'msg_id': msg_id, 'msg': resp.body})
			except HTTPException, e:
				self.emit('err', {'msg_id': msg_id, 'code': e.code, 'msg': str(e)})
				log.error('Error "%s" processing command: %s %s %s' % (str(e), method, args, path))
			except Exception, e:
				self.emit('err', {'msg_id': msg_id, 'code': 500, 'msg': str(e)})
				log.exception('Unhandled Error processing: %s' % args)


		except Exception:
			log.exception('Error processing: %s' % args)

	# Allow custom headers
	def on_HEADER(self, headers):
		for header in headers:
			log.info('HEADER %s = %s' % (header.lower(), headers[header]))
			self.headers[header.lower()] = headers[header]

	# Handle Authentication
	def on_AUTH(self, args):
		"""Auth just sends username/password, which we
		then just build into our request object"""
		with self.cache_lock:
			self.request['AUTH'] = args

	def on_GET(self, args):
		"""GET request"""
		self.spawn(self._request, 'GET', args)

	def on_POST(self, args):
		self.spawn(self._request, 'POST', args)

	def on_PUT(self, args):
		self.spawn(self._request, 'PUT', args)

	def on_DELETE(self, args):
		self.spawn(self._request, 'DELETE', args)

	def on_DESCRIBE(self, args=None):
		self.spawn(self._request, 'GET', args, path='/')


class SocketIOLayer(WSGILayer):
	"""SocketIO WSGI Layer.
	This routes all requests to the application
	but captures socket.io requests routing them
	through the SocketIONamespace
	"""
	namespace_class = BWNamespace

	def update(self, env):
		super(SocketIOLayer, self).update(env)
		# Bootstrap the handlers
		self.routes = {}
		for route in self.env.config.get('botoweb', 'handlers'):
			if route.get('name'):
				self.routes[route['name']] = route['url'].strip('$')

	def __call__(self, environ, start_response):
		"""Intercept Socket.IO requests"""
		path = environ['PATH_INFO'].strip('/')
		if path.startswith('socket.io'):
			socketio_manage(environ, {'':BWNamespace}, request={'app': self.app, 'routes': self.routes})
		else:
			# All other requests get routed to the application
			return self.app(environ, start_response)
