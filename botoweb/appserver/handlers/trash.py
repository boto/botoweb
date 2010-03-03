# Copyright (c) 2008-2010 Chris Moyer http://coredumped.org
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

from botoweb.appserver.handlers.db import DBHandler
from botoweb.exceptions import Unauthorized

class TrashHandler(DBHandler):
	"""Handler for the "deleted" files"""
	show_deleted = True

	# Delete on the Trash handler is a real purge
	def delete(self, obj, user):
		"""Purge the specified object from the system"""
		# Only administrators can purge files
		if not user.has_group("admin"):
			raise Unauthorized()
		obj.delete()
		return obj

	def search(self, params, user):
		"""Search through the trash (Wash your hands!)
		@param params: The Terms to search for
		@type params: Dictionary

		@param user: the user that is searching
		@type user: User
		"""
		query = self.db_class.find()
		query.filter("deleted =", True)
		return self.build_query(params, query=query, user=user, show_deleted=True)

