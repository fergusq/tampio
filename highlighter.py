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

def highlight(tl, pre,
	pre_begin, pre_end,
	document_begin, document_end,
	document_item_begin, document_item_end,
	list_begin, list_end,
	item_begin, item_end,
	markup):
	out = ""
	if pre:
		out += pre_begin
	else:
		out += document_begin + document_item_begin
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
				out += item_end
			out += list_end*(prev_inle-inle)
		
		# jos uusi rivi alkaa
		if not pre and next_is_newline:
			if inle == 0:
				out += document_item_begin
			else:
				out += item_begin
		
		# jos uusi sisennys alkaa
		if not pre and inle > prev_inle:
			out += (list_begin+item_begin)*(inle-prev_inle)
		
		# kommenttien tyylit
		if token.isComment():
			if i == 0 or "\n" in tl.tokens[i-1].token:
				style = "comment-global"
				newline = True
			else:
				style = "comment-inline"
			if token.token[0] != "#":
				style = "block-" + style
		
		# tulostetaan token
		if skip == 0:
			out += markup(style, token.token)
		else:
			skip -= 1
		
		i += 1
		
		# rivinvaihto toteutetaan uutena alkiona listassa
		if not pre and newline:
			if skip == 0:
				skip, out = eatNonwords(i, out, tl, inle > 0)
			
			if inle == 0:
				out += document_item_end
			else:
				out += item_end
		
		prev_inle = inle
		next_is_newline = newline
	
	if pre:
		out += pre_end
	else:
		out += document_item_end + document_end
	return out

def eatNonwords(i, out, tl, eat_comments):
	# välimerkit kuuluvat aina listan edellisen elementin loppuun, eivät uuden alkuun
	j = i
	while j < len(tl.tokens) and not tl.tokens[j].isWord() and not tl.tokens[j].isString() and (eat_comments or not tl.tokens[j].isComment()):
		out += html.escape(tl.tokens[j].token)
		j += 1
	return j-i, out

def highlightHtml(tl, pre=False):
	return highlight(tl, pre,
		pre_begin="<pre>",
		pre_end="</pre>",
		document_begin="<ul class=\"syntax-root\">",
		document_end="</ul>",
		document_item_begin="<li>",
		document_item_end="</li>",
		list_begin="<ul>",
		list_end="</ul>",
		item_begin="<li>",
		item_end="</li>",
		markup=lambda s,t: "<span class=\"" + s + "\">" + html.escape(t) + "</span>" if s != "" else html.escape(t))

def highlightLatex(tl, use_lists=False):
	return highlight(tl, use_lists,
		pre_begin="",
		pre_end="",
		document_begin="\\setlength{\\parskip}{5pt}",
		document_end="",
		document_item_begin="\n",
		document_item_end="\n\\noindent",
		list_begin="\\begin{itemize}",
		list_end="\\end{itemize}",
		item_begin="\\item ",
		item_end="",
		markup=latexMarkup)

def latexMarkup(style, token):
	if style == "comment-global":
		token = token[1:] # poistetaan risuaita edestä
	if style in LATEX_STYLES:
		return LATEX_STYLES[style] + "{" + escapeLatex(token) + "}"
	else:
		return escapeLatex(token)

LATEX_STYLES = {
	"keyword": "\\textbf",
	"function": "\\emph",
	"variable": "\\textsc",
	"type": "\\textsc",
	"comment-global": "\\section",
	"comment-inline": "\\footnote",
	"block-comment-inline": "\\footnote"
}

def escapeLatex(token):
	return (token
		.replace("\\", "\\textbackslash")
		.replace("^", "\\textasciicircum")
		.replace("~", "\\textasciitilde")
		.replace("&", "\\&")
		.replace("%", "\\%")
		.replace("#", "\\#")
		.replace("_", "\\_")
		.replace("{", "\\{")
		.replace("}", "\\}")
		.replace("\"", "''"))

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
	"html-pre": lambda tl: highlightHtml(tl, pre=True),
	"markdown": highlightMarkdown,
	"latex": highlightLatex
}
