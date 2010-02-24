#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Logginghelp wrapper to simplify implementation of message logging for me.

This simple class lets you setup all the magic you want from the python logging
module, without all the work.
example:
	obj = logginghelp('example')
	log = obj.get_log()
	log.info('hello world!')
You can set various parameters of the logging help class on instantiation for
fine grained control of logging behaviour.
"""
# Copyright (C) 2008-2010  James Shubin, McGill University
# Written for McGill University by James Shubin <purpleidea@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging
import logging.handlers
import xdg.BaseDirectory
import errno

_ = lambda x: x			# add fake gettext function until i fix up i18n
DEFAULT_PATH = True

# from: http://svn.python.org/view/python/trunk/Lib/logging/__init__.py?r1=66211&r2=67511
# the above code is under the license for the logging module. it is here until
# it gets backported or this logginghelp module gets updated to a newer version.
# Null handler


class NullHandler(logging.Handler):
	"""
	This handler does nothing. It's intended to be used to avoid the
	"No handlers could be found for logger XXX" one-off warning. This is
	important for library code, which may contain code to log events. If a user
	of the library does not configure logging, the one-off warning might be
	produced; to avoid this, the library developer simply needs to instantiate
	a NullHandler and add it to the top-level logger of the library module or
	package.
	"""
	def emit(self, record):
		pass


class logginghelp:
	def __init__(self, name, wordymode=True, stderrlog=True,
		mylogpath=[DEFAULT_PATH], addxdglog=True, defxdgstr='messages',
		logserver=None, logformat=None, showhello=False, mykerning=7):
		"""this class is meant to ease the use of the python logging
		class. the code assumes some sensible defaults, and if you want
		something different, then this class can probably be easily
		changed to support the feature or parameter that you want."""

		# some variables
		self.name = name			# a name for this log
		self.wordymode = wordymode		# extra speak
		self.stderrlog = stderrlog
		self.mylogpath = mylogpath		# list of rotating logs
		self.addxdglog = addxdglog		# add on xdg log path
		self.defxdgstr = defxdgstr		# default xdg string
		self.logserver = logserver		# for remote syslog
		self.logformat = logformat		# the format for all
		self.mykerning = mykerning		# add extra kerning on

		# add a log file in an xdg compliant path
		if self.addxdglog:
			temp = xdg.BaseDirectory.xdg_cache_home
			self.__cache = os.path.join(temp, self.name)
			try:
				os.makedirs(self.__cache)
			except OSError, e:
				if e.errno != errno.EEXIST:
					self.__cache = None

			if self.__cache is not None:
				temp = '%s.log' % self.defxdgstr
				temp = os.path.join(self.__cache, temp)
				self.mylogpath.append(temp)

		# add os specific default path to the processing
		if os.name == 'nt': path = 'c:\WINDOWS\system32\config\%s.log'
		elif os.name == 'posix': path = '/var/log/%s.log'
		# if the True value is found in log path, then do a default log
		if DEFAULT_PATH in self.mylogpath:
			while DEFAULT_PATH in self.mylogpath:
				self.mylogpath.remove(DEFAULT_PATH)
			# add a log file at the default location for os
			self.mylogpath.append(path % self.name)

		# default log format.
		if self.logformat is None:
			# the `7' as a kerning default is arbitrary.
			self.logformat = '%(asctime)s %(levelname)-8s %(name)-'\
			+ str(self.mykerning + len(self.name)) + 's %(message)s'

		# log objects
		self.log = None			# main logger
		self.logh = {}			# log handles
		self.logs = {}			# other log handles

		# do the logging init
		self.__logging()

		# send a hello message
		if showhello: self.log.debug(_('hello from: %s') % self.name)


	def __logging(self):
		"""setup logging. this function doesn't return any value."""
		# error logging levels:
		#	* CRITICAL
		#	* FATAL
		#	* ERROR
		#	* WARN
		#	* INFO
		#	* DEBUG

		# have every log use this format
		formatter = logging.Formatter(self.logformat)

		# name a log route & set a level
		self.log = logging.getLogger(self.name)
		if self.wordymode: self.log.setLevel(logging.DEBUG)
		else: self.log.setLevel(logging.WARN)

		# add a nullhandler so that if no other handlers are present, we
		# don't get the: `No handlers could be found for logger' message
		# FIXME: the NullHandler is from the python code, and when it is
		# backported to this python version (or if we use a later python
		# version), then replace the NullHandler with the stock version.
		self.logh['NullHandler'] = NullHandler(self.name)
		self.logh['NullHandler'].setFormatter(formatter)
		self.log.addHandler(self.logh['NullHandler'])
		del self.logh['NullHandler']

		# handler for stderr
		if self.stderrlog:
			self.logh['StreamHandler'] = logging.StreamHandler()
			self.logh['StreamHandler'].setFormatter(formatter)
			self.log.addHandler(self.logh['StreamHandler'])
			del self.logh['StreamHandler']

		# handler for global logging server
		if self.logserver is not None:
			# TODO: is there a way to change the facility to a
			# specific name?
			self.logh['SysLogHandler'] = \
			logging.handlers.SysLogHandler(
				tuple(self.logserver),
				logging.handlers.SysLogHandler.LOG_LOCAL7
			)
			self.logh['SysLogHandler'].setFormatter(formatter)
			self.log.addHandler(self.logh['SysLogHandler'])
			del self.logh['SysLogHandler']

		# handler for windows event log
		if os.name == 'nt':
			self.logh['NTEventLogHandler'] = \
			logging.handlers.NTEventLogHandler(self.name)
			self.logh['NTEventLogHandler'].setFormatter(formatter)
			self.log.addHandler(self.logh['NTEventLogHandler'])
			del self.logh['NTEventLogHandler']

		# handlers for local disk
		# NOTE: using access() to check if a user is authorized to e.g.
		# open a file before actually doing so using open() creates a
		# security hole, because the user might exploit the short time
		# interval between checking and opening the file to manipulate
		# it. do a try and catch instead.
		for x in self.mylogpath:
			try:
				self.logh['RotatingFileHandler'] = \
				logging.handlers.RotatingFileHandler(
					x,
					maxBytes=1024*100,
					backupCount=9
				)
				self.logh['RotatingFileHandler'].setFormatter(formatter)
				self.log.addHandler(self.logh['RotatingFileHandler'])
				msg = _('using `%s\' for logging messages.')
				self.log.info(msg % x)

			except IOError:
				# you probably don't have the file permissions
				# to open the file. you probably need root.
				msg = _('unable to open `%s\' for logging messages.')
				self.log.warn(msg % x)

			finally:
				if 'RotatingFileHandler' in self.logh:
					del self.logh['RotatingFileHandler']


	def get_log(self, name=None):
		"""return a handle to the main logger or optionally to
		an additional handler should you specify the name. if
		the additional handler doesn't exist, then it will be
		created."""

		if name is None:
			return self.log

		elif name in self.logs:
			return self.logs[name]

		else:
			# handlers in x propagate down to everyone (y)
			# in the x.y tree
			self.logs[name] = \
			logging.getLogger('%s.%s' % (self.name, name))
			return self.logs[name]


if __name__ == '__main__':
	import sys
	name = os.path.splitext(os.path.basename(__file__))[0]
	obj = logginghelp(name, showhello=True, mykerning=3, defxdgstr=name)
	log = obj.get_log()
	log.info('argv: %s' % ', '.join(sys.argv))

