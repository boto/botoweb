# Author: Chris Moyer
# Config class wrapper to support boto
import ConfigParser
import yaml
import types
import re
import boto
import os
import os.path

from string import Template


class Config(ConfigParser.SafeConfigParser):
	"""
	Support a config defined by a YAML file
	"""
	env = None
	def __init__(self, path="app.yaml"):
		self._sections = {}
		self._defaults = boto.config._defaults
		for key in boto.config._sections:
			value = boto.config._sections[key]
			if "_" in key:
				key = key.split("_")
				if not self._sections.get(key[0]):
					self._sections[key[0]] = {}
				self._sections[key[0]][key[1]] = value
			else:
				if self._sections.get(key):
					for k in value:
						self._sections[key][k] = value[k]
				else:
					self._sections[key] = value

		try:
			self.read(path)
		except:
			pass

	def read(self, path):
		self._sections.update(yaml.load(open(path, "rb")))

		if os.environ.has_key('AWS_ACCESS_KEY_ID'):
			aws_access_key_id = os.environ['AWS_ACCESS_KEY_ID']
		elif self.has_option('Credentials', 'aws_access_key_id'):
			aws_access_key_id = self.get('Credentials', 'aws_access_key_id')
		elif boto.config.has_option('Credentials', 'aws_access_key_id'):
			aws_access_key_id = boto.config.get("Credentials", "aws_access_key_id")

		if os.environ.has_key('AWS_SECRET_ACCESS_KEY'):
			aws_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY']
		elif self.has_option('Credentials', 'aws_secret_access_key'):
			aws_secret_access_key = self.get('Credentials', 'aws_secret_access_key')
		elif boto.config.has_option('Credentials', 'aws_secret_access_key'):
			aws_secret_access_key = boto.config.get("Credentials", "aws_secret_access_key")

		self._sections['Credentials'] = {
			"aws_access_key_id": aws_access_key_id,
			"aws_secret_access_key": aws_secret_access_key
		}


	def has_section(self, section):
		if ConfigParser.SafeConfigParser.has_section(self, section):
			return True
		match = re.match("^([^_]*)_(.*)$", section)
		if match:
			if self.has_section(match.group(1)):
				return self._sections[match.group(1)].has_key(match.group(2))

	def has_option(self, section, option):
		if ConfigParser.SafeConfigParser.has_option(self, section, option):
			return True
		return False

	def get_instance(self, name, default=None):
		return self.get("Instance", name, default)

	def get_user(self, name, default=None):
		return self.get("User", name, default)

	def getint_user(self, name, default=0):
		return int(self.get_user(name, default))

	def get_value(self, section, name, default=None):
		return self.get(section, name, default)

	def getint(self, section, name, default=0):
		return int(self.get(section, name, default))

	def getfloat(self, section, name, default=0.0):
		return float(self.get(section, name, default))

	def getbool(self, section, name, default=False):
		val = self.get(section, name, None)
		if val is not None:
			if (type(val) == types.StringType):
				return val.lower() == "true"
			else:
				return bool(val)
		else:
			return default

	def get(self, section, name, default=None):
		if self._sections.has_key(section) and self._sections[section].has_key(name):
			return self._sections[section][name]

		match = re.match("^([^_]*)_(.*)$", section)
		if match:
			if self._sections.has_key(match.group(1)) and \
				self._sections[match.group(1)].has_key(match.group(2)) and \
				self._sections[match.group(1)][match.group(2)].has_key(name):
				return self._sections[match.group(1)][match.group(2)][name]

		return default

	# Descriptors for direct dictionary-like access
	def __len__(self):
		return len(self._sections)
		
	def __getitem__(self, key):
		return self._sections[key]

	def __setitem__(self, key, value):
		self._sections[key] = value

	def __delitem__(self, key):
		del(self._sections[key])

	def __reversed__(self):
		return reversed(self._sections)
	
	def __contains__(self, key):
		return (key in self._sections)

	def update(self, vals):
		"""
		Merge the sections, don't just replace them
		"""
		for section in vals:
			if self._sections.has_key(section):
				self._sections[section].update(vals[section])
			else:
				self._sections[section] = vals[section]


	def has_key(self, key):
		return self._sections.has_key(key)

	def copy(self):
		conf = Config()
		conf._sections = self._sections.copy()
		conf.env = self.env
		return conf
