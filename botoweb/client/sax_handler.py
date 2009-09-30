# 
# Author: Chris Moyer
#
from xml.sax.handler import ContentHandler

class ObjectHandler(ContentHandler):
	"""
	Simple Object Sax handler, currently only handles string properties
	"""

	def __init__(self, model_class, env):
		self.text = ""
		self.current_obj = None
		self.model_class = model_class
		self.env = env
		self.current_prop = None
		self.objs = []

	def characters(self, ch):
		self.text += ch

	def startElement(self, name, attrs):
		self.text = ""
		if name == "object":
			id = attrs.get("id")
			self.current_obj = self.model_class(self.env, id)
			self.current_prop = None
		elif name == "property":
			self.current_prop = attrs.get('name')

	def endElement(self, name):
		if name == "object":
			self.objs.append(self.current_obj)
			self.current_obj = None
		elif name == "property":
			if not self.current_prop in self.current_obj.__class__._properties:
				self.current_obj.__class__._properties.append(self.current_prop)
			setattr(self.current_obj, self.current_prop, str(self.text))
