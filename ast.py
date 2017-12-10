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

from inflect import CASES_ABRV
from fatal_error import fatalError

def typeToJs(typename):
	if typename == "luku":
		return "Number"
	elif typename == "sivu":
		return "HTMLDocument"
	else:
		return typename

class VariableDecl:
	def __init__(self, var, value):
		self.var = var
		self.value = value
	def __str__(self):
		return self.var + " := " + str(self.value)
	def compile(self):
		return "var " + self.var + " = " + self.value.compile() + ";"

class ProcedureDecl:
	def __init__(self, signature, body):
		self.signature = signature
		self.body = body
	def __str__(self):
		return "prodecure " + str(self.signature) + " { " + " ".join([str(s) for s in self.body]) + " }"
	def compile(self):
		if isinstance(self.signature, ProcedureCallStatement):
			return "function " + self.signature.compile(semicolon=False) + " {\n" + "".join([s.compile(indent=1) for s in self.body]) + "};"
		elif isinstance(self.signature, MethodCallStatement):
			if not isinstance(self.signature.obj, VariableExpr):
				fatalError("Illegal method declaration: subject is not a variable (in \"" + str(self.signature) + "\")")
			return (
				typeToJs(self.signature.obj.type) + ".prototype."
				+ self.signature.compileName()
				+ " = function" + self.signature.compileArgs() + " {\n"
				+ " var " + self.signature.obj.name + " = this;\n"
				+ "".join([s.compile(indent=1) for s in self.body])
				+ "};")
		else:
			fatalError("TODO")

class ClassDecl:
	def __init__(self, name, fields):
		self.name = name
		self.fields = fields
	def __str__(self):
		return self.name + " := class { " + ", ".join(self.fields) + "};"
	def compile(self):
		ans = "function " + self.name + "(vals) {\n"
		for name, number in self.fields:
			ans += " this." + name + " = (\"" + name + "\" in vals) ? vals[\"" + name + "\"] : "
			if number == "plural":
				ans += "[];\n"
			else:
				ans += "undefined;\n"
		ans += "};"
		for name, number in self.fields:
			ans += "\n" + typeToJs(self.name) + ".prototype.f_" + name + " = function() { return this." + name + "; };"
		return ans

class FunctionDecl:
	def __init__(self, vtype, field, param, body):
		self.type = vtype
		self.field = field
		self.param = param
		self.body = body
	def __str__(self):
		return self.type + "." + self.field + " := " + self.param + " => " + str(self.body)
	def compile(self):
		return typeToJs(self.type) + ".prototype.f_" + self.field + " = function() {\n var " + self.param + " = this;\n return " + self.body.compile() + ";\n};"

class IfStatement:
	def __init__(self, conditions, block):
		self.conditions = conditions
		self.block = block
	def __str__(self):
		return "if (" + " and ".join([str(c) for c in self.conditions]) + ") { " + " ".join([str(s) for s in self.block]) + " }"
	def compile(self, indent=0):
		return (" "*indent
			+ "if ((" + ") && (".join([c.compile() for c in self.conditions]) + ")) {\n"
			+ "".join([s.compile(indent=indent+1) for s in self.block])
			+ " "*indent + "}\n")

class CondExpr:
	def __init__(self, negation, operator, left, right):
		self.negation = negation
		self.operator = operator
		self.left = left
		self.right = right
	def __str__(self):
		return str(self.left) + self.operator + str(self.right)
	def compile(self):
		ans = self.left.compile() + self.operator + self.right.compile()
		if self.negation:
			return "!(" + ans + ")"
		else:
			return ans

class CallStatement:
	def __init__(self, name, args, wheres):
		self.name = name
		self.args = args
		self.wheres = wheres
	def compileName(self):
		keys = sorted(self.args.keys())
		return self.name + "_" + "".join([CASES_ABRV[case] for case in keys])
	def compileArgs(self):
		keys = sorted(self.args.keys())
		return "(" + ", ".join([self.args[key].compile() for key in keys]) + ")"
	def compileWheres(self):
		return "".join(["var "+where[0]+" = "+where[1].compile()+"; " for where in self.wheres])
	def compile(self, semicolon=True, indent=0):
		ans = " "*indent + self.compileWheres() + self.compileName() + self.compileArgs()
		if semicolon:
			ans += ";\n"
		return ans

class ProcedureCallStatement(CallStatement):
	def __str__(self):
		return self.name + "(" + ", ".join([key + ": " + str(self.args[key]) for key in self.args]) + ")"

class MethodCallStatement(CallStatement):
	def __init__(self, obj, obj_case, name, args, wheres):
		self.obj = obj
		self.obj_case = obj_case
		self.name = name
		self.args = args
		self.wheres = wheres
	def __str__(self):
		return str(self.obj) + "." + self.name + "_" + self.obj_case + "(" + ", ".join([key + ": " + str(self.args[key]) for key in self.args]) + ")"
	def compileName(self):
		return super(MethodCallStatement, self).compileName() + "_" + CASES_ABRV[self.obj_case]
	def compile(self, semicolon=True, indent=0):
		ans = " "*indent + self.compileWheres() + self.obj.compile() + "." + self.compileName() + self.compileArgs()
		if semicolon:
			ans += ";\n"
		return ans

class VariableExpr:
	def __init__(self, name, vtype="any"):
		self.name = name
		self.type = vtype
	def __str__(self):
		return self.name
	def compile(self):
		return self.name

class FieldExpr:
	def __init__(self, obj, field):
		self.obj = obj
		self.field = field
	def __str__(self):
		return str(self.obj) + "." + self.field
	def compile(self):
		return self.obj.compile() + ".f_" + self.field + "()"

class SubscriptExpr:
	def __init__(self, obj, index):
		self.obj = obj
		self.index = index
	def __str__(self):
		return str(self.obj) + "[" + str(self.index) + "]"
	def compile(self):
		return self.obj.compile() + "[" + self.index.compile() + "-1]"

class SliceExpr:
	def __init__(self, obj, start, end):
		self.obj = obj
		self.start = start
		self.end = end
	def __str__(self):
		return str(self.obj) + "[" + str(self.start) + ":" + str(self.end if self.end else "") + "]"
	def compile(self):
		ans = self.obj.compile() + ".slice("
		ans += self.start.compile() + "-1"
		if self.end:
			ans += ", " + self.end.compile()
		ans += ")"
		return ans

class NumExpr:
	def __init__(self, num):
		self.num = num
	def __str__(self):
		return str(self.num)
	def compile(self):
		return "(" + str(self.num) + ")"

class NewExpr:
	def __init__(self, typename, args):
		self.type = typename
		self.args = args
	def __str__(self):
		return "new " + typeToJs(self.type) + "(" + ", ".join([arg.field + "=" + str(arg.value) for arg in self.args]) + ")"
	def compile(self):
		return "new " + typeToJs(self.type) + "({" + ", ".join(["\"" + arg.field + "\": " + arg.value.compile() for arg in self.args]) + "})"

class CtorArgExpr:
	def __init__(self, field, value):
		self.field = field
		self.value = value

class ListExpr:
	def __init__(self, values):
		self.values = values
	def __str__(self):
		return "[" + ", ".join(map(str, self.values)) + "]"
	def compile(self):
		return "[" + ", ".join([value.compile() for value in self.values]) + "]"

class ArithmeticExpr:
	def __init__(self, operator, left, right):
		self.operator = operator
		self.left = left
		self.right = right
	def __str__(self):
		return "(" + str(self.left) + self.operator + str(self.right) + ")"
	def compile(self):
		return "(" + self.left.compile() + self.operator + self.right.compile() + ")"

class TernaryExpr:
	def __init__(self, conditions, then, otherwise):
		self.conditions = conditions
		self.then = then
		self.otherwise = otherwise
	def __str__(self):
		return str(self.then) + " if (" + " and ".join([str(c) for c in self.conditions]) + ") else " + str(self.otherwise)
	def compile(self):
		return "((" + ") && (".join([c.compile() for c in self.conditions]) + ") ? (" + self.then.compile() + ") : (" + self.otherwise.compile() + "))"
