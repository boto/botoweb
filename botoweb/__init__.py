# Copyright (c) 2008-2014 Chris Moyer http://coredumped.org
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
__version__ = '1.5.0'
env = None
import logging
log = logging.getLogger('botoweb')

HTTP_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
ISO8601 = '%Y-%m-%dT%H:%M:%SZ'

def set_env(name, conf=None):
	from botoweb.environment import Environment
	env = Environment(name, conf)
	import boto
	boto.config = env.config
	import botoweb
	botoweb.env = env
	
	set_user_class()
	set_cache()

	return env

#
# Arecibo Error Reporting
# 
def report_exception(e, req=None, priority=None, msg=None, req_body=None, uri=None):
	"""Report an exception, using arecibo if available"""
	import traceback
	if msg == None:
		msg = str(e)
	report(msg=msg, status=e.code, name=e.__class__.__name__, tb=traceback.format_exc(), req=req, priority=priority, req_body=req_body, uri=uri)
	# If NewRelic is configured, we use that as well:
	try:
		import botoweb
		if botoweb.env.dist.has_resource('conf/newrelic.cfg'):
			import newrelic.agent
			import sys
			params = {}
			if req:
				params['uri'] = req.real_path_url
				params['path'] = req.path_info
				params['body'] = req.body
				params['remote_ip'] = req.headers.get('X-Forwarded-For', req.remote_addr)
				params['method'] = req.method
			if uri:
				params['uri'] = uri
			if priority:
				params['priority'] = priority
			if not hasattr(e, '__name__'):
				e.__name__ = e.__class__.__name__
			newrelic.agent.record_exception(e, msg, sys.exc_info()[2], params=params)
			log.info('logged exception to newrelic')
	except:
		log.exception('Could not log to newrelic')
	

def report(msg, status=400, name=None, tb=None, req=None, priority=None, req_body=None, uri=None):
	"""Generic Error notification"""
	import boto
	from datetime import datetime
	arecibo = None
	if boto.config.get('arecibo', 'public_key'):
		try:
			from arecibo import post
			arecibo = post()
			arecibo.server(url=boto.config.get('arecibo', 'url'))
			arecibo.set('account', boto.config.get('arecibo', 'public_key'))
		except:
			arecibo = None

	method = ''
	remote_ip = ''
	path = uri
	if req:
		uri = req.real_path_url
		path = req.path_info
		req_body = req.body
		remote_ip = req.headers.get('X-Forwarded-For', req.remote_addr)
		method = req.method

	if arecibo:
		log.info('Arecibo Log: %s' % msg)
		try:
			arecibo.set('status', status)
			arecibo.set('msg', msg)
			arecibo.set('server', boto.config.get('Instance', 'public-ipv4'))
			arecibo.set('timestamp', datetime.utcnow().isoformat());

			if name:
				arecibo.set('type', name)

			if priority:
				arecibo.set('priority', str(priority))

			if uri:
				arecibo.set('url', uri)
			if req_body:
				arecibo.set('request', req_body)
			if tb:
				arecibo.set('traceback', tb)

			if req:
				if req.user:
					arecibo.set('username', req.user.username)
				if req.environ.has_key('HTTP_USER_AGENT'):
					arecibo.set('user_agent', req.environ['HTTP_USER_AGENT'])
				if remote_ip:
					arecibo.set('ip', remote_ip)
			arecibo.send()
		except Exception, e:
			log.critical('Exception sending to arecibo: %s' % e)
	else:
		# Only log Server errors as ERROR, everything
		# else is just an informative exception
		if status < 500:
			log.info('%s %s: %s' % (method, path, msg))
		else:
			log.error('%s %s: %s' % (method, path, msg))

def set_user_class():

	import botoweb
	from botoweb.resources.user import User
	botoweb.user = User

	module_path = None

	if botoweb.env:
		module_path = botoweb.env.config.get('app', 'user_class', False)

	if module_path:
		try:
			path = '.'.join(module_path.split('.')[:-1])
			class_name = module_path.split('.')[-1]
			mod = __import__(path, fromlist=[class_name])
			botoweb.user = getattr(mod, class_name)
		except ImportError:
			log.warning("Couldn't import user class %s" % module_path)

	return botoweb.user

def set_cache():

	import botoweb
	servers = []
	if env and env.config.has_section('cache'):
		import memcache
		for server in env.config['cache']['servers']:
			servers.append('%s:%s' % (server['host'], server['port']))
		botoweb.memc = memcache.Client(servers)
	else:
		botoweb.memc = None
		
	return botoweb.memc

from botoweb.resources.user import User
user = User
memc = None
