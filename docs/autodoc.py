#!/usr/bin/env python
# Author: Chris Moyer
DOCS = []
import os, os.path

def appendmodule(docfile, name):
	"""Add the modeledoc to this file"""
	print >>docfile, name
	print >>docfile, "-"*len(name)
	print >>docfile, ""
	print >>docfile, ".. automodule:: ", name
	print >>docfile, "   :members:"
	print >>docfile, "   :undoc-members:"
	print >>docfile, ""

def makedocs(root, name):
	"""Makes the documentation"""
	docfile = open(os.path.join(os.path.join("source", "ref"), "%s.rst" % name), "w")
	DOCS.append(name)
	print >>docfile, ".. _ref-%s:" % name
	print >>docfile, ""
	print >>docfile, "="*len(name)
	print >>docfile, name
	print >>docfile, "="*len(name)
	print >>docfile, ""

	appendmodule(docfile, name)
	
	for m in os.listdir(root):
		if not m.startswith("."):
			if m.endswith(".py") and not m == "__init__.py":
				appendmodule(docfile, "%s.%s" % (name, m.rstrip(".py")))
			elif os.path.isdir(os.path.join(root, m)):
				makedocs(os.path.join(root, m), "%s.%s" % (name, m))


if __name__ == "__main__":
	makedocs(os.path.join("..", "botoweb"), "botoweb")
	index = open(os.path.join(os.path.join("source", "ref"), "index.rst"), "w")
	print >>index, ""
	print >>index, ".. _ref-index"
	print >>index, "============="
	print >>index, "API Reference"
	print >>index, "============="
	print >>index, ""
	print >>index, ".. toctree::"
	print >>index, "   :maxdepth: 4"
	print >>index, ""
	for m in DOCS:
		print >>index, "    ", m
