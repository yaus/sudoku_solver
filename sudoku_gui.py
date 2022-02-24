import itertools
import math
import string
import sys
from copy import copy

import pygame
import numpy as np
from pygame.locals import QUIT

import sudoku


class named_dict(dict):
    def __getattr__(self, item):
        if item in self:
            return self[item]

    def __setattr__(self, key, value):
        if key in self:
            self[key] = value


k = {pygame.K_0: 0, pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3, pygame.K_4: 4, pygame.K_5: 5, pygame.K_6: 6,
     pygame.K_7: 7, pygame.K_8: 8, pygame.K_9: 9, pygame.K_KP0: 0, pygame.K_KP1: 1, pygame.K_KP2: 2, pygame.K_KP3: 3,
     pygame.K_KP4: 4, pygame.K_KP5: 5, pygame.K_KP6: 6, pygame.K_KP7: 7, pygame.K_KP8: 8, pygame.K_KP9: 9}


class sudoku_game:
    def __init__(self, dimension: int = 800, offset: int = 20, number: int = 9):
        self.dimension = dimension
        self.offset = offset
        self.number = number
        self.selected = True
        self.select_pos = [0, 1]
        self.segment = int(math.sqrt(number))
        from argparse import Namespace

        self.color = named_dict(
            background=pygame.Color(255, 255, 255),
            selected=pygame.Color(0xC7, 0x20, 0x5D),
            frame=pygame.Color(0, 0, 0),
            lineframe=pygame.Color(64, 64, 64),
            text=pygame.Color(0, 0, 0),
            selected_text=pygame.Color(255, 255, 255),
            guess_text=pygame.Color(0xDE, 0x36, 0x9D),
            pos_text=pygame.Color(216, 216, 216)
        )
        self.status = [["" for _ in range(number)] for _ in range(number)]
        self.result = [[0 for _ in range(number)] for _ in range(number)]
        self.lock = False
        self._sudoku = sudoku.sudoku(number)
        self.cap_mode = False
        pass

    def setup(self):
        pygame.init()
        self.game_surface = pygame.display.set_mode((self.dimension, self.dimension))
        pygame.display.set_caption("sudoku_solver")
        self.game_surface.fill(self.color.background)
        self._font_cache = pygame.font.Font(None, int(self.dimension / self.number))
        self._sfont_cache = pygame.font.Font(None, int(self.dimension / self.number / self.segment))

        # get font center of h
        self._h = self._font_cache.render("0123456789", True, self.color.text).get_height() / 2
        self._sh = self._sfont_cache.render("0123456789", True, self.color.text).get_height() / 2
        self.cap_mode = False

    def run(self):
        self.text_lock = False
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not self.lock:
                        self.selected = not self.selected
                        self.text_lock = False
                    if event.key == pygame.K_CAPSLOCK:
                        self.cap_mode = not self.cap_mode
                    if self.selected:
                        x, y = self.select_pos
                        if event.key == pygame.K_UP:
                            if self.select_pos[1] > 0:
                                self.select_pos[1] -= 1
                                self.text_lock = False
                        elif event.key == pygame.K_DOWN:
                            if self.select_pos[1] < self.number - 1:
                                self.select_pos[1] += 1
                                self.text_lock = False
                        elif event.key == pygame.K_LEFT:
                            if self.select_pos[0] > 0:
                                self.select_pos[0] -= 1
                                self.text_lock = False
                        elif event.key == pygame.K_RIGHT:
                            if self.select_pos[0] < self.number - 1:
                                self.select_pos[0] += 1
                                self.text_lock = False
                        elif event.key == pygame.K_TAB:
                            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                                if self.select_pos[0] > 0:
                                    self.select_pos[0] -= 1
                                    self.text_lock = False
                                elif self.select_pos[1] > 0:
                                    self.select_pos[1] -= 1
                                    self.select_pos[0] = self.number - 1
                                    self.text_lock = False
                                else:
                                    self.select_pos[1] = self.number - 1
                                    self.select_pos[0] = self.number - 1
                            else:
                                if self.select_pos[0] < self.number - 1:
                                    self.select_pos[0] += 1
                                    self.text_lock = False
                                elif self.select_pos[1] < self.number - 1:
                                    self.select_pos[1] += 1
                                    self.select_pos[0] = 0
                                    self.text_lock = False
                                else:
                                    self.select_pos[1] = 0
                                    self.select_pos[0] = 0
                        elif event.key in k:
                            # print(event.key)
                            if event.key in [0, ' '] and not self.text_lock:
                                self.status[y][x] = ""
                            else:
                                # test if valid
                                test_text = self.status[y][x] + str(k[event.key])
                                if int(test_text) > self.number:
                                    test_text = str(k[event.key])
                                    if int(test_text) > self.number:
                                        continue
                                self.status[y][x] = str(int(test_text)) if int(test_text) != 0 else ""
                            self.text_lock = True
                        elif event.key == pygame.K_BACKSPACE:
                            self.status[y][x] = self.status[y][x][:-1]
                    else:
                        if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                            self.lock = True
                            self.process()
                    if event.key == pygame.K_ESCAPE:
                        self.status = [["" for _ in range(self.number)] for _ in range(self.number)]
                        self.result = [[0 for _ in range(self.number)] for _ in range(self.number)]
                    if event.key == pygame.K_DELETE and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        self.result = [[0 for _ in range(self.number)] for _ in range(self.number)]
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    sx, sy = self.select_pos
                    point_pos = list(np.linspace(self.offset, self.dimension - self.offset, self.number + 1))
                    for idx, a in enumerate(zip(point_pos[:-1], point_pos[1:])):
                        a0, a1 = a
                        if a0 + 1 < x < a1 - 1:
                            sx = idx

                    for idx, a in enumerate(zip(point_pos[:-1], point_pos[1:])):
                        a0, a1 = a
                        if a0 + 1 < y < a1 - 1:
                            self.selected = True
                            sy = idx
                    if pygame.mouse.get_pressed()[0]:
                        self.selected = True
                        self.select_pos = [sx, sy]
                    else:
                        self.selected = True
                        self.select_pos = [sx, sy]
                        self.status[sy][sx] = ""
            self._update(self.cap_mode)

    def _update(self, cap_mod=False):
        self.game_surface.fill(self.color.background)
        point_idx = list(range(self.number + 1))
        point_pos = list(np.linspace(self.offset, self.dimension - self.offset, len(point_idx)))

        # draw_selection
        if self.selected:
            x, y = self.select_pos
            pygame.draw.rect(self.game_surface, self.color.selected,
                             ((point_pos[x], point_pos[y]),
                              (point_pos[x + 1] - point_pos[x], point_pos[y + 1] - point_pos[y])))

        # draw frame

        a = [0, -1]
        outer_frame = [(point_pos[0], point_pos[0]), (point_pos[-1], point_pos[0]), (point_pos[-1], point_pos[-1]),
                       (point_pos[0], point_pos[-1])]
        # print(outer_frame)
        pygame.draw.lines(self.game_surface, self.color.frame, True, outer_frame, width=2)

        # draw subframe
        point_pos_sub = [point_pos[i] for i in range(0, len(point_pos), self.segment)][1:-1]

        sub_frame_line = [*[((point_pos[0], x), (point_pos[-1], x)) for x in point_pos_sub],
                          *[((x, point_pos[0]), (x, point_pos[-1])) for x in point_pos_sub]]
        for st_pt, en_pt in sub_frame_line:
            pygame.draw.line(self.game_surface, self.color.frame, st_pt, en_pt, width=2)

        # draw remain
        point_pos_remain = copy(point_pos)
        point_pos_remain.remove(point_pos[0])
        point_pos_remain.remove(point_pos[-1])
        for sub_point in point_pos_sub:
            point_pos_remain.remove(sub_point)

        sub_frame_line = [*[((point_pos[0], x), (point_pos[-1], x)) for x in point_pos_remain],
                          *[((x, point_pos[0]), (x, point_pos[-1])) for x in point_pos_remain]]
        for st_pt, en_pt in sub_frame_line:
            pygame.draw.line(self.game_surface, self.color.lineframe, st_pt, en_pt, width=1)

        # draw text

        if cap_mod:
            for y, row in enumerate(self.status):
                for x, value in enumerate(row):
                    if value != "":
                        self._sudoku[x, y] = int(value)
                        t_color = self.color.text if (
                                not self.selected or x != self.select_pos[0] or y != self.select_pos[
                            1]) else self.color.selected_text
                        text_img = self._font_cache.render(value, True, t_color)
                        self.game_surface.blit(text_img, ((point_pos[x] + point_pos[x + 1] - text_img.get_width()) / 2,
                                                          (point_pos[y] + point_pos[
                                                              y + 1] - text_img.get_height()) / 2))
                    else:
                        self._sudoku[x, y] = {i + 1 for i in range(self.number)}
            self._sudoku.update()
            sub_point_pos = list(np.linspace(self.offset, self.dimension - self.offset, self.segment * self.number + 1))
            for y, row in enumerate(self.status):
                for x, value in enumerate(row):
                    if value == "":
                        if len(self._sudoku[x, y]) == 1:
                            text_img = self._font_cache.render(str(self.result[y][x]), True, self.color.guess_text)
                            self.game_surface.blit(text_img,
                                                   ((point_pos[x] + point_pos[x + 1] - text_img.get_width()) / 2,
                                                    (point_pos[y] + point_pos[y + 1] - text_img.get_height()) / 2))
                        else:
                            for i in range(1, self.number + 1):
                                if i in self._sudoku[x, y]:
                                    sy, sx = divmod(i - 1, self.segment)
                                    x_off = x * self.segment + sx
                                    y_off = y * self.segment + sy
                                    text_img = self._sfont_cache.render(str(i), True, self.color.pos_text)
                                    self.game_surface.blit(text_img, (
                                        (sub_point_pos[x_off] + sub_point_pos[x_off + 1] - text_img.get_width()) / 2,
                                        (sub_point_pos[y_off] + sub_point_pos[y_off + 1] - text_img.get_height()) / 2))

        else:
            for y, row in enumerate(self.status):
                for x, text in enumerate(row):
                    if self.result[y][x]:
                        text_img = self._font_cache.render(str(self.result[y][x]), True, self.color.guess_text)
                        self.game_surface.blit(text_img, ((point_pos[x] + point_pos[x + 1] - text_img.get_width()) / 2,
                                                          (point_pos[y] + point_pos[
                                                              y + 1] - text_img.get_height()) / 2))
                    elif text:
                        t_color = self.color.text if (
                                not self.selected or x != self.select_pos[0] or y != self.select_pos[
                            1]) else self.color.selected_text
                        text_img = self._font_cache.render(text, True, t_color)
                        self.game_surface.blit(text_img, ((point_pos[x] + point_pos[x + 1] - text_img.get_width()) / 2,
                                                          (point_pos[y] + point_pos[
                                                              y + 1] - text_img.get_height()) / 2))

        pygame.display.update()
        pass

    def process(self):
        for y, col in enumerate(self.status):
            for x, value in enumerate(col):
                if value != "":
                    self._sudoku[x, y] = int(value)
                else:
                    self._sudoku[x, y] = {i + 1 for i in range(self.number)}

        for i in range(1000):
            self._sudoku.iterate(1)

            for y, col in enumerate(self.status):
                for x, value in enumerate(col):
                    if value == "":
                        if len(self._sudoku[x, y]) == 1:
                            self.result[y][x] = next(iter(self._sudoku[x, y]))

            self._update()

        self.lock = False


# pygame.init()
# dimension = 800
# window_surface = pygame.display.set_mode((dimension, dimension))
# pygame.display.set_caption("sudoku_solver")
# window_surface.fill((255, 255, 255))
#
# number_font = pygame.font.SysFont(None, 50)
#
# w_w, w_h = window_surface.get_size()
# offset = 10
# lines = [(offset, offset), (offset, w_h - offset), (w_w - offset, w_h - offset), (w_w - offset, offset)]
# w_s = (dimension - 2 * offset) / 3
# k = np.linspace(offset, w_h - offset, 10).astype(int)
# kk = list(k)
# heavy_rect = [
#     ((kk[3], kk[0]), (kk[3], kk[9]), (kk[6], kk[9]), (kk[6], kk[0])),
#     ((kk[0], kk[3]), (kk[0], kk[6]), (kk[9], kk[6]), (kk[9], kk[3]))
# ]
# temp = [1, 2, 4, 5, 7, 8]
# sublines = [
#     *[((kk[_], kk[0]), (kk[_], kk[9])) for _ in temp],
#     *[((kk[0], kk[_]), (kk[9], kk[_])) for _ in temp]
# ]
#
# print(lines)
#
# pygame.draw.lines(window_surface, pygame.color.Color(0, 0, 0), True, lines, width=2)
# for sub_rect in heavy_rect:
#     pygame.draw.lines(window_surface, pygame.color.Color(0, 0, 0), True, sub_rect, width=2)
# for line_st, line_en in sublines:
#     pygame.draw.line(window_surface, pygame.color.Color(127, 127, 127), line_st, line_en)
#
# # for s, e in points:
# #    pygame.draw.line(window_surface, pygame.color.Color(64, 64, 64), s, e)
#
# pygame.display.update()
#
# while True:
#     for event in pygame.event.get():
#         if event.type == QUIT:
#             pygame.quit()
#             sys.exit()

if __name__ == "__main__":
    a = sudoku_game()
    a.setup()
    a.run()
    pass
