#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Installer for jhelp.
 
This installer packages together a set of miscellaneous libraries that I have
written or use often enough to warrant a dedicated repository to be shared by
relevant software that uses these. They are packaged under the name of jhelp.
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

import sys			# for sys.modules
import pydoc
import distutils.core		#from distutils.core import setup, Extension
import src.misc as misc		# i wrote this

# VARIABLES ###################################################################
description, ldescription = pydoc.splitdoc(pydoc.getdoc(sys.modules[__name__]))

# SETUP #######################################################################
distutils.core.setup(
	name = 'jhelp',
	version = misc.get_version(),
	author='James Shubin',
	author_email='purpleidea@gmail.com',
	url='http://www.cs.mcgill.ca/~james/code/',
	description=description,
	long_description=ldescription,
	# http://pypi.python.org/pypi?%3Aaction=list_classifiers
	classifiers=[
		'Intended Audience :: Developers',
		'License :: OSI Approved :: GNU Affero General Public License v3',
		'Topic :: Software Development :: Libraries'
	],
	packages = ['jhelp'],
	package_dir = {'jhelp':'src'},
	data_files = misc.get_capitalized_files()
)

