#!/usr/bin/env python
# Author: Susan Salkeld
#Description: Creates Sphinx documentation for given modules.

import commands
import sys

class ModuleClass(object):
	def __init__(self,module):
		"""
			Imports the module Sphinx will generate documentation for and creates the paths for the resulting documentation.
			:param module: the module to be documented.
			:type module: str
		"""
		module = __import__(module)
		self.path = commands.getoutput(module.__file__).split(":")[1]

		self.module_length = len("/__init__.pyc")
		self.module_path = self.path[1:-self.module_length]

		self.total_erase = len(module.__name__) + self.module_length
		self.output_path = "%s/sphinx-build/" % self.path[1:-self.total_erase]
		self.built_path = "%s/sphinx-build/" % self.path[1:-self.total_erase]

	def clean(self):
		"""
			Deletes any previous sphinx creation. If this is not done and a function or submodule is created or deleted, the sphinx-build will not find the change.
		"""
		print commands.getoutput('rm -rf %s' % self.output_path)

	def build_source(self):
		"""
			Builds the rst files for sphinx which give the module mapping to all of its functions and related modules. -F means this will create a full Sphinx project automatically. 
		"""
		print commands.getoutput('sphinx-apidoc -F -o %s %s' %(self.output_path, self.module_path))

	def build_types(self,build_list):
		"""
			Builds each type of output from rst files generated in build_source.
			sphinx-build -b <build_type> <output_path> <built_path> where output_path contains build_type is type of sphinx output to be generated, output_path contains the rst files, and built_path is the path the generated files will be located.
			The output_path will be <module>/sphinx-build/<type of build being generated>. 
				:param build_list: comma-separated string containing the types of output desired.
				:type build_list: str
		"""

		for type in build_list.split(','):
			self.built_path = "%s/sphinx-build/%s"% (self.path[1:-self.total_erase], type)
			
			print commands.getoutput('sphinx-build -b %s %s %s' %(type, self.output_path, self.built_path))


if __name__ == "__main__":
	from optparse import OptionParser
	parser = OptionParser()
	parser.add_option("-b", "--build_list", help="Add build types separated by comma. Build types include html,latex,dirhtml,singlehtml,text", default="html", dest="build_list")
	(options, args) = parser.parse_args()

	for module in args:
		try:
			mod = ModuleClass(module)
			mod.clean()
			mod.build_source()
			mod.build_types(options.build_list)
		except:
			print "Could not build %s" % module
			print sys.exc_info()[0]
