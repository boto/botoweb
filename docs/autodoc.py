#!/usr/bin/env python
# Author: Chris Moyer
DOCS = []
import os, os.path

def appendmodule(docfile, name, modname):
	"""Add the module doc to this file
	
	:param docfile: Open file object to write out module markup to
	:type docfile: file
	
	:param name: The name of the module to write out a doc for
	:type name: str
	
	:param modname: The full path name of the module, eg. foo.bar.baz
	:type modname: str
	"""
	print >>docfile, name
	print >>docfile, "-"*len(name)
	print >>docfile, ""
	print >>docfile, ".. automodule:: ", modname
	print >>docfile, "   :members:"
	# Include the members that don't have any docstrings
	print >>docfile, "   :undoc-members:"
	# Include the members that are inherited from other modules
	#print >>docfile, "   :inherited-members:"
	# Show module base class inheritance
	print >>docfile, "   :show-inheritance:"
	print >>docfile, ""

def makedocs(root, modname):
	"""Makes the documentation

	:param root: The directory path to search for modules (recursively)
	:type root: str

	:param modname: The full path name of the module, eg. foo.bar.baz
	:type modname: str
	"""
	name = modname.split('.')[-1]
	DOCS.append(name)
	docfile = open(os.path.join(refpath, "%s.rst" % name), "w")
	
	print >>docfile, ".. _ref-%s:" % name
	print >>docfile, ""
	print >>docfile, "="*len(name)
	print >>docfile, name
	print >>docfile, "="*len(name)
	print >>docfile, ""

	appendmodule(docfile, name, modname)
	
	for m in os.listdir(root):
		if not m.startswith("."):
			if m.endswith(".py") and not m == "__init__.py":
				appendmodule(docfile, m.rsplit(".")[0], "%s.%s" % (modname, m.rsplit(".")[0]))
			elif os.path.isdir(os.path.join(root, m)):
				try:
					# Check if the directory is acutally importable.
					# If not, it's not a module, and doesn't need to be included
					__import__( "%s.%s" % (modname, m) )
					makedocs(os.path.join(root, m), "%s.%s" % (modname, m))
				except:
					pass


if __name__ == "__main__":
	import sys
	from optparse import OptionParser

	scriptpath = sys.path[0]
	# Get the newscore script directory from the parent of the script's
	botowebpath = os.path.join(os.path.dirname(scriptpath),"botoweb")
	# Get the path for the ref files
	refpath = os.path.join(scriptpath,"source","ref")
	# Make cure refpath exists as a directory
	if not os.path.isdir(refpath):
		if os.path.exists(refpath):
			raise Exception(refpath + " was found but is not a directory. Cannot continue.")
		else:
			os.mkdir(refpath,0755)

	parser = OptionParser(usage='Usage: %prog [options]')
	parser.add_option("-c", "--clean", dest="clean", default=False, action="store_true", help="Clean output directories; doesn't output new files")
	(options, args) = parser.parse_args()

	# Delete any previous output files
	if options.clean:
		for m in os.listdir(refpath):
			os.remove(os.path.join(refpath,m))
	else:
		makedocs(botowebpath, "botoweb")
		index = open(os.path.join(refpath, "index.rst"), "w")
		print >>index, ".. _ref-index:"
		print >>index, ""
		print >>index, "============="
		print >>index, "API Reference"
		print >>index, "============="
		print >>index, ""
		print >>index, ".. toctree::"
		print >>index, "   :maxdepth: 4"
		print >>index, ""
		# Two spaces in the following print, because 3 are needed and the comma makes one
		for m in DOCS:
			print >>index, "  ", m
