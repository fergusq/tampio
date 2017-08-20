# -*- coding: utf-8 -*-

# Copyright 2017 Iikka Hauhio
# Contains some minor changes to the original file.

# Copyright 2005-2010 Harri Pitkänen (hatapitk@iki.fi)
# Library for inflecting words for Voikko project.
# This library requires Python version 2.4 or newer.

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import voikko.voikkoutils as voikkoutils
import codecs
import sys
import re

# Size of the affix file is controlled by the following parameter. Only affix rules
# having priority lower or equal to MAX_AFFIX_PRIORITY are written to the
# affix file. Values from 1 to 3 are currently used.
MAX_AFFIX_PRIORITY=2

class InflectionRule:
	"Rule for word inflection"
	def __init__(self):
		self.name = u""
		self.isCharacteristic = False
		self.rulePriority = 1
		self.delSuffix = u""
		self.addSuffix = u""
		self.gradation = voikkoutils.GRAD_WEAK

class InflectionType:
	"Word inflection type"
	def __init__(self):
		self.kotusClasses = []
		self.joukahainenClasses = []
		self.rmsfx = u""
		self.matchWord = u""
		self.gradation = voikkoutils.GRAD_NONE
		self.note = u""
		self.inflectionRules = []
	
	"Return the given word with suffix removed"
	def removeSuffix(self, word):
		l = len(self.rmsfx)
		if l == 0: return word
		elif len(word) <= l: return u""
		else: return word[:-l]
	
	"Return the Kotus gradation class for word and gradation class in Joukahainen"
	def kotusGradClass(self, word, grad_type):
		if not grad_type in ["av1", "av2", "av3", "av4", "av5", "av6"]:
			return u""
		word = self.removeSuffix(word)
		if len(word) == 0: return u""
		if voikkoutils.is_consonant(word[-1]) and not voikkoutils.is_consonant(word[-2]):
			if word[-4:-2] == u'ng': return u'G'
			if word[-4:-2] == u'mm': return u'H'
			if word[-4:-2] == u'nn': return u'J'
			if word[-4:-2] == u'll': return u'I'
			if word[-4:-2] == u'rr': return u'K'
			if word[-3] == u'd': return u'F'
			if word[-3] == u't': return u'C'
			if word[-3] == u'k': return u'A'
			if word[-3] == u'p': return u'B'
			if word[-3] == u'v': return u'E'
		if grad_type == u'av1':
			if word[-3:-1] == u'tt': return u'C'
			if word[-3:-1] == u'kk': return u'A'
			if word[-3:-1] == u'pp': return u'B'
			if word[-3:-1] == u'mp': return u'H'
			if word[-2] == u'p' and not voikkoutils.is_consonant(word[-1]):
				return u'E'
			if word[-3:-1] == u'nt': return u'J'
			if word[-3:-1] == u'lt': return u'I'
			if word[-3:-1] == u'rt': return u'K'
			if word[-2] == u't': return u'F'
			if word[-3:-1] == u'nk': return u'G'
			if word[-3:] == u'uku': return u'M'
			if word[-3:] == u'yky': return u'M'
		if grad_type == u'av2':
			if word[-4:-2] == u'ng': return u'G'
			if word[-4:-2] == u'mm': return u'H'
			if word[-4:-2] == u'nn': return u'J'
			if word[-4:-2] == u'll': return u'I'
			if word[-4:-2] == u'rr': return u'K'
			if word[-3] == u'd': return u'F'
			if word[-3] == u't': return u'C'
			if word[-3] == u'k': return u'A'
			if word[-3] == u'p': return u'B'
			if word[-3] == u'b': return u'O' # Unofficial, not in Kotus
			if word[-3] == u'g': return u'P' # Unofficial, not in Kotus
			if word[-3] == u'v': return u'E'
		if grad_type == u'av3': # k -> j
			if word[-2] == u'k': return u'L'
		if grad_type == u'av4': # j -> k
			if word[-2] == u'j': return u'L'
			if word[-3] == u'j': return u'L'
		if grad_type == u'av5': # k -> -
			if word[-2] == u'k': return u'D'
		if grad_type == u'av6': # - -> k
			return u'D'
		return u''

class InflectedWord:
	"Word in inflected form"
	def __init__(self):
		self.formName = u""
		self.inflectedWord = u""
		self.isCharacteristic = False
		self.priority = 1
	def __str__(self):
		return self.formName + u"\t" + self.inflectedWord

## Function to convert a string containing back vowels to an equivalent string containing
# front vowels.
def __convert_tv_ev(text):
	return text.replace('a', u'ä').replace('o', u'ö').replace('u', u'y')


## Applies given gradation type to given word. Returns a tuple in the form
# (strong, weak) or None if this is not possible. Conditional aposthrope
# is represented by $.
def __apply_gradation(word, grad_type):
	if grad_type == u'-':
		return (word, word)
	
	if voikkoutils.is_consonant(word[-1]) and not voikkoutils.is_consonant(word[-2]) and len(word) >= 3:
		if word[-4:-2] == u'ng':
			return (word[:-4]+u'nk'+word[-2:], word)
		# uvu/yvy->uku/yky not possible?
		if word[-4:-2] == u'mm':
			return (word[:-4]+u'mp'+word[-2:], word)
		if word[-4:-2] == u'nn':
			return (word[:-4]+u'nt'+word[-2:], word)
		if word[-4:-2] == u'll':
			return (word[:-4]+u'lt'+word[-2:], word)
		if word[-4:-2] == u'rr':
			return (word[:-4]+u'rt'+word[-2:], word)
		if word[-3] == u'd':
			return (word[:-3]+u't'+word[-2:], word)
		if word[-3] in u'tkp':
			return (word[:-2]+word[-3:], word)
		if word[-3] == u'v':
			return (word[:-3]+u'p'+word[-2:], word)
	
	if grad_type == u'av1' and len(word) >= 3:
		if word[-3:-1] in (u'tt',u'kk',u'pp'):
			return (word, word[:-2]+word[-1])
		if word[-3:-1] == u'mp':
			return (word, word[:-3]+u'mm'+word[-1])
		if word[-2] == u'p' and not voikkoutils.is_consonant(word[-1]):
			return (word, word[:-2]+u'v'+word[-1])
		if word[-3:-1] == u'nt':
			return (word, word[:-3]+u'nn'+word[-1])
		if word[-3:-1] == u'lt':
			return (word, word[:-3]+u'll'+word[-1])
		if word[-3:-1] == u'rt':
			return (word, word[:-3]+u'rr'+word[-1])
		if word[-2] == u't':
			return (word, word[:-2]+u'd'+word[-1])
		if word[-3:-1] == u'nk':
			return (word, word[:-3]+u'ng'+word[-1])
		if word[-3:] == u'uku':
			return (word, word[:-3]+u'uvu')
		if word[-3:] == u'yky':
			return (word, word[:-3]+u'yvy')
	if grad_type == u'av2' and len(word) >= 2:
		if word[-3:-1] == u'ng':
			return (word[:-3]+u'nk'+word[-1], word)
		# uvu/yvy->uku/yky not possible?
		if word[-3:-1] == u'mm':
			return (word[:-3]+u'mp'+word[-1], word)
		if word[-3:-1] == u'nn':
			return (word[:-3]+u'nt'+word[-1], word)
		if word[-3:-1] == u'll':
			return (word[:-3]+u'lt'+word[-1], word)
		if word[-3:-1] == u'rr':
			return (word[:-3]+u'rt'+word[-1], word)
		if word[-2] == u'd':
			return (word[:-2]+u't'+word[-1], word)
		if word[-2] in u'tkpbg':
			return (word[:-1]+word[-2:], word)
		if word[-2] == u'v':
			return (word[:-2]+u'p'+word[-1], word)
	if grad_type == u'av3' and len(word) >= 3: # k -> j
		if word[-2] == u'k':
			if voikkoutils.is_consonant(word[-3]):
				return (word, word[:-2]+u'j'+word[-1])
			else:
				return (word, word[:-3]+u'j'+word[-1])
	if grad_type == u'av4' and len(word) >= 3: # j -> k
		if word[-2] == u'j':
			return (word[:-2]+u'k'+word[-1], word)
		if word[-3] == u'j':
			return (word[:-3]+u'k'+word[-2]+word[-1], word)
	if grad_type == u'av5' and len(word) >= 2: # k -> -
		if word[-2] == u'k':
			return (word, word[:-2]+u'$'+word[-1])
	if grad_type == u'av6' and len(word) >= 1: # - -> k
		if voikkoutils.is_consonant(word[-1]): # FIXME: hack
			return (word[:-2]+u'k'+word[-2:], word)
		else:
			return (word[:-1]+u'k'+word[-1], word)
	return None


# Read header line from a file. Return value will be a tuple in the form (name, value) or
# None if the end of file was reached.
def __read_header(file):
	while True:
		line = file.readline()
		if not line.endswith('\n'): return None
		strippedLine = voikkoutils.removeComments(line).strip()
		if len(strippedLine) == 0: continue
		valStart = strippedLine.find(':')
		if valStart < 1:
			print('Malformed input file: the problematic line was')
			print(line)
			return None
		return (strippedLine[:valStart].strip(), strippedLine[valStart+1:].strip())


# Read an option "name" from string "options". If it does not exist, then default will be returned.
def __read_option(options, name, default):
	parts = options.split(u',');
	for part in parts:
		nameval = part.split(u'=')
		if len(nameval) == 2 and nameval[0] == name: return nameval[1]
		if len(nameval) == 1 and nameval[0] == name: return u'1'
	return default

# Read and return an inflection rule from a file. Returns None, if
# the end of group or file was reached.
def __read_inflection_rule(file):
	while True:
		line = file.readline()
		if not line.endswith('\n'): return None
		strippedLine = voikkoutils.removeComments(line).strip()
		if len(strippedLine) == 0: continue
		columns = strippedLine.split()
		if columns[0] == 'end:': return None
		
		r = InflectionRule()
		if columns[0].startswith(u'!'):
			r.name = columns[0][1:]
			r.isCharacteristic = True
		else:
			r.name = columns[0]
			if columns[0] in ['nominatiivi', 'genetiivi', 'partitiivi', 'illatiivi',
				'nominatiivi_mon', 'genetiivi_mon', 'partitiivi_mon', 'illatiivi_mon',
				'infinitiivi_1', 'preesens_yks_1', 'imperfekti_yks_3',
				'kondit_yks_3', 'imperatiivi_yks_3', 'partisiippi_2',
				'imperfekti_pass']: r.isCharacteristic = True
			else: r.isCharacteristic = False
		if columns[1] != u'0': r.delSuffix = columns[1]
		if columns[2] != u'0': r.addSuffix = columns[2]
		if columns[3] == u's': r.gradation = voikkoutils.GRAD_STRONG
		if len(columns) > 4:
			if __read_option(columns[4], u'ps', u'') == u'r': continue
			r.rulePriority = int(__read_option(columns[4], u'prio', u'1'))
		
		return r



# Read and return an inflection type from a file.
# If the end of file is reached, this function returns None.
def __read_inflection_type(file):
	header_tuple = __read_header(file)
	if header_tuple == None: return None
	if header_tuple[0] != u'class' or len(header_tuple[1]) == 0:
		print('Class definition expected.')
		return None
	
	t = InflectionType()
	t.kotusClasses = header_tuple[1].split(u",")
	while True:
		header_tuple = __read_header(file)
		if header_tuple == None:
			print('Unexpected end of file.')
			return None
		if header_tuple[0] == u'sm-class': t.joukahainenClasses = header_tuple[1].split(' ')
		if header_tuple[0] == u'rmsfx': t.rmsfx = header_tuple[1]
		if header_tuple[0] == u'match-word': t.matchWord = header_tuple[1]
		if header_tuple[0] == u'consonant-gradation':
			if header_tuple[1] == u'-': t.gradation = voikkoutils.GRAD_NONE
			if header_tuple[1] == u'sw': t.gradation = voikkoutils.GRAD_SW
			if header_tuple[1] == u'ws': t.gradation = voikkoutils.GRAD_WS
		if header_tuple[0] == u'note':
			t.note = header_tuple[1]
		if header_tuple[0] == u'rules':
			rule = __read_inflection_rule(file)
			while rule != None:
				t.inflectionRules.append(rule)
				rule = __read_inflection_rule(file)
		if header_tuple[0] == u'end' and header_tuple[1] == u'class':
			return t


# Convert a Hunspell-fi -style pair of regular expression and replacement string to a list
# of tuples containing corresponding Hunspell affix rule elements (strip_str, affix, condition).
def __regex_to_hunspell(exp, repl):
	# TODO: implement more regular expressions
	rulelist = []
	wchars = u"[a-zäöé]"
	if exp == "": exp = "0"
	if repl == "": repl = "0"
	if exp == "0":
		strip_str = "0"
		condition = "."
		affix = repl
		rulelist.append((strip_str, affix, condition))
		return rulelist
	if re.compile(u"^(?:%s)+$" % wchars).match(exp) != None: # string of letters
		strip_str = exp
		condition = exp
		affix = repl
		rulelist.append((strip_str, affix, condition))
		return rulelist
	m = re.compile(u"^((?:%s)*)\\(\\[((?:%s)*)\\]\\)((?:%s)*)$" % (wchars, wchars, wchars) \
	              ).match(exp)
	if m != None: # exp is of form 'ab([cd])ef'
		start_letters = m.group(1)
		alt_letters = m.group(2)
		end_letters = m.group(3)
		for alt_char in alt_letters:
			strip_str = start_letters + alt_char + end_letters
			condition = start_letters + alt_char + end_letters
			affix = repl.replace('(1)', alt_char)
			rulelist.append((strip_str, affix, condition))
		return rulelist
	m = re.compile("^((?:%s)*)\\[((?:%s)*)\\]((?:%s)*)$" % (wchars, wchars, wchars)).match(exp)
	if m != None: # exp is of form 'ab[cd]ef'
		start_letters = m.group(1)
		alt_letters = m.group(2)
		end_letters = m.group(3)
		for alt_char in alt_letters:
			strip_str = start_letters + alt_char + end_letters
			condition = start_letters + alt_char + end_letters
			affix = repl
			rulelist.append((strip_str, affix, condition))
		return rulelist
	print('Unsupported regular expression: exp=\'' + exp + '\', repl=\'' + repl + '\'')
	return []


# Translates word match pattern to a Perl-compatible regular expression
def __word_pattern_to_pcre(pattern):
	return '.*' + voikkoutils.capital_char_regexp(pattern) + '$'


# Public functions


# Reads and returns a list of word classes from a file named file_name.
def readInflectionTypes(file_name):
	inflection_types = []
	inputfile = codecs.open(file_name, 'r', 'UTF-8')
	inftype = __read_inflection_type(inputfile)
	while inftype != None:
		inflection_types.append(inftype)
		inftype = __read_inflection_type(inputfile)
	inputfile.close()
	return inflection_types


def _replace_conditional_aposthrope(word):
	ind = word.find(u'$')
	if ind == -1: return word
	if ind == 0 or ind == len(word) - 1: return word.replace(u'$', u'')
	if word[ind-1] == word[ind+1]:
		if word[ind-1] in [u'i', u'o', u'u', u'y', u'ö']:
			return word.replace(u'$', u'\'')
		if word[ind-1] in [u'a', u'ä'] and ind > 1 and word[ind-2] == word[ind-1]:
			return word.replace(u'$', u'\'')
	return word.replace(u'$', u'')

DERIVS_VOWEL_HARMONY_SPECIAL_CLASS_1 = [u'subst_tO', u'subst_Os']
DERIVS_VOWEL_HARMONY_SPECIAL_CLASS_2 = [u'verbi_AjAA', 'verbi_AhtAA', 'verbi_AUttAA', 'verbi_AUtellA']

def _normalize_base(base):
	if base.find(u'=') != -1:
		base = base[base.find(u'=') + 1:]
	return base.lower()

def _vtype_special_class_1(base):
	base = _normalize_base(base)
	last_back = max(base.rfind(u'a'), base.rfind(u'o'), base.rfind(u'å'), base.rfind(u'u'))
	last_front = max(base.rfind(u'ä'), base.rfind(u'ö'), base.rfind(u'y'))
	if last_front > last_back: return voikkoutils.VOWEL_FRONT
	else: return voikkoutils.VOWEL_BACK

def _vtype_special_class_2(base):
	base = _normalize_base(base)
	last_back = max(base.rfind(u'a'), base.rfind(u'o'), base.rfind(u'å'), base.rfind(u'u'))
	last_front = max(base.rfind(u'ä'), base.rfind(u'ö'), base.rfind(u'y'))
	if last_front > last_back: return voikkoutils.VOWEL_FRONT
	elif last_front < last_back: return voikkoutils.VOWEL_BACK
	else:
		# no front or back vowels
		if base.rfind(u'e') >= 0:
			# "hel|istä" -> "heläjää"
			return voikkoutils.VOWEL_FRONT
		else:
			# "kih|istä" -> "kihajaa"
			return voikkoutils.VOWEL_BACK

def _vtype_meri_partitive(base):
	return voikkoutils.VOWEL_BACK

def _removeStructure(word):
	return word.replace(u"=", u"").replace(u"|", u"")

## Returns a list of InflectedWord objects for given word and inflection type.
def inflectWordWithType(word, inflection_type, infclass, gradclass, vowel_type = voikkoutils.VOWEL_DEFAULT):
	if not infclass in inflection_type.joukahainenClasses: return []
	word_no_sfx = inflection_type.removeSuffix(word)
	word_grad = __apply_gradation(word_no_sfx, gradclass)
	if word_grad == None: return []
	if gradclass == '-': grad_type = voikkoutils.GRAD_NONE
	elif gradclass in ['av1', 'av3', 'av5']: grad_type = voikkoutils.GRAD_SW
	elif gradclass in ['av2', 'av4', 'av6']: grad_type = voikkoutils.GRAD_WS
	if grad_type != voikkoutils.GRAD_NONE and grad_type != inflection_type.gradation: return []
	if not re.compile(__word_pattern_to_pcre(inflection_type.matchWord),
	                  re.IGNORECASE).match(word): return []
	inflection_list = []
	if vowel_type == voikkoutils.VOWEL_DEFAULT:
		vowel_type = voikkoutils.get_wordform_infl_vowel_type(word)
	for rule in inflection_type.inflectionRules:
		if rule.gradation == voikkoutils.GRAD_STRONG: word_base = word_grad[0]
		else: word_base = word_grad[1]
		hunspell_rules = __regex_to_hunspell(rule.delSuffix, rule.addSuffix)
		for hunspell_rule in hunspell_rules:
			if hunspell_rule[0] == '0': word_stripped_base = word_base
			else: word_stripped_base = word_base[:-len(hunspell_rule[0])]
			if hunspell_rule[1] == '0': affix = ''
			else: affix = hunspell_rule[1]
			if hunspell_rule[2] == '.': pattern = ''
			else: pattern = hunspell_rule[2]
			
			infl = InflectedWord()
			infl.formName = rule.name
			infl.isCharacteristic = rule.isCharacteristic
			infl.priority = rule.rulePriority
			
			vowel_harmony_rule = None
			if rule.name in DERIVS_VOWEL_HARMONY_SPECIAL_CLASS_1:
				vowel_harmony_rule = _vtype_special_class_1
			elif rule.name in DERIVS_VOWEL_HARMONY_SPECIAL_CLASS_2:
				vowel_harmony_rule = _vtype_special_class_2
			elif rule.name == u'partitiivi' and infclass == u'meri':
				vowel_harmony_rule = _vtype_meri_partitive
			final_base = _removeStructure(word_stripped_base)
			if vowel_harmony_rule != None:
				if vowel_harmony_rule(word_stripped_base) == voikkoutils.VOWEL_FRONT:
					infl.inflectedWord = final_base + __convert_tv_ev(affix)
				else:
					infl.inflectedWord = final_base + affix
				inflection_list.append(infl)
				continue
			
			if vowel_type in [voikkoutils.VOWEL_BACK, voikkoutils.VOWEL_BOTH] and \
			   word_base.endswith(pattern):
				infl.inflectedWord = _replace_conditional_aposthrope(
				                     final_base + affix)
				inflection_list.append(infl)
				infl = InflectedWord()
				infl.formName = rule.name
				infl.isCharacteristic = rule.isCharacteristic
				infl.priority = rule.rulePriority
			if vowel_type in [voikkoutils.VOWEL_FRONT, voikkoutils.VOWEL_BOTH] and \
			   word_base.endswith(__convert_tv_ev(pattern)):
				infl.inflectedWord = _replace_conditional_aposthrope(
				                     final_base + __convert_tv_ev(affix))
				inflection_list.append(infl)
	return inflection_list

## Returns a list of InflectedWord objects for given word.
def inflectWord(word, jo_infclass, inflection_types, vowel_type = voikkoutils.VOWEL_DEFAULT):
	dash = jo_infclass.find(u'-')
	if dash == -1:
		infclass = jo_infclass
		gradclass = u'-'
	else:
		infclass = jo_infclass[:dash]
		gradclass = jo_infclass[dash+1:]
		if not gradclass in [u'av1', u'av2', u'av3', u'av4', u'av5', u'av6', u'-']:
			return []
	
	for inflection_type in inflection_types:
		inflection = inflectWordWithType(word, inflection_type, infclass, gradclass, vowel_type)
		if len(inflection) > 0: return inflection
	return []

