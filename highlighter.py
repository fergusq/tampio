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

import html

def prettyPrint(tokens, lang):
	return HIGHLIGHTERS[lang](tokens)

def highlightHtml(tl, pre=False):
	out = ""
	if pre:
		out += "<pre>"
	else:
		out += "<ul class=\"syntax-root\"><li>"
	prev_inle = 0
	next_is_newline = False
	skip = 0
	i = 0
	while i < len(tl.tokens):
		token, style, newline, inle = [x[i] for x in [tl.tokens, tl.styles, tl.newlines, tl.indent_levels]]
		# sisennys toteutetaan listana
		if not pre and inle < prev_inle:
			if skip == 0:
				skip, out = eatNonwords(i, out, tl, inle > 0)
			if not next_is_newline:
				out += "</li>"
			out += "</ul>"*(prev_inle-inle)
		
		# jos uusi rivi alkaa
		if not pre and next_is_newline:
			out += "<li>"
		
		# jos uusi sisennys alkaa
		if not pre and inle > prev_inle:
			out += "<ul><li>"*(inle-prev_inle)
		
		# tulostetaan token
		if skip == 0:
			if style != "":
				out += "<span class=\"" + style + "\">" + html.escape(token.token) + "</span>"
			elif token.isComment():
				out += "<span class=\"comment\">" + html.escape(token.token) + "</span>"
			else:
				out += html.escape(token.token)
		else:
			skip -= 1
		
		if token.isComment() and inle == 0:
			newline = True
		
		i += 1
		
		# rivinvaihto toteutetaan uutena alkiona listassa
		if not pre and newline:
			if skip == 0:
				skip, out = eatNonwords(i, out, tl, inle > 0)
			
			out += "</li>"
		
		prev_inle = inle
		next_is_newline = newline
	
	if pre:
		out += "</pre>"
	else:
		out += "</li></ul>"
	return out

def eatNonwords(i, out, tl, eat_comments):
	# välimerkit kuuluvat aina listan edellisen elementin loppuun, eivät uuden alkuun
	j = i
	while j < len(tl.tokens) and not tl.tokens[j].isWord() and not tl.tokens[j].isString() and (eat_comments or not tl.tokens[j].isComment()):
		out += html.escape(tl.tokens[j].token)
		j += 1
	return j-i, out

def highlightMarkdown(tl):
	out = ""
	for token, style in zip(tl.tokens, tl.styles):
		code = MARKDOWN_STYLES.get(style, "")
		out += code + token.token + code
	return out

MARKDOWN_STYLES = {
	"keyword": "**",
	"function": "_",
	"literal": "`"
}

HIGHLIGHTERS = {
	"html": highlightHtml,
	"markdown": highlightMarkdown
}
