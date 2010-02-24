#!/usr/bin/python
# -*- coding: utf-8 -*-
"""distutils.command.build_manpages

Implements the Distutils 'build_manpages' command.
"""
# Copyright (C) 2009  James Shubin, McGill University
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

# created 2009/10/05, James Shubin

__revision__ = "$Id$"		# TODO: what should i do with this?

import os.path			# for os.path.isfile()
import distutils.core		# from distutils.core import Command
import distutils.command.build	# from distutils.command.build import build
import distutils.errors		# from distutils.errors import DistutilsOptionError
from jhelp import manhelp	# to generate man pages
_ = lambda x: x			# add fake gettext function until i fix up i18n


class build_manpages(distutils.core.Command):
	# FIXME: use the dry-run option...
	description = 'generates groff man pages from templates'
	user_options = [
		('psoutput=', 'p', 'specifies the ps output file location'),
		('gzoutput=', 'o', 'specifies the gzip output file location'),
		('template=', 't', 'specifies which man page template file'),
		('namespace=', 'n', 'specifies the manhelp namespace function'),
		('diroutput=', 'd', 'specifies the base directory for output'),
	]


	def initialize_options(self):
		self.psoutput = None
		self.gzoutput = None
		self.template = None
		self.namespace = {}
		self.diroutput = None


	def finalize_options(self):
		# do some validation
		if type(self.gzoutput) is not str:
			raise distutils.errors.DistutilsOptionError(
			_('the `gzoutput\' option is required.')
			)

		if not(type(self.template) is str) or \
		not(os.path.isfile(self.template)):
			raise distutils.errors.DistutilsOptionError(
			_('the `template\' option requires an existing file.')
			)

		# process self.namespace
		self.namespace = manhelp.acquire_namespace(self.namespace, \
							verbose=self.verbose)


	def run(self):
		if self.verbose: print 'diroutput is: %s' % self.diroutput
		if self.verbose: print 'namespace is: %s' % self.namespace
		if self.verbose: print 'template file is: %s' % self.template
		if self.verbose: print 'gzoutput file is: %s' % self.gzoutput
		if self.verbose and type(self.psoutput) is str:
			print 'psoutput file is: %s' % self.psoutput

		obj = manhelp.manhelp(self.template, self.namespace)
		obj.togzipfile(self.gzoutput)

		if type(self.psoutput) is str:
			obj.topsfile(self.diroutput)


# add this command as a dependency to the build command
# TODO: add a predicate that checks if the man page has been recently built
# FROM: http://docs.python.org/distutils/apiref.html#distutils.cmd.Command
# The parent of a family of commands defines sub_commands as a class attribute;
# it’s a list of 2-tuples (command_name, predicate), with command_name a string
# and predicate an unbound method, a string or None. predicate is a method of
# the parent command that determines whether the corresponding command is
# applicable in the current situation. (Eg. we install_headers is only
# applicable if we have any C header files to install.) If predicate is None,
# that command is always applicable.
distutils.command.build.build.sub_commands.append(('build_manpages', None))
