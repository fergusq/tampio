#!/usr/bin/env python3

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

import os, sys, traceback, argparse, operator, re, readline, atexit
from grammar import *
from fatal_error import fatalError, StopEvaluation

stack = []

# Prints stack traces
def printStack():
	sys.stderr.write("Stack:\n")
	for val in stack:
		sys.stderr.write("  " + val.str() + "\n")
	if debug:
		sys.stderr.write("Defs:\n")
		for defi in DEFS:
			sys.stderr.write("  " + defi.str() + "\n")
	raise(StopEvaluation())

# Fully evaluates an expression
def evals(tree):
	a = evals_(tree)
	c = a.copy()
	while True:
		if visualize:
			print(a.inflect("nimento"))
		b = evals_(a)
		if c.safeEq(b, numOpt=False):
			break
		a = b
		c = a.copy()
	if debug and verbosity >= 1:
		print("\x1b[1;4;31mEnd:\x1b[0m " + a.str())
	return a

# Evaluates an expression lazily (ie. evaluates the uppermost calls, but not arguments)
def evals_(tree, objects=[]):
	for obj in objects:
		if obj is tree:
			return tree
	objects = objects + [tree]
	global stack
	stack += [tree]
	try:
		if magic:
			for opt in OPTIMIZATIONS:
				if opt.match(tree):
					new_tree = opt.optimize(tree)
					if debug and verbosity >= 1:
						print(" "*len(stack) + "\x1b[1;4;31mMatch:\x1b[0m " + tree.str() + " \x1b[1;33m(opt) \x1b[1;4;34m->\x1b[0m " + new_tree.str())
					return new_tree
			for bi in BUILTINS:
				if bi.match(tree):
					if debug and verbosity >= 1:
						print(" "*len(stack) + "\x1b[1;4;31mMatch:\x1b[0m " + tree.str() + " \x1b[1;33m(builtin)\x1b[0m")
					return bi.eval(tree)
		for defi in DEFS:
			ok, subs = defi.left.match(tree)
			if ok:
				for var, body in defi.where[::-1]:
					if var in subs:
						sys.stderr.write("Error: Illegal redefinition of " + var + "\n")
						raise(StopEvaluation())
					subs[var] = body.subs(subs)
				rightsubs = defi.right.subs(subs) if len(subs) > 0 or (defi.always and (impure or not freeMode)) else defi.right
				if debug and verbosity >= 1:
					print(" "*len(stack) + "\x1b[1;4;31mMatch:\x1b[0m " + tree.str() + " \x1b[1;4;34m==\x1b[0m " + defi.left.str() + " \x1b[1;4;34m->\x1b[0m " + rightsubs.str())
				return rightsubs
			elif debug and verbosity >= 2:
				print(" "*len(stack) + "\x1b[1;4;31mNO MATCH:\x1b[0m " + tree.str() + " \x1b[1;4;34m!=\x1b[0m " + defi.left.str() + " \x1b[1;33m(def)\x1b[0m")
		if isinstance(tree, CallTree):
			tree.head = evals_(tree.head, objects)
			if tree.getHead() in FUNCTIONS:
				tree.args = [evals_(arg, objects) if not wildcard else arg for arg, wildcard in zip(tree.args, FUNCTIONS[tree.getHead()])]
			else:
				tree.args = [evals_(arg, objects) for arg in tree.args]
		return tree
	except StopEvaluation as e:
		raise(e)
	except KeyboardInterrupt:
		traceback.print_exc(file=sys.stderr)
		sys.stderr.write(str(e) + "\n")
		printStack()
	except Exception as e:
		traceback.print_exc(file=sys.stderr)
		sys.stderr.write(str(e) + "\n")
		printStack()
	finally:
		del stack[-1]

def evalFile(filename):
	with open(filename) as lines:
		try:
			while True:
				line = next(lines)
				if line == "\n":
					continue
				while line[-2] == "\\":
					line = line[:-2]
					line += next(lines)
				try:
					evalLine(line)
				except StopEvaluation as e:
					raise(e)
		except StopIteration:
			pass

def evalLine(line, allowQueries=False):
	global DEFS
	output = lexLine(line)
	if not output:
		return
	if debug and verbosity >= 0:
		print(tokensToString(output))
	if not allowQueries:
		eqs = parseWhen(output)
	else:
		eqs = [parseEq(output, True)]
	if len(output) != 0:
		fatalError("Syntax error: expected eof, got " + tokensToString(output))
	for eq in eqs:
		if debug and verbosity >= 0:
			print(eq.str())
		if eq.query():
			return evals(eq.left)
		elif eq.op == "#olla":
			DEFS += [eq]
			if not freeMode:
				if isinstance(eq.left, CallTree):
					t = eq.left.getHead()
					FUNCTIONS[t] = [
						flag and (isinstance(arg, VarTree) and arg.isWildcard())
						for arg, flag in zip(eq.left.args, FUNCTIONS[t] if t in FUNCTIONS else [True for x in range(len(eq.left.args))])
					]
				else:
					FUNCTIONS[eq.left] = []

def evalExpression(string):
	output = lexLine(string)
	eq = parseEq(output, True)
	if len(output) != 0:
		fatalError("Syntax error: expected eof, got " + tokensToString(output))
	if not eq.query():
		fatalError("Syntax error: expected expression, got declaration")
	return evals(eq.left)

# In the restricted mode, pattern matching against functions is forbidden.
# This function checks if there are any such forbidden patterns and
# reports the errors.
def checkFunctionMatching():
	a = True
	if not freeMode:
		for defi in DEFS:
			if isinstance(defi.left, CallTree):
				if defi.left.head.containsFunctions():
					functionMatchingError(defi.left)
					a = False
				for arg in defi.left.args:
					if arg.containsFunctions():
						functionMatchingError(defi.left)
						a = False
						break
	return a

def functionMatchingError(left):
	sys.stderr.write("Error: pattern matching against functions is forbidden in the restricted mode (" + left.inflect("nimento") + ")\n")

# This class represents an optimization of a operator handling numbers
# It allows together with NumTree efficient calculations even though
# the standard library implementation of integers is very unefficient.
class OptimizeOperator:
	def __init__(self, operator, opcase, argcases, ok, fun):
		self.operator = operator
		self.opcase = opcase
		self.argcases = argcases
		self.ok = ok
		self.fun = fun
	def match(self, tree):
		if isinstance(tree, CallTree) and tree.headIs(self.operator, self.opcase, self.argcases):
			if all([isinstance(arg, NumTree) for arg in tree.args]):
				return self.ok(*[arg.num for arg in tree.args])
	def optimize(self, tree):
		return NumTree(self.fun(*[arg.num for arg in tree.args]))

OPTIMIZATIONS = [
	OptimizeOperator("$seuraaja", "", ("omanto",), lambda x: True, lambda x: x + 1),
	OptimizeOperator("$plus", "", ("", ""), lambda x, y: True, lambda x, y: x + y),
	OptimizeOperator("$miinus", "", ("", ""), lambda x, y: x >= y, lambda x, y: x - y),
	OptimizeOperator("$kerrottu", "olento", ("", "ulkoolento"), lambda x, y: True, lambda x, y: x * y),
	OptimizeOperator("$jaettu", "olento", ("", "ulkoolento"), lambda x, y: y != 0, lambda x, y: x // y),
	OptimizeOperator("$modulo", "", ("", ""), lambda x, y: True, lambda x, y: x % y)
]

class Builtin:
	def __init__(self, operator, opcase, argcases, ok, fun):
		self.operator = operator
		self.opcase = opcase
		self.argcases = argcases
		self.ok = ok
		self.fun = fun
	def match(self, tree):
		if isinstance(tree, CallTree) and tree.headIs(self.operator, self.opcase, self.argcases):
			return self.ok(*tree.args)
	def eval(self, tree):
		return self.fun(*tree.args)

worldCounter = 0

def checkWorld(w):
	global worldCounter
	if w.counter != worldCounter:
		fatalError("Error: impossible time travel")
	worldCounter += 1
	return w.nextWorld()

def createPair(output, w):
	return CallTree(VarTree("$pari"), [output, checkWorld(w)], "olento", ("", "ulkotulento"))

def writeOutput(tree, w):
	print(evals(tree).inflect("nimento"))
	return createPair(VarTree("$tyhjyys"), w)

BUILTINS = [
	Builtin("$luettu", "olento", ("", "sisaeronto"),
		lambda l, w: isinstance(w, WorldTree),
		lambda l, w: createPair(evalExpression(input(l.inflect("nimento") + "> ")), w)
	),
	Builtin("$tulostettu", "olento", ("", "sisatulento"),
		lambda l, w: isinstance(w, WorldTree),
		writeOutput
	)
]

## Compiler (TODO)

def compileToHaskell():
	type_constructors = []
	print(TREES, "\n", FUNCTIONS)
	for tree in TREES:
		if tree not in FUNCTIONS:
			if isinstance(tree, tuple):
				s = "T" + headToHaskell(tree) + " " + " ".join(["STree"]*len(tree[2]))
			elif isinstance(tree, VarTree):
				s = "T" + varToHaskell(tree)
			if not isinstance(tree, NumTree):
				type_constructors += [s]
	print("data STree = " + " | ".join(type_constructors))
	
	for defi in DEFS:
		print(exprToHaskell(defi.left) + " = " + exprToHaskell(defi.right))

def varToHaskell(tree):
	return tree.name.replace("@", "m").replace("$", "s").replace(".", "x").replace("&", "k").replace("ä", "A").replace("ö", "O")

def headToHaskell(head):
	head, headInfl, argInfls = head
	return varToHaskell(head) + "_" + caseToHaskell(headInfl) + "_" + "_".join([caseToHaskell(case) for case in argInfls])

def caseToHaskell(case):
	return CASES_ABRV[case].replace("*", "_")

def exprToHaskell(expr):
	if isinstance(expr, VarTree):
		if expr.isWildcard():
			return varToHaskell(expr)
		elif expr in FUNCTIONS:
			return "f" + varToHaskell(expr)
		else:
			return "T" + varToHaskell(expr)
	elif isinstance(expr, NumTree):
		return str(expr.num)
	elif isinstance(expr, CallTree):
		if expr.getHead() in FUNCTIONS:
			prefix = "f"
		else:
			prefix = "T"
		return prefix + headToHaskell(expr.getHead()) + " " + " ".join(["(" + exprToHaskell(arg) + ")" for arg in expr.args])

debug = False
visualize = False
verbosity = 0
impure = False

TAMPIO_VERSION = "1.8"
INTERPRETER_VERSION = "2.6.0"

VERSION_STRING = "Tampio %s Interpreter v%s" % (TAMPIO_VERSION, INTERPRETER_VERSION)

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
STD_LIB = os.path.join(SCRIPT_DIR, 'std.suomi')

def main():
	global debug, visualize, verbosity, magic, freeMode, impure
	parser = argparse.ArgumentParser(description='Interprets Tampio code.')
	parser.add_argument('filename', type=str, nargs='?', help='source code file')
	parser.add_argument('-v', '--version', help='show version number and exit', action='store_true')
	
	compiler = parser.add_mutually_exclusive_group()
	free = compiler.add_mutually_exclusive_group()
	free.add_argument('-i', '--free-impure', help='enable impure free mode', action='store_true')
	free.add_argument('-p', '--free-pure', help='enable pure free mode', action='store_true')
	
	compiler.add_argument('--io', help='evaluate "maailman tulos" instead of "tulos"', action='store_true')
	compiler.add_argument('-H', '--to-haskell', help='compile to haskell', action='store_true')
	
	parser.add_argument('--no-magic', help='disable all optimizations and builtins', action='store_true')
	
	debugOptions = parser.add_argument_group('debug options')
	debugOptions.add_argument('--debug', help='enable debug mode', action='store_true')
	debugOptions.add_argument('-V', '--verbosity', help='verbosity level of debug information', action='count', default=0)
	debugOptions.add_argument('--visualize', help='enable inflected debug mode', action='store_true')
	args = parser.parse_args()
	
	if args.version:
		print(VERSION_STRING)
		sys.exit(0)
	
	freeMode = args.free_impure or args.free_pure
	impure = args.free_impure
	debug = args.debug
	magic = not args.no_magic
	verbosity = args.verbosity
	visualize = args.visualize
	
	try:
		evalFile(STD_LIB)
	except StopEvaluation:
		return
	
	if not checkFunctionMatching():
		sys.exit(1)
	
	if args.filename:
		try:
			evalFile(args.filename)
			if args.to_haskell:
				compileToHaskell()
			elif args.io:
				print(evals(CallTree(VarTree("$tulos"), [WorldTree(worldCounter)], "", ("omanto",))).inflect("nimento"))
			else:
				print(evals(parseVar("$tulos")).inflect("nimento"))
		except StopEvaluation:
			return
	else:
		
		histfile = os.path.join(os.path.expanduser("~"), ".tampio_history")
		try:
			readline.read_history_file(histfile)
			readline.set_history_length(1000)
		except FileNotFoundError:
			pass
		atexit.register(readline.write_history_file, histfile)
		
		print(VERSION_STRING + """
Copyright (C) 2017 Iikka Hauhio
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
Read the LICENSE file for details.""")
		while True:
			try:
				line = input(">>> ")
			except KeyboardInterrupt:
				pass
			except EOFError:
				print()
				break
			try:
				out = evalLine(line, True)
				if out:
					print(out.inflect("nimento"))
				else:
					checkFunctionMatching()
			except StopEvaluation:
				continue


if __name__ == "__main__":
	main()
