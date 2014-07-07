#!/usr/bin/python

# Copyright (c) 2008-2012 Chris Moyer http://coredumped.org
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
from setuptools import setup, find_packages

from botoweb import __version__

setup(name = "botoweb",
		version = __version__,
		description = "Boto based webapp framework",
		long_description="Python Enterprise level 3-Tier distributed webapp framework for use within the Amazon Web Services environment.",
		author = "Chris Moyer",
		author_email = "kopertop@gmail.com",
		url = "http://botoweb.com",
		packages = find_packages(exclude=['ez_setup', 'example']),
		include_package_data = True,
		package_data = {
			'': ['*.yaml', 'conf/*.yaml', 'installer/*', 'filters/**/*', 'filters/*.xsl'],
		},
		license = 'MIT',
		scripts = ['tools/botoweb', 'tools/botoweb_client', 'tools/bw_client_upload'],
		platforms = 'Posix; MacOS X; Windows',
		classifiers = [ 
			'Development Status :: 3 - Alpha',
			'Intended Audience :: Developers',
			'License :: OSI Approved :: MIT License',
			'Operating System :: OS Independent',
			'Topic :: Internet',
		],
		dependency_links = [
			"http://code.google.com/p/boto/downloads/list",
		],
		install_requires = [
			"pyyaml",
			"webob",
			"boto",
			"lxml",
			"pytz",
		],
	)
