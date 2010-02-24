#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Manhelp wrapper to simplify creation of man pages.

If you don't want to use a higher level documentation system, manhelp is a
simple, direct way (based on magic templates) to write *roff manuals, without
remembering nearly as much *roff as someone much more hardcore would expect you
to.
"""
# Copyright (C) 2009-2010  James Shubin, McGill University
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

# NOTE: a useful guide to actually writing man pages can be found at:
# http://www.schweikhardt.net/man_page_howto.html

# TODO: manhelp could be extended to aid in actually generating groff, e.g.:
# http://andialbrecht.wordpress.com/2009/03/17/creating-a-man-page-with-distutils-and-optparse/

import os
import re
import sys
import gzip
import subprocess
import Cheetah.Template
import Cheetah.NameMapper
_ = lambda x: x			# add fake gettext function until i fix up i18n

__all__ = ['manhelp', 'install', 'formatting', 'acquire_namespace']

class manhelp:

	def __init__(self, template, namespace={}):

		self.template = template
		self.namespace = namespace
		self.guessed = True	# did we guess the name and section# ?
		self.name = None
		self.section = None
		self.dirname = None

		# process template
		if os.path.isfile(self.template):
			self.groff = Cheetah.Template.Template(file=template, searchList=[namespace])
			# pattern: <name>.<section#>.template
			r = r'(?P<name>\w+).(?P<section>[1-9]).template'
			m = re.match(r, os.path.basename(self.template))
			if m is None: self.guessed = False
			else:
				self.name = m.group('name')
				self.section = int(m.group('section'))
				self.dirname = os.path.dirname(self.template)
		else:
			self.groff = Cheetah.Template.Template(template, searchList=[namespace])
			# TODO: in this case, we could add a simple parser or re
			# that goes through the template to find the guess data.
			self.guessed = False	# until then, it has to be false

		# make the groff...
		try:
			self.groff = str(self.groff)	# runs the NameMapper
		except Cheetah.NameMapper.NotFound, e:
			print >> sys.stderr, _('namespace error: %s' % e)
			self.groff = ''


	def tostdout(self):
		"""write groff output to stdout."""
		try:
			f = sys.stdout
			f.write(self.groff)
			f.close()
			return True
		except IOError, e:
			return False


	def tofile(self, filename=None, dirname=None):
		"""write groff man page output to a file."""
		if filename is None:
			if self.guessed:
				if dirname is None: dirname = self.dirname
				filename = os.path.join(dirname, '%s.%d' % (self.name, self.section))
			else:
				return False

		try:
			f = open(filename, 'w+')
			f.write(self.groff)
			f.close()
			return True
		except IOError, e:
			return False


	def topsfile(self, dirname=None):
		"""write groff man page output to a postscript (.ps) file."""
		# NOTE: this function requires the *guess* capability. i enforce
		# this so that the tofile() function can have a standard spot to
		# put it's output. this way we don't have to think about finding
		# a temporary filename for the initial manpage that gets created

		if self.guessed:
			if dirname is None: dirname = self.dirname
			filename = os.path.join(dirname, '%s.%d' % (self.name, self.section))
		else:
			return False

		self.tofile(dirname=dirname)	# make normal man page
		if not os.path.isfile(filename): return False
		try:
			f = open('%s.ps' % filename, 'w+')
			# groff -t -e -mandoc -Tps manpage.1 > manpage.1.ps
			cmd = ['groff', '-t', '-e', '-mandoc', '-Tps', filename]
			p = subprocess.Popen(cmd, stdout=f)
			f.close()
			return True
		except IOError, e:
			return False


	def togzipfile(self, filename=None):
		"""write groff man page output to a gzip (.gz) file."""
		if filename is None:
			if self.guessed:
				filename = os.path.join(self.dirname, '%s.%d.gz' % (self.name, self.section))
			else:
				return False
		try:
			f = gzip.open(filename, 'wb')
			f.write(self.groff)
			f.close()
			return True
		except IOError, e:
			return False


def formatting():
	"""returns a dict of special functions for use in groff formatting."""
	def header(name, section, date, version, title=''):
		"""writes out a .TH header properly."""
		# example groff for this command:
		#.TH PROGRAM_NAME 1 "2009-06-01" "$version" "???"
		#.TH FOO 1 "MARCH 1995" Linux "User Manuals"

		# the following chunk of code is pretty special. dir() works!
		#inspect.getargspec(formatting)[0] prints the same as dir()
		args = dir()	# get this out of comprehension scope
		# TODO: can we replace eval() with a getattr style thing ?
		args = dict([(arg, eval(arg)) for arg in args])
		# NOTE: section is a number; maybe we can avoid string sections
		return '.TH %(name)s %(section)d "%(date)s" "%(version)s" "%(title)s"' % args

	def option(long=None, short=None, description=None, meta=None):
		"""writes out an entry in the options section"""
		# example groff for this command:
		# .TP
		# \fB\-r\fR, \fB\-\-roption\fR
		# use the r option for magic roaring
		# .TP
		# \fB\-m\fR, \fB\-\-magic\fR=\fIMETA\fR
		# use META option as the magic operator

		if long is None and short is None: return ''
		result = '.TP\n'	# option definition start
		if type(short) is str: result += '\\fB\-%s\\fR' % short
		if type(short) is str and type(long) is str: result += ', '
		if type(long) is str: result += '\\fB\-\-%s\\fR' % long
		if type(meta) is str: result += '=\\fI%s\\fR' % meta
		if type(description) is str: result += '\n%s' % description
		return result

	def seealso(entries):
		"""format a list of (name, section) tuples as see also entries."""
		if type(entries) is not list: return ''
		return ',\n'.join(['.BR %s (%d)' % x for x in entries
		if len(x) == 2 and type(x[0]) is str and type(x[1]) is int])

	def code(text):
		"""return a chunk of code that will be formatted as such."""
		return '.nf\n%s\n.fi' % text

	return {
		# adds the main header/footer
		'header': header,
		# adds name - description line to manual
		'name_description': lambda x, y: '%s \- %s' % (x, y),
		# adds a section header
		'section': lambda x: '.SH %s' % x,
		# formats an option for options list
		'option': option,
		# adds a line break
		'break': lambda: '.br',
		# makes text bold
		'bold': lambda x: '.B %s' % x,
		# makes text underlined
		'underline': lambda x: '.I %s' % x,
		# adds a see also entry with section number
		'seealso': seealso,
		# adds a block of code
		'code': code
	}


def install(namespace, index=os.path.splitext(os.path.basename(__file__))[0]):
	"""adds the manhelp groff template helpers into index of namespace."""
	namespace[index] = formatting()


def acquire_namespace(namespace, verbose=False):
	"""attempt to acquire namespace data that corresponds to the
	magic namespace identifier, e.g. {name:value} or module:func
	if no valid data can be found, then return an empty dict."""

	# attempt to get a function or value externally
	if type(namespace) is str:
		namespace = namespace.strip()	# cleanup
		# looks like we might have a literal dictionary to eval()
		if (namespace[0], namespace[-1]) == ('{', '}'):
			if verbose:
				print >> sys.stderr, _('trying to parse a dictionary...')
			try:
				namespace = eval(namespace)
			except SyntaxError, e:
				print >> sys.stderr, _('error: %s, while parsing:' % e)
				print >> sys.stderr, '%s' % namespace
				return {}	# set a default

		# maybe this is a module to open and look inside of...
		elif namespace.count(':') == 1:	# e.g. module:[func|var]
			if verbose:
				print >> sys.stderr, _('trying to parse a pointer...')
			name, attr = namespace.split(':')
			try:
				module = __import__(name, fromlist=name.split('.'))
				result = getattr(module, attr)
				# if this is a function, run it...
				if type(result) is type(lambda: True):
					try:
						namespace = result()
					except Exception, e:
						if verbose:
							print >> sys.stderr, _('function execution failed with: %s' % e)
						return {}
				# or maybe it's just an attribute
				else:
					namespace = result

			except ImportError, e:
				if verbose:
					print >> sys.stderr, _('error importing: %s.' % name)
				return {}

			except AttributeError, e:
				if verbose:
					print >> sys.stderr, _('missing attribute: %s.' % attr)
				return {}

		# string doesn't seem to have a sensible pattern
		else:
			if verbose:
				print >> sys.stderr, _('namespace didn’t match any signatures.')
			return {}

	# after all of the above, check if there's a dictionary
	if not type(namespace) is dict:
		if verbose:
			print >> sys.stderr, _('the `namespace\' option must evaluate to a dictionary.')
		return {}

	return namespace


def main(argv):
	"""main function for running manhelp as a script utility."""
	# NOTE: if you run this program as: `./manhelp.py -m', you get -m to
	# stdout. this is because it assumes -m is the template. NOT a bug.
	def usage():
		"""print usage information."""
		# usage and other cool tips
		print _('usage: ./%s template [namespace] (groff to stdout)' % b)
		print _('extra: ./%s -m template [namespace] (groff to man)' % b)
		print _('extra: ./%s -z template [namespace] (write gz man)' % b)
		print _('extra: ./%s -p template [namespace] (write ps man)' % b)
		#print _('extra: ./%s template [namespace] | gzip -f > gzoutput.gz' % b)

	if not os.name == 'posix':
		# TODO: maybe we could add something for windows?
		print >> sys.stderr, _('sorry, your os cannot display man pages.')
		sys.exit(1)

	template = ''
	namespace = {}
	b = os.path.basename(argv[0])
	ps = False
	# TODO: in the future, when manhelp generates groff, we should add a gz
	# option that takes the man section number and writes out the name.#.gz
	# filename into the current directory. it makes sense to wait for groff
	# generation so that we can get the name and section number dynamically
	if len(argv) >= 3 and argv[1] in ['-m', '-z', '-p']:
		arg = argv.pop(1)
		if arg == '-m':
			# subprocess is pro magic. it's amazing that it works!
			# if you pay attention, the docs turn out to be great!
			# see: http://docs.python.org/library/subprocess.html
			p1 = subprocess.Popen(['python', b] + argv[1:3], stdout=subprocess.PIPE)
			p2 = subprocess.Popen(['man', '--local-file', '-'], stdin=p1.stdout)
			sts = os.waitpid(p2.pid, 0)	# important to wait!
			sys.exit()
		elif arg == '-z':
			raise NotImplementedError('auto generating gzip man pages is yet to come!')
			sys.exit()
		elif arg == '-p':
			ps = True

	if len(argv) == 3:
		namespace = acquire_namespace(argv[2], verbose=True)

	if len(argv) in [2, 3]:
		template = argv[1]
		obj = manhelp(template, namespace)
		if ps: obj.topsfile()
		else: obj.tostdout()
	else:
		usage()


if __name__ == '__main__':
	main(sys.argv)

