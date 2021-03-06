# -*- coding: utf-8 -*-

import logging

from .Plugin import Plugin, PluginMeta
from .Settings import Settings

class configuration(object):  # pylint: disable=C0103
	""".. py:decorator:: configuration

	This decorator specifies the configurations for a plugin."""
	def __init__(self, **kwargs):
		self.config = kwargs

	def __call__(self, cls):
		def config(self, key):
			return ConfigurationManager(self.context).value(self, key)
		def setConfig(self, key, value):
			ConfigurationManager(self.context).setValue(self, key, value)
		cls.configuration = self.config
		cls.config = config
		cls.setConfig = setConfig
		return cls

class ConfigurationValue(object):
	"""
	Base class for configuration values. Do not use this class directly but use one of the
	subclasses instead.

	.. versionchanged:: 1.2
	   Added parameter *sortOrder*

	:param str valueType: The type of the configuration value. Only set this in subclasses..
	:param str defaultValue: The default value used if not value is set.
	:param bool writable: If this value can be set by the user in the UI.
	:param bool readable: `True` if the current value could be read by user interfaces. Set this to
	  `False` for fields such as password where the current value should not be exposed to the UI.
	:param bool hidden: If this field should be user configurable in the UI or not.
	:param int sortOrder: The order the values should be sorted by in the UI.
	"""
	def __init__(
		self,
		valueType,
		defaultValue,
		writable=True,
		readable=True,
		hidden=False,
		sortOrder=0,
		**kwargs
	):
		self.valueType = valueType
		self.defaultValue = defaultValue
		self.readable = readable
		self.writable = writable
		self.hidden = hidden
		self.sortOrder = sortOrder
		self.title = kwargs.setdefault('title', '')
		self.description = kwargs.setdefault('description', '')

	def serialize(self):
		return {
			'description': self.description,
			'hidden': self.hidden,
			'readable': self.readable,
			'sortOrder': self.sortOrder,
			'title': self.title,
			'type': self.valueType,
			'writable': self.writable,
		}

class ConfigurationBool(ConfigurationValue):
	"""
	Configuration class used to store boolean values

	.. versionadded:: 1.2
	"""
	def __init__(self, defaultValue=False, **kwargs):
		super(ConfigurationBool, self).__init__('bool', defaultValue, **kwargs)

class ConfigurationDict(ConfigurationValue):
	"""
	Configuration class used to store dictionaries
	"""
	def __init__(self, defaultValue=None, **kwargs):
		defaultValue = defaultValue or {}
		super(ConfigurationDict, self).__init__('dict', defaultValue, **kwargs)

class ConfigurationList(ConfigurationValue):
	"""
	Configuration class used to store lists
	"""
	def __init__(self, defaultValue=None, **kwargs):
		defaultValue = defaultValue or []
		super(ConfigurationList, self).__init__('list', defaultValue, **kwargs)

class ConfigurationNumber(ConfigurationValue):
	"""
	Configuration class used to store numbers
	"""
	def __init__(self, defaultValue=0, minimum=0, maximum=0, **kwargs):
		self.minimum = minimum
		self.maximum = maximum
		super(ConfigurationNumber, self).__init__('number', defaultValue, **kwargs)

	def serialize(self):
		retval = super(ConfigurationNumber, self).serialize()
		retval['minimum'] = self.minimum
		retval['maximum'] = self.maximum
		return retval

class ConfigurationSelect(ConfigurationValue):
	"""
	Configuration class used to store one value out of a predefined selection

	.. versionadded:: 1.2
	"""
	def __init__(self, options=None, **kwargs):
		super(ConfigurationSelect, self).__init__('select', **kwargs)
		self.options = options or {}

	def serialize(self):
		retval = super(ConfigurationSelect, self).serialize()
		retval['options'] = self.options
		return retval

class ConfigurationString(ConfigurationValue):
	"""
	Configuration class used to store strings
	"""
	def __init__(self, defaultValue='', minLength=0, maxLength=0, **kwargs):
		self.minLength = minLength
		self.maxLength = maxLength
		super(ConfigurationString, self).__init__('string', defaultValue, **kwargs)

	def serialize(self):
		retval = super(ConfigurationString, self).serialize()
		retval['minLength'] = self.minLength
		retval['maxLength'] = self.maxLength
		return retval

class ConfigurationManager(Plugin):
	def configForClass(self, cls):
		if hasattr(cls, 'configuration') is False:
			return None
		cfgObj = {}
		for key in cls.configuration:
			config = cls.configuration[key].serialize()
			if config['hidden'] is True:
				continue
			if config['title'] == '':
				config['title'] = key
			if config['readable'] is True:
				config['value'] = self.__getValue(cls, key)
			cfgObj[key] = config
		return cfgObj

	def setValue(self, callee, key, value):
		settings = Settings(ConfigurationManager.nameForObject(callee))
		settings[key] = value
		if hasattr(callee, 'configWasUpdated'):
			callee(self.context).configWasUpdated(key, value)

	def value(self, callee, key):
		return self.__getValue(callee.__class__, key)

	@staticmethod
	def __getValue(__class__, key):
		name = ConfigurationManager.nameForClass(__class__)
		# Find out the default value, used to parse the value correctly
		if key not in __class__.configuration:
			logging.warning("%s not in %s", key, __class__.configuration)
			return None
		settings = Settings(name)
		value = settings.get(key, __class__.configuration[key].defaultValue)
		if value is not None:
			return value

	@staticmethod
	def __requestConfigurationObject(obj, name):
		cfg = obj.getConfiguration()
		if name not in cfg:
			return None
		return cfg[name]

	@staticmethod
	def nameForObject(obj):
		if isinstance(obj, PluginMeta):
			return ConfigurationManager.nameForClass(obj)
		if isinstance(obj, Plugin):
			return ConfigurationManager.nameForInstance(obj)
		raise Exception('Object is not a subclass of Plugin')

	@staticmethod
	def nameForClass(cls):  # pylint: disable=W0211
		return '%s.%s' % (cls.__module__, cls.__name__)

	@staticmethod
	def nameForInstance(instance):
		return ConfigurationManager.nameForClass(instance.__class__)
