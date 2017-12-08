# Tampio Interpreter
# Copyright (C) 2017 Iikka Hauhio

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import re
from voikko.inflect_word import inflect_word

CASES_LATIN = {
	"nimento": "nominatiivi",
	"omanto": "genetiivi",
	"osanto": "partitiivi",
	"olento": "essiivi",
	"tulento": "translatiivi",
	"ulkotulento": "allatiivi",
	"ulkoolento": "adessiivi",
	"ulkoeronto": "ablatiivi",
	"sisatulento": "illatiivi",
	"sisaolento": "inessiivi",
	"sisaeronto": "elatiivi",
	"vajanto": "abessiivi",
	"keinonto": "instruktiivi",
	"seuranto": "komitatiivi",
	"kerrontosti": "adverbi"
}

CASES_ENGLISH = {
	"nimento": "nominative",
	"omanto": "genitive",
	"osanto": "partitive",
	"olento": "essive",
	"tulento": "translative",
	"ulkotulento": "allative",
	"ulkoolento": "adessive",
	"ulkoeronto": "ablative",
	"sisatulento": "illative",
	"sisaolento": "inessive",
	"sisaeronto": "elative",
	"vajanto": "abessive",
	"keinonto": "instructive",
	"seuranto": "comitative",
	"kerrontosti": "adverb"
}

CASES_ABRV = {
	"": "*",
	"nimento": "N",
	"omanto": "G",
	"osanto": "P",
	"olento": "E",
	"tulento": "T",
	"ulkotulento": "Ut",
	"ulkoolento": "Uo",
	"ulkoeronto": "Ue",
	"sisatulento": "St",
	"sisaolento": "So",
	"sisaeronto": "Se",
	"vajanto": "A",
	"keinonto": "I",
	"seuranto": "K",
	"kerrontosti": "D"
}

CASES_A = {
	"nimento": "",
	"omanto": ":n",
	"osanto": ":ta",
	"olento": ":na",
	"tulento": ":ksi",
	"ulkotulento": ":lle",
	"ulkoolento": ":lla",
	"ulkoeronto": ":lta",
	"sisatulento": ":han",
	"sisaolento": ":ssa",
	"sisaeronto": ":sta",
	"vajanto": ":tta",
	"keinonto": ":in",
	"seuranto": ":ineen",
	"kerrontosti": ":sti"
}

CASES_F = {
	"nimento": "",
	"omanto": ":n",
	"osanto": ":ää",
	"olento": ":nä",
	"tulento": ":ksi",
	"ulkotulento": ":lle",
	"ulkoolento": ":llä",
	"ulkoeronto": ":ltä",
	"sisatulento": ":ään",
	"sisaolento": ":ssä",
	"sisaeronto": ":stä",
	"vajanto": ":ttä",
	"keinonto": ":in",
	"seuranto": ":ineen",
	"kerrontosti": ":sti"
}

CASES_ELLIPSI = {
	"nimento": "",
	"omanto": ":n",
	"osanto": ":ä",
	"olento": ":nä",
	"tulento": ":ksi",
	"ulkotulento": ":lle",
	"ulkoolento": ":llä",
	"ulkoeronto": ":ltä",
	"sisatulento": ":iin",
	"sisaolento": ":ssä",
	"sisaeronto": ":stä",
	"vajanto": ":ttä",
	"keinonto": ":ein",
	"seuranto": ":eineen",
	"kerrontosti": ":sti"
}

CASE_REGEXES = {
	"singular": {
		"omanto": r"[^:]+:n",
		"osanto": r"[^:]+:(aa?|ää?|t[aä])",
		"olento": r"[^:]+:(n[aä])",
		"tulento": r"[^:]+:ksi",
		"ulkotulento": r"[^:]+:lle",
		"ulkoolento": r"[^:]+:ll[aä]",
		"ulkoeronto": r"[^:]+:lt[aä]",
		"sisatulento": r"[^:]+:(aan|ään|h[aeiouyäöå]n)",
		"sisaolento": r"[^:]+:ss[aä]",
		"sisaeronto": r"[^:]+:st[aä]",
		"vajanto": r"[^:]+:tt[aä]"
	},
	"plural": {
		"omanto": r"[^:]+:ien",
		"osanto": r"[^:]+:(ia?|iä?|it[aä])",
		"olento": r"[^:]+:(in[aä])",
		"tulento": r"[^:]+:iksi",
		"ulkotulento": r"[^:]+:ille",
		"ulkoolento": r"[^:]+:ill[aä]",
		"ulkoeronto": r"[^:]+:ilt[aä]",
		"sisatulento": r"[^:]+:(iin|ih[aeiouyäöå]n)",
		"sisaolento": r"[^:]+:iss[aä]",
		"sisaeronto": r"[^:]+:ist[aä]",
		"vajanto": r"[^:]+:itt[aä]",
		"keinonto": r"[^:]+:in",
		"seuranto": r"[^:]+:ine[^:]*"
	},
	"": {
		"kerrontosti": "[^:]+:sti"
	}
}

def inflect(word, case, plural):
	case_latin = CASES_LATIN[case]
	if plural:
		case_latin += "_mon"
	
	if re.fullmatch(r"[0-9]+", word):
		if case == "sisatulento":
			if word[-1] in "123560":
				return word + ":een"
			elif word[-1] in "479":
				return word + ":ään"
			else: # 8
				return word + ":aan"
		elif word[-1] in "14579":
			return word + CASES_A[case].replace("a", "ä")
		else:
			return word + CASES_A[case]
	elif len(word) == 1:
		if word in "flmnrsx":
			return word + CASES_F[case]
		elif case == "sisatulento":
			if word in "aeiouyäöå":
				return word + ":h" + word + "n"
			elif word in "bcdgptvw":
				return word + ":hen"
			elif word in "hk":
				return word + ":hon"
			elif word == "j":
				return "j:hin"
			elif word == "q":
				return "q:hun"
			elif word == "z":
				return "z:aan"
		elif word in "ahkoquzå":
			return word + CASES_A[case]
		else:
			return word + CASES_A[case].replace("a", "ä")
	else:
		inflections = inflect_word(word)
		if case_latin not in inflections:
			return word + ":" + case
		return inflections[case_latin]
