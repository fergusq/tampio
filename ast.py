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

def formAbrv(form):
	if form in CASES_ABRV:
		return CASES_ABRV[form]
	else:
		return form[0].upper() + form[1:].lower()

def typeToJs(typename):
	if typename == "luku":
		return "Number"
	elif typename == "merkkijono":
		return "String"
	elif typename == "sivu":
		return "HTMLDocument"
	elif typename == "ajankohta":
		return "Date"
	else:
		return escapeIdentifier(typename)

def escapeIdentifier(identifier):
	return identifier.replace("-", "_")

class VariableDecl:
	def __init__(self, var, value):
		self.var = var
		self.value = value
	def __str__(self):
		return self.var + " := " + str(self.value)
	def compile(self):
		return "var " + escapeIdentifier(self.var) + " = " + self.value.compile(0) + ";"

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
				+ " = function" + self.signature.compileArgs(indent=0) + " {\n"
				+ " var " + escapeIdentifier(self.signature.obj.name) + " = this;\n"
				+ "".join([s.compile(indent=1) for s in self.body])
				+ "};")
		else:
			fatalError("TODO")

class ClassDecl:
	def __init__(self, name, fields, super_type=None):
		self.name = name
		self.fields = fields
		self.super = super_type
	def __str__(self):
		return self.name + " := class { " + ", ".join(self.fields) + "};"
	def compile(self):
		ans = "function " + escapeIdentifier(self.name) + "(vals) {\n"
		if self.super:
			ans += " " + escapeIdentifier(self.super) + ".call(this, vals);\n"
		for name, _, number, _, _ in self.fields:
			ans += " this." + escapeIdentifier(name) + " = (\"" + name + "\" in vals) ? vals[\"" + name + "\"] : "
			if number == "plural":
				ans += "[];\n"
			else:
				ans += "undefined;\n"
		ans += "};"
		if self.super:
			ans += "\n" + escapeIdentifier(self.name) + ".prototype = Object.create(" + escapeIdentifier(self.super) + ".prototype);"
			ans += "\n" + escapeIdentifier(self.name) + ".prototype.constructor = " + escapeIdentifier(self.name) + ";"
		ans += "\n" + typeToJs(self.name) + ".prototype.assign = function(n, v) { this[n] = v; };"
		for name, _, _, _, _ in self.fields:
			ans += "\n" + typeToJs(self.name) + ".prototype.f_" + escapeIdentifier(name) + " = function() { return this." + escapeIdentifier(name) + "; };"
		return ans

class Whereable:
	def compileWheres(self, indent=1):
		return "".join([" "*indent + "var "+escapeIdentifier(where[0])+" = "+where[1].compile(indent)+";\n" for where in self.wheres])

class FunctionDecl(Whereable):
	def __init__(self, vtype, field, self_param, param, param_case, body, wheres, memoize):
		self.type = vtype
		self.field = field
		self.self_param = self_param
		self.param = param
		self.param_case = param_case
		self.body = body
		self.wheres = wheres
		self.memoize = memoize
	def __str__(self):
		return self.type + "." + self.field + " := " + self.self_param + (", " + self.param if self.param else "") + " => " + str(self.body)
	def compile(self):
		ans = typeToJs(self.type) + ".prototype.f_" + self.field
		if self.param_case:
			ans += "_" + formAbrv(self.param_case)
		ans += " = function("
		if self.param:
			ans += self.param
		ans += ") {\n"
		if self.memoize:
			ans += " if (this." + escapeIdentifier(self.field) + " !== undefined) return this." + escapeIdentifier(self.field) + ";\n"
		if self.self_param != "":
			ans += " var " + escapeIdentifier(self.self_param) + " = this;\n"
		ans += self.compileWheres()
		if self.memoize:
			ans += " this." + escapeIdentifier(self.field) + " = " + self.body.compile(0) + ";\n"
			ans += " return this." + escapeIdentifier(self.field) + ";\n};"
		else:
			ans += " return " + self.body.compile(0) + ";\n};"
		return ans

class CondFunctionDecl(Whereable):
	def __init__(self, vtype, name, self_param, param, conditions, wheres):
		assert name[0] == "."
		self.type = vtype
		self.name = name
		self.self_param = self_param
		self.param = param
		self.conditions = conditions
		self.wheres = wheres
	def __str__(self):
		ans = self.type + self.name
		if self.param:
			ans += "(" + self.param + ")"
		return ans + " := " + self.self_param + " => " + " and ".join(map(str, self.conditions))
	def compile(self):
		ans = typeToJs(self.type) + ".prototype" + self.name + " = function("
		if self.param != "":
			ans += self.param
		ans += ") {\n"
		if self.self_param != "":
			ans += " var " + escapeIdentifier(self.self_param) + " = this;\n"
		ans += self.compileWheres()
		ans += " return (" + ") && (".join([c.compile(0) for c in self.conditions]) + ");\n};"
		return ans

class ForStatement:
	def __init__(self, var, expr, stmt):
		self.var = var
		self.expr = expr
		self.stmt = stmt
	def __str__(self):
		return "for (" + self.var + " in " + str(self.expr) + ") " + str(self.stmt)
	def compile(self, indent=0):
		return (" "*indent
			+ "for (const " + escapeIdentifier(self.var)
			+ " of " + self.expr.compile(indent)
			+ ") {\n" + self.stmt.compile(indent=indent+1)
			+ " "*indent + "}\n")

class IfStatement:
	def __init__(self, conditions, block):
		self.conditions = conditions
		self.block = block
	def __str__(self):
		return "if (" + " and ".join([str(c) for c in self.conditions]) + ") { " + " ".join([str(s) for s in self.block]) + " }"
	def compile(self, indent=0):
		ans = ""
		for c in self.conditions:
			ans += c.compileWheres()
		return ans + (" "*indent
			+ "if ((" + ") && (".join([c.compile(indent) for c in self.conditions]) + ")) {\n"
			+ "".join([s.compile(indent=indent+1) for s in self.block])
			+ " "*indent + "}\n")

class QuantifierCondExpr(Whereable):
	def __init__(self, quant, var, expr, cond, wheres=[]):
		self.quantifier = quant
		self.var = var
		self.expr = expr
		self.cond = cond
		self.wheres = wheres
	def __str__(self):
		return ("for all" if self.quantifier == "jokainen" else "exists") + " " + self.var + " in " + str(self.expr) + ": " + str(self.cond)
	def compile(self, indent):
		return self.expr.compile(indent) + (".every(" if self.quantifier == "jokainen" else ".some(") + self.var + " => " + self.cond.compile(indent) + ")"

class CondExpr(Whereable):
	def __init__(self, negation, operator, left, right, wheres=[]):
		self.negation = negation
		self.operator = operator
		self.left = left
		self.right = right
		self.wheres = wheres
	def __str__(self):
		return str(self.left) + self.operator + str(self.right)
	def compile(self, indent):
		ans = self.left.compile(indent) + self.operator
		if self.operator[0] == ".":
			ans += "("
		if self.right:
			ans += self.right.compile(indent)
		if self.operator[0] == ".":
			ans += ")"
		if self.negation:
			return "!(" + ans + ")"
		else:
			return ans

class BlockStatement(Whereable):
	def __init__(self, stmts, wheres):
		self.stmts = stmts
		self.wheres = wheres
	def __str__(self):
		return "; ".join(map(str, self.stmts))
	def compile(self, semicolon=True, indent=0):
		return self.compileWheres(indent) + "".join([s.compile(indent=indent) for s in self.stmts])

class CallStatement:
	def __init__(self, name, args, output_var, async_block):
		self.name = name
		self.args = args
		self.output_var = output_var
		self.async_block = async_block
	def compileName(self):
		keys = sorted(self.args.keys())
		return escapeIdentifier(self.name) + "_" + "".join([formAbrv(form) for form in keys])
	def compileArgs(self, indent):
		keys = sorted(self.args.keys())
		return "(" + ", ".join([self.args[key].compile(indent) for key in keys]) + ")"
	def compileAssignment(self):
		if self.output_var:
			return "var " + self.output_var + " = "
		else:
			return ""
	def compileAsync(self, indent):
		ans = ""
		for ab in self.async_block:
			ans += ("." + ab[0]
				+ "(" + ab[1] + " =>\n"
				+ ab[2].compile(indent=indent+1, semicolon=False)
				+ " "*indent + ")")
		return ans
			
	def compile(self, semicolon=True, indent=0):
		ans = " "*indent + self.compileAssignment() + self.compileName() + self.compileArgs(indent) + self.compileAsync(indent)
		if semicolon:
			ans += ";\n"
		return ans

class ProcedureCallStatement(CallStatement):
	def __str__(self):
		return self.name + "(" + ", ".join([key + ": " + str(self.args[key]) for key in self.args]) + ")"

class MethodCallStatement(CallStatement):
	def __init__(self, obj, obj_case, name, args, output_var, async_block):
		self.obj = obj
		self.obj_case = obj_case
		self.name = name
		self.args = args
		self.output_var = output_var
		self.async_block = async_block
	def __str__(self):
		return str(self.obj) + "." + self.name + "_" + self.obj_case + "(" + ", ".join([key + ": " + str(self.args[key]) for key in self.args]) + ")"
	def compileName(self):
		return super(MethodCallStatement, self).compileName() + "_" + formAbrv(self.obj_case)
	def compile(self, semicolon=True, indent=0):
		ans = " "*indent
		is_lval = isinstance(self.obj, VariableExpr) or isinstance(self.obj, SubscriptExpr) or isinstance(self.obj, FieldExpr)
		def compileLval():
			if isinstance(self.obj, FieldExpr):
				return self.obj.obj.compile(indent) + "." + escapeIdentifier(self.obj.field)
			else:
				return self.obj.compile(indent)
		if (is_lval
			and self.name == "asettaa_P"
			and self.obj_case == "tulento"
			and list(self.args.keys()) == ["nimento"]):
			ans += compileLval() + " = " + self.args["nimento"].compile(indent)
		elif (is_lval
			and self.name == "kasvattaa_P"
			and self.obj_case == "osanto"
			and list(self.args.keys()) == ["ulkoolento"]):
			ans += compileLval() + " += " + self.args["ulkoolento"].compile(indent)
		elif self.name == "palauttaa_P" and self.obj_case == "nimento" and len(self.args) == 0:
			ans += "return " + self.obj.compile(indent)
		else:
			ans += self.compileAssignment() + self.obj.compile(indent) + "." + self.compileName() + self.compileArgs(indent) + self.compileAsync(indent)
		if semicolon:
			ans += ";\n"
		return ans

class MethodAssignmentStatement:
	def __init__(self, obj, obj_case, method, params, body):
		self.obj = obj
		self.obj_case = obj_case
		self.method = method
		self.params = params
		self.body = body
	def __str__(self):
		return (str(self.obj) + "." + self.method + " := ("
			+ ", ".join([key + ": " + str(self.args[key]) for key in self.params]) + ") => { " + "; ".join(map(str, self.body)) + " }")
	def compileName(self):
		keys = sorted(self.params.keys())
		return escapeIdentifier(self.method) + "_" + "".join([formAbrv(form) for form in keys]) + "_" + formAbrv(self.obj_case)
	def compileParams(self, indent):
		keys = sorted(self.params.keys())
		return "(" + ", ".join([self.params[key].compile(indent) for key in keys]) + ")"
	def compile(self, semicolon=True, indent=0):
		ans = " "*indent
		ans += self.obj.compile(indent)
		ans += ".assign(\"" + self.compileName()
		ans += "\", "
		ans += self.compileParams(indent)
		ans += " => {\n"
		ans += "".join([s.compile(indent=indent+1) for s in self.body])
		ans += " "*indent + "});"
		if semicolon:
			ans += ";\n"
		return ans

class VariableExpr:
	def __init__(self, name, vtype="any"):
		self.name = name
		self.type = vtype
	def __str__(self):
		return self.name
	def compile(self, indent):
		return escapeIdentifier(self.name)

ARI_OPERATORS = {
	"lisätty_E": ("sisatulento", "+"),
	"ynnätty_E": ("sisatulento", "+"),
	"kasvatettu_E": ("ulkoolento", "+"),
	"yhdistetty_E": ("sisatulento", ".concat"),
	"liitetty_E": ("sisatulento", ".prepend"),
	"vähennetty_E": ("ulkoolento", "-"),
	"kerrottu_E": ("ulkoolento", "*"),
	"jaettu_E": ("ulkoolento", "/"),
	"rajattu_E": ("sisatulento", "%")
}

class FieldExpr:
	def __init__(self, obj, field, arg_case=None, arg=None):
		self.obj = obj
		self.field = field
		self.arg_case = arg_case
		self.arg = arg
	def __str__(self):
		return str(self.obj) + "." + self.field
	def compile(self, indent):
		if self.field in ARI_OPERATORS and self.arg_case == ARI_OPERATORS[self.field][0]:
			return self.compileArithmetic(indent)
		ans = self.obj.compile(indent) + ".f_" + escapeIdentifier(self.field)
		if self.arg_case:
			ans += "_" + formAbrv(self.arg_case)
		ans += "("
		if self.arg:
			ans += self.arg.compile(indent)
		return ans + ")"
	def compileArithmetic(self, indent):
		operator = ARI_OPERATORS[self.field][1]
		if operator[0] == ".":
			return self.obj.compile(indent) + operator + "(" + self.arg.compile(indent) + ")"
		else:
			return "(" + self.obj.compile(indent) + operator + self.arg.compile(indent) + ")"

class SubscriptExpr:
	def __init__(self, obj, index, is_end_index=False):
		self.obj = obj
		self.index = index
		self.is_end_index = is_end_index
	def __str__(self):
		return str(self.obj) + "[" + str(self.index) + "]"
	def compile(self, indent):
		if self.is_end_index:
			return self.obj.compile(indent) + ".nth_last(" + self.index.compile(indent) + ")"
		else:
			return self.obj.compile(indent) + "[" + self.index.compile(indent) + "-1]"

class SliceExpr:
	def __init__(self, obj, start, end):
		self.obj = obj
		self.start = start
		self.end = end
	def __str__(self):
		return str(self.obj) + "[" + str(self.start) + ":" + str(self.end if self.end else "") + "]"
	def compile(self, indent):
		ans = self.obj.compile(indent) + ".slice("
		ans += self.start.compile(indent) + "-1"
		if self.end:
			ans += ", " + self.end.compile(indent)
		ans += ")"
		return ans

class NumExpr:
	def __init__(self, num):
		self.num = num
	def __str__(self):
		return str(self.num)
	def compile(self, indent):
		return "(" + str(self.num) + ")"

class StrExpr:
	def __init__(self, string):
		self.str = string
	def __str__(self):
		return repr(self.str)
	def compile(self, indent):
		return repr(self.str)

class NewExpr:
	def __init__(self, typename, args):
		self.type = typename
		self.args = args
	def __str__(self):
		return "new " + typeToJs(self.type) + "(" + ", ".join([arg.field + "=" + str(arg.value) for arg in self.args]) + ")"
	def compile(self, indent):
		return "new " + typeToJs(self.type) + "({" + ", ".join(["\"" + arg.field + "\": " + arg.value.compile(indent) for arg in self.args]) + "})"

class CtorArgExpr:
	def __init__(self, field, value):
		self.field = field
		self.value = value

class ListExpr:
	def __init__(self, values):
		self.values = values
	def __str__(self):
		return "[" + ", ".join(map(str, self.values)) + "]"
	def compile(self, indent):
		return "[" + ", ".join([value.compile(indent) for value in self.values]) + "]"

class LambdaExpr:
	def __init__(self, body):
		self.body = body
	def __str__(self):
		return "() => { " + "; ".join(map(str, body)) + " }"
	def compile(self, indent):
		return "() => {\n" + "".join([s.compile(indent=indent+1) for s in self.body]) + " }"

class TernaryExpr:
	def __init__(self, conditions, then, otherwise):
		self.conditions = conditions
		self.then = then
		self.otherwise = otherwise
	def __str__(self):
		return str(self.then) + " if (" + " and ".join([str(c) for c in self.conditions]) + ") else " + str(self.otherwise)
	def compile(self, indent):
		return ("((" + ") && (".join([c.compile(indent) for c in self.conditions])
			+ ") ? (" + self.then.compile(indent)
			+ ") : (" + self.otherwise.compile(indent) + "))")
