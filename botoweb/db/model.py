#
# Author: Chris Moyer http://coredumped.org/
#

from boto.sdb.db.model import Model as BotoModel
from botoweb.db.property import DateTimeProperty, ReferenceProperty, BooleanProperty
from botoweb.resources.user import User

class Model(BotoModel):
	"""Standard model plus added some basic tracking information"""
	created_at = DateTimeProperty(auto_now_add=True, verbose_name="Created Date")
	created_by = ReferenceProperty(User, verbose_name="Created By")

	modified_at = DateTimeProperty(verbose_name="Last Modified Date")
	modified_by = ReferenceProperty(User, verbose_name="Last Modified By")

	deleted = BooleanProperty(verbose_name="Deleted")
	deleted_at = DateTimeProperty(verbose_name="Deleted Date")
	deleted_by = ReferenceProperty(User, verbose_name="Deleted By")

	# This is set every time the object is touched, even if it's by the system
	sys_modstamp = DateTimeProperty(auto_now=True)
