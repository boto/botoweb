# Copyright (c) 2009 Chris Moyer http://coredumped.org
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
from botoweb.appserver.handlers import RequestHandler
from boto.utils import find_class
from lxml import etree

import logging
log = logging.getLogger("botoweb.handlers.db")


from botoweb.xmlize import TYPE_NAMES
TYPE_CONVERSIONS = {
	"map": "complexType",
	"datetime": "dateTime",
}

class IndexHandler(RequestHandler):
	"""
	Simple Index Handler which helps to show what
	URLs we have and what objects they provide
	"""

	def __init__(self, env, config):
		"""Set up and fetch the routes for the first time"""
		RequestHandler.__init__(self, env, config)

	def _get(self, request, response, id=None):
		"""List all our APIs,
		as well as properties on each object we have."""
		response.content_type = 'text/xml'
		doc = etree.Element("Index", name=self.env.config.get("app", "name", "botoweb application"))
		if self.env.config.get("app", "version"):
			doc.set("version", self.env.config.get("app", "version"))
		if request.user:
			user_node = etree.SubElement(doc, "User", id=request.user.id)
			etree.SubElement(user_node, "href").text = str("users/%s" % request.user.id)
			etree.SubElement(user_node, "name").text = request.user.name
			etree.SubElement(user_node, "username").text = request.user.username
			etree.SubElement(user_node, "email").text = request.user.email
			auth_node = etree.SubElement(user_node, "groups")
			for auth_group in request.user.auth_groups:
				etree.SubElement(auth_node, "group", name=auth_group)

		for route in self.env.config.get("botoweb", "handlers"):
			if route.get("name"):
				model_name = route.get("name")
				href = route['url'].strip('/')
				api_node = etree.SubElement(doc, "api", name=model_name)
				etree.SubElement(api_node, "href").text = href
				if route.get("description"):
					etree.SubElement(api_node, "description").text = route.get("description")
				handler = find_class(route.get("handler"))
				if not handler:
					raise Exception("Handler not found: %s" % route.get('handler'))
				methods_node = etree.SubElement(api_node, "methods")
				for method_name in handler.allowed_methods:
					method = getattr(handler, "_%s" % method_name)
					etree.SubElement(methods_node, method_name).text = method.__doc__
				if route.get("db_class"):
					model_class = find_class(route.get("db_class"))
					if model_class:
						props_node = etree.SubElement(api_node, "properties")
						for prop in model_class.properties():
							if prop.name.startswith("_"):
								continue
							prop_node = etree.SubElement(props_node, "property")
							prop_node.set("name", prop.name)
							if hasattr(prop, "reference_class"):
								prop_node.set("type", "reference")
								prop_node.set("item_type", prop.reference_class.__name__)
							else:
								prop_type_name = prop.type_name.lower()
								if prop_type_name:
									prop_node.set("type", TYPE_CONVERSIONS.get(prop_type_name, prop_type_name))
								elif hasattr(prop, "calculated_type"):
									prop_node.set("type", TYPE_NAMES.get(prop.calculated_type, "string"))
								else:
									prop_node.set("type", TYPE_NAMES.get(prop.data_type, "string"))
							if prop.data_type in [str, unicode]:
								prop_node.set("max_length", "1024")
							if prop.data_type == int:
								prop_node.set("min", "-2147483648")
								prop_node.set("max", "2147483647")
							if hasattr(prop, "item_type"):
								if hasattr(prop.item_type, "__name__"):
									item_type = prop.item_type.__name__
								else:
									item_type = TYPE_NAMES.get(prop.item_type, "string")
								prop_node.set("item_type", item_type)

							if hasattr(prop, "verbose_name") and prop.verbose_name != None:
								etree.SubElement(prop_node, "description").text = str(prop.verbose_name)

							if hasattr(prop, "default") and prop.default:
								default_node = etree.SubElement(prop_node, "default")
								default_node.text = str(prop.default)
							if hasattr(prop, "choices") and prop.choices:
								choices_node = etree.SubElement(prop_node, "choices")
								for choice in prop.choices:
									etree.SubElement(choices_node, "choice", value=choice)
		response.write(etree.tostring(doc, encoding="utf-8", pretty_print=True))
		return response
