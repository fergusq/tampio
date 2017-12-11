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

import pygame
from tampio import compileCode

WIDTH = 1600
HEIGHT = 800

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

FONT_SIZE = 20

FONTS = {}

default_font = pygame.font.SysFont("liberationserif", FONT_SIZE)
italic_font = pygame.font.SysFont("liberationserif", FONT_SIZE)
italic_font.set_italic(True)
bold_font = pygame.font.SysFont("liberationserif", FONT_SIZE)
bold_font.set_bold(True)
underline_font = pygame.font.SysFont("liberationserif", FONT_SIZE)
underline_font.set_underline(True)
FONTS["default"] = default_font
FONTS["small-caps"] = default_font
FONTS["italic"] = italic_font
FONTS["bold"] = bold_font
FONTS["underline"] = underline_font

STYLES = {
	"": "default",
	"function": "italic",
	"keyword": "bold",
	"field": "underline",
	"variable": "small-caps",
	"type": "small-caps"
}

def make_tokens(code):
	tl, _ = compileCode(code)
	tokens = []
	line = []
	for token, style in zip(tl.tokens, tl.styles):
		for char in list(token.token):
			if char == "\n":
				tokens.append(line)
				line = []
			else:
				line.append((char, style))
	tokens.append(line)
	return tokens

def make_texts(tokens):
	texts = []
	for char, style in tokens:
		font = FONTS[STYLES.get(style, "default")]
		if STYLES.get(style, "default") == "small-caps":
			image = font.render(char.upper(), True, (0, 0, 0))
			if char != char.upper():
				new_image = pygame.Surface((image.get_width(), image.get_height()), pygame.SRCALPHA)
				new_image.blit(pygame.transform.scale(image, (image.get_width(), int(0.9*image.get_height()))), (0, int(0.1*image.get_height())))
				image = new_image
		else:
			image = font.render(char, True, (0, 0, 0))
		texts.append((char, style, image))
	return texts

with open("examples/vektori.itp") as f:
	code = f.read()

tokens = make_tokens(code)
image_lines = [make_texts(l) for l in tokens]

cursor_x = 0
cursor_y = 0

scroll = 0

def fix_scroll():
	global scroll
	if 1.5*FONT_SIZE*(cursor_y-scroll-2) > HEIGHT*0.9:
		scroll += 1
	if cursor_y-scroll < 0:
		scroll -= 1

keys_down = []
key_timer = {}
tick = 0
done = False
while not done:
	tick = (tick + 1) % 80
	line = tokens[cursor_y]
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			done = True
		if event.type == pygame.KEYDOWN:
			keys_down.append(event.key)
			key_timer[event.key] = 0
		elif event.type == pygame.KEYUP:
			keys_down.remove(event.key)
	
	for key in keys_down:
		key_timer[key] += 1
		if 1 < key_timer[key] < 20:
			continue
		if cursor_x > 0 and key == pygame.K_LEFT:
			cursor_x -= 1
		elif cursor_x == 0 and cursor_y > 0 and key == pygame.K_LEFT:
			cursor_y -= 1
			line = tokens[cursor_y]
			cursor_x = len(line)
		elif cursor_x < len(line) and key == pygame.K_RIGHT:
			cursor_x += 1
		elif cursor_x == len(line) and cursor_y < len(tokens)-1 and key == pygame.K_RIGHT:
			cursor_x = 0
			cursor_y += 1
			line = tokens[cursor_y]
		
		elif cursor_y > 0 and key == pygame.K_UP:
			cursor_y -= 1
			line = tokens[cursor_y]
			if cursor_x > len(line):
				cursor_x = len(line)
		elif cursor_y < len(tokens)-1 and key == pygame.K_DOWN:
			cursor_y += 1
			line = tokens[cursor_y]
			if cursor_x > len(line):
				cursor_x = len(line)
		elif cursor_x > 0 and key == pygame.K_BACKSPACE:
			del line[cursor_x-1]
			cursor_x -= 1
		elif cursor_x == 0 and cursor_y > 0 and key == pygame.K_BACKSPACE:
			cursor_x = len(tokens[cursor_y-1])
			tokens[cursor_y-1] += tokens[cursor_y]
			del tokens[cursor_y]
			cursor_y -= 1
			lins = tokens[cursor_y]
			
		elif key == pygame.K_RETURN:
			new_line = line[cursor_x:]
			del line[cursor_x:]
			tokens.insert(cursor_y+1, new_line)
			cursor_y += 1
			cursor_x = 0
		elif key in list(range(ord("a"), ord("z")+1)) + [ord(c) for c in list("åäö.,- \t")]:
			char = chr(key)
			if pygame.K_LSHIFT in keys_down or pygame.K_RSHIFT in keys_down:
				char = char.upper()
			line.insert(cursor_x, (char, ""))
			cursor_x += 1
		image_lines = [make_texts(l) for l in tokens]
		fix_scroll()
	
	if tick%30 == 0:
		tokens = make_tokens("\n".join(["".join([c[0] for c in l]) for l in tokens]))
		image_lines = [make_texts(l) for l in tokens]
	
	screen.fill((255, 255, 255))
	y = 0
	for j, image_line in list(enumerate(image_lines))[scroll:]:
		i = 0
		x = 0
		for token, style, image in image_line:
			if x+5+FONT_SIZE > WIDTH:
				y += int(FONT_SIZE*1.5)
				x = 0
			if i == cursor_x and j == cursor_y:
				pygame.draw.line(screen, (0,0,0), [5+x, 5+y], [5+x,5+y+FONT_SIZE], 1)
			if token == " ":
				x += FONT_SIZE//2
			elif token == "\t":
				x += FONT_SIZE*4
				x -= x%(FONT_SIZE*4)
			else:
				screen.blit(image, (5+x, 5+y))
				x += image.get_width()
				if STYLES.get(style, "default") == "italic":
					x -= int(image.get_width()*0.2)
			i += 1
		if i == cursor_x and j == cursor_y:
			pygame.draw.line(screen, (0,0,0), [5+x, 5+y], [5+x,5+y+FONT_SIZE], 1)
		y += int(FONT_SIZE*1.5)
	
	pygame.display.flip()
	clock.tick(60)
