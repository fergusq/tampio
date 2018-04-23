# Tampio Compiler
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

from fatal_error import typeError

classes = {}

def getClass(name):
	if name in classes:
		return classes[name]
	else:
		typeError("class not found: " + name)

def isClass(name):
	return name in classes

def classSet():
	return set(classes.values())

functions = {}
fields = {}

def getFunctions(name):
	if name in functions:
		return functions[name]
	else:
		return []

def getFields(name):
	if name in fields:
		return fields[name]
	else:
		return []

class Class:
	def __init__(self, name, super_class):
		self.name = name
		self.super_class = super_class and getClass(super_class)
		if self.super_class:
			self.super_class.addSubclass(self)
		self.subclasses = set()
		self.fields = []
		self.functions = []
		self.methods = []
		self.comparison_operators = []
	def __repr__(self):
		return "<Class " + self.name + ">"
	def addSubclass(self, cl):
		self.subclasses.add(cl)
		if self.super_class:
			self.super_class.addSubclass(cl)
	def addField(self, name, plural):
		f = Field(name, plural, self)
		self.fields.append(f)
		if name not in fields:
			fields[name] = []
		fields[name].append(f)
	def addFunction(self, name, arg_form, expr):
		f = Function(name, arg_form, expr, self)
		if name+"_"+str(arg_form) not in functions:
			functions[name+"_"+str(arg_form)] = []
		functions[name+"_"+str(arg_form)].append(f)
		self.functions.append(f)
	def addMethod(self, name, arg_forms):
		self.methods.append(Method(name, arg_forms))
	def addComparisonOperator(self, name):
		self.comparison_operators.append(ComparisonOperator(name))
	def hasField(self, name):
		return any([f.name == name for f in self.fields])
	def hasFunction(self, name):
		return name in [f.name for f in self.functions]

class Field:
	def __init__(self, name, plural, cl):
		self.name = name
		self.plural = plural
		self.cl = cl
	def classes(self):
		return set([self.cl]) | self.cl.subclasses

class Function:
	def __init__(self, name, arg_form, expr, cl):
		self.name = name
		self.arg_form = arg_form
		self.expr = expr
		self.cl = cl
		self.type = None
	def inferType(self):
		if self.type is None:
			self.type = set() # rekursion vuoksi tyypin on oltava inferenssin aikana tyhjä
			self.type = self.expr.inferType()
		return self.type
	def classes(self):
		return set([self.cl]) | self.cl.subclasses

class Method:
	def __init__(self, name, arg_forms):
		self.name = name
		self.arg_forms = arg_forms

class ComparisonOperator:
	def __init__(self, name):
		self.name = name
