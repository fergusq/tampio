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

import argparse, readline, sys, traceback
from fatal_error import fatalError, StopEvaluation
from lex import lexCode
from grammar import parseDeclaration
from highlighter import prettyPrint, HIGHLIGHTERS

def compileCode(code):
	tokens = lexCode(code)
	decls = []
	while not tokens.eof():
		#try:
			decls += [parseDeclaration(tokens)]
		#except StopEvaluation as e:
		#	sys.stderr.write(str(e)+"\n")
		#	while not tokens.eof() and tokens.next().token != ".":
		#		pass
	return tokens, "\n".join([d.compile() for d in decls])

def createHTML(code):
	tokens, compiled = compileCode(code)
	ans = """<html><head><meta charset="utf-8" /><title>Imperatiivinen Tampio</title>"""
	ans += """<script type="text/javascript" src="itp.js" charset="utf-8"></script>"""
	ans += """<link rel="stylesheet" type="text/css" href="syntax.css"></head><body><pre>"""
	ans += prettyPrint(tokens, "html")
	ans += """</pre><script type="text/javascript">\n"""
	ans += compiled
	ans += """\ndocument.avautua__N();\n</script></body></html>"""
	return ans

TAMPIO_VERSION = "1.7"
COMPILER_VERSION = "1.10"
VERSION_STRING = "Tampio " + TAMPIO_VERSION + " Compiler " + COMPILER_VERSION

def main():
	parser = argparse.ArgumentParser(description='Compile Tampio to JavaScript.')
	parser.add_argument('-v', '--version', help='show version number and exit', action='store_true')
	compiler_group = parser.add_argument_group('compiler options')
	compiler_group.add_argument('filename', type=str, nargs='?', help='source code file')
	output_mode = compiler_group.add_mutually_exclusive_group()
	output_mode.add_argument('-s', '--syntax-markup', type=str, choices=HIGHLIGHTERS.keys(), help='do not compile, instead print the source code with syntax markup')
	output_mode.add_argument('-p', '--html-page', help='print a html page containing both compiled code and syntax markup', action='store_true')
	
	args = parser.parse_args()
	
	if args.version:
		print(VERSION_STRING)
		return
	
	if args.filename:
		try:
			with open(args.filename) as f:
				code = f.read()
				if args.html_page:
					print(createHTML(code))
				else:
					tokens, compiled = compileCode(code)
					if args.syntax_markup:
						print(prettyPrint(tokens, args.syntax_markup))
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
					print(prettyPrint(tokens, args.syntax_markup))
				else:
					print(compiled)
			except Exception:
				traceback.print_exc()

if __name__ == "__main__":
	main()
