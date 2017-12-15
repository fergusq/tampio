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
	for word in re.split(r'(\s|\.|,|"[^"]*")', code):
		if word == "":
			continue
		if re.fullmatch(r'\s|\.|,|"[^"]*"', word):
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
		for case in ORDINAL_CASE_REGEXES:
			if re.fullmatch(ORDINAL_CASE_REGEXES[case], word):
				output += [AltWords(word, [Word(word, word[:word.index(":")], case, number, "nimisana", ordinal_like=True)])]
				cont = True
		if cont:
			continue
		
		analysis_list = voikko.analyze(word)
		alternatives = []
		for analysis in analysis_list:
			bf = analysis["BASEFORM"]
			cl = analysis["CLASS"]
			if bf in ORDINALS+CARDINALS:
				cl = "lukusana"
			number = analysis["NUMBER"] if "NUMBER" in analysis else ""
			person = analysis["PERSON"] if "PERSON" in analysis else ""
			possessive = analysis["POSSESSIVE"] if "POSSESSIVE" in analysis else ""
			if "SIJAMUOTO" in analysis:
				form = analysis["SIJAMUOTO"]
			elif "MOOD" in analysis and "TENSE" in analysis:
				form = analysis["MOOD"] + "_" + analysis["TENSE"]
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
			alternatives += [Word(word, bf, form + person, number, cl, possessive)]
		if len(alternatives) == 0:
			alternatives = [Word(word, word, "", "", "")]
		output += [AltWords(word, alternatives)]
	return TokenList(output)

class TokenList:
	def __init__(self, tokens):
		self.tokens = tokens
		self.styles = [""]*len(tokens)
		self.i = -1
		
		# rivinumero jokaiselle tokenille
		self.lines = []
		line = 1
		for token in tokens:
			token.tokens = self
			line += token.token.count("\n")
			self.lines.append(line)
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
			if self.tokens[self.i].isWord() or not self.tokens[self.i].isSpace():
				return self.tokens[self.i]
		return None
	def eof(self):
		return not self.peek()
	def setStyle(self, style):
		self.styles[self.i] = style
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

def eat(tokens, token):
	if not tokens.eof() and tokens.peek().token.lower() == token:
		tokens.next()

eatComma = lambda tokens: eat(tokens, ",")
eatPeriod = lambda tokens: eat(tokens, ".")

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
		return not not re.fullmatch("\\s*", self.token)
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
	def isString(self):
		return False
	def toWord(self, cls=[], forms=[], numbers=[]):
		def score(w):
			return cls.count(w.word_class) + forms.count(w.form) + numbers.count(w.number)
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
	def __init__(self, word, baseform, form, number, word_class, possessive="", ordinal_like=False):
		#print(word, baseform, form, number, word_class)
		self.word = word
		self.baseform = baseform
		self.form = form
		self.number = number
		self.word_class = word_class
		self.possessive = possessive
		self.ordinal_like = ordinal_like
	def __str__(self):
		return self.baseform + "(" + self.word_class + ":" + self.form + ":" + self.number + ")"
	def __repr__(self):
		return "<Word " + str(self) + ">"
	def isVariable(self):
		return len(self.baseform) == 1
	def isNoun(self):
		return self.word_class in ["nimisana"] or len(self.baseform) == 1
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
	def isAdverb(self):
		return self.word_class in ["seikkasana"]
