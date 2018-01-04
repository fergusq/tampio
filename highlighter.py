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

import html, json

def prettyPrint(tokens, lang):
	return HIGHLIGHTERS[lang](tokens)

def markupSpan(token, code, span):
	a = "" if span[0] else code[0]
	a += token
	a += "" if span[1] else code[1]
	return a

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
		token, style, span, newline, inle = [x[i] for x in [tl.tokens, tl.styles, tl.style_spans, tl.newlines, tl.indent_levels]]
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
			out += markup(style, span, token.token)
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

def eatNonwords(i, out, tl, eat_comments, eat_spaces=True):
	# välimerkit kuuluvat aina listan edellisen elementin loppuun, eivät uuden alkuun
	j = i
	while (j < len(tl.tokens) and not tl.tokens[j].isWord() and not tl.tokens[j].isString()
		and (eat_comments or not tl.tokens[j].isComment())
		and (eat_spaces or not tl.tokens[j].isSpace())):
		out += html.escape(tl.tokens[j].token)
		j += 1
	return j-i, out

def highlightHtml(tl, pre=False):
	return highlight(tl, pre,
		pre_begin="",
		pre_end="",
		document_begin="<ul class=\"syntax-root\">",
		document_end="</ul>",
		document_item_begin="<li>",
		document_item_end="</li>",
		list_begin="<ul>",
		list_end="</ul>",
		item_begin="<li>",
		item_end="</li>",
		markup=htmlMarkup)

def htmlMarkup(style, span, token):
	if style == "":
		return html.escape(token)
	style_span = "<span class=\"" + style + "\">"
	if style == "block-comment-global":
		paragraphs = token.split("\n\n")
		return "\n".join(["<p>" + style_span + html.escape(paragraph) + "</span></p>" for paragraph in paragraphs])
	else:
		return markupSpan(html.escape(token), (style_span, "</span>"), span)

def highlightLatex(tl, use_lists=False):
	return highlight(tl, not use_lists,
		pre_begin="",
		pre_end="",
		document_begin="\\setlength{\\parskip}{5pt}",
		document_end="",
		document_item_begin="\n\\noindent",
		document_item_end="\n",
		list_begin="\\begin{itemize}",
		list_end="\\end{itemize}",
		item_begin="\\item ",
		item_end="",
		markup=latexMarkup)

def latexMarkup(style, span, token):
	if style == "comment-global":
		token = token[1:] # poistetaan risuaita edestä
	if style in LATEX_STYLES:
		return markupSpan(escapeLatex(token), (LATEX_STYLES[style] + "{", "}"), span)
	elif style == "block-comment-global":
		paragraphs = token.split("\n\n")
		return "\n\n".join(["\\emph{" + escapeLatex(paragraph) + "}" for paragraph in paragraphs])
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
		.replace("{", "\\{")
		.replace("}", "\\}")
		.replace("\\", "\\textbackslash{}")
		.replace("^", "\\textasciicircum{}")
		.replace("~", "\\textasciitilde{}")
		.replace("&", "\\&")
		.replace("%", "\\%")
		.replace("#", "\\#")
		.replace("_", "\\_")
		.replace("\"", "''"))

def highlightIndent(tl, nl, indent, item_start, global_sep, markup):
	out = ""
	prev_inle = 0
	next_is_newline = False
	prev_is_space = False
	skip = 0
	i = 0
	while i < len(tl.tokens):
		token, style, span, newline, inle = [x[i] for x in [tl.tokens, tl.styles, tl.style_spans, tl.newlines, tl.indent_levels]]
		# sisennys muuttuu
		if inle != prev_inle:
			if skip == 0:
				skip, out = eatNonwords(i, out, tl, inle > 0, False)
			if not next_is_newline:
				out += nl
				prev_is_space = True
		
		# jos uusi rivi alkaa
		if next_is_newline or inle != prev_inle:
			out += indent*inle
			prev_is_space = True
			if inle > 0:
				out += item_start
			else:
				out += global_sep
		
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
			if token.isSpace() and not token.isComment():
				if not prev_is_space: out += " "
				prev_is_space = True
			else:
				out += markup(style, span, token.token)
				prev_is_space = False
		else:
			skip -= 1
		
		i += 1
		
		# rivinvaihto
		if newline:
			if skip == 0:
				skip, out = eatNonwords(i, out, tl, inle > 0, False)
			
			out += nl
			prev_is_space = True
		
		prev_inle = inle
		next_is_newline = newline
	return out

def highlightMarkdown(tl):
	out = ""
	for style, span, token in zip(tl.styles, tl.style_spans, tl.tokens):
		out += markupMarkdown(style, span, token.token)
	return out

def highlightMarkdownIndent(tl):
	return highlightIndent(tl, "\n", "  ", "- ", "\n", markupMarkdown)

def markupMarkdown(s, c, t):
	code = MARKDOWN_STYLES.get(s, "")
	return markupSpan(t, (code, code), c)

MARKDOWN_STYLES = {
	"keyword": "**",
	"function": "_",
	"literal": "`"
}

def highlightTxt(tl):
	return highlightIndent(tl, "\n", "    ", "", "", lambda s,c,t: t)

def highlightTxtWithKeywords(tl):
	return highlightIndent(tl, "\n", "    ", "", "", lambda s,c,t: t.upper() if s == "keyword" else t)

def highlightJson(tl):
	tokens = []
	line = 1
	column = 1
	for style, token in zip(tl.styles, tl.tokens):
		new_line = line + token.token.count("\n")
		if line != new_line:
			new_column = len(token.token.split("\n")[-1])+1
		else:
			new_column = column + len(token.token)
		tokens.append({"token": token.token, "style": style, "startLine": line, "startColumn": column, "endLine": new_line, "endColumn": new_column})
		line = new_line
		column = new_column
	return json.dumps({"tokens": tokens})

HIGHLIGHTERS = {
	"html": highlightHtml,
	"html-pre": lambda tl: highlightHtml(tl, pre=True),
	"markdown": highlightMarkdown,
	"markdown-lists": highlightMarkdownIndent,
	"latex": highlightLatex,
	"latex-lists": lambda tl: highlightLatex(tl, use_lists=True),
	"txt": highlightTxt,
	"txt-kwuc": highlightTxtWithKeywords,
	"json": highlightJson
}
