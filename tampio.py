#!/usr/bin/env python3
#
# Tampio Interpreter
# Copyright (C) 2018 Iikka Hauhio
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

import argparse, readline, sys, traceback, os
from fatal_error import TampioSyntaxError
from lex import lexCode
from grammar import initializeParser, parseDeclaration
from highlighter import prettyPrint, HIGHLIGHTERS
from ast import initializeCompiler, compileModule

DEBUG = False
PRINT_INCLUDED = False

included_code = ""

def includeFile(filename):
	global included_code
	with open(filename) as f:
		_, ans, _ = compileCode(f.read())
		if PRINT_INCLUDED:
			included_code += ans

def compileCode(code):
	tokens = lexCode(code)
	decls = []
	num_errors = 0
	def handleError(e):
		nonlocal num_errors
		if DEBUG:
			traceback.print_exc()
		else:
			e.printMe(sys.stderr)
		while not tokens.eof() and tokens.next().token != ".":
			pass
		num_errors += 1
	initializeParser()
	while not tokens.eof():
		try:
			decls += [parseDeclaration(tokens)]
		except TampioSyntaxError as e:
			handleError(e)
	target_code = compileModule(decls, on_error=handleError)
	return tokens, target_code, num_errors

def createHTML(code):
	tokens, compiled, _ = compileCode(code)
	ans = """<!DOCTYPE html><html><head><meta charset="utf-8" /><title>Imperatiivinen Tampio</title>"""
	ans += """<script type="text/javascript" src="itp.js" charset="utf-8"></script>"""
	ans += """<link rel="stylesheet" type="text/css" href="syntax.css"></head><body>"""
	ans += """<div style="max-height:98vh;overflow:auto;float:left;width:50%;">"""
	ans += prettyPrint(tokens, "html")
	ans += """</div><div style="max-height:98vh;overflow:auto;float:right;width:calc(50% - 5px);padding-left:5px;"><div id="output"><script type="text/javascript">\n"""
	ans += included_code + "\n" + compiled
	ans += """\ndocument.avautua_A__N();\n</script></div></div></body></html>"""
	return ans

def createLatex(code):
	tokens, _, _ = compileCode(code)
	ans = """\\documentclass{article}\\usepackage[utf8]{inputenc}\\usepackage[T1]{fontenc}\\usepackage[finnish]{babel}"""
	ans += """\\title{Tampiokoodi}"""
	ans += """\\begin{document}\\setlength\\emergencystretch{\\hsize}"""
	ans += prettyPrint(tokens, "latex-lists")
	ans += "\\end{document}"
	return ans

TAMPIO_VERSION = "1.34"
COMPILER_VERSION = "1.45.0"
VERSION_STRING = "Tampio " + TAMPIO_VERSION + " Compiler " + COMPILER_VERSION

def main():
	global DEBUG, PRINT_INCLUDED
	parser = argparse.ArgumentParser(description='Compile Tampio to JavaScript.')
	parser.add_argument('-v', '--version', help='show version number and exit', action='store_true')
	parser.add_argument('--debug', help='enable debug mode', action='store_true')
	compiler_group = parser.add_argument_group('compiler options')
	compiler_group.add_argument('filename', type=str, nargs='?', help='source code file')
	compiler_group.add_argument('-i', '--print-included', help='print all included files in addition to the given file', action='store_true')
	output_mode = compiler_group.add_mutually_exclusive_group()
	output_mode.add_argument('-s', '--syntax-markup', type=str, choices=HIGHLIGHTERS.keys(), help='do not compile, instead print the source code with syntax markup')
	output_mode.add_argument('-p', '--html-page', help='print a html page containing both compiled code and syntax markup', action='store_true')
	output_mode.add_argument('-l', '--latex-document', help='print a latex document containing the code and markup', action='store_true')
	output_mode.add_argument('-V', '--validate-syntax', help='parse the code and print syntax errors', action='store_true')
	
	args = parser.parse_args()
	
	if args.version:
		print(VERSION_STRING)
		return
	
	if args.debug:
		DEBUG = True
	
	if args.print_included:
		PRINT_INCLUDED = True
	
	initializeCompiler(includeFile)
	
	# ladataan standardikirjasto
	includeFile(os.path.join(os.path.dirname(__file__), "std.itp"))
	
	if args.filename:
		with open(args.filename) as f:
			code = f.read()
			if args.html_page:
				print(createHTML(code))
			elif args.latex_document:
				print(createLatex(code))
			else:
				tokens, compiled, n = compileCode(code)
				if args.validate_syntax:
					print("OK" if n == 0 else "ERROR")
				elif args.syntax_markup:
					print(prettyPrint(tokens, args.syntax_markup))
				else:
					print(included_code+compiled)
				if n > 0:
					sys.exit(1)
	else:
		while True:
			try:
				code = input(">>> ")
				tokens, compiled, _ = compileCode(code)
				if args.validate_syntax:
					print("OK" if n == 0 else "ERROR")
				elif args.syntax_markup:
					print(prettyPrint(tokens, args.syntax_markup))
				else:
					print(compiled)
			except EOFError:
				print("")
				break
			except Exception:
				traceback.print_exc()

if __name__ == "__main__":
	main()
