#!/usr/bin/env python
import sys
sys.path.append(".")
import boto
from getpass import getpass
boto.config.set("DB", "db_type", "XML")
boto.config.set("DB", "db_host", "localhost")
boto.config.set("DB", "enable_ssl", "False")
boto.config.set("DB", "db_port", "9080")
boto.config.set("DB", "db_user", raw_input("Username: "))
boto.config.set("DB", "db_passwd", getpass())


import readline
import code
session = {}
from example.resources.post import Post
Post._manager.db_name = "blog"
from boto_web.resources.filter_rule import FilterRule
FilterRule._manager.db_name = "rules"
from boto_web.resources.user import User
User._manager.db_name = "user"

session['Post'] = Post
session['Rule'] = FilterRule
session['User'] = User

code.interact(local=session)
