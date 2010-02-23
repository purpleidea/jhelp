#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Dbushelp dbus functions to aid in playing with and learning about dbus.

Dbushelp is a library of helper functions for use with dbus. It is written in a
manner that makes the code easy to follow for new dbus programmers not familiar
with the dbus hierarchy of objects. The library helps to untangle the hierarchy
of the dbus design, to parse dbus xml introspection data, and more.
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

import dbus
import xml.etree.ElementTree

# read the docs to see the arguments you can add for more power!
# http://dbus.freedesktop.org/doc/dbus-python/api/dbus.proxies.ProxyObject-class.html#connect_to_signal
DBUS_SIGNAL_KEYWORDS = {	# a dictionary of sensible dbus signal keywords
	'sender_keyword': 'sender',
	'destination_keyword': 'destination',
	'interface_keyword': 'interface',
	'member_keyword': 'member',
	'path_keyword': 'path',
	'message_keyword': 'message'
}


# NOTES ON DBUS HIERARCHY #####################################################
# BUS TYPE		-> dbus.SessionBus() / dbus.SystemBus()
# BUSES			-> list_buses()
# OBJECT PATHS		-> list_objects()
# INTERFACES		-> list_interfaces()			eg: org.freedesktop.DBus.Properties / Introspectable
# METHODS/SIGNALS	-> list_methods() / list_signals()
# ARGS IN/OUT VALUES	-> list_arguments()


def introspect_object_xml(bus=dbus.SessionBus(), namedBus='org.freedesktop.DBus', objectPath='/'):
	"""returns xml introspect data of specified object path on bus name."""
	obj = bus.get_object(namedBus, objectPath)
	iface = dbus.Interface(obj, 'org.freedesktop.DBus.Introspectable')
	return iface.Introspect()


def list_buses(bus=dbus.SessionBus(), hideInactive=True, showPrivate=False, sort=True):
	"""list the various named buses on a particular dbus bus."""
	remote_object = bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
	interface = dbus.Interface(remote_object, 'org.freedesktop.DBus')
	# PICK WHETHER WE WANT ALL OR ACTIVE
	if hideInactive: a = interface.ListNames()
	else: a = interface.ListActivatableNames()
	arr = []

	for i in a:
		# private listings start with a :
		if not(i.startswith(':')) or showPrivate:
			arr.append(i)

	if sort: arr.sort()
	return arr


def list_objects(bus=dbus.SessionBus(), namedBus='org.freedesktop.DBus', objectPath='/'):
	"""return a list of object paths. eg: /this/is/an/object/path. this
	function has an extra parameter: objectPath which by default starts
	the search at `/' (the root) to be able to return the max possible.
	you can specify a different starting path, if you want a subset."""
	# NOTE: this function turned out to be a bit elusive because:
	# from: http://dbus.freedesktop.org/doc/dbus-specification.html#introspection-format
	# If a child <node> has any sub-elements, then they must represent a
	# complete introspection of the child. If a child <node> is empty, then
	# it may or may not have sub-elements; the child must be introspected
	# in order to find out. The intent is that if an object knows that its
	# children are "fast" to introspect it can go ahead and return their
	# information, but otherwise it can omit it.

	def pick_tag_from_list(arr, tag='interface'):
		"""return all elements in a list that have a particular tag."""
		return [x for x in arr if hasattr(x, 'tag') and x.tag == tag]

	objects = []	# list of found object paths to return

	# this function call *must* specify an objectPath which is not None
	assert objectPath is not None, 'objectPath must not be None'
	# get the xml that we need
	xml_output = introspect_object_xml(
		bus=bus, namedBus=namedBus, objectPath=objectPath
	)
	#print str(xml_output)		# debugging
	root = xml.etree.ElementTree.fromstring(xml_output)	# same as next 3
	#import StringIO
	#tree = xml.etree.ElementTree.parse(StringIO.StringIO(xml_output))
	#root = tree.getroot()

	# if this node has interfaces, then add this object path to list.
	if len(pick_tag_from_list(root.getchildren(), 'interface')) > 0:
		objects.append(objectPath)

	# iterate & recurse through any child nodes of type 'node'
	for i in pick_tag_from_list(root.getchildren(), 'node'):
		name = i.get('name')
		if name is not None:
			# avoid creating a path like: //org
			if objectPath == '/':
				newObjectPath = objectPath + name
			else:
				newObjectPath = objectPath + '/' + name
			result = list_objects(bus=bus, namedBus=namedBus, objectPath=newObjectPath)
			objects.extend(result)

	# remove duplicates and compare lengths. they should be the same
	assert len(objects) == len(list(set(objects))), 'duplicates found'
	return objects


def list_interfaces(bus=dbus.SessionBus(), namedBus='org.freedesktop.DBus', objectPath=None):
	"""return a list of interfaces on the particular object path."""
	interfaces = []	# list of found interfaces to return

	# XXX: if objectPath is None, use the first objectPath on a namedBus?
	# XXX: this can be found out with list_objects() function.
	assert objectPath is not None, 'objectPath must not be None'	# temp.
	# get the xml that we need
	xml_output = introspect_object_xml(
		bus=bus, namedBus=namedBus, objectPath=objectPath
	)
	root = xml.etree.ElementTree.fromstring(xml_output)

	for i in root.getchildren():
		if hasattr(i, 'tag') and i.tag == 'interface':
			interfaces.append(i.get('name'))

	return interfaces


def __list_interface_children(bus=dbus.SessionBus(), namedBus='org.freedesktop.DBus', objectPath='XXX', interface=None, tag='method'):
	"""return list of object methods or signals on an interface. this method
	exists as a helper to reuse code privately between list_methods and
	list_signals."""
	output = []
	if tag not in ('method', 'signal'):
		tag = 'method'

	# get the xml that we need
	xml_output = introspect_object_xml(
		bus=bus, namedBus=namedBus, objectPath=objectPath
	)
	#print xml_output
	# get the xml
	root = xml.etree.ElementTree.fromstring(xml_output)

	# get the list of interfaces with the interface name i want (from above)
	for i in [x for x in root.findall('interface') if x.get('name') == interface]:
		for j in i:
			if j.tag == tag:
				output.append(j.get('name'))
	return output


def list_methods(bus=dbus.SessionBus(), namedBus='org.freedesktop.DBus', objectPath='XXX', interface=None, returnObjects=False):
	"""return list of object methods on an interface."""

	result = __list_interface_children(
		bus=bus, namedBus=namedBus, objectPath=objectPath,
		interface=interface, tag='method'
	)

	# return the actual proxy functions instead of their names
	if returnObjects:
		remote_object = bus.get_object(namedBus, objectPath)
		iface = dbus.Interface(remote_object, interface)
		return [iface.get_dbus_method(x) for x in result]

	else: return result


def list_signals(bus=dbus.SessionBus(), namedBus='org.freedesktop.DBus', objectPath='XXX', interface=None):
	"""return list of object signals on an interface."""
	return __list_interface_children(
		bus=bus, namedBus=namedBus, objectPath=objectPath,
		interface=interface, tag='signal'
	)


def list_arguments(bus=dbus.SessionBus(), namedBus='org.freedesktop.DBus', objectPath='XXX', interface=None, method=None, signal=None):
	"""return list of arguments of a method or signal. use all desired
	parameters to this function and either method (for method name) or
	signal for signal name. the other should be omitted or be None."""
	args = []
	if not((method is None) ^ (signal is None)): return []
	if method is None:
		tag = 'signal'
		name = signal
	if signal is None:
		tag = 'method'
		name = method

	# get the xml that we need
	xml_output = introspect_object_xml(
		bus=bus, namedBus=namedBus, objectPath=objectPath
	)
	#print xml_output
	# get the xml
	root = xml.etree.ElementTree.fromstring(xml_output)
	# NOTE: root.findall('method') returns an empty string! (weird)
	for i in [x for x in root.findall('interface') if x.get('name') == interface]:
		for j in i:
			if j.tag == tag and j.get('name') == name:
				for k in j.getchildren():
					args.append(dict(k.items()))
				break
	return args


# function status: maybe keep
# FIXME: the default path of `/' is not necessarily correct. write the function to get paths on an object.
import dbus._expat_introspect_parser
def introspect_object(bus=dbus.SessionBus(), namedBus='org.freedesktop.DBus', objectPath=None):
	"""returns method list introspect data of specified object."""
	if objectPath is None:
		objects = list_objects(bus=bus, namedBus=namedBus)
		if len(objects) == 0: return {}
		else: objectPath = objects[0]	# pick the first one? XXX loop ?
		#else: objectPath = '/'	# XXX
	#else if type(objectPath) is str:

	obj = bus.get_object(namedBus, objectPath)
	iface = dbus.Interface(obj, 'org.freedesktop.DBus.Introspectable')
	func = dbus._expat_introspect_parser.process_introspection_data
	return func(iface.Introspect())




subset = []
#subset.append('org.gnome.ScreenSaver')
#subset.append('org.gnome.Nautilus')
#subset.append('org.bluez.applet')
subset.append('org.gnome.Do')
subset.append('org.gnome.Billreminder.Daemon')
if __name__ == '__main__':

	class testiter:

		def __init__(self):
			pass

		def dude(self):
			print 'dude'

		def __iter__(self):
			l = ['hey', 'man']
			# __iter__() needs an iterator as a result...
			for i in l:
				yield i

			#return list_to_generator(l)

		def __len__(self):
			return 99

	x = testiter()
#	print len(x)
# THIS ITERATOR WORKS
#	for i in x:
#		print i



	#print '# LISTNAMES:'
	print '#'*79
	for i in list_buses():
	#	if i not in subset: continue	# make visibility easier for now...
		print '* %s' % i
		for j in list_objects(namedBus=i):
			print '\t> %s' % j
			for k in list_interfaces(namedBus=i, objectPath=j):
				print '\t\t& %s' % k
				for l in list_methods(namedBus=i, objectPath=j, interface=k):
					print '\t\t\t@ (method) %s' % l
					for m in list_arguments(namedBus=i, objectPath=j, interface=k, method=l):
						print '\t\t\t\t%% %s' % str(m)[1:-1]
				print ''
				for l in list_signals(namedBus=i, objectPath=j, interface=k):
					print '\t\t\t@ (signal) %s' % l
					for m in list_arguments(namedBus=i, objectPath=j, interface=k, signal=l):
						print '\t\t\t\t%% %s' % str(m)[1:-1]

	print ''
		#for j in introspect_object(namedBus=i, process=True):
		#	print '\t) %s' % j

	#print '# INTROSPECT:'
	#print introspect_object_xml()

	#print '# INTROSPECT_OBJ:'
	#print introspect_object()

