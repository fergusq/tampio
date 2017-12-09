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

import re
from voikko.libvoikko import Voikko, Token
from fatal_error import fatalError
from inflect import *

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
