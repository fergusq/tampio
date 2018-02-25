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
import sys
from itertools import chain
from collections import namedtuple

from fatal_error import syntaxError
from inflect import *

from ast import *
from lex import accept, checkEof, eat, eatComma, eatPeriod, afterCommaThereIs, ADJ, NOUN, NAME, PRONOUN, NUMERAL, VERB, CONJ, CARDINALS, ORDINALS

def initializeParser():
	global options, current_class
	options = {
		"kohdekoodi": False,
		"takaisinviittaukset": False
	}
	current_class = None

POSTPOSITIONS = {
	"nimento": ["kertaa"],
	"omanto": [
		"alla", "alta", "alle",
		"keskellä", "keskeltä", "keskelle",
		"edessä", "edestä", "eteen",
		"takana", "takaa", "taakse",
		"vieressä", "vierestä", "viereen",
		"vierellä", "viereltä", "vierelle",
		"luona", "luota", "luokse",
		"lähellä", "läheltä", "lähelle",
		"ohessa", "ohesta", "oheen",
		"ohella", "ohelta", "ohelle",
		"seassa", "seasta", "sekaan",
		"sisällä", "sisältä", "sisälle",
		
		"ali", "alitse",
		"ohi", "ohitse",
		"lomitse",
		"läpi", "lävitse",
		"poikki", "poikitse",
		"yli", "ylitse",
		"ympäri",
		
		"mukaisesti", "mukaan",
		
		"kanssa",
		"suhteen",
		"takia",
		
		"kuluessa"
	],
	"osanto": [
		"kohden", "kohti",
		"vastaan",
		"vasten",
		"varten"
	],
	"sisatulento": [
		"asti",
		"mennessä",
		"saakka"
	]
}

FAKE_INTRANSITIVES = [
	"ammuttu",
	"halveksuttu",
	"haukuttu",
	"hyväksytty",
	"kammoksuttu",
	"kaduttu",
	"kehuttu",
	"kutsuttu",
	"kysytty",
	"lausuttu",
	"lähestytty",
	"manguttu",
	"noiduttu", 
	"omaksuttu",
	"oudoksuttu",
	"paheksuttu",
	"peruttu",
	"puhuttu",
	"riisuttu",
	"uhkuttu",
	"väheksytty",
	"väijytty",
	"yllätytty"
]

def isPartitiveIntransitiveParticiple(word):
	return (word.isAdjective()
		and word.form == "osanto"
		and len(word.baseform) > 4 and word.baseform[-4:] in ["uttu", "ytty"]
		and word.baseform not in FAKE_INTRANSITIVES)

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
		else: # intransitive participle
			return "an agent to the " + form + " participle"

def parseDeclaration(tokens):
	global current_class
	current_class = None
	checkEof(tokens)
	token = tokens.peek()
	# Metodi, proseduuri
	if token.token.lower() == "kun":
		tokens.next()
		tokens.setStyle("keyword")
		signature = parseSentence(tokens, signature=True)
		if isinstance(signature, MethodCallStatement):
			current_class = signature.obj.type
		with AllowBackreferences():
			body = parseList(parseSentence, tokens, do_format=True)
		stmts = parseAdditionalStatements(tokens)
		eatPeriod(tokens)
		tokens.addNewline()
		return ProcedureDecl(signature, body, stmts)
	# Globaali muuttuja
	elif token.token.lower() == "olkoon":
		tokens.next()
		tokens.setStyle("keyword")
		word1, word2 = parseVariable(tokens, case="nimento")
		value = parseNominativePredicative(tokens)
		stmts = parseAdditionalStatements(tokens)
		eatPeriod(tokens)
		tokens.addNewline()
		return VariableDecl(word1.baseform + "_" + word2.baseform, word2.baseform, value, stmts)
	# Imperatiivit
	elif token.token.lower() == "sisällytä":
		tokens.next()
		tokens.setStyle("keyword")
		if options["kohdekoodi"] and tokens.peek() and tokens.peek().token.lower() == "kohdekoodi":
			tokens.next()
			tokens.setStyle("keyword")
			code = tokens.next()
			if not code.isString():
				syntaxError("target code is not a string token", tokens)
			tokens.setStyle("literal")
			stmts = parseAdditionalStatements(tokens)
			eatPeriod(tokens)
			tokens.addNewline()
			return TargetCodeDecl(parseString(code.token), stmts)
		elif tokens.peek() and tokens.peek().token.lower() in ["tiedosto"]+(["kohdekooditiedosto"] if options["kohdekoodi"] else []):
			tc = tokens.next().token.lower() == "kohdekooditiedosto"
			tokens.setStyle("keyword")
			filename = tokens.next()
			if not filename.isString():
				syntaxError("file name is not a string token", tokens)
			tokens.setStyle("literal")
			stmts = parseAdditionalStatements(tokens)
			eatPeriod(tokens)
			tokens.addNewline()
			if not tc:
				return IncludeFileDecl(parseString(filename.token), stmts)
			else:
				return IncludeTargetCodeFileDecl(parseString(filename.token), stmts)
	elif token.token.lower() in ["salli", "kiellä"]:
		positive = tokens.next().token.lower() == "salli"
		tokens.setStyle("keyword")
		if tokens.peek() and tokens.peek().isWord():
			option = tokens.next().token.lower()
			tokens.setStyle("literal")
			options[option] = positive
			eatPeriod(tokens)
			tokens.addNewline()
			return SetOptionDecl(positive, option)
	elif token.token.lower() == "tulkitse":
		tokens.next()
		tokens.setStyle("keyword")
		cl = tokens.next().toWord(cls=NOUN,forms="nimento")
		if cl.form != "nimento":
			syntaxError("class name not in the nominative case", tokens)
		tokens.setStyle("type")
		if (options["kohdekoodi"]
			and tokens.peek() and tokens.peek().token.lower() == "kohdekoodityyppinä"
			and tokens.peek(2) and tokens.peek(2).isString()):
			tokens.next()
			tokens.setStyle("keyword")
			tc_class = parseString(tokens.next().token)
			tokens.setStyle("literal")
			stmts = parseAdditionalStatements(tokens)
			eatPeriod(tokens)
			tokens.addNewline()
			return TargetCodeClassDecl(cl.baseform, tc_class, stmts)
		else:
			cl2 = tokens.next().toWord(cls=NOUN,forms="olento")
			if cl2.form != "olento":
				syntaxError("class name not in the essive case", tokens)
			tokens.setStyle("type")
			stmts = parseAdditionalStatements(tokens)
			eatPeriod(tokens)
			tokens.addNewline()
			return AliasClassDecl(cl.baseform, cl2.baseform, stmts)
	# Vertailuoperaattori
	elif afterCommaThereIs("jos", tokens):
		varname, typename, case = parseSelfVariable(tokens)
		signature = parseConditionPredicateAndArgs(tokens, VariableExpr(varname, typename), case, allow_negation=False)
		accept([","], tokens)
		accept(["jos"], tokens)
		tokens.setStyle("keyword")
		conditions = parseOuterCondition(tokens, do_format=True)
		wheres = parseWheres(tokens)
		stmts = parseAdditionalStatements(tokens)
		eatPeriod(tokens)
		tokens.addNewline()
		return CondFunctionDecl(typename, signature, conditions, wheres, stmts)
	# Muut
	else:
		word = token.toWord(cls=NOUN+ADJ,forms=["ulkoolento", "omanto", "nimento"])
		# Luokka
		if word.isNoun() and word.form == "ulkoolento":
			tokens.next()
			tokens.setStyle("type")
			accept(["on"], tokens)
			tokens.setStyle("keyword")
			fields = parseList(parseFieldDecl, tokens)
			stmts = parseAdditionalStatements(tokens)
			eatPeriod(tokens)
			tokens.addNewline()
			return ClassDecl(word.baseform, fields, stmts)
		elif word.isNoun() or word.isAdjective():
			varname, typename, case = parseSelfVariable(tokens, ["omanto", "nimento"])
			current_class = typename
			# Perivä luokka
			if varname == "" and case == "nimento" and tokens.peek() and tokens.peek().token.lower() == "on":
				tokens.next()
				tokens.setStyle("keyword")
				if word.form != "nimento":
					syntaxError("class name not in the nominative case", tokens)
				checkEof(tokens)
				super_type = tokens.next().toWord(cls=NOUN,forms=["nimento"])
				if not super_type.isNoun() or super_type.form != "nimento":
					syntaxError("super type must be a noun in the nominative case", tokens)
				if tokens.peek() and tokens.peek().token == ",":
					tokens.next()
					accept(["jolla"], tokens)
					tokens.setStyle("keyword")
					accept(["on"], tokens)
					tokens.setStyle("keyword")
					fields = parseList(parseFieldDecl, tokens)
				else:
					fields = []
				stmts = parseAdditionalStatements(tokens)
				eatPeriod(tokens)
				tokens.addNewline()
				return ClassDecl(typename, fields, stmts, super_type=super_type.baseform)
			# Funktio
			elif case in ["omanto", "nimento"]:
				place = tokens.place()
				field, field_case, field_number, param, param_case = parseFieldName(tokens, word.form)
				if field in ARI_OPERATORS and ARI_OPERATORS[field][0] == param_case:
					tokens.setPlace(place)
					tokens.next()
					syntaxError("redefinition of builtin", tokens)
				if (field_case == "nimento" and field_number == "plural") or (field_case == "olento" and word.number == "plural"):
					accept(["ovat"], tokens)
				else:
					accept(["on"], tokens)
				tokens.setStyle("keyword")
				if tokens.peek().token.lower() == "pysyvästi":
					tokens.next()
					tokens.setStyle("keyword")
					memoize = True
				else:
					memoize = False
				body = parseNominativePredicative(tokens)
				wheres = parseWheres(tokens)
				stmts = parseAdditionalStatements(tokens)
				eatPeriod(tokens)
				tokens.addNewline()
				return FunctionDecl(typename, field, varname, param, param_case, body, wheres, memoize, stmts)
	tokens.next()
	syntaxError("malformed declaration", tokens)

def parseSelfVariable(tokens, forms=[]):
	word = tokens.next().toWord(cls=ADJ+NOUN,forms=forms)
	if word.isAdjective():
		tokens.setStyle("variable")
		_, typeword = parseVariable(tokens, word=word, case="")
		varname = word.baseform + "_" + typeword.baseform
	elif word.isNoun():
		typeword = word
		tokens.setStyle("type")
		varname = ""
	else:
		syntaxError("expected variable or type name", tokens)
	return varname, typeword.baseform, typeword.form

def parseVariable(tokens, word=None, case="nimento"):
	if not word:
		checkEof(tokens)
		word = tokens.next().toWord(cls=ADJ, forms=[case])
		if not word.isAdjective() or (case and word.form != case):
			syntaxError("this variable must begin with an adjective " + formToEnglish(case, article=False), tokens)
		tokens.setStyle("variable")
	checkEof(tokens)
	word2 = tokens.next().toWord(cls=NOUN, forms=[word.form])
	if not word2.isNoun() or (case and word2.form != case):
		syntaxError("this variable must end with a noun " + formToEnglish(case, article=False), tokens)
	if not word.agreesWith(word2):
		syntaxError("variable words do not agree", tokens)
	tokens.setStyle("type")
	return word, word2

# predikatiivi voi olla joko nominaalilauseke tai yksi substantiivi (=new-lauseke)
# nominatiivisen merkkijonon edessä ei tarvitse olla substantiivia
def parsePredicative(tokens):
	return parseNominalPhrase(tokens, promoted_cases=["nimento"], predicative=True)

def parseNominativePredicative(tokens, name="predicative"):
	value, case = parsePredicative(tokens)
	if case != "nimento":
		syntaxError(name + " is " + formToEnglish(case) + " (should be in the nominative case)")
	return value

INITIAL_VALUE_KEYWORDS = ["aluksi", "alussa", "yleensä"]

def parseFieldDecl(tokens):
	field_name = parseFieldName(tokens)
	if tokens.peek() and tokens.peek().token == "," and tokens.peek(2) and tokens.peek(2).token.lower() == ("jotka" if field_name[2] == "plural" else "joka"):
		tokens.next()
		tokens.next()
		tokens.setStyle("keyword")
		accept(["ovat" if field_name[2] == "plural" else "on"], tokens)
		tokens.setStyle("keyword")
		if eat(INITIAL_VALUE_KEYWORDS, tokens):
			tokens.setStyle("keyword")
		value = parseNominativePredicative(tokens)
		eatComma(tokens)
		return field_name + (value,)
	elif field_name[2] == "plural" and tokens.peek() and tokens.peek().token == "," and tokens.peek(2) and tokens.peek(2).token.lower() == "joita":
		tokens.next()
		tokens.next()
		tokens.setStyle("keyword")
		accept(["ovat"], tokens)
		tokens.setStyle("keyword")
		if eat(INITIAL_VALUE_KEYWORDS, tokens):
			tokens.setStyle("keyword")
		value = ListExpr(parseList(parseNominativePredicative, tokens))
		eatComma(tokens)
		return field_name + (value,)
	elif tokens.peek() and tokens.peek().token == "[":
		tokens.next()
		if eat(INITIAL_VALUE_KEYWORDS, tokens):
			tokens.setStyle("keyword")
		value = parseNominativePredicative(tokens)
		accept("]", tokens)
		return field_name + (value,)
	else:
		return field_name + (None,)

def parseFieldName(tokens, form="omanto"):
	expected_form = "nimento" if form == "omanto" else "olento"
	checkEof(tokens)
	word = tokens.next().toWord(cls=NOUN,forms=[expected_form,"superlative"])
	if word.form != expected_form:
		syntaxError("malformed member name, expected a noun " + formToEnglish(expected_form, article=False), tokens)
	tokens.setStyle("field")
	field = word.baseform
	# jäsennetään superlatiiviattribuutti
	if word.isAdjective() and word.comparison == "superlative":
		word2 = tokens.next().toWord(cls=NOUN,forms=[expected_form])
		if word2.form != expected_form:
			syntaxError("malformed member name, expected a noun " + formToEnglish(expected_form, article=False), tokens)
		if word2.number != word.number:
			syntaxError("malformed member name, the adjective and the noun do not agree in number", tokens)
		tokens.setStyle("field", continued=True)
		field += "_" + word2.baseform
		word = word2
	if word.form == "olento":
		field += "_E"
		# jäsennetään parametri
		if tokens.peek() and tokens.peek().toWord(cls=VERB).isAdjective():
			w1, w2 = parseVariable(tokens, case="")
			return field, word.form, word.number, w1.baseform + "_" + w2.baseform, w1.form
	return field, word.form, word.number, None, None

def parseWheres(tokens):
	token = tokens.peek()
	if token and token.token.lower() == "," and tokens.peek(2) and tokens.peek(2).token.lower() == "missä":
		tokens.next()
		tokens.next()
		tokens.setStyle("keyword")
		wheres = parseList(parseAssignment, tokens, do_format=True)
		eatComma(tokens)
	elif token and token.token.lower() == "missä":
		if tokens.current().token != ",":
			syntaxError("there must be a comma before \"missä\"", tokens)
		tokens.next()
		tokens.setStyle("keyword")
		wheres = parseList(parseAssignment, tokens, do_format=True)
		eatComma(tokens)
	else:
		wheres = []
	return wheres

def parseAdditionalStatements(tokens):
	ans = []
	with AllowBackreferences():
		while not tokens.eof() and tokens.peek().token == ";":
			tokens.next()
			ans += parseList(parseSentence, tokens, do_format=True)
	return ans

# takaisinviittauksien sallija

class AllowBackreferences:
	def __enter__(self):
		global allow_backreferences
		self.prev = allow_backreferences
		allow_backreferences = options["takaisinviittaukset"]
	def __exit__(self, *args):
		global allow_backreferences
		allow_backreferences = self.prev

allow_backreferences = False

# pino jokainen-lausekkeiden tallentamista varten (siis for-silmukoiden, vrt. rödan _)
FOR_STACK = []

ForVar = namedtuple("ForVar", ["name", "expr", "type"])

def pushFor(*allowed_types):
	FOR_STACK.append((allowed_types, []))

def addForVar(i_name, expr, var_type, tokens):
	if var_type == "mikään":
		var_type = "jokainen"
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

def parseSentence(tokens, signature=False):
	checkEof(tokens)
	token = tokens.peek()
	if not signature and token.token.lower() == "jos" or (token.token == "," and tokens.peek(2) and tokens.peek(2).token.lower() == "jos"):
		if token.token == ",":
			tokens.next()
		elif tokens.current().token != ",":
			syntaxError("there must be a comma before \"jos\"", tokens)
		tokens.next()
		tokens.setStyle("keyword")
		conditions = parseOuterCondition(tokens, False, ["niin"])
		if tokens.peek().token.lower() == "niin":
			tokens.next()
			tokens.setStyle("keyword")
		block = parseList(parseSentence, tokens, do_format=True)
		eatComma(tokens)
		return IfStatement(conditions, block)
	
	pushFor("jokainen")
	word = tokens.peek().toWord(
		cls=ADJ*2+NUMERAL*2+NAME*2+VERB,
		forms=["imperative_present_simple2", "indicative_present_simple4", "nimento", "osanto"])
	if word.isVerb():
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
		subject, case = parseNominalPhrase(tokens, promoted_cases=["nimento", "omanto"])
		if signature and not isinstance(subject, VariableExpr):
			syntaxError("malformed parameter", tokens)
		
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
			
			subject_case = "nimento" if word.form[-1] == "3" else case
			
			params = {}
			while not tokens.eof():
				peek = tokens.peek()
				if peek.token.lower() == "käyköön":
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
			
			for for_var in reversed(for_vars):
				stmt = ForStatement(for_var.name, for_var.expr, stmt)
			return stmt
		
		predicate, passive = parsePredicate(word, tokens, case)
		
		subjectless = False
		subject_case = case
	
	for_var_list = []
	args_list = []
	output_vars = []
	
	prev_args = {}
	while True:
		pushFor("jokainen")
		args, ov = parseArgs(tokens, passive, predicate=="olla_A", signature=signature)
		
		args_list.append({**prev_args, **args})
		prev_args = args
		
		output_vars.append(ov)
		
		for_var_list.append(for_vars+popFor())
		
		if not signature and not tokens.eof() and tokens.peek().token.lower() == "sekä":
			tokens.next()
			tokens.setStyle("keyword")
			continue
		else:
			break
	
	if len(args_list) == 1:
		async_block = parseAsyncBlock(tokens)
	else:
		async_block = []
	
	eatComma(tokens)
	
	wheres = parseWheres(tokens)
	
	stmts = []
	
	for args, output_var, for_vars in zip(args_list, output_vars, for_var_list):
		if subjectless:
			stmt = ProcedureCallStatement(predicate, args, output_var, async_block)
		else:
			stmt = MethodCallStatement(subject, subject_case, predicate, args, output_var, async_block)
		
		for for_var in reversed(for_vars):
			stmt = ForStatement(for_var.name, for_var.expr, stmt)
		
		stmts.append(stmt)
	
	if len(stmts) == 1 and len(wheres) == 0:
		return stmts[0]
	else:
		return BlockStatement(stmts, wheres)

def parsePredicate(word, tokens, subject_case):
	if not word.isVerb() or word.form not in ["indicative_present_simple3", "indicative_present_simple4"]:
		syntaxError("predicate is not in indicative simple present 3rd active or passive", tokens)
	tokens.setStyle("function")
	
	passive = word.form[-1] == "4"
	predicate = word.baseform + readVerbModifiers(tokens, word.baseform=="olla") + ("_P" if passive else "_A")
	
	return predicate, passive

def nextIsValidVerbModifier(tokens, allow_adverbs=True, allow_verbs=True, disallow_nominative_noun=False):
	token = tokens.peek()
	if not token or not token.isWord():
		return False
	word = token.toWord(cls=NOMINAL_PHRASE_CLASS)
	return ((word.isNoun()
		and (not disallow_nominative_noun or word.form != "nimento")
		and not canStartNominalPhrase(word, tokens)
		and word.form != "olento")
		or (allow_adverbs and word.isAdverb())
		or (allow_verbs and word.isVerb() and "E-infinitive" not in word.form and "infinitive" in word.form))

def readVerbModifiers(tokens, is_be_verb=False):
	ans = ""
	while not tokens.eof():
		if nextIsValidVerbModifier(tokens, disallow_nominative_noun=is_be_verb):
			token = tokens.next()
			tokens.setStyle("function", continued=True)
			ans += "_" + token.token.lower()
		else:
			break
	return ans

def parseArgs(tokens, passive, allow_predicatives, signature=False, allow_return_var=True):
	args = {}
	while not tokens.eof():
		if tokens.peek().token.lower() in [",", ";", ".", "]", "eikä", "ja", "sekä", "tai", "taikka", "tuloksenaan"]:
			break
		arg, case = parsePredicative(tokens) if allow_predicatives else parseNominalPhrase(tokens)
		if signature and not isinstance(arg, VariableExpr):
			syntaxError("malformed parameter", tokens)
		if case in args:
			syntaxError(formToEnglish(case, short=True) + " argument repeated twice", tokens)
		args[case] = arg
		if isinstance(arg, LambdaExpr): # että-lohkot ovat lauseissa aina viimeisenä
			break
	if (allow_return_var and not tokens.eof() and (
			(tokens.peek().token.lower() == "tuloksenaan" and not passive)
			or (tokens.peek().token.lower() == "tuloksena" and passive)
			)):
		tokens.next()
		tokens.setStyle("keyword")
		w1, w2 = parseVariable(tokens)
		return args, (w1.baseform + "_" + w2.baseform, w2.baseform)
	else:
		return args, None

def parseAsyncBlock(tokens):
	ans = []
	last = False
	while not last and tokens.peek() and tokens.peek().token.lower() in [",", "ja"] and tokens.peek(2) and tokens.peek(2).token.lower() == "minkä":
		if tokens.next().token.lower() == "ja":
			tokens.setStyle("keyword")
			last = True
		place = tokens.place()
		tokens.next() # minkä
		tokens.setStyle("keyword")
		method_name = "a_" + tokens.next().token.lower()
		tokens.setStyle("field")
		w1, w2 = parseVariable(tokens, case="")
		parameter = w1.baseform + "_" + w2.baseform
		word = tokens.next().toWord(cls=VERB,forms=["indicative_present_simple3", "indicative_present_simple4"])
		predicate, passive = parsePredicate(word, tokens, w1.form)
		args, ov = parseArgs(tokens, passive, predicate=="olla_A")
		eatComma(tokens)
		ans.append((method_name, parameter, w2.baseform, MethodCallStatement(VariableExpr(parameter, w2.baseform), w1.form, predicate, args, ov, [])))
	if len(ans) > 1 and not last:
		tokens.setPlace(place)
		syntaxError("the last sentence in this list must be separated from the others by \"ja\"", tokens)
	return ans

CMP_OPERATORS = {
	"yhtä suuri kuin": "==",
	"yhtäsuuri kuin": "==",
	"yhtä kuin": "==",
	"tasan": "==",
	"sama kuin": "===",
	"erisuuri kuin": "!=",
	"pienempi kuin": "<",
	"pienempi tai yhtä suuri kuin": "<=",
	"pienempi tai yhtäsuuri kuin": "<=",
	"enintään": "<=",
	"suurempi kuin": ">",
	"suurempi tai yhtä suuri kuin": ">=",
	"suurempi tai yhtäsuuri kuin": ">=",
	"vähintään": ">="
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

def parseOuterCondition(tokens, prefix=False, end_keyword=[], do_format=False):
	if do_format:
		tokens.increaseIndentLevel()
	expr = parseInnerCondition(tokens, prefix, end_keyword)
	while tokens.peek().token.lower() in ["sekä", "taikka"]:
		if do_format:
			tokens.addNewline()
		op = "&&" if tokens.next().token.lower() == "sekä" else "||"
		tokens.setStyle("keyword")
		expr = CondConjunctionExpr(op, [expr, parseInnerCondition(tokens, prefix, end_keyword)])
	if do_format:
		tokens.decreaseIndentLevel()
	expr.wheres = parseWheres(tokens)
	eatComma(tokens)
	return expr

def parseInnerCondition(tokens, prefix, custom_endings):
	conds, op = parseList(lambda t: parseCondition(t, prefix), tokens, custom_endings+["sekä", "taikka"], custom_conjunctions=["ja", "tai"])
	if len(conds) == 1:
		return conds[0]
	else:
		return CondConjunctionExpr("&&" if op == "ja" else "||", conds)

def parseCondition(tokens, prefix=False):
	pushFor("jokainen", "jokin")
	predicate = None
	verbIsOlla = None
	if prefix:
		checkEof(tokens)
		if tokens.peek().token.lower() == "eikö":
			tokens.next()
			tokens.setStyle("keyword")
			negation = True
		else:
			predicate, verbIsOlla = parseConditionPredicate(tokens, True, False)
			negation = False
	operand1, self_case = parseNominalPhrase(tokens, promoted_cases=["nimento"])
	expr = parseConditionPredicateAndArgs(tokens, operand1, self_case, predicate=predicate, verbIsOlla=verbIsOlla, prefix=prefix, negation=prefix and negation)
	for_vars = popFor()
	for for_var in reversed(for_vars):
		expr = QuantifierCondExpr(for_var.type, for_var.name, for_var.expr, expr)
	return expr

def parseConditionPredicateAndArgs(tokens, operand1, self_case, predicate=None, verbIsOlla=None, prefix=False, negation=False, allow_negation=True):
	if not prefix:
		checkEof(tokens)
		if allow_negation and tokens.peek().token.lower() == "ei":
			tokens.next()
			tokens.setStyle("keyword")
			predicate, verbIsOlla = parseConditionPredicate(tokens, False, True)
			negation = True
		else:
			predicate, verbIsOlla = parseConditionPredicate(tokens, False, False)
			negation = False
	elif negation:
		predicate, verbIsOlla = parseConditionPredicate(tokens, True, True)
		tokens.setStyle("keyword")
	args = []
	if verbIsOlla:
		operator, requires_second_operand = parseOperator(tokens)
		if requires_second_operand:
			operand2, case = parseNominalPhrase(tokens, promoted_cases=[self_case])
			if case != self_case:
				syntaxError("predicative is in " +formToEnglish(case) + " (should be in " +formToEnglish(self_case)+ ")", tokens)
		else:
			operand2 = None
		return CondOperatorExpr(negation, operator, operand1, operand2)
	else:
		args, _ = parseArgs(tokens, False, False, allow_return_var=False)
		return CondFunctionExpr(negation, predicate, operand1, args)

def parseConditionPredicate(tokens, prefix, negative):
	verb = tokens.next().toWord(cls=VERB,forms=["indicative_present_simple3", "indicative_present_simple4"])
	if not negative:
		if prefix and not verb.interrogative:
			syntaxError("predicate does not contain the interrogative suffix \"-ko\"", tokens)
		if verb.form not in ["indicative_present_simple3", "indicative_present_simple4"]:
			syntaxError("predicative is not in indicative simple present 3rd person active or passive", tokens)
	else:
		if verb.form != "imperative_present_simple2":
			syntaxError("predicative is not in negative form (imperative)", tokens)
	passive = verb.form[-1] == "4"
	verbIsOlla = verb.baseform == "olla"
	predicate = verb.baseform
	if verbIsOlla:
		tokens.setStyle("keyword")
	else:
		tokens.setStyle("conditional-operator")
		predicate += readVerbModifiers(tokens)
	predicate += "_P" if passive else "_A"
	return predicate, verbIsOlla

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
	elif (tokens.peek().isWord()
		and tokens.peek(2)
		and tokens.peek().toWord(cls=ADJ).isAdjective()
		and (not tokens.peek(2).isWord() or not tokens.peek(2).toWord(cls=NOUN).isNoun())):
		word = tokens.next().toWord(cls=ADJ)
		tokens.setStyle("conditional-operator")
		if word.form != "nimento":
			syntaxError("expected an adjective in the nominative case", tokens)
		if word.comparison == "comparative":
			accept(["kuin"], tokens)
			tokens.setStyle("keyword")
			return ".c_" + word.baseform, True
		else:
			return ".p_" + word.baseform, False
	elif tokens.peek().isWord() and not nextStartsNominalPhrase(tokens):
		word = tokens.next().token.lower()
		tokens.setStyle("conditional-operator")
		return ".p_" + word, False
	else:
		return "==", True

NOMINAL_PHRASE_CLASS = 2*ADJ+2*NUMERAL+2*CONJ+2*PRONOUN+NOUN

def nextStartsNominalPhrase(tokens):
	if tokens.eof():
		return False
	peek = tokens.peek()
	if not peek.isWord():
		return False
	word = peek.toWord(cls=NOMINAL_PHRASE_CLASS)
	return canStartNominalPhrase(word, tokens)

def canStartNominalPhrase(word, tokens):
	return ((word.isAdjective()
			and tokens.peek(2) and tokens.peek(2).isWord()
			and tokens.peek(2).toWord(cls=NOUN).isNoun() and tokens.peek(2).toWord(cls=NOUN,forms=word.form).agreesWith(word))
		or word.isPronoun()
		or word.isVariable()
		or word.isOrdinal()
		or word.isCardinal()
		or re.fullmatch(r'\d+', word.baseform)
		or (word.isNoun() and tokens.peek(2) and tokens.peek(2).isString())
		or (word.isNoun() and tokens.peek(2) and tokens.peek(2).token == "," and tokens.peek(3) and tokens.peek(3).token.lower() == "jonka")
		or word.word.lower() == "riippuen")

def parseNominalPhrase(tokens, must_be_in_genitive=False, promoted_cases=[], predicative=False):
	checkEof(tokens)
	if tokens.peek().token.lower() == "riippuen":
		accept(["riippuen"], tokens)
		tokens.setStyle("keyword")
		accept(["siitä"], tokens)
		tokens.setStyle("keyword")
		accept([","], tokens)
		conds = parseOuterCondition(tokens, True, ["joko"])
		if tokens.peek().token.lower() == "joko":
			tokens.next()
			tokens.setStyle("keyword")
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
	if predicative and tokens.peek().isString():
		expr = StrExpr(parseString(tokens.next().token))
		tokens.setStyle("literal")
		case = "nimento"
	else:
		expr = None
		case = None
		word = tokens.next().toWord(cls=ADJ+NAME+NUMERAL+PRONOUN,forms=promoted_cases)
	if expr:
		pass
	elif word.isVariable():
		tokens.setStyle("variable")
		expr = VariableExpr(word.baseform)
		case = word.form
	elif word.isNoun() and word.possessive == "" and word.form == "olento" and word.word != "tuloksena":
		tokens.setStyle("field")
		expr, case = parseNominalPhrase(tokens)
	elif word.baseform in ["jokainen", "jokin", "mikään"]:
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
		if word.form in ["nimento", "osanto"] and nextIsValidVerbModifier(tokens, allow_adverbs=False, allow_verbs=False):
			word2 = tokens.next().toWord(cls=NOUN)
			tokens.setStyle("keyword")
			if word.form == "nimento":
				case = word2.form if word2.form != "osanto" else "nimento"
			elif word.form == "osanto" and word2.form == "osanto":
				case = "osanto"
			else:
				syntaxError("the unit should be in the partitive case", tokens)
		else:
			case = word.form
		expr = NumExpr(int(word.baseform))
	elif word.isNoun() and tokens.peek() and tokens.peek().isString():
		tokens.setStyle("keyword")
		case = word.form
		expr = StrExpr(parseString(tokens.next().token))
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
			with AllowBackreferences():
				body = parseList(parseSentence, tokens, do_format=True)
			eatComma(tokens)
			case = word.form
			expr = LambdaExpr(body)
		elif (allow_backreferences and
			nextIsValidVerbModifier(tokens, allow_adverbs=False, allow_verbs=False)
			and tokens.peek().toWord(cls=NOUN,forms=word.form).agreesWith(word)): # takaisinviittaus edelliseen lausekkeeseen esim. "se olio"
			tokens.setStyle("variable")
			word2 = tokens.next().toWord(cls=NOUN,forms=word.form)
			if word2.form == "omanto":
				tokens.setStyle("variable-or-field")
				case = "omanto"
				expr = BackreferenceExpr(word2.baseform, may_be_field=True)
			else:
				tokens.setStyle("variable", continued=True)
				case = word.form
				expr = BackreferenceExpr(word2.baseform)
		else:
			tokens.setStyle("variable")
			if tokens.peek() and tokens.peek().isWord():
				word2 = tokens.peek().toWord(cls=PRONOUN)
				if word2.baseform == "itse" and word2.agreesWith(word):
					tokens.next()
					tokens.setStyle("variable", continued=True)
			case = word.form
			expr = VariableExpr("this", vtype=current_class)
	elif word.baseform == "siellä":
		tokens.setStyle("variable")
		if word.word.lower() == "siellä":
			case = "sisaolento"
		elif word.word.lower() == "sinne":
			case = "sisatulento"
		elif word.word.lower() == "sieltä":
			case = "sisaeronto"
		else:
			syntaxError("unexpected word", tokens)
		# takaisinviittaus
		if (nextIsValidVerbModifier(tokens, allow_adverbs=False, allow_verbs=False)
			and tokens.peek().toWord(cls=NOUN,forms=word.form).agreesWith(word)):
			word2 = tokens.next().toWord(cls=NOUN,forms=word.form)
			tokens.setStyle("variable", continued=True)
			expr = BackreferenceExpr(word2.baseform)
		else:
			if tokens.peek() and tokens.peek().isWord():
				word2 = tokens.peek().toWord(cls=PRONOUN)
				if word2.baseform == "itse" and word2.agreesWith(word):
					tokens.next()
					tokens.setStyle("variable", continued=True)
			expr = VariableExpr("this", vtype=current_class)
	elif ((word.isAdjective() and word.baseform == "uusi")
		or (word.isAdjective() and tokens.peek() and tokens.peek().toWord(cls=NOUN,forms=[word.form]).agreesWith(word, baseform="uusi"))
		or (word.isNoun() and tokens.peek(1) and tokens.peek(1).token == "," and tokens.peek(2).token.lower() == "jonka")
		):
		# uusi-lausekkeen yhteydessä voidaan luoda uusi muuttuja ylimääräisen adjektiivin avulla, esim. "kiva uusi tyyppi" tai "uusi kiva tyyppi"
		varname = None
		if word.baseform == "uusi":
			tokens.setStyle("keyword")
			checkEof(tokens)
			
			word2 = tokens.next().toWord(cls=NOUN,forms=[word.form])
			if word2.isAdjective():
				if not word.agreesWith(word2):
					syntaxError("the adjectives of a constructor call must be in the same case", tokens)
				tokens.setStyle("variable")
				varname = word2.baseform
				word2 = tokens.next().toWord(cls=NOUN,forms=[word.form])
			
			if not word2.isNoun():
				syntaxError("type must be a noun", tokens)
			if not word.agreesWith(word2):
				syntaxError("the adjective and the noun of a constructor call must be in the same case", tokens)
		elif word.isAdjective():
			tokens.setStyle("variable")
			varname = word.baseform
			word2 = tokens.next().toWord(cls=ADJ,forms=[word.form])
			if word2.baseform != "uusi":
				syntaxError("unexpected token, expected \"uusi\"", tokens)
			if not word.agreesWith(word2):
				syntaxError("the adjectives of a constructor call must be in the same case", tokens)
			tokens.setStyle("keyword")
			word2 = tokens.next().toWord(cls=NOUN,forms=[word.form])
			if not word2.isNoun():
				syntaxError("type must be a noun", tokens)
			if not word.agreesWith(word2):
				syntaxError("the adjective and the noun of a constructor call must be in the same case", tokens)
		else:
			word2 = word
		
		tokens.setStyle("type")
		
		if varname:
			varname += "_" + word2.baseform
		
		case = word.form
		if tokens.peek(1) and tokens.peek(2) and tokens.peek(1).token == "," and tokens.peek(2).token.lower() == "jonka":
			tokens.next()
			tokens.next()
			tokens.setStyle("keyword")
			
			args = parseList(parseCtorArg, tokens)
			
			eatComma(tokens)
		else:
			args = []
		expr = NewExpr(word2.baseform, args, variable=varname)
	elif predicative and word.isNoun():
		tokens.setStyle("type")
		expr = NewExpr(word.baseform, [])
		case = word.form
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
		if not word.agreesWith(word2):
			syntaxError("the adjective and the noun of a variable must be in the same case", tokens)
		
		tokens.setStyle("type")
		case = word.form
		variable = word.baseform + "_" + word2.baseform
		
		if tokens.peek() and tokens.peek().isWord() and tokens.peek().toWord().agreesWith(word, baseform="itse"):
			tokens.next()
			tokens.setStyle("keyword")
		
		# muuttujan luominen ensimmäisen viittauksen yhteydessä: "kiva luku, joka on nätin luvun neliöjuuri"
		if tokens.peek() and tokens.peek().token in [",", "["] and tokens.peek(2) and tokens.peek(2).token.lower() == "joka":
			start_token = tokens.next().token
			tokens.next()
			tokens.setStyle("keyword")
			if word.number == "plural":
				accept(["ovat"], tokens)
			else:
				accept(["on"], tokens)
			if tokens.peek() and tokens.peek().token.lower() in INITIAL_VALUE_KEYWORDS:
				tokens.next()
				tokens.setStyle("keyword")
			val_expr = parseNominativePredicative(tokens)
			if start_token == ",":
				eatComma(tokens)
			else:
				accept(["]"], tokens)
			expr = VariableExpr(variable, word2.baseform, initial_value=val_expr, place=place)
		else:
			expr = VariableExpr(variable, word2.baseform, place=place)
	
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
					index = VariableExpr(word.baseform, "luku")
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
			if not token.isWord() or token.token.lower() in POSTPOSITIONS["omanto"]:
				break
			word = token.toWord(cls=2*NOUN+2*NUMERAL+PRONOUN, forms=["omanto", "E-infinitive_sisaolento", "E-infinitive_sisaolento"]+4*["superlative"])
			if must_be_in_genitive and word.form != "omanto":
				break
			peek2 = tokens.peek(2)
			if word.baseform in ["jokainen", "jokin", "mikään"] and peek2 and peek2.toWord(cls=NOUN, forms=[word.form]).isNoun():
				tokens.next()
				tokens.setStyle("keyword")
				checkEof(tokens)
				word2 = tokens.next().toWord(cls=NOUN, forms=[word.form])
				if not word2.isNoun() or not word2.agreesWith(word):
					syntaxError("expected a noun " + formToEnglish(word.form, article=False), tokens)
				tokens.setStyle("field")
				case = word.form
				field = word2.baseform
				field_expr = FieldExpr(expr, field, place=tokens.place())
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
					index = VariableExpr(word.baseform, "luku")
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
				expr = SubscriptExpr(FieldExpr(expr, field, place=tokens.place()), index, end_index)
				cont = True
			elif word.isNoun() and word.possessive == "":
				tokens.next()
				tokens.setStyle("field")
				case = word.form
				field = word.baseform
				
				expr = FieldExpr(expr, field, place=tokens.place())
				cont = True
			elif word.isAdjective() and word.comparison == "superlative":
				tokens.next()
				tokens.setStyle("field")
				
				word2 = tokens.next().toWord(cls=NOUN,forms=[word.form])
				if not word.agreesWith(word2):
					syntaxError("malformed member name, the adjective and the noun do not agree", tokens)
				tokens.setStyle("field", continued=True)
				
				case = word.form
				field = word.baseform + "_" + word2.baseform
				
				expr = FieldExpr(expr, field, place=tokens.place())
				cont = True
			else:
				break
		
		# essiiviketju
		# esim. <lauseke> kerrottuna <lausekkeella> ja <toisella>
		# esim. <luku> pyöristettynä ja merkkijonona
		
		require_ja = False
		chain_end = False
		while not tokens.eof() and tokens.peek().isWord():
			word = tokens.peek().toWord(cls=NOUN, forms="olento")
			if word.isNoun() and word.form == "olento" and word.possessive == "" and word.word != "tuloksena":
				tokens.next()
				tokens.setStyle("operator")
				expr = FieldExpr(expr, word.baseform + "_E", place=tokens.place())
				cont = True
			elif word.isAdjective() and word.form == "olento":
				tokens.next()
				tokens.setStyle("operator")
				place = tokens.place()
				if nextStartsNominalPhrase(tokens) and tokens.peek().toWord(cls=NOUN).form != "olento":
					arg, arg_case = parseNominalPhrase(tokens)
					expr = FieldExpr(expr, word.baseform + "_E", arg_case, arg, place=place)
				else:
					expr = FieldExpr(expr, word.baseform + "_E", place=place)
				cont = True
			else:
				break
			if chain_end:
				break
			peek1 = tokens.peek(1)
			peek2 = tokens.peek(2)
			word2 = peek2.toWord(cls=NOUN, forms="olento") if peek2 and peek2.isWord() else None
			if (peek1 and peek2 and peek1.token.lower() in [",", "ja"]
				and (peek2.isWord() and (word2.isNoun() or word2.isAdjective()) and word2.form == "olento")):
				if tokens.next().token == ",":
					require_ja = True
				else: # ja
					require_ja = False
					chain_end = True
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
	elif case == "omanto" and tokens.peek().isWord() and isPartitiveIntransitiveParticiple(tokens.peek().toWord(cls=ADJ,forms=["osanto"])):
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
		vtype = "luku"
	else:
		word, word2 = parseVariable(tokens)
		var = word.baseform + "_" + word2.baseform
		vtype = word2.baseform
	accept(["on", "ovat"], tokens)
	tokens.setStyle("keyword")
	value, case = parseNominalPhrase(tokens, promoted_cases=["nimento"])
	if case != "nimento":
		syntaxError("contructor argument value is not in nominative case", tokens)
	return (var, vtype, value)

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
		value = parseNominativePredicative(tokens, name="constructor argument value")
		return CtorArgExpr(word.baseform, value)
	else: # partitiivi, ovat (esim. alkioita ovat x ja y)
		values_cases = parseList(parseNominalPhrase, tokens)
		values = []
		for value, case in values_cases:
			values += [value]
			if case != "nimento":
				syntaxError("contructor argument value is not in nominative case", tokens)
		return CtorArgExpr(word.baseform, ListExpr(values))

def parseString(string):
	return string[1:-1].replace("\\l", "\"").replace("\\u", "\n").replace("\\s", "\t").replace("\\\\", "\\")

def parseList(parseChild, tokens, custom_endings=[], do_format=False, custom_conjunctions=[]):
	if do_format:
		tokens.increaseIndentLevel()
	ans = []
	force = False
	checkEof(tokens)
	peek = tokens.peek().token.lower()
	while (force or peek not in [";", ".", "]", "ja", "eikä"]+custom_conjunctions) and peek not in custom_endings:
		if do_format and len(ans) > 0:
			tokens.addNewline()
		ans += [parseChild(tokens)]
		if not tokens.eof() and tokens.peek().token == ",":
			tokens.next()
			force = True
		else:
			force = False
		checkEof(tokens)
		peek = tokens.peek().token.lower()
	if len(ans) == 1 and tokens.peek().token in [".", ";", "]"]:
		if do_format:
			tokens.decreaseIndentLevel()
		if custom_conjunctions:
			return ans, custom_conjunctions[0]
		else:
			return ans
	if do_format:
		tokens.addNewline()
	
	ending = tokens.peek().token.lower()
	if ending not in custom_endings:
		tokens.next()
		tokens.setStyle("keyword")
		if ending == "eikä":
			accept(["muuta"], tokens)
			tokens.setStyle("keyword")
		elif custom_conjunctions and ending in custom_conjunctions:
			ans += [parseChild(tokens)]
		elif ending == "ja":
			ans += [parseChild(tokens)]
		else:
			syntaxError("unexpected token, expected " + ", ".join(["\""+t+"\"" for t in custom_endings+["ja"]]) + " or \"eikä\"", tokens)
	
	if do_format:
		tokens.decreaseIndentLevel()
	
	# jos annettiin vaihtoehtoisia konjunktioita, palautetaan mitä niistä käytettiin
	if custom_conjunctions:
		return ans, ending
	else:
		return ans
