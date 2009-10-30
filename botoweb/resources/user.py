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
from boto.sdb.db.model import Model
from boto.sdb.db import property

class User(Model):
	"""
	Simple user object
	"""
	username = property.StringProperty(verbose_name="Username", unique=True)
	name = property.StringProperty(verbose_name="Name")
	email = property.StringProperty(verbose_name="Email Adress")
	auth_groups = property.ListProperty(str, verbose_name="Authorization Groups")
	password = property.PasswordProperty(verbose_name="Password")

	def __str__(self):
		return self.name

	def notify(self, subject, body=''):
		"""
		Send notification to this user

		@param subject: Subject for this notification
		@type subject: str

		@param body: The message to send you
		@type body: str
		"""
		from_string = boto.config.get('Notification', 'smtp_from', 'botoweb')
		msgRoot = MIMEMultipart('related')
		msgRoot['Subject'] = subject
		msgRoot['From'] = from_string
		msgRoot['To'] = self.email
		msgRoot.preamble = 'This is a multi-part message in MIME format.'
		if isinstance(body, MIMEMultipart):
			msg = body
		else:
			msg = MIMEText(body, 'html')

		msgRoot.attach(msg)

		smtp_host = boto.config.get('Notification', 'smtp_host', 'localhost')
		server = smtplib.SMTP(smtp_host)
		smtp_user = boto.config.get('Notification', 'smtp_user', '')
		smtp_pass = boto.config.get('Notification', 'smtp_pass', '')
		if smtp_user:
			server.login(smtp_user, smtp_pass)
		server.sendmail(from_string, self.email, msgRoot.as_string())
		server.quit()


	def has_auth_group(self, group):
		return (group in self.auth_groups)

	def has_auth_group_ctx(self, ctx, group):
		return (group in self.auth_groups)
