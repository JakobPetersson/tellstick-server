# -*- coding: utf-8 -*-

from threading import Timer

from base import Plugin, implements
from events.base import IEventFactory, Action, Condition, Trigger
from .Device import Device
from .DeviceManager import DeviceManager, IDeviceChange

class DeviceEventFactory(Plugin):
	implements(IEventFactory)
	implements(IDeviceChange)

	def __init__(self):
		self.deviceTriggers = []
		self.sensorTriggers = []
		self.deviceManager = DeviceManager(self.context)  # pylint: disable=E1121

	def clearAll(self):
		self.deviceTriggers = []
		self.sensorTriggers = []

	def createAction(self, type, params, **kwargs):  # pylint: disable=W0622
		if type == 'device':
			if 'local' in params and params['local'] == 1:
				return DeviceAction(manager=self.deviceManager, **kwargs)
		return None

	def createCondition(self, type, params, **kwargs):  # pylint: disable=W0622
		if type == 'device':
			if 'local' in params and params['local'] == 1:
				return DeviceCondition(manager=self.deviceManager, **kwargs)
			return None
		if type == 'sensor':
			if 'local' in params and params['local'] == 1:
				return SensorCondition(manager=self.deviceManager, **kwargs)
		return None

	def createTrigger(self, type, **kwargs):  # pylint: disable=W0622
		if type == 'device':
			deviceTrigger = DeviceTrigger(self, **kwargs)
			self.deviceTriggers.append(deviceTrigger)
			return deviceTrigger
		if type == 'sensor':
			sensorTrigger = SensorTrigger(self, **kwargs)
			self.sensorTriggers.append(sensorTrigger)
			return sensorTrigger
		return None

	def deleteTrigger(self, trigger):
		if trigger in self.deviceTriggers:
			self.deviceTriggers.remove(trigger)
		elif trigger in self.sensorTriggers:
			self.sensorTriggers.remove(trigger)

	def sensorValueUpdated(self, device, valueType, value, scale):
		for trigger in self.sensorTriggers:
			if trigger.sensorId == device.id():
				trigger.triggerSensorUpdate(valueType, value, scale)

	def stateChanged(self, device, method, statevalue):
		del statevalue
		for trigger in self.deviceTriggers:
			if trigger.deviceId == device.id() and trigger.method == int(method):
				trigger.triggered({
					'triggertype': 'device',
					'clientdeviceid': device.id(),
					'method': int(method)
				})

class DeviceActionExecutor(object):
	def __init__(self, device, method, value, repeats, description):
		self.device = device
		self.method = method
		self.value = value
		self.repeats = repeats
		self.description = description

		if device.typeString() == '433' and self.repeats > 1:
			self.retries = 0  # No retries for 433
			i = 1
			while i < self.repeats:
				tmr = Timer(3*i, self.execute)
				tmr.start()
				i += 1
		else:
			self.retries = self.repeats
		self.execute()

	def execute(self):
		self.device.command(
			self.method,
			self.value,
			origin='Event - %s' % self.description,
			failure=self.__failure
		)

	def __failure(self, reason):
		del reason
		self.retries -= 1
		if self.retries > 0:
			tmr = Timer(60, self.execute)
			tmr.start()

class DeviceAction(Action):
	def __init__(self, manager, **kwargs):
		super(DeviceAction, self).__init__(**kwargs)
		self.manager = manager
		self.deviceId = 0
		self.method = 0
		self.repeats = 1
		self.value = ''

	def parseParam(self, name, value):
		if name == 'clientDeviceId':
			self.deviceId = int(value)
		elif name == 'method':
			self.method = int(value)
		elif name == 'repeats':
			self.repeats = min(10, max(1, int(value)))
		elif name == 'value':
			self.value = int(value)

	def execute(self, triggerInfo=None):
		del triggerInfo
		device = self.manager.device(self.deviceId)
		if device is None:
			return
		# We do not store the deviceExecutor object so it can be garbage collected
		# when it is done.
		deviceExecutor = DeviceActionExecutor(  # pylint: disable=W0612
			device,
			self.method,
			self.value,
			self.repeats,
			self.event.description
		)

class DeviceCondition(Condition):
	def __init__(self, manager, **kwargs):
		super(DeviceCondition, self).__init__(**kwargs)
		self.manager = manager
		self.deviceId = 0
		self.method = 0

	def parseParam(self, name, value):
		if name == 'clientDeviceId':
			self.deviceId = int(value)
		elif name == 'method':
			self.method = int(value)

	def validate(self, success, failure):
		device = self.manager.device(self.deviceId)
		if device is None:
			failure()
			return
		(state, __stateValue) = device.state()
		if state == self.method:
			success()
		else:
			failure()

class DeviceTrigger(Trigger):
	def __init__(self, factory, **kwargs):
		super(DeviceTrigger, self).__init__(**kwargs)
		self.deviceId = 0
		self.method = 0
		self.factory = factory

	def close(self):
		self.factory.deleteTrigger(self)

	def parseParam(self, name, value):
		if name == 'clientDeviceId':
			self.deviceId = int(value)
		elif name == 'method':
			self.method = int(value)

class SensorCondition(Condition):
	def __init__(self, manager, **kwargs):
		super(SensorCondition, self).__init__(**kwargs)
		self.manager = manager
		self.sensorId = 0
		self.value = 0
		self.edge = 0
		self.valueType = 0
		self.scale = 0

	def parseParam(self, name, value):
		if name == 'clientSensorId':
			self.sensorId = int(value)
		elif name == 'value':
			self.value = float(value)
		elif name == 'edge':
			self.edge = int(value)
		elif name == 'valueType':
			if value == 'temperature' or value == 'temp':
				self.valueType = Device.TEMPERATURE
			elif value == 'humidity':
				self.valueType = Device.HUMIDITY
			elif value == 'wgust':
				self.valueType = Device.WINDGUST
			elif value == 'rrate':
				self.valueType = Device.RAINRATE
			elif value == 'wavg':
				self.valueType = Device.WINDAVERAGE
			elif value == 'uv':
				self.valueType = Device.UV
			elif value == 'watt':
				self.valueType = Device.WATT
			elif value == 'lum':
				self.valueType = Device.LUMINANCE
			elif value == 'genmeter':
				self.valueType = Device.GENERIC_METER
			elif value == 'weight':
				self.valueType = Device.WEIGHT
			elif value == 'co2':
				self.valueType = Device.CO2
			elif value == 'volume':
				self.valueType = Device.VOLUME
			elif value == 'loudness':
				self.valueType = Device.LOUDNESS
			elif value == 'particulatematter25':
				self.valueType = Device.PM25
			elif value == 'co':
				self.valueType = Device.CO
			elif value == 'moisture':
				self.valueType = Device.MOISTURE
		elif name == 'scale':
			self.scale = int(value)

	def validate(self, success, failure):
		sensor = self.manager.device(self.sensorId)
		if sensor is None:
			failure()
			return
		value = sensor.sensorValue(self.valueType, self.scale)
		if value is None:
			failure()
			return
		if self.__compare(float(value), self.value, self.edge):
			success()
		else:
			failure()

	@staticmethod
	def __compare(value, condition, edge):
		if edge == 1:
			return value > condition
		if edge == 0:
			return value == condition
		if edge == -1:
			return value < condition

class SensorTrigger(Trigger):
	def __init__(self, factory, *args, **kwargs):
		super(SensorTrigger, self).__init__(*args, **kwargs)
		self.isTriggered = False
		self.requireReload = False
		self.reloadValue = 1
		self.firstValue = True
		self.scale = None
		self.factory = factory
		self.edge = 0
		self.sensorId = 0
		self.value = None
		self.valueType = None

	def close(self):
		self.factory.deleteTrigger(self)

	def parseParam(self, name, value):
		if name == 'clientSensorId':
			self.sensorId = int(value)
		elif name == 'value':
			self.value = float(value)
		elif name == 'edge':
			self.edge = int(value)
		elif name == 'reloadValue':
			self.reloadValue = min(15.0, max(0.1, float(value)))
		elif name == 'scale':
			self.scale = int(value)
		elif name == 'valueType':
			if value == 'temperature' or value == 'temp':
				self.valueType = Device.TEMPERATURE
			elif value == 'humidity':
				self.valueType = Device.HUMIDITY
			elif value == 'wgust':
				self.valueType = Device.WINDGUST
			elif value == 'rrate':
				self.valueType = Device.RAINRATE
			elif value == 'wavg':
				self.valueType = Device.WINDAVERAGE
			elif value == 'uv':
				self.valueType = Device.UV
			elif value == 'watt':
				self.valueType = Device.WATT
			elif value == 'lum':
				self.valueType = Device.LUMINANCE

	def triggerSensorUpdate(self, ttype, value, scale):
		try:
			if ttype != self.valueType:
				return
			if scale != self.scale:
				return
			value = float(value)
			if not self.isTriggered:
				if self.__compare(value, self.value, self.edge):
					self.isTriggered = True
					self.requireReload = True
					if not self.firstValue:
						self.triggered({
							'triggertype': 'sensor',
							'clientsensorid': self.sensorId,
							'value': value,
							'valueType': ttype,
							'scale': scale
						})
			else:
				if self.requireReload:
					self.requireReload = abs(value-self.value) < self.reloadValue
				if not self.requireReload:
					if self.edge == 0:
						self.isTriggered = False
					else:
						self.isTriggered = self.__compare(value, self.value, self.edge)
			self.firstValue = False
		except Exception as _error:
			pass

	@staticmethod
	def __compare(value, trigger, edge):
		if edge == 1:
			return value > trigger
		if edge == 0:
			return value == trigger
		if edge == -1:
			return value < trigger
