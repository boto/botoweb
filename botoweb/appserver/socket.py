"""
Author: Chris Moyer <cmoyer@newstex.com>
SocketIO Basic functionality
"""

from botoweb.appserver.wsgi_layer import WSGILayer
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
import logging
log = logging.getLogger('botoweb.appserver.socketio')

class BWNamespace(BaseNamespace):
	"""Simple BotoWeb Namespace which routes requests directly
	to the application object"""

	def on_GET(self, model, id=None, args=None):
		"""GET request"""
		log.info('GET %s, %s, %s' % (model, id, args))

class SocketIOLayer(WSGILayer):
	"""SocketIO WSGI Layer.
	This routes all requests to the application
	but captures socket.io requests routing them
	through the SocketIONamespace
	"""

	def __call__(self, environ, start_response):
		"""Intercept Socket.IO requests"""
		path = environ['PATH_INFO'].strip('/')
		if path.startswith('socket.io'):
			socketio_manage(environ, {'':BWNamespace}, {'app': self.app})
		else:
			# All other requests get routed to the application
			return self.app(environ, start_response)
