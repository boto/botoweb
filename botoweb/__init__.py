# Copyright (c) 2008 Chris Moyer http://coredumped.org
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
__version__ = "0.7"
env = None
import logging
log = logging.getLogger("botoweb")

def set_env(name, conf=None):
	from botoweb.environment import Environment
	env = Environment(name, conf)
	import boto
	boto.config = env.config
	import botoweb
	botoweb.env = env
	return env

#
# Arecibo Error Reporting
# 
def report_exception(e, req=None, priority=None, msg=None, req_body=None, uri=None):
	"""Report an exception, using arecibo if available"""
	import traceback
	log.info("Report Exception: %s" % e)
	if msg == None:
		msg = e.message
	report(msg=msg, status=e.code, name=e.__class__.__name__, tb=traceback.format_exc(), req=req, priority=priority, req_body=req_body, uri=uri)

def report(msg, status=400, name=None, tb=None, req=None, priority=None, req_body=None, uri=None):
	"""Generic Error notification"""
	log.info("Arecibo Log: %s" % msg)
	import boto
	from datetime import datetime
	try:
		from arecibo import post
		arecibo = post()
		arecibo.server(url=boto.config.get("arecibo", "url"))
		arecibo.set("account", boto.config.get("arecibo", "public_key"))
	except:
		arecibo = None

	if arecibo:
		try:
			arecibo.set("status", status)
			arecibo.set("msg", msg)
			arecibo.set("server", boto.config.get("Instance", "public-ipv4"))
			arecibo.set("timestamp", datetime.utcnow().isoformat());

			if name:
				arecibo.set("type", name)

			if priority:
				arecibo.set("priority", str(priority))

			if req:
				uri = req.real_path_url
				req_body = req.body
				if req.user:
					arecibo.set("username", req.user.username)
				if req.environ.has_key("HTTP_USER_AGENT"):
					arecibo.set("user_agent", req.environ['HTTP_USER_AGENT'])
				if req.remote_addr:
					arecibo.set("ip", req.remote_addr)
			if uri:
				arecibo.set("url", uri)
			if req_body:
				arecibo.set("request", req_body)
			if tb:
				arecibo.set("traceback", tb)

			arecibo.send()
		except Exception, e:
			log.critical("Exception sending to arecibo: %s" % e)
	else:
		log.warn("Warning, Arecibo not set up")
		log.warn(msg)
