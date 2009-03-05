# Author: Chris Moyer
# Extra XSLT functions that are farily common
from Ft.Xml.XPath import Conversions
from boto.utils import find_class

# TODO: Clean this up, perhaps we can 
# re-use the to_xml functionality already in the
# objects? if not we at least need to support 
# more then just string-able properties
def getObj(ctx, nodes):
    """
    Get this object and return it's XML format
    """
    for obj in nodes:
        myDoc = obj.ownerDocument
        id = obj.getAttributeNS(None, "id")
        cls_name = obj.getAttributeNS(None, "class")
        cls = find_class(cls_name)
        obj_new = cls.get_by_ids(id)

        for prop in obj_new.properties():
            if prop.name:
                prop_node = myDoc.createElementNS(None, "property")
                prop_node.setAttributeNS(None, "name", prop.name)
                prop_node.appendChild(myDoc.createTextNode(str(getattr(obj_new, prop.name))))
                obj.appendChild(prop_node)

    return nodes


ExtFunctions = {
    (u'python://boto_web/xslt_functions', u'getObj'): getObj,
}
