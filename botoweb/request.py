import webob
import cgi
from botoweb.resources.user import User
import logging
log = logging.getLogger("botoweb.request")
from botoweb.response import Response
import time

CACHE_TIMEOUT = 300 # Keep user objects around for 300 seconds (5 minutes)
USER_CACHE = {}
def getCachedUser(username):
	if USER_CACHE.has_key(username):
		user, t = USER_CACHE[username]
		if (time.time() - t) < CACHE_TIMEOUT:
			return user
	return None

def addCachedUser(user):
	USER_CACHE[user.username] = (user, time.time())
	return user

class Request(webob.Request):
	"""We add in a few special extra functions for us here."""
	file_extension = "html"
	ResponseClass = Response

	def __init__(self, environ):
		self._user = None
		charset = 'ascii'
		if environ.get('CONTENT_TYPE', '').find('charset') == -1:
			charset = 'utf-8'

		webob.Request.__init__(self, environ, charset=charset,
			unicode_errors= 'ignore', decode_param_names=True)
		if self.headers.has_key("X-Forwarded-Host"):
			self.real_host_url = "%s://%s" % (self.headers.get("X-Forwarded-Proto", "http"), self.headers.get("X-Forwarded-Host"))
		else:
			self.real_host_url = self.host_url
		self.real_path_url = self.real_host_url + self.path

	def get(self, argument_name, default_value='', allow_multiple=False):
		param_value = self.get_all(argument_name, default_value)
		if allow_multiple:
			return param_value
		else:
			if len(param_value) > 0:
				return param_value[0]
			else:
				return default_value

	def get_all(self, argument_name, default_value=''):
		if self.charset:
			argument_name = argument_name.encode(self.charset)

		try:
			param_value = self.params.getall(argument_name)
		except KeyError:
			return default_value

		for i in range(len(param_value)):
			if isinstance(param_value[i], cgi.FieldStorage):
				param_value[i] = param_value[i].value

		return param_value

	def formDict(self):
		vals = {}
		if self.GET:
			for k in self.GET:
				vals[k] = self.GET[k]
		if self.POST:
			for k in self.POST:
				vals[k] = self.POST[k]
		return vals

	def getUser(self):
		"""
		Get the user from this request object
		@return: User object, or None
		@rtype: User or None
		"""
		if not self._user:
			# Basic Authentication
			auth_header =  self.environ.get("HTTP_AUTHORIZATION")
			if auth_header:
				auth_type, encoded_info = auth_header.split(None, 1)
				if auth_type.lower() == "basic":
					unencoded_info = encoded_info.decode('base64')
					username, password = unencoded_info.split(':', 1)
					log.info("Looking up user: %s" % username)
					user = getCachedUser(username)
					if not user:
						try:
							user = User.find(username=username).next()
							addCachedUser(user)
						except:
							user = None
					if user and user.password == password:
						self._user = user
						return self._user
			# Cookie based Authentication Token
			auth_token_header = self.cookies.get("BW_AUTH_TOKEN")
			if auth_token_header:
				unencoded_info = auth_token_header
				username, auth_token = unencoded_info.split(':', 1)
				if username and auth_token:
					user = getCachedUser(username)
					if not user or not user.auth_token == unencoded_info:
						try:
							user = User.find(username=username).next()
							addCachedUser(user)
						except:
							user = None
					if user and user.auth_token == unencoded_info:
						self._user = user
						return self._user
			# JanRain Authentication token
			jr_auth_token = self.POST.get("token")
			if jr_auth_token:
				import urllib, urllib2, json, boto
				api_params = {
					"token": jr_auth_token,
					"apiKey": boto.config.get("JanRain", "api_key"),
					"format": "json"
				}
				http_response = urllib2.urlopen(boto.config.get("JanRain", "url"), urllib.urlencode(api_params))
				auth_info = json.loads(http_response.read())
				if auth_info['stat'] == "ok":
					profile = auth_info['profile']
					identifier = profile['identifier']
					email = profile.get("verifiedEmail")
					try:
						user = User.find(oid=identifier).next()
					except:
						try:
							if email:
								user = User.find(email=email).next()
						except:
							user = None

					if user:
						self._user = user

						# Set up an Auth Token
						bw_auth_token = "%s:%s" % (user.username, jr_auth_token)
						self.cookies['BW_AUTH_TOKEN'] = bw_auth_token
						user.auth_token = bw_auth_token
						user.put()
						addCachedUser(user)
				else:
					boto.log.warn("An error occured trying to authenticate the user: %s" % auth_info['err']['msg'])

		return self._user

	user = property(getUser, None, None)

	def get_base_url(self):
		return self.headers.get("X-Forwarded-URL", "")
	base_url = property(get_base_url, None, None)
