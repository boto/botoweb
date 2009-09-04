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
from boto_web.appserver.handlers import RequestHandler
from boto.utils import find_class
from lxml import etree
import copy

import logging
log = logging.getLogger("boto_web.handlers.db")

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
		doc = etree.Element("Index", name=self.env.config.get("app", "name", "boto_web application"))
		if request.user:
			user_node = etree.SubElement(doc, "User", id=request.user.id)
			etree.SubElement(user_node, "href").text = str("users/%s" % request.user.id)

		for route in self.env.config.get("boto_web", "handlers"):
			if route.get("name"):
				model_name = route.get("name")
				href = route['url'].strip('/')
				api_node = etree.SubElement(doc, "api", name=model_name)
				etree.SubElement(api_node, "href").text = href
				if route.get("description"):
					etree.SubElement(api_node, "description").text = route.get("description")
				handler = find_class(route.get("handler"))
				methods_node = etree.SubElement(api_node, "methods")
				for method_name in handler.allowed_methods:
					method = getattr(handler, "_%s" % method_name)
					etree.SubElement(methods_node, method_name).text = method.__doc__
				if route.get("db_class"):
					model_class = find_class(route.get("db_class"))
					if model_class:
						props_node = etree.SubElement(api_node, "properties")
						for prop_name in model_class._prop_names:
							prop_node = etree.SubElement(props_node, "property")
							prop = model_class.find_property(prop_name)
							prop_node.set("name", prop_name)
							prop_node.set("type", prop.type_name.lower())
							prop_node.text = prop.verbose_name
		response.write(etree.tostring(doc, encoding="utf-8", pretty_print=True))
		return response
