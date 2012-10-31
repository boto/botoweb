#
# Author: Chris Moyer http://coredumped.org/
#

from botoweb.db.coremodel import Model as CoreModel
from botoweb.db.property import DateTimeProperty, ReferenceProperty, BooleanProperty
from botoweb.resources.user import User

class Model(CoreModel):
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

	@classmethod
	def query(cls, qs):
			return query(cls, qs)



def query(cls, qs):
	"""A generic SQL-like query function, which even allows for
	nested queries using special syntax. 

	In general, this follows the generic SQL-based syntax that
	SDB uses after the WHERE clause, but it adds a special 
	modifier for allowing you to specify properties by 
	VerboseName or name. It also allows you to specify 
	sub-queries using [ ], which returns a list of items in 
	it's place. These are always evaluated first, before 
	evaluating the rest of the query.

			* Backticks (`) specify a property.
			* Single quotes (') specify a value.
			* Square Brackets ([ ]) specify a sub-query.

	For a simple example, take a model Book, which extends
	this base-class therefore has a created_by property.
	To look for all books created by any administrator, you
	could simply use:
			`Created By` in [ User `auth_groups` = 'admin' ]
	The first thing that happens is the sub query is evaluated
	(note that the sub-query must define what model we're searching
	on), then that value replaces the original query:
			`Created By` in ('123987123-29384732', '129387218371-1293874213'...)
	When processed, this is translated into the SimpleDB query:
			`created_by` in ('123987123-29384732', '129387218371-1293874213'...)

	:NOTE: Due to this handling of passing the query directly onto SDB,
	you're limitted to the number of query modifiers you may use. This may be
	quite quickly reached if you hit a sub-query which returns a lot of results.
	I haven't yet figured out a better way to handle this.
	"""
	# First we need to find and resolve any sub-queries
	qs = _findSubQueries(cls, qs)
	for prop in cls.properties():
		qs = qs.replace("`%s`" % prop.verbose_name, "`%s`" % prop.name)
	q = cls.all()
	q.select = qs

	return q

def _findSubQueries(cls, qs):
	"""Find any possible sub-queries in this query
	This is a complicated bit of parsing which essentially
	allows for nested sub-queries"""
	# If there's no "[" in it, just return the query
	if not "[" in qs:
		return qs
	# Otherwise, we split this apart, 
	# the retQ is the return query we're
	# building, and the leftovers still need
	# to be processed
	(retQ, leftovers) = qs.split("[", 1)
	leftovers = _findSubQueries(cls, leftovers).split("]", 1)
	subQ = leftovers[0].strip()

	# Now that we FOUND the sub query, we need to 
	# perform the query, and insert the IDs in
	# it's place
	# Step 1, find the model to use
	(model_name, q2) = subQ.split(" ", 1)
	model = CoreModel.find_subclass(model_name)
	if not model:
		raise Exception, "Error, model: %s not found" % model_name
	subq_results = query(model, q2)
	# A limit placed here to prevent catostrophic failures, 
	# you can't really make this much higher or bad things happen
	subq_results.limit = 30

	ids = ["'%s'" % obj.id for obj in subq_results]
	retQ += "(%s)" % ",".join(ids)
	if len(leftovers) > 1:
		retQ += leftovers[1]

	return retQ
