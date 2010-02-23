#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Recipes for adding magic to terminals.

Useful classes for doing lightweight terminal magic without requiring *curses
libraries. Adds some polish to simple terminal apps.
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

# original version by Edward Loper: http://code.activestate.com/recipes/475116/
# progressbar2 by Nadia Alramli: http://nadiana.com/animated-terminal-progress-bar-in-python
# modified by James Shubin <purpleidea@gmail.com>

import sys
import re
import struct				# for refresh()
import fcntl				# for refresh()
import termios				# for refresh()

__all__ = ['TerminalController', 'ProgressBar', 'Block', 'ProgressBar2']

class TerminalController:
	"""A class that can be used to portably generate formatted output to a
	terminal.

	`TerminalController' defines a set of instance variables whose values
	are initialized to the control sequence necessary to perform a given
	action. These can be simply included in normal output to the terminal:

		>>> term = TerminalController()
		>>> print 'This is '+term.GREEN+'green'+term.NORMAL

	Alternatively, the `render()' method can used, which replaces
	'${action}' with the string required to perform 'action':

		>>> term = TerminalController()
		>>> print term.render('This is ${GREEN}green${NORMAL}')

	If the terminal doesn't support a given action, then the value of the
	corresponding instance variable will be set to ''.  As a result, the
	above code will still work on terminals that do not support colour,
	except that their output will not be coloured. Also, this means that you
	can test whether the terminal supports a given action by simply testing
	the truth value of the corresponding instance variable:

		>>> term = TerminalController()
		>>> if term.CLEAR_SCREEN:
		...	 print 'This terminal supports clearing the screen.'

	Finally, if the width and height of the terminal are known, then they
	will be stored in the `COLS' and `LINES' attributes."""

	# sound:
	BELL = ''		# make the terminal sound

	# cursor movement:
	BOL = ''		# move the cursor to the beginning of the line
	UP = ''			# move the cursor up one line
	DOWN = ''		# move the cursor down one line
	LEFT = ''		# move the cursor left one char
	RIGHT = ''		# move the cursor right one char

	# deletion:
	CLEAR_SCREEN = ''	# clear the screen and move to home position
	CLEAR_EOL = ''		# clear to the end of the line
	CLEAR_BOL = ''		# clear to the beginning of the line
	CLEAR_EOS = ''		# clear to the end of the screen

	# output modes:
	BOLD = ''		# turn on bold mode
	BLINK = ''		# turn on blink mode
	DIM = ''		# turn on half-bright mode
	REVERSE = ''		# turn on reverse-video mode
	UNDERLINE = ''		# turn on underline mode
	NORMAL = ''		# turn off all modes

	# cursor display:
	HIDE_CURSOR = ''	# make the cursor invisible
	SHOW_CURSOR = ''	# make the cursor visible

	# terminal size:
	COLS = None		# width of the terminal (None for unknown)
	LINES = None		# height of the terminal (None for unknown)

	# foreground colours:
	BLACK = BLUE = GREEN = CYAN = RED = MAGENTA = YELLOW = WHITE = ''

	# background colours:
	BG_BLACK = BG_BLUE = BG_GREEN = BG_CYAN = ''
	BG_RED = BG_MAGENTA = BG_YELLOW = BG_WHITE = ''

	_STRING_CAPABILITIES = """BELL=bel
	BOL=cr UP=cuu1 DOWN=cud1 LEFT=cub1 RIGHT=cuf1
	CLEAR_SCREEN=clear CLEAR_EOL=el CLEAR_BOL=el1 CLEAR_EOS=ed
	BOLD=bold BLINK=blink DIM=dim REVERSE=rev UNDERLINE=smul NORMAL=sgr0
	HIDE_CURSOR=cinvis SHOW_CURSOR=cnorm""".split()	# is it civis or cinvis?
	_COLORS = """BLACK BLUE GREEN CYAN RED MAGENTA YELLOW WHITE""".split()
	_ANSICOLORS = "BLACK RED GREEN YELLOW BLUE MAGENTA CYAN WHITE".split()

	def __init__(self, term_stream=sys.stdout):
		"""Create a `TerminalController` and initialize its attributes
		with appropriate values for the current terminal. `term_stream`
		is the stream that will be used for terminal output; if this
		stream is not a tty, then the terminal is assumed to be a dumb
		terminal (i.e., has no capabilities)."""
		# curses isn't available on all platforms
		try: import curses
		except: return

		# if the stream isn't a tty, then assume it has no capabilities.
		if not hasattr(term_stream, 'isatty') or not term_stream.isatty():
			return

		# check the terminal type.  if we fail, then assume that the
		# terminal has no capabilities.
		try: curses.setupterm()
		except: return

		# look up numeric capabilities.
		self.COLS = curses.tigetnum('cols')
		self.LINES = curses.tigetnum('lines')
		
		# look up string capabilities.
		for capability in self._STRING_CAPABILITIES:
			(attrib, cap_name) = capability.split('=')
			setattr(self, attrib, self._tigetstr(cap_name) or '')

		# colours
		set_fg = self._tigetstr('setf')
		if set_fg:
			for i,color in zip(range(len(self._COLORS)), self._COLORS):
				setattr(self, color, curses.tparm(set_fg, i) or '')
		set_fg_ansi = self._tigetstr('setaf')
		if set_fg_ansi:
			for i,color in zip(range(len(self._ANSICOLORS)), self._ANSICOLORS):
				setattr(self, color, curses.tparm(set_fg_ansi, i) or '')
		set_bg = self._tigetstr('setb')
		if set_bg:
			for i,color in zip(range(len(self._COLORS)), self._COLORS):
				setattr(self, 'BG_'+color, curses.tparm(set_bg, i) or '')
		set_bg_ansi = self._tigetstr('setab')
		if set_bg_ansi:
			for i,color in zip(range(len(self._ANSICOLORS)), self._ANSICOLORS):
				setattr(self, 'BG_'+color, curses.tparm(set_bg_ansi, i) or '')


	def _tigetstr(self, cap_name):
		# string capabilities can include "delays" of the form "$<2>".
		# for any modern terminal, we should be able to just ignore
		# these, so strip them out.
		import curses
		cap = curses.tigetstr(cap_name) or ''
		return re.sub(r'\$<\d+>[/*]?', '', cap)


	def render(self, template, magic=True):
		"""Replace each $-substitutions in the given template string
		with the corresponding terminal control string (if it's defined)
		or '' (if it's not). When magic is True, then return a magic
		string class instead of a normal string when needed. The magic
		string returns the actual printed length instead of byte string
		length. It also provides an intelligent truncate() method."""
		if magic:
			class mystr(str):
				"""String class for setting length manually."""
				def __new__(self, value, length=None):
					# specify a length when needed
					if isinstance(length, int):
						self.__length = length
						# sneak in the template! (shh!)
						self.__template = template
					return str.__new__(self, value)

				def __len__(self):
					try:
						# return specified length
						return self.__length
					except AttributeError:
						# return real length
						return str.__len__(self)

				def truncate(self, length):
					"""Truncates a string to length."""
					# check length appropriately
					if len(self) > length:
						# XXX XXX XXX XXX XXX XXX XXX
						# if we *have* to truncate,
						# strip out text chars, but not
						# control characters, since
						# they don't contribute to the
						# visible length of the string.
						# we would have to parse the
						# template which is provided
						# and take out only non control
						# chars. this is a bit tricky
						# to write and will be deferred
						# for now.
						return self[0:length]	# XXX BAD
					else:
						# no truncation
						return str(self)

			func = self._render_sub_clean
		else:
			func = self._render_sub

		# do the rendering
		result = re.sub(r'\$\$|\${\w+}', func, template)

		if magic:
			# recurse to get the rendered string
			rendered = self.render(template, magic=False)
			length = len(result)
			# if they're the same string, the just return normally
			if len(rendered) == length:
				return rendered
			else:
				return mystr(rendered, length)
		else:
			return result


	def _render_sub(self, match):
		s = match.group()
		if s == '$$': return s
		else: return getattr(self, s[2:-1])


	def _render_sub_clean(self, match):
		"""Doesn't add in the control codes."""
		s = match.group()
		if s == '$$': return s
		else: return ''


	def refresh(self):
		"""refresh any parameters that may change and need updating."""
		# TODO: this only refreshes COLS and LINES; if there are other
		# parameters that change, then add the code to refresh them too
		fd = sys.stdout.fileno()
		winsize = struct.pack('HHHH', 0, 0, 0, 0)
		winsize = fcntl.ioctl(fd, termios.TIOCGWINSZ, winsize)
		result = struct.unpack('HHHH', winsize)

		self.COLS = result[1]
		self.LINES = result[0]


class ProgressBar:
	"""A 3-line progress bar, which looks like:

				Header
	20% [===========----------------------------------]
			progress message

	the progress bar is coloured, if the terminal supports colour output; and
	adjusts to the width of the terminal."""

	BAR = '%3d%% ${GREEN}[${BOLD}%s%s${NORMAL}${GREEN}]${NORMAL}\n'
	HEADER = '${BOLD}${CYAN}%s${NORMAL}\n\n'

	def __init__(self, term, header):
		self.term = term
		if not (self.term.CLEAR_EOL and self.term.UP and self.term.BOL):
			raise ValueError("Terminal isn't capable enough -- you "
			"should use a simpler progress display.")
		self.width = self.term.COLS or 75
		self.bar = term.render(self.BAR)
		self.header = self.term.render(self.HEADER % header.center(self.width))
		self.cleared = True	# true if we haven't drawn the bar yet.
		self.update(0, '')


	def update(self, percent, message):
		if self.cleared:
			sys.stdout.write(self.header)
			self.cleared = False
		n = int((self.width-10)*percent)
		sys.stdout.write(
			self.term.BOL + self.term.UP + self.term.CLEAR_EOL +
			(self.bar % (100*percent, '='*n, '-'*(self.width-10-n))) +
			self.term.CLEAR_EOL + message.center(self.width))


	def clear(self):
		if not self.cleared:
			sys.stdout.write(self.term.BOL + self.term.CLEAR_EOL +
					self.term.UP + self.term.CLEAR_EOL +
					self.term.UP + self.term.CLEAR_EOL)
			self.cleared = True


class Block:
	"""a block class to aid in the implementing of gterminal."""

	def __init__(self, term):
		self.term = term
		self.cleared = False
		self.lines = 0


	def settc(self, tc=None):
		"""update the terminal controller. (useful for sigwinch)"""
		if tc is None or not(isinstance(tc, TerminalController)):
			tc = TerminalController()

		self.term = tc


	def update(self, *lines):
		"""write out each line. doesn't check for cleared status."""
		# either pass a list of strings or a string in each arg
		if len(lines) == 1 and type(lines[0]) is list: lines = lines[0]
		for (index, item) in enumerate(list(lines)):
			# write out each line, truncating at max width
			# if the string contains special formatting for term
			# colours or otherwise, it appears longer than it
			# actually is, and characters get truncated. to solve
			# this a magic string is sometimes returned by the tc
			# render function which has a magic length and a magic
			# truncate function that works properly. use the
			# truncate function if it exists.
			if hasattr(item, 'truncate'):
				truncated = item.truncate(self.term.COLS)
			else:	truncated = item[:self.term.COLS]
			sys.stdout.write(truncated)
			sys.stdout.flush()
			if index < len(lines)-1: sys.stdout.write('\n')

		self.lines = index + 1	# number of lines written
		self.cleared = False


	def clear(self):
		"""clear the allocated block of lines only after an update."""
		if self.cleared: return

		for i in range(self.lines):
			if i == 0:
				# goto beginning of line
				sys.stdout.write(self.term.BOL)
			else:
				# clear each extra line
				sys.stdout.write(self.term.UP)

			# and clear until the end
			sys.stdout.write(self.term.CLEAR_EOL)

		self.cleared = True


class ProgressBar2():
	"""terminal progress bar class"""
	TEMPLATE = (
	 '%(percent)-2s%% %(color)s%(progress)s%(normal)s%(empty)s %(message)s\n'
	)
	PADDING = 7

	def __init__(self, color=None, width=None, block='█', empty=' '):
		"""
		color -- color name (BLUE GREEN CYAN RED MAGENTA YELLOW WHITE BLACK)
		width -- bar width (optinal)
		block -- progress display character (default '█')
		empty -- bar display character (default ' ')"""
		self.term = TerminalController()
		if color:
			self.color = getattr(self.term, color.upper())
		else:
			self.color = ''
		if width and width < self.term.COLS - self.PADDING:
			self.width = width
		else:
			# adjust to the width of the terminal
			self.width = self.term.COLS - self.PADDING
		self.block = block
		self.empty = empty
		self.progress = None
		self.lines = 0


	def render(self, percent, message = ''):
		"""Print the progress bar
		percent -- the progress percentage %
		message -- message string (optional)"""
		inline_msg_len = 0
		if message:
			# the length of the first line in the message
			inline_msg_len = len(message.splitlines()[0])
		if inline_msg_len + self.width + self.PADDING > self.term.COLS:
			# the message is too long to fit in one line.
			# adjust the bar width to fit.
			bar_width = self.term.COLS - inline_msg_len -self.PADDING
		else:
			bar_width = self.width

		# check if render is called for the first time
		if self.progress != None:
			self.clear()
		self.progress = (bar_width * percent) / 100
		data = self.TEMPLATE % {
			'percent': percent,
			'color': self.color,
			'progress': self.block * self.progress,
			'normal': self.term.NORMAL,
			'empty': self.empty * (bar_width - self.progress),
			'message': message
		}
		sys.stdout.write(data)
		sys.stdout.flush()
		# the number of lines printed
		self.lines = len(data.splitlines())


	def clear(self):
		"""Clear all printed lines"""
		sys.stdout.write(
			self.lines * (self.term.UP + self.term.BOL + self.term.CLEAR_EOL)
		)


if __name__ == '__main__':
	if not(len(sys.argv) > 1 and sys.argv[1] in __all__):
		commands = ' | '.join(__all__)
		print 'usage: %s %s' % (sys.argv[0], commands)
		sys.exit(1)

	if sys.argv[1] == 'TerminalController':
		term = TerminalController()
		print term.render('${YELLOW}Warning:${NORMAL}'), 'i warned you!'
		print term.render('${RED}Error:${NORMAL}'), 'bad fail, ahhh...'

	elif sys.argv[1] == 'ProgressBar':
		import time
		term = TerminalController()
		progress = ProgressBar(term, 'Processing some files')
		filenames = ['this', 'that', 'other', 'foo', 'bar', 'baz']
		for i, filename in zip(range(len(filenames)), filenames):
			progress.update(float(i)/len(filenames), 'working on %s' % filename)
			time.sleep(1)
		progress.clear()

	elif sys.argv[1] == 'Block':
		print 'sorry, no fun examples are available.'

	elif sys.argv[1] == 'ProgressBar2':
		import time
		p = ProgressBar2('blue', width=20, block='▣', empty='□')
		for i in range(101):
			p.render(i, 'step %s\nProcessing...\nDescription: write something.' % i)
			time.sleep(0.1)

