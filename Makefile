#
# Makefile for jhelp packages.
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


# version of the program
VERSION := $(shell cat VERSION)

# name of this project
NAME := $(shell basename `pwd` "-$(VERSION)")

# where am i ?
PWD := $(shell pwd)

# executables
RMTOOL = rm -i

# www source and metadata paths
WWW = $(PWD)/../www/code/$(NAME)/
METADATA = $(WWW)/$(NAME)
EXT = .tar.bz2

PREFIX = /usr/

.PHONY: all clean install uninstall purge man source www perms
.SILENT:


# if someone runs make without a target, print some useful messages
all:
	# list the available targets and what they do
	echo -e 'available targets:'
	echo -e '- clean:\tcleans up any files that can be generated again.'
	echo -e '- install:\tinstalls this package on the machine.'
	echo -e '- uninstall:\tuninstalls this package from the machine.'
	echo -e '- purge:\tdelete all traces of the install from the machine.'
	echo -e '- source:\tmake a source archive for distribution.'
	echo -e '- www:\t\tput an archive on the local webserver.'
	#echo -e '- man:\t\tbuild the man pages and then view them.'


# clean up any mess that can be generated
clean:
	# let distutils try to clean up first
	python setup.py clean
	# remove the generated manifest file
	if [ -e MANIFEST ]; then $(RMTOOL) MANIFEST; fi
	# remove distutils mess with -f because they're write protected
	if [ -e build/ ]; then $(RMTOOL) -rf build/; fi
	# remove any python mess (let above scripts rm the bulk first)
	find . -name '*.pyc' -type f -print0 | xargs -0 rm -f


# this installs code to your machine
install: clean
	python setup.py build
	sudo python setup.py install
	#sudo mandb	# update the man index for `apropos' and `whatis'


# uninstalls the package
uninstall:
	sudo python setup.py uninstall


# purge any unwanted files
purge: uninstall
#	# remove the install log file generated if it exists
	if [ -e install.log ]; then $(RMTOOL) install.log; fi
#	# empty man index even though it should eventually get updated by cron
#	#sudo mandb


# build the man pages, and then view them
#man:
#	python setup.py build_manpages
#	cd man/ ;\
#	./viewthis.sh


# make a source package for distribution
source: clean
	python setup.py sdist --formats=bztar


# move current version to www folder
www:
	# rsync directories so they are equivalent in terms of files with: $EXT
	rsync -avz --include=*$(EXT) --exclude='*' --delete dist/ $(WWW)
	# empty the file
	echo -n '' > $(METADATA)
	cd $(WWW); \
	for i in *$(EXT); do \
		b=$$(basename $$i $(EXT)); \
		V=$$(echo -n $$(basename "`echo -n "$$b" | rev`" \
		"`echo -n "$(NAME)-" | rev`") | rev); \
		echo $(NAME) $$V $$i >> $(METADATA); \
	done; \
	sort -V -k 2 -o $(METADATA) $(METADATA)		# sort by version key


# fix permissions of files to be installed so that they work properly
# TODO: this should be implemented as a distutils addon to affect the installed
perms:
	find . -type d -perm u=rwx -exec chmod go+rx {} \;
	find . -type f -perm u=rw -exec chmod go+r {} \;
	find . -type f -perm u=rwx -exec chmod go+rx {} \;

