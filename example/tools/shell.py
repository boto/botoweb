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


boto.config.add_section("DB_Post")
boto.config.set("DB_Post", "db_name", "blog")

boto.config.set("DB_User", "db_name", "users")

import readline
import code
session = {}
from example.resources.post import Post
session['Post'] = Post
code.interact(local=session)
