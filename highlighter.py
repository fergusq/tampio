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

def highlightHtml(tl):
	out = ""
	for token, style in zip(tl.tokens, tl.styles):
		if style != "":
			out += "<span class=\"" + style + "\">" + html.escape(token.token) + "</span>"
		else:
			out += html.escape(token.token)
	return out

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
