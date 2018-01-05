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

import html, re
from voikko.libvoikko import Voikko, Token
from fatal_error import syntaxError
from inflect import *

LANGUAGE = "fi-x-morpho"
ENCODING = "UTF-8"

voikko = Voikko(LANGUAGE)

def lexCode(code):
	output = []
	for word in re.split(r'(\s|\.|,|;|\[|\]|"[^"]*"|#[^\n]*\n|\([^()]*\))', code):
		if word == "":
			continue
		if re.fullmatch(r'\s|\.|,|;|\[|\]|"[^"]*"|#[^\n]*\n|\([^()]*\)', word):
			output += [Punctuation(word)]
			continue
		
		cont = False
		for number in CASE_REGEXES:
			for case in CASE_REGEXES[number]:
				if re.fullmatch(CASE_REGEXES[number][case], word):
					bf = word[:word.index(":")]
					cl = "lukusana" if re.fullmatch(r'\d+', bf) else "nimisana"
					output += [AltWords(word, [Word(word, bf, case, number, cl)])]
					cont = True
		if cont:
			continue
		for case in ORDINAL_CASE_REGEXES:
			if re.fullmatch(ORDINAL_CASE_REGEXES[case], word):
				bf = word[:word.index(":")]
				cl = "lukusana" if re.fullmatch(r'\d+', bf) else "nimisana"
				output += [AltWords(word, [Word(word, bf, case, number, cl, ordinal_like=True)])]
				cont = True
		if cont:
			continue
		
		analysis_list = voikko.analyze(word)
		prefix = ""
		if len(analysis_list) == 0 and "-" in word:
			i = word.rindex("-")+1
			analysis_list = voikko.analyze(word[i:])
			prefix = word[:i].lower()
		alternatives = []
		for analysis in analysis_list:
			bf = prefix+analysis["BASEFORM"]
			cl = analysis["CLASS"]
			if bf in ORDINALS+CARDINALS or re.fullmatch(r'\d+', bf):
				cl = "lukusana"
			elif "PARTICIPLE" in analysis and analysis["PARTICIPLE"] == "agent":
				cl = "laatusana"
			number = analysis.get("NUMBER", "")
			person = analysis.get("PERSON", "")
			comparison = analysis.get("COMPARISON", "")
			possessive = analysis.get("POSSESSIVE", "")
			if "MOOD" in analysis and "SIJAMUOTO" in analysis:
				form = analysis["MOOD"] + "_" + analysis["SIJAMUOTO"]
			elif "SIJAMUOTO" in analysis:
				form = analysis["SIJAMUOTO"]
			elif "MOOD" in analysis and "TENSE" in analysis:
				form = analysis["MOOD"] + "_" + analysis["TENSE"]
				if "NEGATIVE" in analysis and analysis["NEGATIVE"] == "true":
					form += "_negative"
			elif "MOOD" in analysis and analysis["MOOD"] == "E-infinitive":
				if re.fullmatch(r'.*taess[aä]', word.lower()):
					form = "E-infinitive_sisaolento"
					person = "4"
				elif re.fullmatch(r'.*taen', word.lower()):
					form = "E-infinitive_keinonto"
					person = "4"
				elif re.fullmatch(r'.*ss[aä]', word.lower()):
					form = "E-infinitive_sisaolento"
					person = "3"
				elif re.fullmatch(r'.*n', word.lower()):
					form = "E-infinitive_keinonto"
					person = "3"
				else:
					form = analysis["MOOD"]
			elif "MOOD" in analysis:
				form = analysis["MOOD"]
			else:
				form = ""
			alternatives += [Word(word, bf, form + person, number, cl, possessive, comparison)]
		if len(alternatives) == 0:
			alternatives = [Word(word, word, "", "", "")]
		output += [AltWords(word, alternatives)]
	return TokenList(output)

class TokenList:
	def __init__(self, tokens):
		self.tokens = tokens
		self.styles = [""]*len(tokens)
		self.style_spans = [(False, False)]*len(tokens)
		self.newlines = [False]*len(tokens)
		self.indent_levels = [0]*len(tokens)
		self.i = -1
		
		# rivinumero jokaiselle tokenille
		self.lines = []
		line = 1
		for token in tokens:
			token.tokens = self
			line += token.token.count("\n")
			self.lines.append(line)
		
		self.indent_level = 0
	def setPlace(self, i):
		self.i = i
	def place(self):
		return self.i
	def current(self):
		return self.tokens[self.i]
	def prev(self, n=1):
		j = self.i<1
		while j >= 0:
			if self.tokens[j].isWord() or not self.tokens[j].isSpace():
				n -= 1
				if n == 0:
					return self.tokens[j]
			j -= 1
		return None
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
			self.indent_levels[self.i] = self.indent_level
			if self.tokens[self.i].isWord() or not self.tokens[self.i].isSpace():
				return self.tokens[self.i]
		return None
	def eof(self):
		return not self.peek()
	def setStyle(self, style, continued=False):
		self.styles[self.i] = style
		if continued:
			self.style_spans[self.i] = (True, False)
			j = self.i-1
			while self.styles[j] == "":
				self.style_spans[j] = (True, True)
				j -= 1
			self.style_spans[j] = (self.style_spans[j][0], True)
	def increaseIndentLevel(self):
		self.indent_level += 1
	def decreaseIndentLevel(self):
		self.indent_level -= 1
	def addNewline(self):
		self.newlines[self.i] = True
	def context(self, place):
		a = max(0, place-10)
		b = min(len(self.tokens), place+10)
		out = ""
		for i in range(a, b):
			if i == place:
				out += "<here>"
			out += self.tokens[i].token
		return out
	def fancyContext(self, place):
		a = max(0, place-10)
		b = min(len(self.tokens), place+10)
		out = "Line " + str(self.lines[place]) + ": "
		column = 0
		for i in range(a, b):
			if i == place:
				column = len(out)
			if self.lines[i] == self.lines[place] and "\n" not in self.tokens[i].token:
				out += self.tokens[i].token.replace("\t", " ")
		out += "\n" + " "*column + "^" + "~"*(len(self.tokens[place].token)-1)
		return out

def eat(token, tokens):
	if not tokens.eof():
		next_token = tokens.peek().token.lower()
		if (isinstance(token, list) and next_token in token) or next_token == token:
			tokens.next()
			return True
	return False

eatComma = lambda tokens: eat(",", tokens)
eatPeriod = lambda tokens: eat(".", tokens)

def checkEof(tokens):
	if tokens.eof():
		syntaxError("unexpected eof", tokens)

def accept(accepted, tokens):
	checkEof(tokens)
	if tokens.next().token.lower() not in accepted:
		syntaxError("unexpected token, expected " + " or ".join(["\"" + t + "\"" for t in accepted]), tokens)

CARDINALS = ["nolla", "yksi", "kaksi", "kolme", "neljä", "viisi", "kuusi", "seitsemän", "kahdeksan", "yhdeksän", "kymmenen"]
ORDINALS = ["ensimmäinen", "toinen", "kolmas", "neljäs", "viides", "kuudes", "seitsemäs", "kahdeksas", "yhdeksäs", "kymmenes"]

class Punctuation:
	def __init__(self, token):
		self.token = token
		self.tokens = None
	def isWord(self):
		return False
	def isSpace(self):
		return self.isComment() or not not re.fullmatch("\s*", self.token)
	def isComment(self):
		return not not re.fullmatch("#[^\n]*\n|\([^()]*\)", self.token)
	def isString(self):
		return not not re.fullmatch(r'"[^"]*"', self.token)
	def toWord(self, cls=[], forms=[], numbers=[]):
		syntaxError("unexpected token, expected a word", self.tokens)
	def __str__(self):
		return self.token
	def __repr__(self):
		return "<Punctuation " + self.token + ">"

class AltWords:
	def __init__(self, token, alternatives):
		self.token = token
		self.alternatives = alternatives
		self.tokens = None
	def isWord(self):
		return True
	def isSpace(self):
		return False
	def isComment(self):
		return False
	def isString(self):
		return False
	def toWord(self, cls=[], forms=[], numbers=[]):
		def score(w):
			return (cls.count(w.word_class)
				+ forms.count(w.form)
				+ forms.count(w.comparison)
				+ numbers.count(w.number)
				+ (-2 if w.form == "keinonto" and "nimisana" in cls else 0))
		return sorted(self.alternatives, key=score)[-1]
	def __str__(self):
		return self.token
	def __repr__(self):
		return "<AltWord " + self.token + ">"

ADJ = ["laatusana", "nimisana_laatusana"]
NOUN = ["nimisana"]
NAME = ["etunimi", "sukunimi"]
PRONOUN = ["asemosana"]
NUMERAL = ["lukusana"]
VERB = ["teonsana", "kieltosana"]
CONJ = ["sidesana"]

class Word:
	def __init__(self, word, baseform, form, number, word_class, possessive="", comparison="", ordinal_like=False):
		#print(word, baseform, form, number, word_class)
		self.word = word
		self.baseform = baseform
		self.form = form
		self.number = number
		self.word_class = word_class
		self.possessive = possessive
		self.ordinal_like = ordinal_like
		self.comparison = comparison
	def __str__(self):
		return self.baseform + "(" + self.word_class + ":" + self.form + ":" + self.number + ")"
	def __repr__(self):
		return "<Word " + str(self) + ">"
	def isVariable(self):
		return len(self.baseform) == 1 and self.baseform not in [str(i) for i in range(0,10)]
	def isNoun(self):
		return self.word_class in ["nimisana"] or self.isVariable()
	def isName(self):
		return self.word_class in ["etunimi", "sukunimi"] and self.word[0].upper() == self.word[0]
	def isPronoun(self):
		return self.word_class in ["asemosana"]
	def isAdjective(self):
		return self.word_class in ["laatusana", "nimisana_laatusana"] and not self.isAdverb()
	def isOrdinal(self):
		return self.baseform in ORDINALS
	def isCardinal(self):
		return self.baseform in CARDINALS
	def isVerb(self):
		return self.word_class in ["teonsana", "kieltosana"]
	def isConjunction(self):
		return self.word_class in ["sidesana"]
	def isAdverb(self):
		return self.word_class in ["seikkasana"] or self.form == "kerrontosti"
