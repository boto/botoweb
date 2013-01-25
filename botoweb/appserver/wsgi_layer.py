# Copyright (c) 2009 Chris Moyer http://coredumped.org
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
import httplib

import boto
import botoweb
from botoweb.resources.user import User
from botoweb.request import Request
from botoweb.response import Response
from botoweb.exceptions import *

try:
	import simplejson as json
except:
	import json

import uuid
import traceback
import logging
log = logging.getLogger("botoweb")

class WSGILayer(object):
	"""
	Base WSGI Layer. This simply gives us an additional
	few functions that allow this object to be called as a function,
	but also allows us to chain them together without having to re-build
	the request/response objects
	"""
	threadpool = None
	maxthreads = None

	def __init__(self, env, app=None):
		"""
		Initialize this WSGI layer.

		@param env: A botoweb environment object that represents what we're running in
		@type env: botoweb.environment.Environment

		@param app: An optional WSGI layer that this layer is on top of.
		@type app: WSGILayer

		"""
		self.app = app
		self.update(env)

	def __call__(self, environ, start_response):
		"""
		Handles basic one-time-only WSGI setup, and handles
		error catching.
		"""
		resp = Response()
		req = Request(environ)

		try:
			# If there's too many threads already, just toss a
			# ServiceUnavailable to let the user know they should re-connect
			# later
			if self.maxthreads and self.threadpool:
				if len(self.threadpool.working) > self.maxthreads:
					raise ServiceUnavailable("Service Temporarily Overloaded")
			resp = self.handle(req, resp)
		except AssertionError, e:
			resp.set_status(400)
			resp.content_type = "text/plain"
			resp.body = str(e)
		except HTTPRedirect, e:
			resp.set_status(e.code)
			resp.headers['Location'] = str(e.url)
			resp = self.format_exception(e, resp, req)
		except Unauthorized, e:
			resp.set_status(e.code)
			if self.env.config.get("app", "basic_auth", True):
				resp.headers.add("WWW-Authenticate", 'Basic realm="%s"' % self.env.config.get("app", "name", "Boto Web"))
			
			# ajax authorization relies on memcached for session persistence.
			elif self.env.config.get("app", "ajax_auth", False) and botoweb.memc:
				# the session challenge header was set in the request, so
				# assume this is an authentication attempt and check the
				# hashed values provided for the user against what's stored
				# in the db.
				if req.headers.get("X-Session-Challenge", False):
					challenge_id, challenge = req.headers.get("X-Session-Challenge").split(":")
					challenge_hash = req.headers.get("X-Challenge-Hash")
					username = req.headers.get("X-Username")
					stored_challenge = botoweb.memc.get(str(challenge_id))

					if not challenge == stored_challenge:
						resp = self.format_exception(Unauthorized("Invalid challenge."), resp, req)
						return resp(environ, start_response)

					try:
						user = botoweb.user.find(username=username).next()
					except StopIteration:
						resp = self.format_exception(NotFound("Invalid user."), resp, req)
						return resp(environ, start_response)

					if check_challenge(challenge_hash, stored_challenge, str(user.password)):
						# save a session in memcache
						session = {
							"user": user.username,
							"last_ip": req.real_remote_addr,
							"challenge": challenge,
							"session_key": str(uuid.uuid4())
						}
						botoweb.memc.delete(str(challenge_id))
						botoweb.memc.set(session["session_key"], str(json.dumps(session)))
						# this cookie will be encrypted and last until the browser is
						# closed.
						resp.set_cookie("session", session["session_key"], secure=False)
						resp.body = json.dumps(session)
						resp.content_type = "application/json"
						resp.set_status(200)
						return resp(environ, start_response)

				# generate a challenge value, cache it, and transmit it back
				# to the user in the X-Session-Challenge custom header.
				else:
					challenge_id, challenge = generate_challenge()
					botoweb.memc.set(str(challenge_id), str(challenge))
					resp.headers.add("X-Session-Challenge","%s:%s" % (challenge_id, challenge))

			resp = self.format_exception(e, resp, req)
		except HTTPException, e:
			resp.set_status(e.code)
			resp = self.format_exception(e, resp, req)
			log.debug(traceback.format_exc())
			botoweb.report_exception(e, req, priority=5)
		except Exception, e:
			log.exception(e)
			content = InternalServerError(message=e.message)
			resp.set_status(content.code)
			resp = self.format_exception(content, resp, req)
			botoweb.report_exception(content, req, priority=1)

		return resp(environ, start_response)

	def format_exception(self, e, resp, req):
		resp.set_status(e.code)
		if((req and req.file_extension == "json") or self.env.config.get("app", "format") == 'json'):
			resp.content_type = "application/json"
			resp.body = e.to_json()
		else:
			resp.content_type = "text/xml"
			e.to_xml().writexml(resp)
		return resp

	def update(self, env):
		"""
		Update this layer to use a new environment. Minimally
		this will set "self.env = env", but for specific layers
		you may have to undate or invalidate your cache
		"""
		self.env = env

	def handle(self, req, response):
		"""
		This is the function that is called when chainging WSGI layers
		together, it has the request and response objects passed
		into it so they are not re-created.
		"""
		return self.app.handle(req, response)

	def reload(self, *args, **params):
		"""Reload this application"""
		if self.app:
			return self.app.reload()

def generate_challenge():
	import random
	import uuid

	challenge_id = str(uuid.uuid4())
	challenge = random.getrandbits(32)
	return challenge_id, str(challenge)

def check_challenge(challenge_hash, challenge, password_hash):
	import hashlib

	sha512 = hashlib.sha512()
	sha512.update(password_hash + str(challenge))
	check_value = sha512.hexdigest()

	return check_value == challenge_hash