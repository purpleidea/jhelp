#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Setup file for jhelp.

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

import distutils.core		#from distutils.core import setup, Extension
import src.misc as misc		# i wrote this

# SETUP #######################################################################
distutils.core.setup(
	name = 'jhelp',
	version = misc.get_version(),
	packages = ['jhelp'],
	package_dir = {'jhelp':'src'},
	data_files = misc.get_capitalized_files()
)

