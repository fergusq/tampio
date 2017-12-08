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

import traceback
from voikko.libvoikko import Voikko, Token
from inflect import *
from fatal_error import fatalError, StopEvaluation

LANGUAGE = "fi-x-morpho"
ENCODING = "UTF-8"

voikko = Voikko(LANGUAGE)

def lexCode(code):
	output = []
	for word in re.split("(\\s|\\.|,)", code):
		if word == "":
			continue
		if re.fullmatch("\\s+|\\.|,", word):
			output += [Punctuation(word)]
			continue
		
		cont = False
		for number in CASE_REGEXES:
			for case in CASE_REGEXES[number]:
				if re.fullmatch(CASE_REGEXES[number][case], word):
					output += [AltWords(word, [Word(word, word[:word.index(":")], case, number, "nimisana")])]
					cont = True
		if cont:
			continue
		
		analysis_list = voikko.analyze(word)
		alternatives = []
		for analysis in analysis_list:
			bf = analysis["BASEFORM"]
			cl = analysis["CLASS"]
			if "SIJAMUOTO" in analysis:
				form = analysis["SIJAMUOTO"]
			elif "MOOD" in analysis and "TENSE" in analysis:
				form = analysis["MOOD"] + "_" + analysis["TENSE"]
			else:
				form = ""
			number = analysis["NUMBER"] if "NUMBER" in analysis else ""
			person = analysis["PERSON"] if "PERSON" in analysis else ""
			alternatives += [Word(word, bf, form + person, number, cl)]
		if len(alternatives) == 0:
			alternatives = [Word(word, word, "", "", "")]
		output += [AltWords(word, alternatives)]
	return TokenList(output)

class TokenList:
	def __init__(self, tokens):
		self.tokens = tokens
		self.styles = [""]*len(tokens)
		self.i = -1
		
		for token in tokens:
			token.tokens = self
	def peek(self, n=1):
		j = self.i+1
		while j < len(self.tokens):
			if self.tokens[j].isWord() or not self.tokens[j].isSpace():
				n -= 1
				if n == 0:
					return self.tokens[j]
			j += 1
		return None
	def next(self):
		while self.i < len(self.tokens):
			self.i += 1
			if self.tokens[self.i].isWord() or not self.tokens[self.i].isSpace():
				return self.tokens[self.i]
		return None
	def eof(self):
		return not self.peek()
	def setStyle(self, style):
		self.styles[self.i] = style
	def prettyPrint(self):
		out = ""
		for token, style in zip(self.tokens, self.styles):
			if style != "":
				out += "<span class=\"" + style + "\">" + token.token + "</span>"
			else:
				out += token.token
		return out
	def context(self):
		a = max(0, self.i-10)
		b = min(len(self.tokens), self.i+10)
		out = ""
		for i in range(a, b):
			if i == self.i:
				out += "<here>"
			out += self.tokens[i].token
		return out

def eat(tokens, token):
	if not tokens.eof() and tokens.peek().token.lower() == token:
		tokens.next()

eatComma = lambda tokens: eat(tokens, ",")
eatPeriod = lambda tokens: eat(tokens, ".")

def checkEof(tokens):
	if tokens.eof():
		fatalError("Syntax error: unexpected eof (in \""+tokens.context()+"\")")

def accept(accepted, tokens):
	if tokens.next().token.lower() not in accepted:
		fatalError("Syntax error: unexpected token, expected " + " or ".join(["\"" + t + "\"" for t in accepted]) + " (in \"" + tokens.context() + "\")")

CARDINALS = ["nolla", "yksi", "kaksi", "kolme", "neljä", "viisi", "kuusi", "seitsemän", "kahdeksan", "yhdeksän", "kymmenen"]
ORDINALS = ["ensimmäinen", "toinen", "kolmas", "neljäs", "viides", "kuudes", "seitsemäs", "kahdeksas", "yhdeksäs", "kymmenes"]

class Punctuation:
	def __init__(self, token):
		self.token = token
		self.tokens = None
	def isWord(self):
		return False
	def isSpace(self):
		return not not re.fullmatch("\\s*", self.token)
	def toWord(self, cls=[], forms=[], numbers=[]):
		fatalError("Syntax error: unexpected token, expected a word (in \"" + self.tokens.context() + "\")")
	def __str__(self):
		return self.token
	def __repr__(self):
		return "Punctuation{" + self.token + "}"

class AltWords:
	def __init__(self, token, alternatives):
		self.token = token
		self.alternatives = alternatives
		self.tokens = None
	def isWord(self):
		return True
	def toWord(self, cls=[], forms=[], numbers=[]):
		def score(w):
			return cls.count(w.word_class) + forms.count(w.form) + numbers.count(w.number)
		return sorted(self.alternatives, key=score)[-1]
	def __str__(self):
		return self.token
	def __repr__(self):
		return "AltWord{" + self.token + "}"
				
ADJ = ["laatusana", "nimisana_laatusana"]
NOUN = ["nimisana"]
NAME = ["etunimi", "sukunimi"]
PRONOUN = ["asemosana"]
NUMERAL = ["lukusana"]
VERB = ["teonsana", "kieltosana"]
CONJ = ["sidesana"]

class Word:
	def __init__(self, word, baseform, form, number, word_class):
		#print(word, baseform, form, number, word_class)
		self.word = word
		self.baseform = baseform
		self.form = form
		self.number = number
		self.word_class = word_class
	def isNoun(self):
		return self.word_class in ["nimisana"]
	def isName(self):
		return self.word_class in ["etunimi", "sukunimi"]
	def isPronoun(self):
		return self.word_class in ["asemosana"]
	def isAdjective(self):
		return self.word_class in ["laatusana", "nimisana_laatusana"]
	def isOrdinal(self):
		return self.baseform in ORDINALS
	def isCardinal(self):
		return self.baseform in CARDINALS
	def isVerb(self):
		return self.word_class in ["teonsana", "kieltosana"]
	def isConjunction(self):
		return self.word_class in ["sidesana"]

def parseDeclaration(tokens):
	checkEof(tokens)
	token = tokens.peek()
	if token.token.lower() == "kun":
		tokens.next()
		tokens.setStyle("keyword")
		signature = parseSentence(tokens)
		body = parseList(parseSentence, tokens)
		eatPeriod(tokens)
		return ProcedureDecl(signature, body)
	elif token.token.lower() == "olkoon":
		tokens.next()
		tokens.setStyle("keyword")
		word1, word2 = parseVariable(tokens, case="nimento")
		value, case = parseNominalPhrase(tokens, promoted_cases=["nimento"])
		if case != "nimento":
			fatalError("Syntax error: predicative is in "+CASES_ENGLISH[case]+" case (should be in nominative case) (in \"" + tokens.context() + "\")")
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
			return ClassDecl(word.baseform, fields)
		elif word.isAdjective() and word.form == "omanto":
			tokens.next()
			tokens.setStyle("variable")
			_, word2 = parseVariable(tokens, word=word, case="omanto")
			field, _ = parseFieldName(tokens)
			accept(["on", "ovat"], tokens)
			tokens.setStyle("keyword")
			body, case = parseNominalPhrase(tokens, promoted_cases=["nimento"])
			if case != "nimento":
				fatalError("Syntax error: predicative is in "+CASES_ENGLISH[case]+" case (should be in nominative case) (in \"" + tokens.context() + "\")")
			return FunctionDecl(word2.baseform, field, word.baseform + "_" + word2.baseform, body)

def parseVariable(tokens, word=None, case="nimento"):
	if not word:
		checkEof(tokens)
		word = tokens.next().toWord(cls=ADJ, forms=[case])
		if not word.isAdjective() or word.form != case:
			fatalError("Syntax error: this variable must begin with an adjective in "+CASES_ENGLISH[case]+" case (in \""+tokens.context()+"\")")
		tokens.setStyle("variable")
	checkEof(tokens)
	word2 = tokens.next().toWord(cls=NOUN, forms=[case])
	if not word2.isNoun() or word2.form != case:
		fatalError("Syntax error: this variable must end with a noun in "+CASES_ENGLISH[case]+" case (in \""+tokens.context()+"\")")
	tokens.setStyle("type")
	return word, word2

def parseFieldName(tokens):
	word = tokens.next().toWord(cls=NOUN,forms=["nimento"])
	if word.form != "nimento":
		fatalError("Syntax error: malformed member name, expected nominative noun (in \""+tokens.context()+"\"")
	tokens.setStyle("field")
	return word.baseform, word.number

def parseSentence(tokens):
	args = {}
	checkEof(tokens)
	token = tokens.peek()
	if token.token.lower() == "jos" or (token.token == "," and tokens.peek(2) and tokens.peek(2).token.lower() == "jos"):
		if token.token == ",":
			tokens.next()
		tokens.next()
		tokens.setStyle("keyword")
		conditions = parseList(parseCondition, tokens, ["niin"])
		block = parseList(parseSentence, tokens)
		eatComma(tokens)
		return IfStatement(conditions, block)
	word = tokens.peek().toWord(
		cls=ADJ+NUMERAL+NAME+VERB,
		forms=["imperative_present_simple2", "indicative_present_simple4", "nimento", "osanto"])
	if word.isAdjective() or word.isOrdinal() or word.isName():
		subject, case = parseNominalPhrase(tokens, promoted_cases=["nimento", "osanto"])
		if case not in ["nimento", "osanto"]:
			fatalError("Syntax error: subject is not in nominative / passive argument is not in nominative or partitive: " + str(subject) + " (in \""+tokens.context()+"\")")
		
		word = tokens.next().toWord(
			cls=VERB,
			forms=["indicative_present_simple3", "indicative_present_simple4"])
		tokens.setStyle("function")
		
		if not word.isVerb() or word.form not in ["indicative_present_simple3", "indicative_present_simple4"]:
			fatalError("Syntax error: predicate is not in indicative simple present (in \""+tokens.context()+"\")")
		predicate = word.baseform
		subjectless = word.form[-1] == "4"
		
		if case == "osanto" and not subjectless:
			fatalError("Syntax error: subject may be in partitive only if predicate is passive (in \""+tokens.context()+"\")")
		
		if subjectless:
			args[case] = subject
	elif word.isVerb():
		tokens.next()
		tokens.setStyle("function")
		subjectless = True
		if word.form == "imperative_present_simple2":
			predicate = word.baseform + "!"
		elif word.form == "indicative_present_simple4":
			predicate = word.baseform
		else:
			fatalError("Syntax error: predicate ("+word.word+") is not in indicative or imperative simple present (in \""+tokens.context()+"\")")
	else:
		fatalError("Syntax error: malformed sentence (in \""+tokens.context()+"\")")
	
	while not tokens.eof():
		if tokens.peek().token.lower() in [",", ".", "eikä", "ja"]:
			break
		arg, case = parseNominalPhrase(tokens)
		if case in args:
			fatalError("Syntax error: " + CASES_ENGLISH[case] + " argument repeated twice (in \""+tokens.context()+"\")")
		args[case] = arg
	
	eatComma(tokens)
	
	token = tokens.peek()
	if token and token.token.lower() == "missä":
		tokens.next()
		tokens.setStyle("keyword")
		wheres = parseList(parseAssignment, tokens)
		eatComma(tokens)
	else:
		wheres = []
	
	if subjectless:
		return ProcedureCallStatement(predicate, args, wheres)
	else:
		return MethodCallStatement(subject, predicate, args, wheres)

ARI_OPERATORS = {
	"lisättynä": ("sisatulento", "+"),
	"ynnättynä": ("sisatulento", "+"),
	"vähennettynä": ("ulkoolento", "-"),
	"kerrottuna": ("ulkoolento", "*"),
	"jaettuna": ("ulkoolento", "/")
}

CMP_OPERATORS = {
	"yhtä suuri kuin": "==",
	"yhtäsuuri kuin": "==",
	"yhtä kuin": "==",
	"erisuuri kuin": "!=",
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
	if prefix:
		checkEof(tokens)
		if tokens.peek().token.lower() == "eikö":
			tokens.setStyle("keyword")
			checkEof(tokens)
			accept(["ole"], tokens)
			tokens.setStyle("keyword")
			negation = True
		else:
			accept(["onko"], tokens)
			tokens.setStyle("keyword")
			negation = False
	operand1, case = parseNominalPhrase(tokens, promoted_cases=["nimento"])
	if case != "nimento":
		fatalError("Syntax error: subject is not in nominative case (in \""+tokens.context()+"\")")
	if not prefix:
		checkEof(tokens)
		if tokens.peek().token.lower() == "ei":
			tokens.setStyle("keyword")
			checkEof(tokens)
			accept(["ole"], tokens)
			tokens.setStyle("keyword")
			negation = True
		else:
			accept(["on"], tokens)
			tokens.setStyle("keyword")
			negation = False
	operator = parseOperator(tokens)
	operand2, case = parseNominalPhrase(tokens, promoted_cases=["nimento"])
	if case != "nimento":
		fatalError("Syntax error: predicative is in "+CASES_ENGLISH[case]+" case (should be in nominative case) (in \""+tokens.context()+"\")")
	eatComma(tokens)
	return CondExpr(negation, operator, operand1, operand2)

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
				fatalError("Syntax error: unexpected token, expected " + " or ".join(["\"" + t + "\"" for t in branch.keys()]) + " (in "+tokens.context()+"\")")
		return branch
	else:
		return "=="

def parseNominalPhrase(tokens, must_be_in_genitive=False, promoted_cases=[]):
	checkEof(tokens)
	if tokens.peek().token.lower() == "riippuen":
		accept(["riippuen"], tokens)
		tokens.setStyle("keyword")
		accept(["siitä"], tokens)
		tokens.setStyle("keyword")
		accept([","], tokens)
		conds = parseList(lambda t: parseCondition(t, prefix=True), tokens, ["joko"])
		alt1, case1 = parseNominalPhrase(tokens)
		accept(["tai"], tokens)
		tokens.setStyle("keyword")
		alt2, case2 = parseNominalPhrase(tokens)
		if case1 != case2:
			fatalError("Syntax error: both operands of \"tai\" must be in the same case (in \"" + tokens.context() + "\")")
		return TernaryExpr(conds, alt1, alt2), case1
	word = tokens.next().toWord(cls=ADJ+NAME+NUMERAL,forms=promoted_cases)
	if word.isOrdinal():
		tokens.setStyle("literal")
		case = word.form
		index = NumExpr(ORDINALS.index(word.baseform))
		expr, case2 = parseNominalPhrase(tokens, case == "omanto")
		if case != case2:
			fatalError("Syntax error: an ordinal and its nominal phrase must be in the same case (in \""+tokens.context()+"\")")
		expr = SubscriptExpr(expr, index)
	elif word.isCardinal():
		tokens.setStyle("literal")
		case = word.form
		num = NumExpr(CARDINALS.index(word.baseform))
		expr = num
	elif word.isName():
		tokens.setStyle("variable")
		case = word.form
		variable = word.baseform
		
		expr = VariableExpr(variable)
	elif word.isAdjective() and word.baseform == "uusi":
		tokens.setStyle("keyword")
		checkEof(tokens)
		word2 = tokens.next().toWord(cls=NOUN,forms=[word.form])
		if not word2.isNoun():
			fatalError("Syntax error: a type must be a noun (in \""+tokens.context()+"\")")
		if word.form != word2.form:
			fatalError("Syntax error: the adjective and the noun of a constructor call must be in the same case (in \""+tokens.context()+"\")")
		
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
			fatalError("Syntax error: unexpected eof, a variable must have at least two words (in \""+tokens.context()+"\")")
		word2 = tokens.next().toWord(cls=NOUN,forms=[word.form])
		if not word.isAdjective() or not word2.isNoun():
			fatalError("Syntax error: a variable must begin with an adjective: "+word.baseform+" "+word2.baseform+" (in \""+tokens.context()+"\")")
		if word.form != word2.form:
			fatalError("Syntax error: the adjective and the noun of a variable must be in the same case (in \""+tokens.context()+"\")")
		
		tokens.setStyle("type")
		case = word.form
		variable = word.baseform + "_" + word2.baseform
		
		expr = VariableExpr(variable, word2.baseform)
	
	cont = True
	while cont:
		cont = False
		while case == "omanto" and not tokens.eof():
			token = tokens.peek()
			if not token.isWord():
				break
			word = token.toWord(cls=NOUN, forms=["omanto"])
			if not word.isNoun() or (must_be_in_genitive and word.form != "omanto"):
				break
			tokens.next()
			tokens.setStyle("field")
			case = word.form
			field = word.baseform
			
			expr = FieldExpr(expr, field)
			cont = True
		
		require_ja = False
		while not tokens.eof() and tokens.peek().token.lower() in ARI_OPERATORS.keys():
			operator = tokens.next().token.lower()
			tokens.setStyle("keyword")
			required_arg_case, op = ARI_OPERATORS[operator]
			arg, arg_case = parseNominalPhrase(tokens, promoted_cases=[required_arg_case])
			if arg_case != required_arg_case:
				fatalError("Syntax error: the operand of \"" + operator + "\" must be in " + CASES_ENGLISH[required_arg_case] + " case (in \"" + tokens.context() + "\")")
			expr = ArithmeticExpr(op, expr, arg)
			cont = True
			if tokens.peek(1) and tokens.peek(2) and tokens.peek(1).token.lower() in [",", "ja"] and tokens.peek(2).token.lower() in ARI_OPERATORS.keys():
				if tokens.next().token == ",":
					require_ja = True
				else: # ja
					require_ja = False
					tokens.setStyle("keyword")
				continue
			else:
				if require_ja:
					fatalError("Syntax error: an operator chain must end with \"ja\" (in \"" + tokens.context() + "\")")
				break
	
	return expr, case

def parseAssignment(tokens):
	word, word2 = parseVariable(tokens)
	var = word.baseform + "_" + word2.baseform
	checkEof(tokens)
	accept(["on", "ovat"], tokens)
	tokens.setStyle("keyword")
	value, case = parseNominalPhrase(tokens, promoted_cases=["nimento"])
	if case != "nimento":
		fatalError("Syntax error: contructor argument value is not in nominative case (in \""+tokens.context()+"\")")
	return (var, value)

def parseCtorArg(tokens):
	checkEof(tokens)
	word = tokens.next().toWord(cls=NOUN, forms=["nimento"])
	if not word.isNoun() or word.form != "nimento":
		fatalError("Syntax error: constructor argument name is not a noun in nominative case (in \""+tokens.context()+"\")")
	tokens.setStyle("field")
	checkEof(tokens)
	token = tokens.peek().token.lower()
	accept(["on", "ovat"], tokens)
	tokens.setStyle("keyword")
	if token == "on":
		value, case = parseNominalPhrase(tokens, promoted_cases=["nimento"])
		if case != "nimento":
			fatalError("Syntax error: contructor argument value is not in nominative case (in \""+tokens.context()+"\")")
		return CtorArgExpr(word.baseform, value)
	else: # ovat
		values_cases = parseList(parseNominalPhrase, tokens)
		values = []
		for value, case in values_cases:
			values += [value]
			if case != "nimento":
				fatalError("Syntax error: contructor argument value is not in nominative case (in \""+tokens.context()+"\")")
		return CtorArgExpr(word.baseform, ListExpr(values))

def parseList(parseChild, tokens, custom_endings=[]):
	ans = []
	force = False
	while force or (not tokens.eof() and not tokens.peek().token.lower() in [".", "ja", "eikä"] + custom_endings):
		ans += [parseChild(tokens)]
		if not tokens.eof() and tokens.peek().token == ",":
			tokens.next()
			force = True
		else:
			force = False
	checkEof(tokens)
	if tokens.peek().token == ".":
		return ans
	token = tokens.next()
	tokens.setStyle("keyword")
	if token.token.lower() == "eikä":
		checkEof(tokens)
		accept(["muuta"], tokens)
		tokens.setStyle("keyword")
	elif token.token.lower() == "ja":
		ans += [parseChild(tokens)]
	return ans

def typeToJs(typename):
	if typename == "luku":
		return "Number"
	elif typename == "lista":
		return "Array"
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
			return "function " + self.signature.compile(semicolon=False) + " { " + " ".join([s.compile() for s in self.body]) + " };"
		elif isinstance(self.signature, MethodCallStatement):
			if not isinstance(self.signature.obj, VariableExpr):
				fatalError("Illegal method declaration: subject is not a variable (in \"" + str(self.signature) + "\")")
			return (
				typeToJs(self.signature.obj.type) + ".prototype."
				+ self.signature.compileName()
				+ " = function" + self.signature.compileArgs() + " { "
				+ "var " + self.signature.obj.name + " = this; "
				+ " ".join([s.compile() for s in self.body])
				+ " };")
		else:
			fatalError("TODO")

class ClassDecl:
	def __init__(self, name, fields):
		self.name = name
		self.fields = fields
	def __str__(self):
		return self.name + " := class { " + ", ".join(self.fields) + "};"
	def compile(self):
		ans = "function " + self.name + "(vals) { "
		for name, number in self.fields:
			ans += "this." + name + " = (\"" + name + "\" in vals) ? vals[\"" + name + "\"] : "
			if number == "plural":
				ans += "[]; "
			else:
				ans += "undefined; "
		ans += "};"
		for name, number in self.fields:
			ans += " " + typeToJs(self.name) + ".prototype.f_" + name + " = function() { return this." + name + "; };"
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
		return typeToJs(self.type) + ".prototype.f_" + self.field + " = function() { var " + self.param + " = this; return " + self.body.compile() + " };"

class IfStatement:
	def __init__(self, conditions, block):
		self.conditions = conditions
		self.block = block
	def __str__(self):
		return "if (" + " and ".join([str(c) for c in self.conditions]) + ") { " + " ".join([str(s) for s in self.block]) + " }"
	def compile(self):
		return "if ((" + ") && (".join([c.compile() for c in self.conditions]) + ")) { " + " ".join([s.compile() for s in self.block]) + " }"

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
	def compile(self, semicolon=True):
		ans = self.compileWheres() + self.compileName() + self.compileArgs()
		if semicolon:
			ans += ";"
		return ans

class ProcedureCallStatement(CallStatement):
	def __str__(self):
		return self.name + "(" + ", ".join([key + ": " + str(self.args[key]) for key in self.args]) + ")"

class MethodCallStatement(CallStatement):
	def __init__(self, obj, name, args, wheres):
		self.obj = obj
		self.name = name
		self.args = args
		self.wheres = wheres
	def __str__(self):
		return str(self.obj) + "." + self.name + "(" + ", ".join([key + ": " + str(self.args[key]) for key in self.args]) + ")"
	def compile(self, semicolon=True):
		ans = self.compileWheres() + self.obj.compile() + "." + self.compileName() + self.compileArgs()
		if semicolon:
			ans += ";"
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
		return self.obj.compile() + "[" + self.index.compile() + "]"

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

while 1:
	line = input("> ")
	tokens = lexCode(line)
	try:
		print(parseDeclaration(tokens).compile())
	except Exception as e:
		traceback.print_exc()
	print(tokens.prettyPrint())
