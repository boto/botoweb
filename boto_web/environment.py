# Author: Chris Moyer
import os, os.path
import yaml
from boto_web.config import Config
from pkg_resources import get_provider, ResourceManager

import logging
log = logging.getLogger("boto_web")

class Environment(object):
    """
    boto_web Environment
    """

    def __init__(self, module, env="prod"):
        self.module = module
        self.env = env

        # Config setup
        self.config = Config()

        self.dist = get_provider(self.module)
        self.mgr = ResourceManager()

        if self.dist.has_resource("conf"):
            self.config.update(self.get_config("conf"))
            if self.dist.has_resource("conf/env/%s.yaml" % self.env):
                log.info("Loading environment: %s" % self.env)
                self.config.update(yaml.load(self.dist.get_resource_stream(self.mgr,"conf/env/%s.yaml" % self.env)))

        # Set up the DB shortcuts
        if not self.config.has_key("DB"):
            self.config['DB'] = {
                                    "db_type": self.config.get("db_type", "SimpleDB"),
                                    "db_user": self.conf.get("Credentials", "aws_access_key_id"),
                                    "db_passwd": self.conf.get("Credentials", "aws_secret_access_key")
                                }
        if self.config.has_key("auth_db"):
            self.config['DB']['User'] = {"db_name": self.config['auth_db']}
        if self.config.has_key("default_db"):
            self.config['DB']['db_name'] = self.config.get("default_db")
        if self.config.has_key("session_db"):
            self.config['DB']['Session'] = {'db_name': self.config.get("session_db")}

    def get_config(self, path):
        config = {}
        for cf in self.dist.resource_listdir(path):
            if cf.endswith(".yaml"):
                config[cf[:-5]] = yaml.load(self.dist.get_resource_stream(self.mgr, os.path.join(path, cf)))
            elif not cf.startswith("."):
                config[cf] = self.get_config(os.path.join(path, cf))
        return config

    # Add in the shortcuts that are normally in boto
    def connect_sqs(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
        if aws_access_key_id == None:
            aws_access_key_id = self.config.get("Credentials", "aws_access_key_id")
        if aws_secret_access_key == None:
            aws_secret_access_key = self.config.get("Credentials", "aws_secret_access_key")
        return boto.connect_sqs(aws_access_key_id, aws_access_key_id, **kwargs)

    def connect_s3(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
        if aws_access_key_id == None:
            aws_access_key_id = self.config.get("Credentials", "aws_access_key_id")
        if aws_secret_access_key == None:
            aws_secret_access_key = self.config.get("Credentials", "aws_secret_access_key")
        return boto.connect_s3(aws_access_key_id, aws_access_key_id, **kwargs)

    def connect_ec2(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
        if aws_access_key_id == None:
            aws_access_key_id = self.config.get("Credentials", "aws_access_key_id")
        if aws_secret_access_key == None:
            aws_secret_access_key = self.config.get("Credentials", "aws_secret_access_key")
        return boto.connect_ec2(aws_access_key_id, aws_access_key_id, **kwargs)

    def connect_sdb(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
        if aws_access_key_id == None:
            aws_access_key_id = self.config.get("Credentials", "aws_access_key_id")
        if aws_secret_access_key == None:
            aws_secret_access_key = self.config.get("Credentials", "aws_secret_access_key")
        return boto.connect_sdb(aws_access_key_id, aws_access_key_id, **kwargs)

    def connect_fps(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
        if aws_access_key_id == None:
            aws_access_key_id = self.config.get("Credentials", "aws_access_key_id")
        if aws_secret_access_key == None:
            aws_secret_access_key = self.config.get("Credentials", "aws_secret_access_key")
        return boto.connect_fps(aws_access_key_id, aws_access_key_id, **kwargs)

    def connect_cloudfront(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
        if aws_access_key_id == None:
            aws_access_key_id = self.config.get("Credentials", "aws_access_key_id")
        if aws_secret_access_key == None:
            aws_secret_access_key = self.config.get("Credentials", "aws_secret_access_key")
        return boto.connect_cloudfront(aws_access_key_id, aws_access_key_id, **kwargs)
