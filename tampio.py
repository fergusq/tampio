# Tampio Interpreter
# Copyright (C) 2017 Iikka Hauhio
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import argparse, readline, traceback
from fatal_error import fatalError, StopEvaluation
from lex import lexCode
from grammar import parseDeclaration

def compileCode(code):
	tokens = lexCode(code)
	decls = []
	while not tokens.eof():
		decls += [parseDeclaration(tokens)]
	return tokens, "\n".join([d.compile() for d in decls])

TAMPIO_VERSION = "1.0"
COMPILER_VERSION = "1.0"
VERSION_STRING = "Tampio " + TAMPIO_VERSION + " Compiler " + COMPILER_VERSION

def main():
	parser = argparse.ArgumentParser(description='Compile Tampio to JavaScript.')
	parser.add_argument('filename', type=str, nargs='?', help='source code file')
	parser.add_argument('-v', '--version', help='show version number and exit', action='store_true')
	parser.add_argument('-s', '--syntax-markup', help='do not compile, instead print the source code with syntax markup', action='store_true')
	
	args = parser.parse_args()
	
	if args.version:
		print(VERSION_STRING)
		return
	
	if args.filename:
		try:
			with open(args.filename) as f:
				code = f.read()
				tokens, compiled = compileCode(code)
				if args.syntax_markup:
					print(tokens.prettyPrint())
				else:
					print(compiled)
		except Exception:
			traceback.print_exc()
	else:
		while True:
			try:
				code = input(">>> ")
				tokens, compiled = compileCode(code)
				if args.syntax_markup:
					print(tokens.prettyPrint())
				else:
					print(compiled)
			except Exception:
				traceback.print_exc()

if __name__ == "__main__":
	main()
