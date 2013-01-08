# Author: Chris Moyer
# Exception classes
from botoweb import status
from xml.dom.minidom import getDOMImplementation

class TimeDecodeError(Exception):
	pass

class HTTPException(Exception):
	"""
	Base HTTP Exception class
	"""

	def __init__(self, code, message = None, description = None):
		self.code = code
		self.message = message
		self.description = description
		Exception.__init__(self)

	def __str__(self):
		return "%s %s\n%s" % (self.message, self.code, self.description)

	def to_xml(self):
		"""
		Turn this into an XML
		document
		"""
		impl = getDOMImplementation()
		doc = impl.createDocument(None, 'Exception', None)

		rootNode = doc.documentElement

		type_node = doc.createElement("type")
		text_node = doc.createTextNode(self.__class__.__name__)
		type_node.appendChild(text_node)
		rootNode.appendChild(type_node)

		type_node = doc.createElement("code")
		text_node = doc.createTextNode(str(self.code))
		type_node.appendChild(text_node)
		rootNode.appendChild(type_node)

		type_node = doc.createElement("message")
		text_node = doc.createTextNode(self.message)
		type_node.appendChild(text_node)
		rootNode.appendChild(type_node)

		type_node = doc.createElement("description")
		text_node = doc.createTextNode(self.description)
		type_node.appendChild(text_node)
		rootNode.appendChild(type_node)

		return doc
	
	def to_json(self):
		"""Turn this into a JSON representation"""
		import json
		r = {}
		r['__type__'] = "Exception"
		r['type'] = self.__class__.__name__
		r['code'] = self.code
		r['message'] = self.message
		r['description'] = self.description
		return json.dumps(r)

# 3xx Redirection
class HTTPRedirect(HTTPException):
	"""
	These are redirections, not all out failures
	"""
	def __init__(self, url, code, message=None, description=None):
		self.url = url
		HTTPException.__init__(self, code, message, description)

class TemporaryRedirect(HTTPRedirect):
	def __init__(self, url, message=status.message[status.HTTP_TEMPORARY_REDIRECT], description=status.description[status.HTTP_TEMPORARY_REDIRECT]):
		HTTPRedirect.__init__(self, url, status.HTTP_TEMPORARY_REDIRECT, message, description)

class SeeOther(HTTPRedirect):
	def __init__(self, url, message=status.message[status.HTTP_SEE_OTHER], description=status.description[status.HTTP_SEE_OTHER]):
		HTTPRedirect.__init__(self, url, status.HTTP_SEE_OTHER, message, description)

# 4xx Client Errors
class BadRequest(HTTPException):
	def __init__(self, message=status.message[status.HTTP_BAD_REQUEST], description=status.description[status.HTTP_BAD_REQUEST]):
		HTTPException.__init__(self, status.HTTP_BAD_REQUEST, message, description)

class Unauthorized(HTTPException):
	def __init__(self, message=status.message[status.HTTP_UNAUTHORIZED], description=status.description[status.HTTP_UNAUTHORIZED]):
		HTTPException.__init__(self, status.HTTP_UNAUTHORIZED, message, description)

class PaymentRequired(HTTPException):
	def __init__(self, message=status.message[status.HTTP_PAYMENT_REQUIRED], description=status.description[status.HTTP_PAYMENT_REQUIRED]):
		HTTPException.__init__(self, status.HTTP_PAYMENT_REQUIRED, message, description)

class Forbidden(HTTPException):
	def __init__(self, message=status.message[status.HTTP_FORBIDDEN], description=status.description[status.HTTP_FORBIDDEN]):
		HTTPException.__init__(self, status.HTTP_FORBIDDEN, message, description)

class NotFound(HTTPException):
	def __init__(self, message=status.message[status.HTTP_NOT_FOUND], description= status.description[status.HTTP_NOT_FOUND], url=None):
		if url:
			description = "URL Not Found: %s" % url
		self.url = url
		HTTPException.__init__(self, status.HTTP_NOT_FOUND, message,description)

class MethodNotAllowed(HTTPException):
	def __init__(self, message=status.message[status.HTTP_METHOD_NOT_ALLOWED], description= status.description[status.HTTP_METHOD_NOT_ALLOWED]):
		HTTPException.__init__(self, status.HTTP_METHOD_NOT_ALLOWED, message,description)

class NotAcceptable(HTTPException):
	def __init__(self, message=status.message[status.HTTP_NOT_ACCEPTABLE], description= status.description[status.HTTP_NOT_ACCEPTABLE]):
		HTTPException.__init__(self, status.HTTP_NOT_ACCEPTABLE, message,description)

class ProxyAuthRequired(HTTPException):
	def __init__(self, message=status.message[status.HTTP_PROXY_AUTH_REQUIRED], description= status.description[status.HTTP_PROXY_AUTH_REQUIRED]):
		HTTPException.__init__(self, status.HTTP_PROXY_AUTH_REQUIRED, message,description)

class RequestTimeout(HTTPException):
	def __init__(self, message=status.message[status.HTTP_REQUEST_TIMEOUT], description= status.description[status.HTTP_REQUEST_TIMEOUT]):
		HTTPException.__init__(self, status.HTTP_REQUEST_TIMEOUT, message,description)

class Conflict(HTTPException):
	def __init__(self, message=status.message[status.HTTP_CONFLICT], description= status.description[status.HTTP_CONFLICT]):
		HTTPException.__init__(self, status.HTTP_CONFLICT, message,description)

class Gone(HTTPException):
	def __init__(self, message=status.message[status.HTTP_GONE], description= status.description[status.HTTP_GONE]):
		HTTPException.__init__(self, status.HTTP_GONE, message,description)

class LengthRequired(HTTPException):
	def __init__(self, message=status.message[status.HTTP_LENGTH_REQUIRED], description= status.description[status.HTTP_LENGTH_REQUIRED]):
		HTTPException.__init__(self, status.HTTP_LENGTH_REQUIRED, message,description)

class PreconditionFailed(HTTPException):
	def __init__(self, message=status.message[status.HTTP_PRECONDITION_FAILED], description= status.description[status.HTTP_PRECONDITION_FAILED]):
		HTTPException.__init__(self, status.HTTP_PRECONDITION_FAILED, message,description)

class RequestTooLarge(HTTPException):
	def __init__(self, message=status.message[status.HTTP_REQUEST_TOO_LARGE], description= status.description[status.HTTP_REQUEST_TOO_LARGE]):
		HTTPException.__init__(self, status.HTTP_REQUEST_TOO_LARGE, message,description)

class URITooLarge(HTTPException):
	def __init__(self, message=status.message[status.HTTP_REQUEST_URI_TOO_LARGE], description= status.description[status.HTTP_REQUEST_URI_TOO_LARGE]):
		HTTPException.__init__(self, status.HTTP_REQUEST_URI_TOO_LARGE, message,description)

class UnsuportedMedia(HTTPException):
	def __init__(self, message=status.message[status.HTTP_UNSUPORTED_MEDIA], description= status.description[status.HTTP_UNSUPORTED_MEDIA]):
		HTTPException.__init__(self, status.HTTP_UNSUPORTED_MEDIA, message,description)

class RequestNotSatisfiable(HTTPException):
	def __init__(self, message=status.message[status.HTTP_REQUEST_NOT_SATISFIABLE], description= status.description[status.HTTP_REQUEST_NOT_SATISFIABLE]):
		HTTPException.__init__(self, status.HTTP_REQUEST_NOT_SATISFIABLE, message,description)

class ExpectationFailed(HTTPException):
	def __init__(self, message=status.message[status.HTTP_EXPECTATION_FAILED], description= status.description[status.HTTP_EXPECTATION_FAILED]):
		HTTPException.__init__(self, status.HTTP_EXPECTATION_FAILED, message,description)


# 5xx Server Errors
class InternalServerError(HTTPException):
	def __init__(self, message=status.message[status.HTTP_INTERNAL_SERVER_ERROR], description= status.description[status.HTTP_INTERNAL_SERVER_ERROR]):
		HTTPException.__init__(self, status.HTTP_INTERNAL_SERVER_ERROR, message,description)

class NotImplemented(HTTPException):
	def __init__(self, message=status.message[status.HTTP_NOT_IMPLEMENTED], description= status.description[status.HTTP_NOT_IMPLEMENTED]):
		HTTPException.__init__(self, status.HTTP_NOT_IMPLEMENTED, message,description)

class BadGateway(HTTPException):
	def __init__(self, message=status.message[status.HTTP_BAD_GATEWAY], description= status.description[status.HTTP_BAD_GATEWAY]):
		HTTPException.__init__(self, status.HTTP_BAD_GATEWAY, message,description)

class ServiceUnavailable(HTTPException):
	def __init__(self, message=status.message[status.HTTP_SERVICE_UNAVAILABLE], description= status.description[status.HTTP_SERVICE_UNAVAILABLE]):
		HTTPException.__init__(self, status.HTTP_SERVICE_UNAVAILABLE, message,description)

class GatewayTimeout(HTTPException):
	def __init__(self, message=status.message[status.HTTP_GATEWAY_TIMEOUT], description= status.description[status.HTTP_GATEWAY_TIMEOUT]):
		HTTPException.__init__(self, status.HTTP_GATEWAY_TIMEOUT, message,description)

class VersionNotSupported(HTTPException):
	def __init__(self, message=status.message[status.HTTP_VERSION_NOT_SUPPORTED], description= status.description[status.HTTP_VERSION_NOT_SUPPORTED]):
		HTTPException.__init__(self, status.HTTP_VERSION_NOT_SUPPORTED, message,description)

