# -*- coding: utf-8 -*-

# Copyright 2017 Iikka Hauhio
# Contains some minor changes to the original file.

# Copyright 2007 - 2012 Harri Pitkänen (hatapitk@iki.fi)

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

# This module contains general helper functions and classes for use
# with Python and Voikko.

import codecs
import os
import locale
import sys
import xml.dom.minidom
import gzip

# Word classes
NOUN=1
ADJECTIVE=2
VERB=3

# Vowel types
VOWEL_DEFAULT=0
VOWEL_FRONT=1
VOWEL_BACK=2
VOWEL_BOTH=3

# Gradation types
GRAD_NONE = 0
GRAD_SW = 1
GRAD_WS = 2

GRAD_WEAK = 3
GRAD_STRONG = 4

class FlagAttribute:
	"Vocabulary flag attribute"
	joukahainen = 0
	xmlGroup = None
	xmlFlag = None
	malagaFlag = None
	description = None

## Remove comments from a given line of text.
def removeComments(line):
	comment_start = line.find(u'#')
	if comment_start == -1:
		return line
	if comment_start == 0:
		return u''
	return line[:comment_start]

def readFlagAttributes(filename):
	"""Returns a map of flag attributes from given file. The keys in the
	map are in form xmlGroup/xmlFlag, such as 'compounding/ei_ys'."""
	inputfile = codecs.open(filename, 'r', 'UTF-8')
	flags = {}
	fileCont = True
	while fileCont:
		line = inputfile.readline()
		fileCont = line.endswith('\n')
		line = removeComments(line).strip()
		if len(line) > 0:
			f = FlagAttribute()
			endind = line.find(u' ')
			f.joukahainen = int(line[:endind])
			line = line[endind:].strip()
			endind = line.find(u'/')
			f.xmlGroup = line[:endind]
			line = line[endind + 1:]
			endind = line.find(u' ')
			f.xmlFlag = line[:endind]
			line = line[endind:].strip()
			endind = line.find(u' ')
			if line[:endind] != u'-': f.malagaFlag = line[:endind]
			line = line[endind:].strip()
			if len(line) > 0: f.description = line
			flags[f.xmlGroup + u'/' + f.xmlFlag] = f
	inputfile.close()
	return flags

## Function that returns the type of vowels that are allowed in the suffixes for
# given simple word.
# The possible values are VOWEL_FRONT, VOWEL_BACK and VOWEL_BOTH.
def _simple_vowel_type(word):
	word = word.lower()
	last_back = max(word.rfind(u'a'), word.rfind(u'o'), word.rfind(u'å'), word.rfind(u'u'))
	last_ord_front = max(word.rfind(u'ä'), word.rfind(u'ö'))
	last_y = word.rfind(u'y')
	if last_back > -1 and max(last_ord_front, last_y) == -1:
		return VOWEL_BACK
	if last_back == -1 and max(last_ord_front, last_y) > -1:
		return VOWEL_FRONT
	if max(last_back, last_ord_front, last_y) == -1:
		return VOWEL_FRONT
	if last_y < max(last_back, last_ord_front):
		if last_back > last_ord_front: return VOWEL_BACK
		else: return VOWEL_FRONT
	else:
		return VOWEL_BOTH

## Returns autodetected vowel type of infection suffixes for a word.
# If word contains character '=', automatic detection is only performed on the
# trailing part. If word contains character '|', automatic detection is performed
# on the trailing part and the whole word, and the union of accepted vowel types is returned.
def get_wordform_infl_vowel_type(wordform):
	# Search for last '=' or '-', check the trailing part using recursion
	startind = max(wordform.rfind(u'='), wordform.rfind(u'-'))
	if startind == len(wordform) - 1: return VOWEL_BOTH # Not allowed
	if startind != -1: return get_wordform_infl_vowel_type(wordform[startind+1:])
	
	# Search for first '|', check the trailing part using recursion
	startind = wordform.find(u'|')
	if startind == len(wordform) - 1: return VOWEL_BOTH # Not allowed
	vtype_whole = _simple_vowel_type(wordform)
	if startind == -1: return vtype_whole
	vtype_part = get_wordform_infl_vowel_type(wordform[startind+1:])
	if vtype_whole == vtype_part: return vtype_whole
	else: return VOWEL_BOTH

## Returns True, if given character is a consonant, otherwise retuns False.
def is_consonant(letter):
	if letter.lower() in u'qwrtpsdfghjklzxcvbnm':
		return True
	else:
		return False

## Function that returns the type of vowels that are allowed in the affixes for given word.
# The possible values are VOWEL_FRONT, VOWEL_BACK and VOWEL_BOTH.
def vowel_type(word):
	word = word.lower()
	last_back = max(word.rfind(u'a'), word.rfind(u'o'), word.rfind(u'å'), word.rfind(u'u'))
	last_ord_front = max(word.rfind(u'ä'), word.rfind(u'ö'))
	last_y = word.rfind(u'y')
	if last_back > -1 and max(last_ord_front, last_y) == -1:
		return VOWEL_BACK
	if last_back == -1 and max(last_ord_front, last_y) > -1:
		return VOWEL_FRONT
	if max(last_back, last_ord_front, last_y) == -1:
		return VOWEL_FRONT
	if last_y < max(last_back, last_ord_front):
		if last_back > last_ord_front: return VOWEL_BACK
		else: return VOWEL_FRONT
	else:
		return VOWEL_BOTH


## Expands capital letters to useful character classes for regular expressions
def capital_char_regexp(pattern):
	pattern = pattern.replace('V', u'(?:a|e|i|o|u|y|ä|ö|é|è|á|ó|â)')
	pattern = pattern.replace('C', u'(?:b|c|d|f|g|h|j|k|l|m|n|p|q|r|s|t|v|w|x|z|š|ž)')
	pattern = pattern.replace('A', u'(?:a|ä)')
	pattern = pattern.replace('O', u'(?:o|ö)')
	pattern = pattern.replace('U', u'(?:u|y)')
	return pattern

## Reads the word list in XML format specified by filename. If the name ends
# with .gz, the file is assumed to be gzip compressed. Calls function word_handler
# for each word, passing a XML Document object representing the word as a parameter.
# If show_progress == True, prints progess information to stdout
def process_wordlist(filename, word_handler, show_progress = False):
	if filename.endswith(".gz"):
		listfile = gzip.GzipFile(filename, 'r')
	else:
		listfile = open(filename, 'r', encoding="UTF-8")
	line = ""
	while line != '<wordlist xml:lang="fi">\n':
		line = listfile.readline()
		if line == '':
			sys.stderr.write("Malformed file " + filename + "\n")
			return
	
	wcount = 0
	while True:
		wordstr = ""
		line = listfile.readline()
		if line == "</wordlist>\n": break
		while line != '</word>\n':
			wordstr = wordstr + line
			line = listfile.readline()
		word = xml.dom.minidom.parseString(wordstr + line)
		word_handler(word.documentElement)
		wcount = wcount + 1
		if show_progress and wcount % 1000 == 0:
			sys.stdout.write("#")
			sys.stdout.flush()
	
	if show_progress: sys.stdout.write("\n")
	listfile.close()

