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
import sys
from itertools import chain
from collections import namedtuple

from fatal_error import syntaxError
from inflect import *

from ast import *
from lex import accept, checkEof, eatComma, eatPeriod, ADJ, NOUN, NAME, PRONOUN, NUMERAL, VERB, CONJ, CARDINALS, ORDINALS

POSTPOSITIONS = {
	"nimento": ["kertaa"],
	"omanto": [
		"alla", "alta", "alle",
		"keskellä", "keskeltä", "keskelle",
		"edessä", "edestä", "eteen",
		"takana", "takaa", "taakse",
		"mukaisesti"
	]
}

def formToEnglish(form, article=True, short = False):
	if short:
		if form in CASES_ENGLISH:
			return CASES_ENGLISH[form]
		else:
			return form
	else:
		if form in CASES_ENGLISH:
			return "in " + CASES_ENGLISH[form] + " case"
		elif form in chain.from_iterable(POSTPOSITIONS.values()):
			return ("an " if article else "") + "argument to the " + form + " postposition"
		else:
			return "in " + form

def parseDeclaration(tokens):
	checkEof(tokens)
	token = tokens.peek()
	if token.token.lower() == "kun":
		tokens.next()
		tokens.setStyle("keyword")
		signature = parseSentence(tokens)
		body = parseList(parseSentence, tokens, do_format=True)
		eatPeriod(tokens)
		tokens.addNewline()
		return ProcedureDecl(signature, body)
	elif token.token.lower() == "olkoon":
		tokens.next()
		tokens.setStyle("keyword")
		word1, word2 = parseVariable(tokens, case="nimento")
		value, case = parseNominalPhrase(tokens, promoted_cases=["nimento"])
		if case != "nimento":
			syntaxError("predicative is " + formToEnglish(case) + " (should be in the nominative case)", tokens)
		eatPeriod(tokens)
		tokens.addNewline()
		return VariableDecl(word1.baseform + "_" + word2.baseform, value)
	else:
		word = token.toWord(cls=NOUN+ADJ,forms=["ulkoolento", "omanto"])
		if word.isNoun() and word.form == "ulkoolento":
			tokens.next()
			tokens.setStyle("type")
			accept(["on"], tokens)
			tokens.setStyle("keyword")
			fields = parseList(parseFieldName, tokens)
			eatPeriod(tokens)
			tokens.addNewline()
			return ClassDecl(word.baseform, fields)
		elif word.isNoun() and word.form == "nimento":
			tokens.next()
			tokens.setStyle("type")
			accept(["on"], tokens)
			tokens.setStyle("keyword")
			checkEof(tokens)
			super_type = tokens.next().toWord(cls=NOUN,forms=["nimento"])
			if not super_type.isNoun() or super_type.form != "nimento":
				syntaxError("super type must be a noun in the nominative case", tokens)
			accept([","], tokens)
			accept(["jolla"], tokens)
			tokens.setStyle("keyword")
			accept(["on"], tokens)
			tokens.setStyle("keyword")
			fields = parseList(parseFieldName, tokens)
			eatPeriod(tokens)
			tokens.addNewline()
			return ClassDecl(word.baseform, fields, super_type=super_type.baseform)
		elif (word.isAdjective() or word.isNoun()) and word.form == "omanto":
			if word.isAdjective():
				tokens.next()
				tokens.setStyle("variable")
				_, typeword = parseVariable(tokens, word=word, case="omanto")
				varname = word.baseform + "_" + typeword.baseform
			elif word.isNoun():
				typeword = word
				tokens.next()
				tokens.setStyle("type")
				varname = ""
			field, field_number = parseFieldName(tokens, word.form)
			if field_number == "plural":
				accept(["ovat"], tokens)
			else:
				accept(["on"], tokens)
			tokens.setStyle("keyword")
			body, case = parseNominalPhrase(tokens, promoted_cases=["nimento"])
			if case != "nimento":
				syntaxError("predicative is " + formToEnglish(case) + " (should be in the nominative case)", tokens)
			wheres = parseWheres(tokens)
			eatPeriod(tokens)
			tokens.addNewline()
			return FunctionDecl(typeword.baseform, field, varname, body, wheres)
	tokens.next()
	syntaxError("unexpected token \"" + token.token + "\"", tokens)

def parseVariable(tokens, word=None, case="nimento"):
	if not word:
		checkEof(tokens)
		word = tokens.next().toWord(cls=ADJ, forms=[case])
		if not word.isAdjective() or word.form != case:
			syntaxError("this variable must begin with an adjective " + formToEnglish(case, article=False), tokens)
		tokens.setStyle("variable")
	checkEof(tokens)
	word2 = tokens.next().toWord(cls=NOUN, forms=[case])
	if not word2.isNoun() or word2.form != case:
		syntaxError("this variable must end with a noun " + formToEnglish(case, article=False), tokens)
	if word.number != word2.number:
		syntaxError("variable words do not accept in number", tokens)
	tokens.setStyle("type")
	return word, word2

def parseFieldName(tokens, form="omanto"):
	expected_form = "nimento" if form == "omanto" else "olento"
	checkEof(tokens)
	word = tokens.next().toWord(cls=NOUN,forms=[expected_form])
	if word.form != expected_form:
		syntaxError("malformed member name, expected a noun " + formToEnglish(expected_form, article=False), tokens)
	tokens.setStyle("field")
	field = word.baseform
	if word.form == "olento":
		field += "_E"
	return field, word.number

def parseWheres(tokens):
	token = tokens.peek()
	if token and token.token.lower() == "," and tokens.peek(2) and tokens.peek(2).token.lower() == "missä":
		tokens.next()
		tokens.next()
		tokens.setStyle("keyword")
		wheres = parseList(parseAssignment, tokens)
		eatComma(tokens)
	elif token and token.token.lower() == "missä":
		if tokens.current().token != ",":
			syntaxError("there must be a comma before \"missä\"", tokens)
		tokens.next()
		tokens.setStyle("keyword")
		wheres = parseList(parseAssignment, tokens)
		eatComma(tokens)
	else:
		wheres = []
	return wheres

# pino jokainen-lausekkeiden tallentamista varten (siis for-silmukoiden, vrt. rödan _)
FOR_STACK = []

ForVar = namedtuple("ForVar", ["name", "expr", "type"])

def pushFor(*allowed_types):
	FOR_STACK.append((allowed_types, []))

def addForVar(i_name, expr, var_type, tokens):
	if len(FOR_STACK) == 0 or var_type not in FOR_STACK[-1][0]:
		syntaxError("\"" + var_type + "\" can't be used in this context", tokens)
	name = i_name
	i = 1
	while [fv.name for fv in FOR_STACK[-1][1]].count(name) > 0:
		name = i_name + str(i)
		i += 1
	FOR_STACK[-1][1].append(ForVar(name, expr, var_type))
	return name

def popFor():
	return FOR_STACK.pop()[1]

def parseSentence(tokens):
	checkEof(tokens)
	token = tokens.peek()
	if token.token.lower() == "jos" or (token.token == "," and tokens.peek(2) and tokens.peek(2).token.lower() == "jos"):
		if token.token == ",":
			tokens.next()
		elif tokens.current().token != ",":
			syntaxError("there must be a comma before \"jos\"", tokens)
		tokens.next()
		tokens.setStyle("keyword")
		conditions = parseList(parseCondition, tokens, ["niin"])
		block = parseList(parseSentence, tokens, do_format=True)
		eatComma(tokens)
		return IfStatement(conditions, block)
	
	pushFor("jokainen")
	word = tokens.peek().toWord(
		cls=ADJ*2+NUMERAL*2+NAME*2+VERB,
		forms=["imperative_present_simple2", "indicative_present_simple4", "nimento", "osanto"])
	if word.isAdjective() or word.isOrdinal() or word.isName() or word.isPronoun() or word.isNoun():
		subject, case = parseNominalPhrase(tokens, promoted_cases=["nimento", "omanto"])
		
		place = tokens.place()
		
		for_vars = popFor()
		
		checkEof(tokens)
		word = tokens.next().toWord(
			cls=VERB,
			forms=["indicative_present_simple3", "indicative_present_simple4", "E-infinitive_sisaolento"])
		
		if word.isVerb() and word.form in ["E-infinitive_sisaolento3", "E-infinitive_sisaolento4"]:
			tokens.setStyle("function")
			method = word.baseform + readVerbModifiers(tokens)
			if word.form[-1] == "3":
				method += "_A"
			else:
				method += "_P"
			
			if word.form[-1] == "3" and case != "omanto":
				syntaxError("subject is not in the genitive case", tokens, place)
			
			subject_case = case
			
			params = {}
			while not tokens.eof():
				peek = tokens.peek()
				if peek.token.lower() in [",", ".", "eikä", "ja"]:
					break
				if not peek.isWord() or not peek.toWord(cls=ADJ).isAdjective():
					break
				param, case = parseNominalPhrase(tokens)
				if not isinstance(param, VariableExpr):
					syntaxError("malformed parameter", tokens)
				if case in params:
					syntaxError("parameter repeated twice", tokens)
				params[case] = param
			for keyword in ["käyköön", "niin", ",", "että"]:
				accept([keyword], tokens)
				if keyword != ",":
					tokens.setStyle("keyword")
			body = parseList(parseSentence, tokens, do_format=True)
			eatComma(tokens)
			stmt = MethodAssignmentStatement(subject, subject_case, method, params, body)
			
			for for_var in for_vars:
				stmt = ForStatement(for_var.name, for_var.expr, stmt)
			return stmt
		
		if not word.isVerb() or word.form not in ["indicative_present_simple3", "indicative_present_simple4"]:
			syntaxError("predicate is not in indicative simple present", tokens)
		tokens.setStyle("function")
		
		passive = word.form[-1] == "4"
		predicate = word.baseform + readVerbModifiers(tokens) + ("_P" if passive else "_A")
		
		if case != "nimento" and not passive:
			syntaxError("subject must be in nominative case", tokens, place)
		
		subjectless = False
		subject_case = case
	elif word.isVerb():
		tokens.next()
		tokens.setStyle("function")
		place = tokens.place()
		for_vars = popFor()
		subjectless = True
		passive = True
		if word.form == "imperative_present_simple2":
			predicate = word.baseform + "!"
		elif word.form == "indicative_present_simple4":
			predicate = word.baseform + readVerbModifiers(tokens)
		else:
			syntaxError("predicate ("+word.word+") is not in indicative or imperative simple present", tokens, place)
	else:
		syntaxError("malformed sentence", tokens)
	
	for_var_list = []
	args_list = []
	output_vars = []
	
	prev_args = {}
	while True:
		pushFor("jokainen")
		args = {}
		while not tokens.eof():
			if tokens.peek().token.lower() in ["sekä", ",", ".", "eikä", "ja", "tuloksenaan"]:
				break
			arg, case = parseNominalPhrase(tokens)
			if case in args:
				syntaxError(formToEnglish(case, short=True) + " argument repeated twice", tokens)
			args[case] = arg
			if isinstance(arg, LambdaExpr): # että-lohkot ovat lauseissa aina viimeisenä
				break
		args_list.append({**prev_args, **args})
		prev_args = args
		
		if (not tokens.eof() and (
				(tokens.peek().token.lower() == "tuloksenaan" and not passive)
				or (tokens.peek().token.lower() == "tuloksena" and passive)
				)):
			tokens.next()
			tokens.setStyle("keyword")
			w1, w2 = parseVariable(tokens)
			output_vars.append(w1.baseform + "_" + w2.baseform)
		else:
			output_vars.append(None)
		
		for_var_list.append(for_vars+popFor())
		
		if not tokens.eof() and tokens.peek().token.lower() == "sekä":
			tokens.next()
			tokens.setStyle("keyword")
			continue
		else:
			break
	
	eatComma(tokens)
	
	wheres = parseWheres(tokens)
	
	stmts = []
	
	for args, output_var, for_vars in zip(args_list, output_vars, for_var_list):
		if subjectless:
			stmt = ProcedureCallStatement(predicate, args, output_var)
		else:
			stmt = MethodCallStatement(subject, subject_case, predicate, args, output_var)
		
		for for_var in for_vars:
			stmt = ForStatement(for_var.name, for_var.expr, stmt)
		
		stmts.append(stmt)
	
	if len(stmts) == 1 and len(wheres) == 0:
		return stmts[0]
	else:
		return BlockStatement(stmts, wheres)

def readVerbModifiers(tokens):
	ans = ""
	while not tokens.eof():
		token = tokens.peek()
		if token.isWord():
			word = token.toWord(cls=ADJ+NUMERAL+CONJ+PRONOUN)
			if ((word.isNoun()
				and word.baseform not in CARDINALS
				and word.baseform not in ORDINALS
				and (not tokens.peek(2) or not tokens.peek(2).isString())
				and word.form != "olento"
				and len(word.baseform) > 1)
				or word.isAdverb()):
				
				tokens.next()
				tokens.setStyle("function")
				ans += "_" + token.token.lower()
			else:
				break
		else:
			break
	return ans

ARI_OPERATORS = {
	"lisättynä": ("sisatulento", "+"),
	"ynnättynä": ("sisatulento", "+"),
	"yhdistettynä": ("sisatulento", ".concat"),
	"liitettynä": ("sisatulento", ".prepend"),
	"vähennettynä": ("ulkoolento", "-"),
	"kerrottuna": ("ulkoolento", "*"),
	"jaettuna": ("ulkoolento", "/")
}

CMP_OPERATORS = {
	"yhtä suuri kuin": "===",
	"yhtäsuuri kuin": "===",
	"yhtä kuin": "===",
	"sama kuin": "===",
	"erisuuri kuin": "!==",
	"pienempi kuin": "<",
	"pienempi tai yhtä suuri kuin": "<=",
	"pienempi tai yhtäsuuri kuin": "<=",
	"suurempi kuin": ">",
	"suurempi tai yhtä suuri kuin": ">=",
	"suurempi tai yhtäsuuri kuin": ">="
}

CMP_TREE = {}

for key in CMP_OPERATORS.keys():
	words = key.split()
	branch = CMP_TREE
	for word in words[:-1]:
		if word not in branch:
			branch[word] = {}
		branch = branch[word]
	branch[words[-1]] = CMP_OPERATORS[key]

def parseCondition(tokens, prefix=False):
	pushFor("jokainen", "jokin")
	if prefix:
		checkEof(tokens)
		if tokens.peek().token.lower() == "eikö":
			tokens.next()
			tokens.setStyle("keyword")
			negation = True
		else:
			accept(["onko"], tokens)
			tokens.setStyle("keyword")
			negation = False
	operand1, case = parseNominalPhrase(tokens, promoted_cases=["nimento"])
	if case != "nimento":
		syntaxError("subject is not in nominative case", tokens)
	if not prefix:
		checkEof(tokens)
		if tokens.peek().token.lower() == "ei":
			tokens.next()
			tokens.setStyle("keyword")
			accept(["ole"], tokens)
			tokens.setStyle("keyword")
			negation = True
		else:
			accept(["on"], tokens)
			tokens.setStyle("keyword")
			negation = False
	elif negation:
		accept(["ole"], tokens)
		tokens.setStyle("keyword")
	operator, requires_second_operand = parseOperator(tokens)
	if requires_second_operand:
		operand2, case = parseNominalPhrase(tokens, promoted_cases=["nimento"])
		if case != "nimento":
			syntaxError("predicative is " +formToEnglish(case) + " (should be in the nominative case)", tokens)
	else:
		operand2 = None
	eatComma(tokens)
	for_vars = popFor()
	expr = CondExpr(negation, operator, operand1, operand2)
	for for_var in for_vars:
		expr = QuantifierCondExpr(for_var.type, for_var.name, for_var.expr, expr)
	return expr

def parseOperator(tokens):
	checkEof(tokens)
	if tokens.peek().token.lower() in CMP_TREE.keys():
		branch = CMP_TREE
		while isinstance(branch, dict):
			token = tokens.next().token.lower()
			if token in branch:
				branch = branch[token]
				tokens.setStyle("keyword")
			else:
				syntaxError("unexpected token, expected " + " or ".join(["\"" + t + "\"" for t in branch.keys()]), tokens)
		return branch, True
	elif tokens.peek(2) and tokens.peek().toWord(cls=ADJ).isAdjective() and (not tokens.peek(2).isWord() or not tokens.peek(2).toWord(cls=NOUN).isNoun()):
		word = tokens.next().toWord(cls=ADJ)
		tokens.setStyle("function")
		if word.form != "nimento":
			syntaxError("expected an adjective in the nominative case", tokens)
		if word.comparison == "comparative":
			accept(["kuin"], tokens)
			tokens.setStyle("keyword")
			return ".c_" + word.baseform, True
		else:
			return ".p_" + word.baseform, False
	else:
		return "===", True

def parseNominalPhrase(tokens, must_be_in_genitive=False, promoted_cases=[]):
	checkEof(tokens)
	if tokens.peek().token.lower() == "riippuen":
		accept(["riippuen"], tokens)
		tokens.setStyle("keyword")
		accept(["siitä"], tokens)
		tokens.setStyle("keyword")
		accept([","], tokens)
		conds = parseList(lambda t: parseCondition(t, prefix=True), tokens, ["joko"])
		tokens.increaseIndentLevel()
		alt1, case1 = parseNominalPhrase(tokens)
		accept(["tai"], tokens)
		tokens.addNewline()
		tokens.setStyle("keyword")
		alt2, case2 = parseNominalPhrase(tokens)
		tokens.decreaseIndentLevel()
		if case1 != case2:
			syntaxError("both operands of \"tai\" must be in the same case", tokens)
		return TernaryExpr(conds, alt1, alt2), case1
	word = tokens.next().toWord(cls=ADJ+NAME+NUMERAL+PRONOUN,forms=promoted_cases)
	if word.isVariable():
		tokens.setStyle("variable")
		expr = VariableExpr(word.baseform)
		case = word.form
	elif word.isNoun() and word.possessive == "" and word.form == "olento" and word.word != "tuloksena":
		tokens.setStyle("field")
		expr, case = parseNominalPhrase(tokens)
	elif word.baseform in ["jokainen", "jokin"]:
		tokens.setStyle("keyword")
		case = word.form
		expr, case2 = parseNominalPhrase(tokens, case == "omanto")
		if case != case2:
			syntaxError("a quantifier and its nominal phrase must be in the same case", tokens)
		name = addForVar(word.baseform, expr, word.baseform, tokens)
		expr = VariableExpr(name)
	elif word.isOrdinal():
		tokens.setStyle("literal")
		case = word.form
		index = NumExpr(ORDINALS.index(word.baseform)+1)
		expr, case2 = parseNominalPhrase(tokens, case == "omanto")
		if case != case2:
			syntaxError("an ordinal and its nominal phrase must be in the same case", tokens)
		expr = SubscriptExpr(expr, index)
	elif word.isCardinal():
		tokens.setStyle("literal")
		case = word.form
		expr = NumExpr(CARDINALS.index(word.baseform))
	elif re.fullmatch(r'\d+', word.baseform):
		tokens.setStyle("literal")
		case = word.form
		expr = NumExpr(int(word.baseform))
	elif word.isNoun() and tokens.peek() and tokens.peek().isString():
		tokens.setStyle("keyword")
		case = word.form
		expr = StrExpr(tokens.next().token[1:-1])
		tokens.setStyle("literal")
	elif word.isName():
		tokens.setStyle("variable")
		case = word.form
		variable = word.baseform
		expr = VariableExpr(variable)
	elif word.isPronoun() and word.baseform == "se":
		if tokens.peek(1) and tokens.peek(1).token == "," and tokens.peek(2) and tokens.peek(2).token.lower() == "että":
			tokens.setStyle("keyword")
			accept([","], tokens)
			accept(["että"], tokens)
			tokens.setStyle("keyword")
			body = parseList(parseSentence, tokens, do_format=True)
			eatComma(tokens)
			case = word.form
			expr = LambdaExpr(body)
		else:
			tokens.setStyle("variable")
			case = word.form
			expr = VariableExpr("this")
	elif word.isAdjective() and word.baseform == "uusi":
		tokens.setStyle("keyword")
		checkEof(tokens)
		word2 = tokens.next().toWord(cls=NOUN,forms=[word.form])
		if not word2.isNoun():
			syntaxError("a type must be a noun", tokens)
		if word.form != word2.form:
			syntaxError("the adjective and the noun of a constructor call must be in the same case", tokens)
		
		tokens.setStyle("type")
		case = word.form
		if tokens.peek(1) and tokens.peek(2) and tokens.peek(1).token == "," and tokens.peek(2).token.lower() == "jonka":
			tokens.next()
			tokens.next()
			tokens.setStyle("keyword")
			
			args = parseList(parseCtorArg, tokens)
			
			eatComma(tokens)
		else:
			args = []
		expr = NewExpr(word2.baseform, args)
	else:
		tokens.setStyle("variable")
		if tokens.eof():
			syntaxError("unexpected eof, a variable must have at least two words", tokens)
		place = tokens.place()
		word2 = tokens.next().toWord(cls=NOUN,forms=[word.form])
		if not word.isAdjective():
			syntaxError("a variable must begin with an adjective: "+word.baseform+" "+word2.baseform, tokens, place)
		if not word2.isNoun():
			syntaxError("a variable must end with a noun: "+word.baseform+" "+word2.baseform, tokens)
		if word.form != word2.form:
			syntaxError("the adjective and the noun of a variable must be in the same case", tokens)
		
		tokens.setStyle("type")
		case = word.form
		variable = word.baseform + "_" + word2.baseform
		
		expr = VariableExpr(variable, word2.baseform)
	
	cont = True
	while cont:
		cont = False
		
		# slice
		
		if not tokens.eof() and tokens.peek().isWord():
			word = tokens.peek().toWord(cls=NUMERAL, forms=["sisatulento", "sisaeronto"])
			if word.form in ["sisatulento", "sisaeronto"] and tokens.peek(2) and tokens.peek(2).token.lower() in ["alkaen", "päättyen"]:
				is_slice = False
				if word.isOrdinal():
					tokens.next()
					tokens.setStyle("literal")
					index = NumExpr(ORDINALS.index(word.baseform)+1)
					is_slice = True
				elif word.isVariable() and word.ordinal_like:
					tokens.next()
					tokens.setStyle("variable")
					index = VariableExpr(word.baseform)
					is_slice = True
				if is_slice:
					if word.form == "sisaeronto":
						accept(["alkaen"], tokens)
						expr = SliceExpr(expr, index, None)
					elif word.form == "sisatulento":
						accept(["päättyen"], tokens)
						expr = SliceExpr(expr, NumExpr(1), index)
					tokens.setStyle("keyword")
					cont = True
					
		
		# omistusrakenne
		
		while case == "omanto" and not tokens.eof():
			token = tokens.peek()
			if not token.isWord():
				break
			word = token.toWord(cls=2*NOUN+2*NUMERAL+PRONOUN, forms=["omanto", "E-infinitive_sisaolento", "E-infinitive_sisaolento"])
			if must_be_in_genitive and word.form != "omanto":
				break
			peek2 = tokens.peek(2)
			if word.baseform in ["jokainen", "jokin"] and peek2 and peek2.toWord(cls=NOUN, forms=[word.form]).isNoun():
				tokens.next()
				tokens.setStyle("keyword")
				checkEof(tokens)
				word2 = tokens.next().toWord(cls=NOUN, forms=[word.form])
				if not word2.isNoun() or word2.form != word.form:
					syntaxError("expected a noun " + formToEnglish(word.form, article=False), tokens)
				tokens.setStyle("field")
				case = word.form
				field = word2.baseform
				field_expr = FieldExpr(expr, field)
				var = addForVar(word.baseform + "_" + word2.baseform, field_expr, word.baseform, tokens)
				expr = VariableExpr(var)
			elif ((word.isOrdinal() or (word.isVariable() and word.ordinal_like) or word.baseform == "viimeinen")
				and peek2 and (
					peek2.toWord(cls=NOUN, forms=[word.form]).isNoun()
					or peek2.toWord(cls=ADJ, forms=[word.form]).baseform == "viimeinen")):
				tokens.next()
				if word.isOrdinal():
					tokens.setStyle("literal")
					index = NumExpr(ORDINALS.index(word.baseform)+1)
					end_index = False
				elif word.baseform == "viimeinen":
					tokens.setStyle("keyword")
					index = NumExpr(1)
					end_index = True
				else:
					tokens.setStyle("variable")
					index = VariableExpr(word.baseform)
					end_index = False
				checkEof(tokens)
				word2 = tokens.next().toWord(cls=NOUN, forms=[word.form])
				if word.form == "tulento" and word2.baseform == "viimeinen" and not end_index:
					tokens.setStyle("keyword")
					end_index = True
					checkEof(tokens)
					word = word2
					word2 = tokens.next().toWord(cls=NOUN, forms=[word.form])
				if not word2.isNoun() or word2.form != word.form:
					syntaxError("expected a noun " + formToEnglish(word.form, article=False), tokens)
				tokens.setStyle("field")
				case = word.form
				field = word2.baseform
				expr = SubscriptExpr(FieldExpr(expr, field), index, end_index)
				cont = True
			elif word.isNoun() and word.possessive == "":
				tokens.next()
				tokens.setStyle("field")
				case = word.form
				field = word.baseform
				
				expr = FieldExpr(expr, field)
				cont = True
			else:
				break
		
		# essiiviketju
		# esim. <lauseke> kerrottuna <lausekkeella> ja <toisella>
		# esim. <luku> pyöristettynä ja merkkijonona
		
		require_ja = False
		while not tokens.eof() and tokens.peek().isWord():
			word = tokens.peek().toWord(cls=NOUN, forms="olento")
			if word.word.lower() in ARI_OPERATORS.keys():
				operator = tokens.next().token.lower()
				tokens.setStyle("keyword")
				required_arg_case, op = ARI_OPERATORS[operator]
				arg, arg_case = parseNominalPhrase(tokens, promoted_cases=[required_arg_case])
				if arg_case != required_arg_case:
					syntaxError("the operand of \"" + operator + "\" must be "
						+ formToEnglish(required_arg_case), tokens)
				expr = ArithmeticExpr(op, expr, arg)
				cont = True
			elif word.isNoun() and word.form == "olento" and word.possessive == "" and word.word != "tuloksena":
				tokens.next()
				tokens.setStyle("field")
				expr = FieldExpr(expr, word.baseform + "_E")
				cont = True
			else:
				break
			peek1 = tokens.peek(1)
			peek2 = tokens.peek(2)
			word2 = peek2.toWord(cls=NOUN, forms="olento") if peek2 and peek2.isWord() else None
			if (peek1 and peek2 and peek1.token.lower() in [",", "ja"]
				and (peek2.token.lower() in ARI_OPERATORS.keys()
					or (peek2.isWord() and word2.isNoun() and word2.form == "olento"))):
				if tokens.next().token == ",":
					require_ja = True
				else: # ja
					require_ja = False
					tokens.setStyle("keyword")
				continue
			else:
				if require_ja:
					tokens.next()
					syntaxError("an essive chain must end with \"ja\"", tokens)
				break
	
	if case in POSTPOSITIONS and tokens.peek() and tokens.peek().token.lower() in POSTPOSITIONS[case]:
		pp = tokens.next().token.lower()
		tokens.setStyle("keyword")
		return expr, pp
	
	else:
		return expr, case

def parseAssignment(tokens):
	checkEof(tokens)
	if tokens.peek().toWord().isVariable():
		var = tokens.next().toWord().baseform
		tokens.setStyle("variable")
	else:
		word, word2 = parseVariable(tokens)
		var = word.baseform + "_" + word2.baseform
	accept(["on", "ovat"], tokens)
	tokens.setStyle("keyword")
	value, case = parseNominalPhrase(tokens, promoted_cases=["nimento"])
	if case != "nimento":
		syntaxError("contructor argument value is not in nominative case", tokens)
	return (var, value)

def parseCtorArg(tokens):
	checkEof(tokens)
	word = tokens.next().toWord(cls=NOUN, forms=["nimento", "partitive"])
	if not word.isNoun() or not (word.form == "nimento" or (word.form == "osanto" and word.number == "plural")):
		syntaxError("constructor argument name is not a noun in nominative case or a plural noun in partitive case", tokens)
	tokens.setStyle("field")
	checkEof(tokens)
	token = tokens.peek().token.lower()
	if word.number == "plural":
		accept(["ovat"], tokens)
	else:
		accept(["on"], tokens)
	tokens.setStyle("keyword")
	if token == "on" or word.form == "nimento": # (esim. alkio on x, alkiot ovat y:t)
		value, case = parseNominalPhrase(tokens, promoted_cases=["nimento"])
		if case != "nimento":
			syntaxError("contructor argument value is not in nominative case", tokens)
		return CtorArgExpr(word.baseform, value)
	else: # partitiivi, ovat (esim. alkioita ovat x ja y)
		values_cases = parseList(parseNominalPhrase, tokens)
		values = []
		for value, case in values_cases:
			values += [value]
			if case != "nimento":
				syntaxError("contructor argument value is not in nominative case", tokens)
		return CtorArgExpr(word.baseform, ListExpr(values))

def parseList(parseChild, tokens, custom_endings=[], do_format=False):
	if do_format:
		tokens.increaseIndentLevel()
	ans = []
	force = False
	while force or (not tokens.eof() and not tokens.peek().token.lower() in [".", "ja", "eikä"] + custom_endings):
		if do_format and len(ans) > 0:
			tokens.addNewline()
		ans += [parseChild(tokens)]
		if not tokens.eof() and tokens.peek().token == ",":
			tokens.next()
			force = True
		else:
			force = False
	checkEof(tokens)
	if len(ans) == 1 and tokens.peek().token == ".":
		if do_format:
			tokens.decreaseIndentLevel()
		return ans
	if do_format:
		tokens.addNewline()
	token = tokens.next()
	tokens.setStyle("keyword")
	if token.token.lower() == "eikä":
		accept(["muuta"], tokens)
		tokens.setStyle("keyword")
	elif token.token.lower() == "ja":
		ans += [parseChild(tokens)]
	elif token.token.lower() not in custom_endings:
		syntaxError("unexpected token, expected " + ", ".join(["\""+t+"\"" for t in custom_endings+["ja"]]) + " or \"eikä\"", tokens)
	if do_format:
		tokens.decreaseIndentLevel()
	return ans
