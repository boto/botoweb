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
from Ft.Lib.Uri import FtUriResolver, Absolutize
from Ft.Lib import UriException
from cStringIO import StringIO
from pkg_resources import resource_string
import re
import boto

class FilterResolver (FtUriResolver):
    """
        This resolver extends the standard URI resolver
        and adds the following URLs

        s3://bucket_name/key_name
        python://module.name/file.name

        This resolver also caches files locally once it has been initialized
    """

    def __init__(self):
        self.files = {}
        FtUriResolver.__init__(self)

    def normalize(self, uriRef, baseUri):
        return Absolutize(uriRef, baseUri)

    def resolve(self, uri):
        if not self.files.has_key(uri):
            if uri.startswith("s3://"):
                match = re.match("^s3:\/\/([^\/]*)\/(.*)$", uri)
                if match:
                    s3 = boto.connect_s3()
                    b = s3.get_bucket(match.group(1))
                    k = b.get_key(match.group(2))
                    if k:
                        self.files[uri] = k.read()
            elif uri.startswith("python://"):
                match = re.match("^python:\/\/([^\/]*)\/(.*)$", uri)
                if match:
                    module = match.group(1)
                    name = match.group(2)
                    self.files[uri] = resource_string(module, name)
            else:
                file =  FtUriResolver.resolve(self, uri)
                self.files[uri] = file.read()
        if not self.files.has_key(uri):
            raise UriException(UriException.RESOURCE_ERROR, loc=uri, msg="not found, sorry")
        return StringIO(self.files[uri])
