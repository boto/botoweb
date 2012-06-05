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
from botoweb.db.coremodel import Model
from botoweb.db import property

class Authorization(Model):
	"""Authorization Grant"""
	auth_group = property.StringProperty(verbose_name="Authorization Group")
	method = property.StringProperty(default="*", verbose_name="Permission", choices=["*", "GET", "POST", "PUT", "DELETE"])
	obj_name = property.StringProperty(default="", verbose_name="Object Name")
	prop_name = property.StringProperty(default="", verbose_name="Property Name")

	def put(self):
		"""These need to be unique, so if we don't have an ID we
		search for another authorization with all the same properties"""
		if not self.id:
			for obj in self.find(auth_group=self.auth_group, method=self.method, obj_name=self.obj_name, prop_name=self.prop_name):
				self.id = obj.id
				break
		Model.put(self)
