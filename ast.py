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

from collections import namedtuple
from itertools import chain
from inflect import CASES_ABRV
from fatal_error import fatalError, typeError, notfoundError, warning, TampioError
from hierarchy import Class, classes, getClass, isClass, classSet, getFunctions, getFields

# kääntäjän tila

def initializeCompiler(include_file):
	global global_variables, aliases, includeFile, options, block_frame, tokens
	options = {}
	block_frame = BlockData(None, set(), False, None)
	global_variables = {}
	aliases = {}
	includeFile = include_file
	tokens = None

class CompilerFrame:
	def __init__(self, tl):
		self.tokens = tl
	def __enter__(self):
		global options, block_frame, tokens
		self.prev_options = options
		self.prev_block_frame = block_frame
		self.prev_tokens = tokens
		options = {
			"kohdekoodi": False,
			"käyttömäärittelyt": False
		}
		block_frame = BlockData(None, {}, False, None)
		tokens = self.tokens
	def __exit__(self, *args):
		global options, block_frame, tokens
		options = self.prev_options
		block_frame = self.prev_block_frame
		tokens = self.prev_tokens

BlockData = namedtuple("BlockData", "variables backreferences block_mode self_type")

class BlockFrame:
	def __init__(self, new_frame):
		self.new_frame = new_frame
	def __enter__(self):
		global block_frame
		self.prev_frame = block_frame
		block_frame = self.new_frame
	def __exit__(self, *args):
		global block_frame
		block_frame = self.prev_frame

# apufunktiot

def formAbrv(form):
	if form in CASES_ABRV:
		return CASES_ABRV[form]
	else:
		return form[0].upper() + form[1:].lower()

def typeToJs(typename):
	while typename in aliases:
		typename = aliases[typename]
	return escapeIdentifier(typename)

def escapeIdentifier(identifier):
	return identifier.replace("-", "_")

# moduulin käätäminen

def compileModule(declarations, on_error, tokens):
	with CompilerFrame(tokens):
		for decl in declarations:
			try:
				decl.buildHierarchy()
			except TampioError as e:
				on_error(e)
	with CompilerFrame(tokens):
		ans = ""
		additional_statements = ""
		for decl in declarations:
			try:
				decl.validateTree()
				ans += decl.compile() + "\n"
				additional_statements += decl.compileAdditionalStatements()
			except TampioError as e:
				on_error(e)
		return ans + additional_statements

# lohkon kääntäminen

def compileBlock(statements, indent, parameters):
	bcs = set()
	for stmt in statements:
		bcs.update(set(stmt.backreferences()))
	
	ans = ""
	for bc in bcs:
		ans += " "*indent + "var se_" + escapeIdentifier(bc) + " = null;\n"
	
	prev_variables = block_frame.variables or {**global_variables}
	variables = {**prev_variables, **parameters}
	
	with BlockFrame(BlockData(variables, bcs, True, block_frame.self_type)):
		for stmt in statements:
			# eksplisiittisesti luodut uudet muuttujat
			variables.update(stmt.createdVariables())
			# uusi-avainsanalla luodut uudet muuttujat
			new_vars = stmt.newVariables()
			for name, vtype in new_vars.items():
				ans += " "*indent + "var " + escapeIdentifier(name) + " = null;\n"
			variables.update(new_vars)
			# vielä mainitsemattomat muuttujat ovat luodaan (poisluetaan väliaikaismuuttujat)
			if options["käyttömäärittelyt"]:
				new_vars = stmt.variables()
				tmp_vars = stmt.temporaryVariables()
				for name, vtype in new_vars.items():
					if name not in variables and name not in tmp_vars:
						warning("autodeclaration of " + name + " as " + vtype)
						ans += " "*indent + "var " + escapeIdentifier(name) + " = new " + escapeIdentifier(vtype) + "({});\n"
				variables.update(new_vars)
			ans += stmt.compile(indent=indent)
	
	return ans

# määrittelyjen kääntäminen

class Decl:
	def __init__(self, statements):
		self.statements = statements
	def compile(self):
		return self.compileDecl()
	def compileAdditionalStatements(self):
		if self.statements:
			return ";(function() {\n" + compileBlock(self.statements, 0, {}) + "})();\n"
		else:
			return ""
	def buildHierarchy(self):
		pass
	def validateTree(self):
		pass

class SetOptionDecl(Decl):
	def __init__(self, positive, option):
		self.positive = positive
		self.option = option
		self.statements = []
	def compileDecl(self):
		options[self.option] = self.positive
		return ""
	def buildHierarchy(self):
		options[self.option] = self.positive
		return ""

class TargetCodeDecl(Decl):
	def __init__(self, code, stmts):
		Decl.__init__(self, stmts)
		self.code = code
	def compileDecl(self):
		return self.code

class IncludeTargetCodeFileDecl(Decl):
	def __init__(self, filename, stmts):
		Decl.__init__(self, stmts)
		self.file = filename
	def compileDecl(self):
		with open(self.file) as f:
			return f.read()

class IncludeFileDecl(Decl):
	def __init__(self, filename, stmts):
		Decl.__init__(self, stmts)
		self.file = filename
	def compileDecl(self):
		return ""
	def buildHierarchy(self):
		includeFile(self.file)

class VariableDecl(Decl):
	def __init__(self, var, vtype, value, stmts):
		Decl.__init__(self, stmts)
		self.var = var
		self.type = vtype
		self.value = value
	def compileDecl(self):
		return "var " + escapeIdentifier(self.var) + " = " + self.value.compile(0) + ";"
	def compileAdditionalStatements(self):
		if self.statements:
			return ";(function() {\n" + compileBlock(self.statements, 1, {}) + "}).call(" + escapeIdentifier(self.var) + ");\n"
		else:
			return ""
	def buildHierarchy(self):
		global_variables[self.var] = self.value.inferType()
	def validateTree(self):
		self.value.validateTree()

class ProcedureDecl(Decl):
	def __init__(self, signature, body, stmts):
		Decl.__init__(self, stmts)
		self.signature = signature
		self.body = body
	def compileDecl(self):
		if isinstance(self.signature, ProcedureCallStatement):
			return ("function " + self.signature.compile(semicolon=False)
				+ " {\n" + compileBlock(self.body, 1, self.signature.variables()) + "};")
		elif isinstance(self.signature, MethodCallStatement):
			with BlockFrame(block_frame._replace(self_type=self.signature.obj.type)):
				return (
					typeToJs(self.signature.obj.type) + ".prototype."
					+ self.signature.compileName()
					+ " = function" + self.signature.compileArgs(indent=0) + " {\n"
					+ " var " + escapeIdentifier(self.signature.obj.name) + " = this;\n"
					+ compileBlock(self.body, 1, self.signature.variables())
					+ "};")
		else:
			fatalError("TODO")
	def buildHierarchy(self):
		if isinstance(self.signature, MethodCallStatement):
			getClass(self.signature.obj.type).addMethod(self.signature.name, sorted(self.signature.args.keys()))
	def validateTree(self):
		if isinstance(self.signature, MethodCallStatement):
			with BlockFrame(block_frame._replace(self_type=self.signature.obj.type)):
				for s in self.body:
					s.validateTree()
		else:
			for s in self.body:
				s.validateTree()

class ClassDecl(Decl):
	def __init__(self, name, fields, stmts, super_type=None):
		Decl.__init__(self, stmts)
		self.name = name
		self.fields = fields
		self.super = super_type
	def compile(self):
		class_name = escapeIdentifier(self.name)
		ans = "function " + class_name + "(vals) {\n"
		if self.super:
			ans += " " + escapeIdentifier(self.super) + ".call(this, vals);\n"
		for name, _, number, _, _, def_val in self.fields:
			field = "this." + escapeIdentifier(name)
			ans += " if (\"" + name + "\" in vals) " + field + " = vals[\"" + name + "\"];\n"
			if def_val:
				ans += " else " + field + " = " + def_val.compile(0) + ";\n"
			elif number == "plural":
				ans += " else " + field + " = [];\n"
		ans += " if (" + class_name + ".prototype.syntyä_A__N) " + class_name + ".prototype.syntyä_A__N.call(this);\n"
		ans += "};"
		if self.super:
			ans += "\n" + class_name + ".prototype = Object.create(" + escapeIdentifier(self.super) + ".prototype);"
			ans += "\n" + class_name + ".prototype.constructor = " + class_name + ";"
		for name, _, _, _, _, _ in self.fields:
			ans += "\n" + class_name + ".prototype.f_" + escapeIdentifier(name) + " = function() { return this." + escapeIdentifier(name) + "; };"
		return ans
	def buildHierarchy(self):
		cl = Class(self.name, self.super)
		classes[self.name] = cl
		for name, _, number, _, _, _ in self.fields:
			cl.addField(name, number)

class TargetCodeClassDecl(Decl):
	def __init__(self, name, tc_name, stmts):
		Decl.__init__(self, stmts)
		self.name = name
		self.tc_name = tc_name
	def compileDecl(self):
		return ""
	def buildHierarchy(self):
		cl = Class(self.name, None)
		classes[self.name] = cl
		if self.name != self.tc_name:
			aliases[self.name] = self.tc_name

class AliasClassDecl(Decl):
	def __init__(self, alias_name, real_name, stmts):
		Decl.__init__(self, stmts)
		self.alias_name = alias_name
		self.real_name = real_name
	def compileDecl(self):
		return ""
	def buildHierarchy(self):
		classes[self.alias_name] = getClass(self.real_name)
		aliases[self.alias_name] = self.real_name

class Whereable:
	def compileWheres(self, indent=1):
		return "".join([" "*indent + "var "+escapeIdentifier(name)+" = "+val.compile(indent)+";\n" for name, _, val in self.wheres])
	def whereSubexpressions(self):
		ans = []
		for _, _, val in self.wheres:
			ans += val.subexpressions()
		return ans
	def whereCreatedVariables(self):
		ans = {}
		for name, vtype, val in self.wheres:
			ans[name] = val.inferType()
		return ans
	def validateWheres(self):
		for _, _, val in self.wheres:
			val.validateTree()

class FunctionDecl(Whereable,Decl):
	def __init__(self, vtype, field, self_param, param, param_case, body, wheres, memoize, stmts):
		Decl.__init__(self, stmts)
		self.type = vtype
		self.field = field
		self.self_param = self_param
		self.param = param
		self.param_case = param_case
		self.body = body
		self.wheres = wheres
		self.memoize = memoize
	def compile(self):
		ans = typeToJs(self.type) + ".prototype.f_" + escapeIdentifier(self.field)
		if self.param_case:
			ans += "_" + formAbrv(self.param_case)
		ans += " = function("
		if self.param:
			ans += escapeIdentifier(self.param)
		ans += ") {\n"
		if self.memoize:
			ans += " if (this." + escapeIdentifier(self.field) + " !== undefined) return this." + escapeIdentifier(self.field) + ";\n"
		if self.self_param != "":
			ans += " var " + escapeIdentifier(self.self_param) + " = this;\n"
		with BlockFrame(block_frame._replace(self_type=self.type)):
			ans += self.compileWheres()
			if self.memoize:
				ans += " this." + escapeIdentifier(self.field) + " = " + self.body.compile(0) + ";\n"
				ans += " return this." + escapeIdentifier(self.field) + ";\n};"
			else:
				ans += " return " + self.body.compile(0) + ";\n};"
		return ans
	def buildHierarchy(self):
		getClass(self.type).addFunction(self.field, self.param_case, self.body)
	def validateTree(self):
		with BlockFrame(block_frame._replace(self_type=self.type)):
			self.validateWheres()
			self.body.validateTree()

class CondFunctionDecl(Whereable,Decl):
	def __init__(self, vtype, name, self_param, param, condition, wheres, stmts):
		Decl.__init__(self, stmts)
		assert name[0] == "."
		self.type = vtype
		self.name = name
		self.self_param = self_param
		self.param = param
		self.condition = condition
		self.wheres = wheres
	def compileDecl(self):
		ans = typeToJs(self.type) + ".prototype" + self.name + " = function("
		if self.param != "":
			ans += escapeIdentifier(self.param)
		ans += ") {\n"
		if self.self_param != "":
			ans += " var " + escapeIdentifier(self.self_param) + " = this;\n"
		ans += self.compileWheres()
		ans += " return " + self.condition.compile(0) + ";\n};"
		return ans
	def buildHierarchy(self):
		getClass(self.type).addComparisonOperator(self.name)
	def validateTree(self):
		with BlockFrame(block_frame._replace(self_type=self.type)):
			self.validateWheres()
			self.condition.validateTree()

# lauseiden kääntäminen

class Recursive:
	def subexpressions(self):
		return [self]
	def search(self, f):
		ans = []
		for subexpr in self.subexpressions():
			if subexpr is not self:
				ans += f(subexpr)
		return ans
	def searchDict(self, f):
		ans = {}
		for subexpr in self.subexpressions():
			if subexpr is not self:
				ans.update(f(subexpr))
		return ans
	def backreferences(self):
		return self.search(lambda e: e.backreferences())
	# kaikki muuttujat
	def variables(self):
		return self.searchDict(lambda e: e.variables())
	# lausekkeissa luodut muuttujat (muuttujaluonti käännetään lausekkeen yhteydessä)
	def createdVariables(self):
		return self.searchDict(lambda e: e.createdVariables())
	# lausekkeissa luodut muuttujat (muuttujaluonti käännetään ennen lauseketta)
	def newVariables(self):
		return self.searchDict(lambda e: e.newVariables())
	# väliaikaismuuttujat
	def temporaryVariables(self):
		return self.searchDict(lambda e: e.temporaryVariables())
	# syntaksipuun validoiminen
	def validateTree(self):
		self.validate()
		for e in self.subexpressions():
			if e is not self:
				e.validateTree()
	def validate(self):
		pass

class ForStatement(Recursive):
	def __init__(self, var, expr, stmt):
		self.var = var
		self.expr = expr
		self.stmt = stmt
	def subexpressions(self):
		return self.expr.subexpressions() + self.stmt.subexpressions()
	def compile(self, indent=0):
		return (" "*indent
			+ "for (const " + escapeIdentifier(self.var)
			+ " of " + self.expr.compile(indent)
			+ ") {\n" + self.stmt.compile(indent=indent+1)
			+ " "*indent + "}\n")

class IfStatement(Recursive):
	def __init__(self, condition, block):
		self.condition = condition
		self.block = block
	def subexpressions(self):
		ans = []
		ans += self.condition.subexpressions()
		for s in self.block:
			ans += s.subexpressions()
		return ans
	def compile(self, indent=0):
		ans = ""
		self.condition.compileWheres()
		return ans + (" "*indent
			+ "if (" + self.condition.compile(indent+1) + ") {\n"
			+ "".join([s.compile(indent=indent+1) for s in self.block])
			+ " "*indent + "}\n")

class QuantifierCondExpr(Whereable,Recursive):
	def __init__(self, quant, var, expr, cond, wheres=[]):
		self.quantifier = quant
		self.var = var
		self.expr = expr
		self.cond = cond
		self.wheres = wheres
	def subexpressions(self):
		return self.expr.subexpressions() + self.cond.subexpressions() + self.whereSubexpressions()
	def createdVariables(self):
		return {**super().createdVariables(), **self.whereCreatedVariables()}
	def compile(self, indent):
		return self.expr.compile(indent) + (".every(" if self.quantifier == "jokainen" else ".some(") + self.var + " => " + self.cond.compile(indent) + ")"
	def validate(self):
		self.validateWheres()

class CondConjunctionExpr(Whereable,Recursive):
	def __init__(self, op, exprs, wheres=[]):
		self.op = op
		self.exprs = exprs
		self.wheres = []
	def subexpressions(self):
		ans = []
		for expr in self.exprs:
			ans += expr.subexpressions()
		return ans
	def createdVariables(self):
		return {**super().createdVariables(), **self.whereCreatedVariables()}
	def compile(self, indent):
		return "((" + (") " + self.op + " (").join([e.compile(indent) for e in self.exprs]) + "))"
	def validate(self):
		self.validateWheres()

class CondExpr(Whereable,Recursive):
	def __init__(self, negation, operator, left, right, wheres=[]):
		self.negation = negation
		self.operator = operator
		self.left = left
		self.right = right
		self.wheres = wheres
	def subexpressions(self):
		return self.left.subexpressions() + (self.right.subexpressions() if self.right else []) + self.whereSubexpressions()
	def createdVariables(self):
		return {**super().createdVariables(), **self.whereCreatedVariables()}
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
	def validate(self):
		self.validateWheres()

class BlockStatement(Whereable,Recursive):
	def __init__(self, stmts, wheres):
		self.stmts = stmts
		self.wheres = wheres
	def subexpressions(self):
		ans = []
		for s in self.stmts:
			ans += s.subexpressions()
		return ans + self.whereSubexpressions()
	def createdVariables(self):
		return {**super().createdVariables(), **self.whereCreatedVariables()}
	def compile(self, semicolon=True, indent=0):
		return self.compileWheres(indent) + "".join([s.compile(indent=indent) for s in self.stmts])
	def validate(self):
		self.validateWheres()

class CallStatement(Recursive):
	def __init__(self, name, args, output_var, async_block):
		self.name = name
		self.args = args
		self.output_var = output_var
		self.async_block = async_block
	def subexpressions(self):
		ans = [self]
		for v in self.args.values():
			ans += v.subexpressions()
		for _, _, _, s in self.async_block:
			ans += s.subexpressions()
		return ans
	def variables(self):
		return super().variables()
	def createdVariables(self):
		if self.output_var:
			return dict([self.output_var])
		else:
			return {}
	def temporaryVariables(self):
		ans = []
		for _, param, ptype, _ in self.async_block:
			ans += [(param, ptype)]
		return ans
	def compileName(self):
		keys = sorted(self.args.keys())
		return escapeIdentifier(self.name) + "_" + "".join([formAbrv(form) for form in keys])
	def compileArgs(self, indent):
		keys = sorted(self.args.keys())
		return "(" + ", ".join([self.args[key].compile(indent) for key in keys]) + ")"
	def compileAssignment(self):
		if self.output_var:
			return "var " + escapeIdentifier(self.output_var[0]) + " = "
		else:
			return ""
	def compileAsync(self, indent):
		ans = ""
		for mname, param, ptype, stmt in self.async_block:
			with BlockFrame(block_frame._replace(variables={**block_frame.variables, **dict([(param, ptype)])})):
				ans += ("." + escapeIdentifier(mname)
					+ "(" + escapeIdentifier(param) + " =>\n"
					+ stmt.compile(indent=indent+1, semicolon=False)
					+ " "*indent + ")")
		return ans
			
	def compile(self, semicolon=True, indent=0):
		ans = " "*indent + self.compileAssignment() + self.compileName() + self.compileArgs(indent) + self.compileAsync(indent)
		if semicolon:
			ans += ";\n"
		return ans

class ProcedureCallStatement(CallStatement):
	def compile(self, semicolon=True, indent=0):
		if self.name == "suorittaa!" and list(self.args.keys()) == ["nimento"] and isinstance(self.args["nimento"], StrExpr) and options["kohdekoodi"]:
			return " "*indent + self.args["nimento"].str + ("\n" if semicolon else "")
		else:
			return super().compile(semicolon=semicolon, indent=indent)

BUILTIN_ASSIGN_METHODS = [
	("asettaa_P", "tulento", "nimento", lambda lval, arg: lval + " = " + arg),
	("olla_A", "nimento", "nimento", lambda lval, arg: lval + " = " + arg),
	("kasvattaa_P", "osanto", "ulkoolento", lambda lval, arg: lval + " += " + arg)
]

class MethodCallStatement(CallStatement,Recursive):
	def __init__(self, obj, obj_case, name, args, output_var, async_block):
		self.obj = obj
		self.obj_case = obj_case
		self.name = name
		self.args = args
		self.output_var = output_var
		self.async_block = async_block
	def subexpressions(self):
		return super().subexpressions() + self.obj.subexpressions()
	def compileName(self):
		return super().compileName() + "_" + formAbrv(self.obj_case)
	def compile(self, semicolon=True, indent=0):
		ans = " "*indent
		is_lval = isinstance(self.obj, VariableExpr) or isinstance(self.obj, SubscriptExpr) or isinstance(self.obj, FieldExpr)
		def compileLval():
			if isinstance(self.obj, FieldExpr):
				return self.obj.obj.compile(indent) + "." + escapeIdentifier(self.obj.field)
			else:
				return self.obj.compile(indent)
		for mname, ocase, acase, f in BUILTIN_ASSIGN_METHODS:
			if is_lval and self.name == mname and self.obj_case == ocase and list(self.args.keys()) == [acase]:
				ans += f(compileLval(), self.args[acase].compile(indent))
				break
		else:
			if self.name == "palauttaa_P" and self.obj_case == "nimento" and len(self.args) == 0:
				ans += "return " + self.obj.compile(indent)
			else:
				ans += self.compileAssignment() + self.obj.compile(indent) + "." + self.compileName() + self.compileArgs(indent) + self.compileAsync(indent)
		if semicolon:
			ans += ";\n"
		return ans

class MethodAssignmentStatement(Recursive):
	def __init__(self, obj, obj_case, method, params, body):
		self.obj = obj
		self.obj_case = obj_case
		self.method = method
		self.params = params
		self.body = body
	def subexpressions(self):
		return self.obj.subexpressions() # ei palauta vartalon sisältämiä alalausekkeita (kuten ei lambdakaan)
	def compileName(self):
		keys = sorted(self.params.keys())
		return escapeIdentifier(self.method) + "_" + "".join([formAbrv(form) for form in keys]) + "_" + formAbrv(self.obj_case)
	def compileParams(self, indent):
		keys = sorted(self.params.keys())
		with BlockFrame(block_frame._replace(block_mode=False)):
			ans = "(" + ", ".join([self.params[key].compile(indent) for key in keys]) + ")"
		return ans
	def compile(self, semicolon=True, indent=0):
		ans = " "*indent
		ans += self.obj.compile(indent)
		ans += ".t_assign(\"" + self.compileName()
		ans += "\", "
		ans += self.compileParams(indent)
		ans += " => {\n"
		ans += compileBlock(self.body, indent+1, dict(chain.from_iterable([self.params[key].variables().items() for key in self.params])))
		ans += " "*indent + "});"
		if semicolon:
			ans += ";\n"
		return ans

# lausekkeiden kääntäminen

class Expr:
	def __init__(self):
		self.type_cache = None
	def inferType(self, expected_types=[]):
		if self.type_cache is None:
			self.type_cache = self.infer(expected_types)
		return self.type_cache

class VariableExpr(Expr,Recursive):
	def __init__(self, name, vtype=None, initial_value=None, place=None):
		Expr.__init__(self)
		self.name = name
		self.type = vtype
		self.initial_value = initial_value
		self.place = place
	def subexpressions(self):
		if self.initial_value:
			return [self] + self.initial_value.subexpressions()
		else:
			return [self]
	def newVariables(self):
		if self.type and self.initial_value:
			return {self.name: self.type}
		else:
			return {}
	def variables(self):
		if self.type:
			return {self.name: self.type}
		else:
			return {}
	def compile(self, indent):
		ans = escapeIdentifier(self.name)
		if self.initial_value:
			ans = "(" + ans + "=" + self.initial_value.compile(indent) + ")"
		if self.type in block_frame.backreferences:
			ans = "(se_" + escapeIdentifier(self.type) + "=" + ans + ")"
		return ans
	def infer(self, expected_types):
		if block_frame.block_mode and self.name in block_frame.variables:
			ans = block_frame.variables[self.name]
		elif self.name in global_variables:
			ans = global_variables[self.name]
		elif self.type:
			ans = {}
		else:
			return classSet()
		
		if not ans:
			ans = set()
			for i in range(len(self.type)):
				if isClass(self.type[i:]):
					ans.add(getClass(self.type[i:]))
		
		return ans
	def validate(self):
		if block_frame.block_mode and self.type and not self.initial_value:
			if self.name not in block_frame.variables:
				if self.place:
					notfoundError("variable not found: " + self.name, tokens, self.place)
				else:
					notfoundError("variable not found: " + self.name)
		#if self.type and len(self.infer([])) == 0:
		#	warning("class not found: " + self.type, tokens, self.place)

class BackreferenceExpr(Expr,Recursive):
	def __init__(self, name, may_be_field=False):
		Expr.__init__(self)
		self.name = name
		self.may_be_field = may_be_field
	def backreferences(self):
		return [self.name]
	def compile(self, indent):
		name = escapeIdentifier(self.name)
		if self.may_be_field:
			return "(this.f_" + name + "!==undefined ? this.f_" + name + " : se_" + name + ")"
		else:
			return "se_" + name
	def infer(self, expected_types):
		# TODO
		return classSet()

ARI_OPERATORS = {
	"lisätty_E": ("sisatulento", "+", ["luku", "merkkijono"]),
	"ynnätty_E": ("sisatulento", "+", ["luku", "merkkijono"]),
	"kasvatettu_E": ("ulkoolento", "+", ["luku", "merkkijono"]),
	"yhdistetty_E": ("sisatulento", ".concat", []),
	"liitetty_E": ("sisatulento", ".t_prepend", ["kohdekoodilista"]),
	"vähennetty_E": ("ulkoolento", "-", ["luku"]),
	"kerrottu_E": ("ulkoolento", "*", ["luku"]),
	"jaettu_E": ("ulkoolento", "/", ["luku"]),
	"rajattu_E": ("sisatulento", "%", ["luku"])
}

class FieldExpr(Expr,Recursive):
	def __init__(self, obj, field, arg_case=None, arg=None, place=None):
		Expr.__init__(self)
		self.obj = obj
		self.field = field
		self.arg_case = arg_case
		self.arg = arg
		self.place = place
	def subexpressions(self):
		return [self] + self.obj.subexpressions() + (self.arg.subexpressions() if self.arg else [])
	def isArithmetic(self):
		return self.field in ARI_OPERATORS and self.arg_case == ARI_OPERATORS[self.field][0]
	def isTargetCode(self):
		return self.field == "kohdekoodi_E" and isinstance(self.obj, StrExpr) and options["kohdekoodi"]
	def compile(self, indent):
		if self.isArithmetic():
			return self.compileArithmetic(indent)
		elif self.isTargetCode():
			return "(" + self.obj.str + ")"
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
	def infer(self, expected_types):
		if self.isArithmetic():
			return set(map(getClass, ARI_OPERATORS[self.field][2])) or classSet()
		elif self.isTargetCode():
			return classSet()
		functions = [
			f
			for f in getFunctions(self.field+"_"+str(self.arg_case))
			if not expected_types or not f.inferType().isdisjoint(expected_types)
		]
		possible_obj_types = set()
		for f in functions:
			possible_obj_types.update(f.classes())
		fields = getFields(self.field) if not self.arg_case else []
		if fields:
			for f in fields:
				possible_obj_types.update(f.classes())
		obj_types = self.obj.inferType(possible_obj_types)
		for f in fields:
			if not f.classes().isdisjoint(obj_types):
				return classSet()
		ret_types = set()
		for f in functions:
			if not f.classes().isdisjoint(obj_types):
				ret_types.update(f.inferType())
		if not ret_types:
			warning("unsuccessful inference of " + self.field + ", argument type is illegal: "
				+ "expected argument to be one of: {" + ", ".join([cl.name for cl in possible_obj_types])
				+ "}, but it is one of: {" + ", ".join([cl.name for cl in obj_types]) + "}",
				tokens, self.place, severity="Note")
		return ret_types
	def validate(self):
		if len(self.inferType()) == 0:
			if self.place:
				typeError("cannot infer the type of expression", tokens, self.place)
			else:
				typeError("cannot infer the type of expression")
		
		# erikoistapaukset
		if self.isArithmetic() or self.isTargetCode():
			pass
		
		# päätapaus
		elif len(getFunctions(self.field+"_"+str(self.arg_case)) + (getFields(self.field) if not self.arg_case else [])) == 0:
			if self.place:
				typeError("member not found", tokens, self.place)
			else:
				typeError("member not found")

class SubscriptExpr(Expr,Recursive):
	def __init__(self, obj, index, is_end_index=False):
		Expr.__init__(self)
		self.obj = obj
		self.index = index
		self.is_end_index = is_end_index
	def subexpressions(self):
		return [self] + self.obj.subexpressions()
	def compile(self, indent):
		if self.is_end_index:
			return self.obj.compile(indent) + ".nth_last(" + self.index.compile(indent) + ")"
		else:
			return self.obj.compile(indent) + "[" + self.index.compile(indent) + "-1]"
	def infer(self, expected_types):
		return classSet()

class SliceExpr(Expr,Recursive):
	def __init__(self, obj, start, end):
		Expr.__init__(self)
		self.obj = obj
		self.start = start
		self.end = end
	def subexpressions(self):
		return [self] + self.obj.subexpressions()
	def compile(self, indent):
		ans = self.obj.compile(indent) + ".slice("
		ans += self.start.compile(indent) + "-1"
		if self.end:
			ans += ", " + self.end.compile(indent)
		ans += ")"
		return ans
	def infer(self, expected_types):
		return set([getClass("kohdekoodilista")])

class NumExpr(Expr,Recursive):
	def __init__(self, num):
		Expr.__init__(self)
		self.num = num
	def compile(self, indent):
		return "(" + str(self.num) + ")"
	def infer(self, expected_types):
		return set([getClass("luku")])

class StrExpr(Expr,Recursive):
	def __init__(self, string):
		Expr.__init__(self)
		self.str = string
	def compile(self, indent):
		return repr(self.str)
	def infer(self, expected_types):
		return set([getClass("merkkijono")])

class NewExpr(Expr,Recursive):
	def __init__(self, typename, args, variable=None):
		Expr.__init__(self)
		self.type = typename
		self.args = args
		self.variable = variable
	def subexpressions(self):
		ans = []
		for arg in self.args:
			ans += arg.value.subexpressions()
		return [self] + ans
	def newVariables(self):
		if self.variable:
			return {self.variable: self.type}
		else:
			return {}
	def compile(self, indent):
		ans = "new " + typeToJs(self.type) + "({" + ", ".join(["\"" + arg.field + "\": " + arg.value.compile(indent) for arg in self.args]) + "})"
		if self.type in block_frame.backreferences:
			ans = "(se_" + escapeIdentifier(self.type) + "=" + ans + ")"
		if self.variable:
			ans = "(" + escapeIdentifier(self.variable) + "=" + ans + ")"
		return ans
	def infer(self, expected_types):
		return set([getClass(self.type)])

class CtorArgExpr:
	def __init__(self, field, value):
		self.field = field
		self.value = value

class ListExpr(Expr,Recursive):
	def __init__(self, values):
		Expr.__init__(self)
		self.values = values
	def subexpressions(self):
		ans = []
		for val in self.values:
			ans += val.subexpressions()
		return [self] + ans
	def compile(self, indent):
		return "[" + ", ".join([value.compile(indent) for value in self.values]) + "]"
	def infer(self, expected_types):
		return set([getClass("kohdekoodilista")])

class LambdaExpr(Expr,Recursive):
	def __init__(self, body):
		Expr.__init__(self)
		self.body = body
	def compile(self, indent):
		return "() => {\n" + compileBlock(self.body, indent+1, {}) + " "*indent + "}"
	def infer(self, expected_types):
		return set([getClass("kohdekoodifunktio")])
	# ei alalausekkeita

class TernaryExpr(Expr,Recursive):
	def __init__(self, condition, then, otherwise):
		Expr.__init__(self)
		self.condition = condition
		self.then = then
		self.otherwise = otherwise
	def subexpressions(self):
		ans = []
		ans += self.condition.subexpressions()
		return [self] + ans + self.then.subexpressions() + self.otherwise.subexpressions()
	def compile(self, indent):
		return ("((" + self.condition.compile(indent)
			+ ") ? (" + self.then.compile(indent)
			+ ") : (" + self.otherwise.compile(indent) + "))")
	def infer(self, expected_types):
		return self.then.inferType(expected_types) | self.otherwise.inferType(expected_types)
