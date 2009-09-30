# Author: Chris Moyer
# HTTP Status code definitions, from RFC2616

# 1xx Informational
HTTP_CONTINUE = 100
HTTP_SWITCHING_PROTOCOLS = 101

# 2xx Successful
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_ACCEPTED = 202
HTTP_NON_AUTHORITATIVE = 203
HTTP_NO_CONTENT = 204
HTTP_RESET_CONTENT = 205
HTTP_PARTIAL_CONTENT = 206

# 3xx Redirection
HTTP_MULTIPLE_CHOICES = 300
HTTP_MOVED_PERMANENT = 301
HTTP_MOVED_TEMPORARY = HTTP_FOUND = 302
HTTP_SEE_OTHER = 303
HTTP_NOT_MODIFIED = 304
HTTP_USE_PROXY = 305
HTTP_TEMPORARY_REDIRECT = 307


# 4xx Client Errors
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_PAYMENT_REQUIRED = 402
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_NOT_ACCEPTABLE = 406
HTTP_PROXY_AUTH_REQUIRED = 407
HTTP_REQUEST_TIMEOUT = 408
HTTP_CONFLICT = 409
HTTP_GONE = 410
HTTP_LENGTH_REQUIRED = 411
HTTP_PRECONDITION_FAILED = 412
HTTP_REQUEST_TOO_LARGE = 413
HTTP_REQUEST_URI_TOO_LARGE = 414
HTTP_UNSUPORTED_MEDIA = 415
HTTP_REQUEST_NOT_SATISFIABLE = 416
HTTP_EXPECTATION_FAILED = 417

# 5xx Server Errors
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_NOT_IMPLEMENTED = 501
HTTP_BAD_GATEWAY = 502
HTTP_SERVICE_UNAVAILABLE = 503
HTTP_GATEWAY_TIMEOUT = 504
HTTP_VERSION_NOT_SUPPORTED = 505

message = {
	HTTP_CONTINUE: 'Continue',
	HTTP_SWITCHING_PROTOCOLS: 'Switching Protocols',
	HTTP_OK: 'OK',
	HTTP_CREATED: 'Created',
	HTTP_ACCEPTED: 'Accepted',
	HTTP_NON_AUTHORITATIVE: 'Non-Authoritative Information',
	HTTP_NO_CONTENT: 'No Content',
	HTTP_RESET_CONTENT: 'Reset Content',
	HTTP_PARTIAL_CONTENT: 'Partial Content',

	HTTP_MULTIPLE_CHOICES: 'Multiple Choices',
	HTTP_MOVED_PERMANENT: 'Moved Permanently',
	HTTP_FOUND: 'Moved Temporarily',
	HTTP_SEE_OTHER: 'See Other',
	HTTP_NOT_MODIFIED: 'Not Modified',
	HTTP_USE_PROXY: 'Use Proxy',
	HTTP_TEMPORARY_REDIRECT: 'Temporary Redirect',

	HTTP_BAD_REQUEST: 'Bad Request',
	HTTP_UNAUTHORIZED: 'Unauthorized',
	HTTP_PAYMENT_REQUIRED: 'Payment Required',
	HTTP_FORBIDDEN: 'Forbidden',
	HTTP_NOT_FOUND: 'Page Not Found',
	HTTP_METHOD_NOT_ALLOWED: 'Method Not Allowed',
	HTTP_NOT_ACCEPTABLE: 'Not Acceptable',
	HTTP_PROXY_AUTH_REQUIRED: 'Proxy Authentication Required',
	HTTP_REQUEST_TIMEOUT: 'Request Time-out',
	HTTP_CONFLICT: 'Conflict',
	HTTP_GONE: 'Gone',
	HTTP_LENGTH_REQUIRED: 'Length Required',
	HTTP_PRECONDITION_FAILED: 'Precondition Failed',
	HTTP_REQUEST_TOO_LARGE: 'Request Entity Too Large',
	HTTP_REQUEST_URI_TOO_LARGE: 'Request-URI Too Large',
	HTTP_UNSUPORTED_MEDIA: 'Unsupported Media Type',
	HTTP_REQUEST_NOT_SATISFIABLE: 'Requested Range Not Satisfiable',
	HTTP_EXPECTATION_FAILED: 'Expectation Failed',

	HTTP_INTERNAL_SERVER_ERROR: 'Internal Server Error',
	HTTP_NOT_IMPLEMENTED: 'Not Implemented',
	HTTP_BAD_GATEWAY: 'Bad Gateway',
	HTTP_SERVICE_UNAVAILABLE: 'Service Unavailable',
	HTTP_GATEWAY_TIMEOUT: 'Gateway Time-out',
	HTTP_VERSION_NOT_SUPPORTED: 'HTTP Version not supported'
}

description = {
	HTTP_CONTINUE: 'Nothing to see here, move along',
	HTTP_SWITCHING_PROTOCOLS: 'I\'d like to speak a different language',
	HTTP_OK: 'Everything is OK',
	HTTP_CREATED: 'Object has been created',
	HTTP_ACCEPTED: 'Input has been accepted',
	HTTP_NON_AUTHORITATIVE: 'Non-Authoritative Information',
	HTTP_NO_CONTENT: 'I have nothing to say',
	HTTP_RESET_CONTENT: 'Reset Content',
	HTTP_PARTIAL_CONTENT: 'Partial Content',

	HTTP_MULTIPLE_CHOICES: 'Multiple Choices',
	HTTP_MOVED_PERMANENT: 'Moved Permanently',
	HTTP_FOUND: 'Moved Temporarily',
	HTTP_SEE_OTHER: 'See Other',
	HTTP_NOT_MODIFIED: 'Not Modified',
	HTTP_USE_PROXY: 'Use Proxy',
	HTTP_TEMPORARY_REDIRECT: 'Temporary Redirect',

	HTTP_BAD_REQUEST: 'Bad Request',
	HTTP_UNAUTHORIZED: 'You are not Authorized to use this service.',
	HTTP_PAYMENT_REQUIRED: 'Payment Required',
	HTTP_FORBIDDEN: 'You don\'t have permission to access this.',
	HTTP_NOT_FOUND: 'You may have mistyped the address or the page may have moved.',
	HTTP_METHOD_NOT_ALLOWED: 'Method Not Allowed',
	HTTP_NOT_ACCEPTABLE: 'Not Acceptable',
	HTTP_PROXY_AUTH_REQUIRED: 'Proxy Authentication Required',
	HTTP_REQUEST_TIMEOUT: 'Request Time-out',
	HTTP_CONFLICT: 'Conflict',
	HTTP_GONE: 'Gone',
	HTTP_LENGTH_REQUIRED: 'Length Required',
	HTTP_PRECONDITION_FAILED: 'Precondition Failed',
	HTTP_REQUEST_TOO_LARGE: 'Request Entity Too Large',
	HTTP_REQUEST_URI_TOO_LARGE: 'Request-URI Too Large',
	HTTP_UNSUPORTED_MEDIA: 'Unsupported Media Type',
	HTTP_REQUEST_NOT_SATISFIABLE: 'Requested Range Not Satisfiable',
	HTTP_EXPECTATION_FAILED: 'Expectation Failed',

	HTTP_INTERNAL_SERVER_ERROR: 'Internal Server Error',
	HTTP_NOT_IMPLEMENTED: 'Not Implemented',
	HTTP_BAD_GATEWAY: 'Bad Gateway',
	HTTP_SERVICE_UNAVAILABLE: 'Service Unavailable',
	HTTP_GATEWAY_TIMEOUT: 'Gateway Time-out',
	HTTP_VERSION_NOT_SUPPORTED: 'HTTP Version not supported'
}
