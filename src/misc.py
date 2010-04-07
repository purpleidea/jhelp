#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Misc helper functions.

This is an assortment of small functions that don't belong anywhere important.
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
_ = lambda x: x			# add fake gettext function until i fix up i18n
__all__ = ('get_authors', 'get_license', 'get_version', 'get_home',
	'get_capitalized_files',
	'path_search',
)


def get_authors(wd=None):
	"""Little function that pulls the authors from a text file."""
	if wd is None: wd = os.getcwd()
	try:
		f = open(os.path.join(wd, 'AUTHORS'), 'r')
		authors = f.readlines()
		# assume it's an author if there is an email
		return [x.strip() for x in authors if '@' in x]
	except IOError:
		return []
	finally:
		try: f.close()
		except: pass
		f = None


def get_license(wd=None):
	"""Little function that pulls the license from a text file."""
	if wd is None: wd = os.getcwd()
	try:
		f = open(os.path.join(wd, 'COPYING'), 'r')
		return f.read().strip()
	except IOError:
		return None
	finally:
		try: f.close()
		except: pass
		f = None


def get_version(wd=None):
	"""Little function that pulls the version from a text file."""
	if wd is None: wd = os.getcwd()
	try:
		f = open(os.path.join(wd, 'VERSION'), 'r')
		return f.read().strip()
	except IOError:
		return '0.0'
	finally:
		try: f.close()
		except: pass
		f = None


def get_home():
	"""Returns the location of the users home directory."""
	return os.getenv('USERPROFILE', False) or os.getenv('HOME')


def get_capitalized_files(wd=None):
	"""Returns a list of files whose names are all capitalized."""
	if wd is None: wd = os.getcwd()
	files = os.listdir(wd)
	return [filename for filename in files if filename.isupper()]


def path_search(filename, paths=[]):
	"""Return the first full path to filename found in the search array."""
	# accepts either a list of paths, or a traditional path search string
	if isinstance(paths, str): paths = paths.split(':')
	for path in paths:
		f = os.path.join(path, filename)
		if os.path.isfile(f):
			return f
	return False


if __name__ == '__main__':
	# command line argument parsing
	import optparse
	description = _('Test out the various miscellaneous functions.')
	parser = optparse.OptionParser(description=description)
	parser = optparse.OptionParser()
	parser.add_option('-x', '--execute', dest='execute', choices=__all__,
		metavar=_('<function>'), help=_('execute this function')
	)
	(options, args) = parser.parse_args()

	if options.execute:
		print eval(options.execute)(*args)
	else:
		parser.error(_('No function specified.'))

