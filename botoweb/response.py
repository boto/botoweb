import webob
from botoweb import status

class Response(webob.Response):
	"""
	Simple Adapter class for a WSGI response object
	This object is pickleable
	"""

	def __init__(self, body=None, **params):
		if body:
			webob.Response.__init__(self, body=body, **params)
		elif params:
			webob.Response.__init__(self, **params)
		else:
			webob.Response.__init__(self, body="")

	def set_status(self, code, message=None):
		"""
		Set the HTTP status of our response

		@param code: HTTP Status Code, should be one of the (appengine.webapp.status)s
		@type code: integer from status.HTTP_*
		"""
		if not message:
			message = status.message[code]
		self.status = "%s %s" % (code, message)

	def clear(self):
		self.body = ""

	def wsgi_write(self, environ, start_response):
		return self.__call__(environ, start_response)

	# Pickle functions
	def __getstate__(self):
		return {"body": self.body, "headers": self.headers, "status": self.status}

	def __setstate__(self, state):
		self.__init__(body=state['body'])
		self.headers = state['headers']
		self.status = state['status']
		return True

	def close(self):
		webob.Response.close(self)
		self.app_iter.close()
