#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Yamlhelp wrapper to simplify yaml reading and writing for me.

This class was created to abstract away many of the yaml calls which I didn't
want to think about and see. It needs some love if it wants to be a more useful
library.
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

import yaml
import os	# for os.linesep

# TODO: rewrite yamlhelp class to provide useful one liner functions to call.
class yamlhelp:

	def __init__(self, filename):
		# TODO: should we use: os.path.abspath ?
		self.filename = filename


	def get_yaml(self):
		"""load data from a yaml file"""

		data = None
		try:
			f = None
			f = open(self.filename, 'r')
			text = f.read()	# read it all
			#text = self.tabs2spaces(text)

			try:
				data = yaml.load(text)

			except yaml.scanner.ScannerError, e:
				#return None
				raise SyntaxError("yaml error: `%s', with: `%s'" % (str(e), self.filename))

		except IOError, e:
			raise IOError(e)
			#pass


		finally:
			try: f.close()
			except: pass
			f = None

		return data


	def put_yaml(self, data, mode='w+'):
		"""dump data into a yaml file"""

		try:
			f = None
			f = open(self.filename, mode)	# overwrite is default
			try:
				text = yaml.dump(data)

			except yaml.scanner.ScannerError, e:
				#return None
				raise SyntaxError("yaml error: `%s', with: `%s'" % (str(e), self.filename))

			#text = self.spaces2tabs(text)


			f.writelines(text)

		except IOError, e:
			raise IOError(e)
			#pass

		finally:
			try: f.close()
			except: pass
			f = None

		return None


	def tabs2spaces(self, text):
		"""this converts a nicely tabbed version into yaml load input."""
		return text.replace('\t', ' '*8)


	def spaces2tabs(self, text):
		"""this converts yaml dump output into a nicely tabbed version."""

		# TODO: this version of the function doesn't work properly!
		# it needs to be fixed-- it leaves extra spaces. see below.

		text = text.splitlines()	# make an array of the lines
		for i in range(len(text)):		# for each line...

			c = text[i].count('  ')	# how many pairs of spaces are there.
			# remove all except the last two, because those are probably the `  ' under a: `- ' for a list.
			text[i] = text[i].replace('  ', '\t', c-1)

		text = map(lambda x: x+os.linesep, text)	# add a newline onto the end of each line
		return ''.join(text)

		# TODO: make this function. i had a simple version but it doesn't work properly.
		# what is below is excerpts from the trials and is a mess of partially finished-ness

		### uhh append keep levels as we descend into deeper hierarchy in the text, and remove and use as we ascend back up?
		"""
		keep = []			# number of pairs of spaces to not replace away
		keep.append(0)
		text = text.splitlines()	# make an array of the lines
		for i in range(len(text)):		# for each line...
			lstrip = text[i].lstrip()	# strip off leading whitespace
			wc = len(text[i]) - len(lstrip)	# how many whitespace chars were removed

			c = text[i].count('  ')	# how many pairs of spaces are there.
			# remove all except the last two, because those are probably the `  ' under a: `- ' for a list.
			text[i] = text[i].replace('  ', '\t', c-1)

			# for the child
			if lstrip[0:2] == '- ':
				keep = 1

			if different len:
				keep = 0

		text = map(lambda x: x+os.linesep, text)	# add a newline onto the end of each line
		"""


if __name__ == '__main__':
	# TODO: run some yaml code here.
	print 'TODO: run some yaml code.'

