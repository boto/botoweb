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
PASSWORD_TEMPLATE = """<html>
	<body>
		<h3>%(name)s, your %(appname)s password has been reset!</h3>
		<p>Your username is: <b>%(username)s</b></p>
		<p>Your new password is: <b>%(password)s</b></p>
		<p>You can log in at: <a href="%(applink)s">%(applink)s</a></p>
	</body>
</html>
"""
from boto.sdb.db.model import Model
from boto.sdb.db import property

class User(Model):
	"""Simple user object"""
	username = property.StringProperty(verbose_name="Username", unique=True)
	name = property.StringProperty(verbose_name="Name")
	_indexed_name = property.StringProperty()
	email = property.StringProperty(verbose_name="Email Adress")
	auth_groups = property.ListProperty(str, verbose_name="Authorization Groups")
	password = property.PasswordProperty(verbose_name="Password")
	auth_token = property.StringProperty(verbose_name="Authentication Token")
	authorizations = None


	# These fields are easy to add in
	created_at = property.DateTimeProperty(auto_now_add=True, verbose_name="Created Date")
	modified_at = property.DateTimeProperty(verbose_name="Last Modified Date")
	deleted = property.BooleanProperty(verbose_name="Deleted")
	deleted_at = property.DateTimeProperty(verbose_name="Deleted Date")
	sys_modstamp = property.DateTimeProperty(auto_now=True)

	def __str__(self):
		return self.name

	def notify(self, subject, body=''):
		"""Send notification to this user

		@param subject: Subject for this notification
		@type subject: str

		@param body: The message to send you
		@type body: str
		"""
		import boto.utils
		boto.utils.notify(subject=subject, html_body=body, to_string=self.email, append_instance_id=False)

	def generate_password(self, length=10):
		"""Generate and return a random password
		:param length: the optional length of the password (default 10
		:type length: int
		"""
		import boto, urllib2
		url = "https://www.random.org/cgi-bin/randstring?num=1&len=%s&digits=on&upperalpha=on&loweralpha=on&unique=on&format=text&rnd=new" % (length)
		headers = {"User-Agent": "%s %s (%s)" % (boto.config.get("app", "name", "botoweb"), boto.config.get("app", "version", "0.1"), boto.config.get("app", "admin_email", ""))}
		req = urllib2.Request(url, None, headers)
		hand = urllib2.urlopen(req)
		return hand.read().strip()


	def send_password(self, app_link):
		"""Send the user a random password"""
		import boto
		passwd = self.generate_password()
		self.password = passwd
		self.put()
		args = {
			"appname": boto.config.get("app", "name", "botoweb"),
			"applink": app_link,
			"password": passwd,
			"name": self.name,
			"username": self.username
		}
		self.notify("[%s] Password Reset" % boto.config.get("app", "name", "botoweb"), PASSWORD_TEMPLATE % args)

	def has_auth_group(self, group):
		return (group in self.auth_groups)

	def has_auth_group_ctx(self, ctx, group):
		return self.has_auth_group(group)

	def load_auths(self):
		"""Load up all the authorizations this user has"""
		from botoweb.resources.authorization import Authorization
		self.authorizations = {
			"*": {"*": {"*": False} },
			"": {"": {"": False} }
		}
		query = Authorization.all()
		query.filter("auth_group =", self.auth_groups)
		for auth in query:
			if not self.authorizations.has_key(auth.method):
				self.authorizations[auth.method] = {}
			if not self.authorizations[auth.method].has_key(auth.obj_name):
				self.authorizations[auth.method][auth.obj_name] = {}
			self.authorizations[auth.method][auth.obj_name][auth.prop_name] = True

			# Weird indexing to say "Yes, they have a value here somewhere"
			if not self.authorizations[auth.method].has_key(""):
				self.authorizations[auth.method][""] = {}
			if not self.authorizations[""].has_key(auth.obj_name):
				self.authorizations[""][auth.obj_name] = {"": True}
			self.authorizations[""][""][""] = True
			self.authorizations[""][""][auth.prop_name] = True
			self.authorizations[""][auth.obj_name][""] = True
			self.authorizations[""][auth.obj_name][auth.prop_name] = True
			self.authorizations[auth.method][auth.obj_name][""] = True
			self.authorizations[auth.method][""][auth.prop_name] = True
			self.authorizations[auth.method][""][""] = True

		return self.authorizations

	def has_auth(self, method="", obj_name="", prop_name=""):
		if self.has_auth_group("admin"):
			return True
		if not self.authorizations:
			self.load_auths()

		method = method.upper()
		if not self.authorizations.has_key(method):
			method = "*"
		if not self.authorizations[method].has_key(obj_name):
			obj_name = "*"
			if not self.authorizations[method].has_key(obj_name):
				return False
		if not self.authorizations[method][obj_name].has_key(prop_name):
			prop_name = "*"
			if not self.authorizations[method][obj_name].has_key(prop_name):
				return False
		return self.authorizations[method][obj_name][prop_name]

	def has_auth_ctx(self, ctx, method="", obj_name="", prop_name=""):
		if isinstance(method, list):
			method = method[0]
		if isinstance(obj_name, list):
			obj_name = obj_name[0]
		if isinstance(prop_name, list):
			prop_name = prop_name[0]
		method = method.upper()
		if method == "HEAD":
			method = "GET"
		if method == "OPTIONS":
			method = "GET"
		return self.has_auth(method=method, obj_name=obj_name, prop_name=prop_name)

	def put(self):
		"""Auto-index"""
		self._indexed_name = self.name.upper().strip()
		super(self.__class__, self).put()
