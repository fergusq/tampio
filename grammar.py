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

from fatal_error import fatalError
from inflect import *

from ast import *
from lex import accept, checkEof, eatComma, eatPeriod, ADJ, NOUN, NAME, PRONOUN, NUMERAL, VERB, CONJ, CARDINALS, ORDINALS

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
		eatPeriod(tokens)
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
			eatPeriod(tokens)
			return FunctionDecl(word2.baseform, field, word.baseform + "_" + word2.baseform, body)
	tokens.next()
	fatalError("Syntax error: unexpected token \"" + token.token + "\" (in \"" + tokens.context() + "\")")

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
		subject, case = parseNominalPhrase(tokens, promoted_cases=["nimento"])
		
		word = tokens.next().toWord(
			cls=VERB,
			forms=["indicative_present_simple3", "indicative_present_simple4"])
		
		if not word.isVerb() or word.form not in ["indicative_present_simple3", "indicative_present_simple4"]:
			fatalError("Syntax error: predicate is not in indicative simple present (in \""+tokens.context()+"\")")
		tokens.setStyle("function")
		
		predicate = word.baseform + readVerbModifiers(tokens)
		passive = word.form[-1] == "4"
		
		if case != "nimento" and not passive:
			fatalError("Syntax error: subject must be in nominative case (in \""+tokens.context()+"\")")
		
		subjectless = False
		subject_case = case
	elif word.isVerb():
		tokens.next()
		tokens.setStyle("function")
		subjectless = True
		if word.form == "imperative_present_simple2":
			predicate = word.baseform + "!"
		elif word.form == "indicative_present_simple4":
			predicate = word.baseform + readVerbModifiers(tokens)
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
		return MethodCallStatement(subject, subject_case, predicate, args, wheres)

def readVerbModifiers(tokens):
	ans = ""
	while not tokens.eof():
		token = tokens.peek()
		if token.isWord() and token.toWord(cls=NOUN).isNoun():
			tokens.next()
			tokens.setStyle("function")
			ans += "_" + token.token.lower()
		else:
			break
	return ans

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
		
		if not tokens.eof() and tokens.peek().isWord():
			word = tokens.peek().toWord(cls=NUMERAL, forms=["sisatulento", "sisaeronto"])
			print(word.baseform, word.form, tokens.peek(2).token)
			if word.isOrdinal() and word.form in ["sisatulento", "sisaeronto"] and tokens.peek(2) and tokens.peek(2).token.lower() in ["alkaen", "päättyen"]:
				tokens.next()
				tokens.setStyle("literal")
				if word.form == "sisaeronto":
					accept(["alkaen"], tokens)
					expr = SliceExpr(expr, NumExpr(ORDINALS.index(word.baseform)), None)
				elif word.form == "sisatulento":
					accept(["päättyen"], tokens)
					expr = SliceExpr(expr, NumExpr(0), NumExpr(ORDINALS.index(word.baseform)))
				tokens.setStyle("keyword")
				cont = True
		
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
