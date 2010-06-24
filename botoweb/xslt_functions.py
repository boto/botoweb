# Author: Chris Moyer
# Extra XSLT functions that are farily common
from boto.utils import find_class
from lxml import etree

# TODO: Clean this up, currently there's two 
# different libraries doing XML creation which is
# why we have one dump and then parse using the second
# Perhaps this needs to be changed in boto.sdb.db?
def getObj(ctx, nodes):
	"""
	Get this object and return it's XML format
	"""
	from StringIO import StringIO
	node = nodes[0]
	cls = find_class(node.get("class"))
	obj = cls.get_by_id(node.get('id'))
	doc = obj.to_xml().toxml()
	doc = etree.parse(StringIO(doc))
	return doc.getroot().getchildren()

uri = "python://botoweb/xslt_functions"
functions = {
	"getObj": getObj
}

def ends_with(ctx, string1, string2):
	return string1.endswith(string2)

def starts_with(ctx, string1, string2):
	return string1.startswith(string2)
