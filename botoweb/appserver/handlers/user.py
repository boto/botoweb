# Copyright (c) 2008 Chris Moyer http://coredumped.org
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

from botoweb.appserver.handlers.db import DBHandler
from botoweb.exceptions import Unauthorized

class UserHandler(DBHandler):
    """
    Specific permissions on top of a DB hander for 
    modifying users
    """

    def create(self, params, user):
        """
        Admin only function
        """
        if not user or not user.has_auth_group("admin"):
            raise Unauthorized()
        return DBHandler.create(self, params, user)

    def update(self, obj, props, user):
        """
        you can only update this object if it is you or you are an admin, 
        Only admins can modify auth_groups
        """
        if not user:
            raise Unauthorized()
        if not user.has_auth_group("admin"):
            if user.id == obj.id:
                for prop_name in props:
                    prop_val = props[prop_name]
                    if prop_name and prop_name in ("name", "password"):
                        setattr(obj, prop_name, prop_val)
            else:
                raise Unauthorized()
        else:
            for prop_name in props:
                prop_val = props[prop_name]
                #print "%s: %s" % (prop_name, prop_val)
                setattr(obj, prop_name, prop_val)
        obj.put()
        return obj

