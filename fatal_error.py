# Tampio Interpreter
# Copyright (C) 2017 Iikka Hauhio

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import sys

def fatalError(msg):
	sys.stderr.write(msg + "\n")
	raise(StopEvaluation())

class StopEvaluation(Exception):
	pass

class TampioError(Exception):
	def __init__(self, msg, tokens=None, place=None):
		self.msg = msg
		self.tokens = tokens
		self.place = place
	def printMe(self, stream):
		if self.tokens and self.place:
			stream.write(self.msg + "\n" + self.tokens.fancyContext(self.place) + "\n")
		else:
			stream.write(self.msg + "\n")
	def __str__(self):
		if self.tokens  and self.place:
			return "Syntax error: " + self.msg + " (in \"" + self.tokens.context(self.place) + "\")"
		else:
			return self.msg

def syntaxError(msg, tokens, place=None):
	raise(TampioSyntaxError(msg, tokens, place if place else tokens.place()))

class TampioSyntaxError(TampioError):
	def __init__(self, msg, tokens, i):
		self.msg = "Syntax error: " + msg
		self.tokens = tokens
		self.place = i

def typeError(msg, tokens=None, place=None):
	raise(TampioError("Type error: " + msg, tokens, place))

def notfoundError(msg, tokens=None, place=None):
	raise(TampioError("Not found error: " + msg, tokens, place))

def warning(msg, tokens=None, place=None, severity="Warning"):
	if tokens and place:
		sys.stderr.write(severity + ": " + msg + "\n" + tokens.fancyContext(place) + "\n")
	else:
		sys.stderr.write(severity + ": " + msg + "\n")
