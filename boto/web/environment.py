# Author: Chris Moyer
import os, os.path
import yaml
from boto.web.config import Config
from pkg_resources import get_provider, ResourceManager

import logging
log = logging.getLogger("boto.web")

class Environment(object):
    """
    boto.web Environment
    """

    def __init__(self, module, env="prod"):
        self.module = module
        self.env = env

        # Config setup
        self.conf = Config()
        self.config = self.conf._sections

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
