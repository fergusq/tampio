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

class Class:
	def __init__(self, name, super_class):
		self.name = name
		self.super_class = super_class
		self.fields = []
		self.functions = []
		self.methods = []
		self.comparison_operators = []
	def addField(self, name, plural):
		self.fields.append(Field(name, plural))
	def addFunction(self, name, arg_form=None):
		self.functions.append(Function(name, arg_form))
	def addMethod(self, name, arg_forms):
		self.methods.append(Method(name, arg_forms))
	def addComparisonOperator(self, name):
		self.comparison_operators.append(ComparisonOperator(name))

class Field:
	def __init__(self, name, plural):
		self.name = name
		self.plural = plural

class Function:
	def __init__(self, name, arg_form):
		self.name = name
		self.arg_form = arg_form

class Method:
	def __init__(self, name, arg_forms):
		self.name = name
		self.arg_forms = arg_forms

class ComparisonOperator:
	def __init__(self, name):
		self.name = name
