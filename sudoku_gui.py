import math
import sys

import pygame
import numpy as np
from pygame.locals import QUIT
from dataclasses import dataclass, field
from enum import Enum, Flag, IntFlag
from copy import copy
from sudoku import Sudoku, SudokuElement


class NamedDict(dict):
    def __getattr__(self, item):
        if item in self:
            return self[item]

    def __setattr__(self, key, value):
        if key in self:
            self[key] = value


keymap = {pygame.K_0: 0, pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3, pygame.K_4: 4, pygame.K_5: 5, pygame.K_6: 6,
          pygame.K_7: 7, pygame.K_8: 8, pygame.K_9: 9, pygame.K_KP0: 0, pygame.K_KP1: 1, pygame.K_KP2: 2,
          pygame.K_KP3: 3, pygame.K_KP4: 4, pygame.K_KP5: 5, pygame.K_KP6: 6, pygame.K_KP7: 7, pygame.K_KP8: 8,
          pygame.K_KP9: 9}


@dataclass
class CellState:
    input_value: int
    element: SudokuElement | None = None
    valid_value: list[int] = field(default_factory=list)


class GameMode(IntFlag):
    InputLock = 1
    GuessMode = 2
    Process = 4


class SuDoKuGame:
    def __init__(self, dimension: int = 800, offset: int = 20, number: int = 9):
        self.dimension = dimension
        self.offset = offset
        self.number = number
        self.selected = True
        self.select_pos = [0, 1]
        self.segment = math.isqrt(number)
        self.color = NamedDict(
            background=pygame.Color(255, 255, 255),
            selected=pygame.Color(0xC7, 0x20, 0x5D),
            frame=pygame.Color(0, 0, 0),
            lineframe=pygame.Color(64, 64, 64),
            text=pygame.Color(0, 0, 0),
            selected_text=pygame.Color(255, 255, 255),
            guess_text=pygame.Color(0xDE, 0x36, 0x9D),
            pos_text=pygame.Color(216, 216, 216)
        )
        self.cells = [[CellState(0) for i in range(number)] for i in range(number)]
        self.mode = GameMode.InputLock
        self.game_surface = None
        self._font_cache = None
        self._small_font_cache = None
        self.event_map = {
            QUIT: self.game_exit,
            pygame.KEYDOWN: self.key_handler,
            pygame.MOUSEBUTTONDOWN: self.mouse_handler
        }
        # Y, X
        self.select_pos = [0, 0]
        self.sudoku_solver: Sudoku | None = None

    def setup(self):
        pygame.init()
        self.game_surface = pygame.display.set_mode((self.dimension, self.dimension))
        pygame.display.set_caption("sudoku_solver")
        self.game_surface.fill(self.color.background)
        self._font_cache = pygame.font.Font(None, int(self.dimension / self.number))
        self._small_font_cache = pygame.font.Font(None, int(self.dimension / self.number / self.segment))
        self._h = self._font_cache.render("0123456789", True, self.color.text).get_height() / 2
        self._sh = self._small_font_cache.render("0123456789", True, self.color.text).get_height() / 2

        self.sudoku_solver = Sudoku.create_classic(self.number)

        for y, row in enumerate(self.cells):
            for x, cell in enumerate(row):
                cell.element = self.sudoku_solver.nodes[y][x]

    def test_case(self, setup: str):
        for y, line in enumerate(setup.splitlines()):
            for x, num in enumerate(line.strip().split(" ")):
                if num.isdigit:
                    if (g := int(num)) != 0:
                        self.cells[y][x].input_value = g

    def run(self):
        while True:
            for event in pygame.event.get():
                self.event_map.setdefault(event.type, self.dummy)(event)
            self.selected = GameMode.InputLock not in self.mode
            self.model_update()
            if GameMode.GuessMode in self.mode:
                self.guess()
            self.draw()

    def game_exit(self, dummy: pygame.event):
        print("Exit pressed")
        pygame.quit()
        sys.exit()

    def dummy(self, dummy: pygame.event):
        pass

    def key_handler(self, event: pygame.event):
        match event.type, event.key, GameMode.InputLock in self.mode:
            case pygame.KEYDOWN, pygame.K_SPACE, _:
                self.mode = self.mode ^ GameMode.InputLock
            case pygame.KEYDOWN, pygame.K_BACKQUOTE, _:
                self.mode = self.mode ^ GameMode.GuessMode
            case pygame.KEYDOWN, pygame.K_UP, False:
                if 0 < self.select_pos[0] < self.number:
                    self.select_pos[0] -= 1
            case pygame.KEYDOWN, pygame.K_DOWN, False:
                if 0 <= self.select_pos[0] < self.number - 1:
                    self.select_pos[0] += 1
            case pygame.KEYDOWN, pygame.K_LEFT, False:
                if 0 < self.select_pos[1] < self.number:
                    self.select_pos[1] -= 1
            case pygame.KEYDOWN, pygame.K_RIGHT, False:
                if 0 <= self.select_pos[1] < self.number - 1:
                    self.select_pos[1] += 1
            case pygame.KEYDOWN, pygame.K_TAB, False:
                self.select_pos[1] += 1
                if self.select_pos[1] == self.number:
                    self.select_pos[0] += 1
                    self.select_pos[1] = 0
                if self.select_pos[0] == self.number:
                    self.select_pos[0] = 0
            case pygame.KEYDOWN, key, 0 if key in keymap:
                selected_cell = self.cells[self.select_pos[0]][self.select_pos[1]]
                test_text = f"{selected_cell.input_value}{keymap[key]}"
                input_num = int(test_text)
                if input_num > self.number:
                    selected_cell.input_value = keymap[key]
                    if selected_cell.input_value > self.number:
                        selected_cell.input_value = 0
                else:
                    selected_cell.input_value = input_num
            case pygame.KEYDOWN, pygame.K_BACKSPACE, False:
                selected_cell = self.cells[self.select_pos[0]][self.select_pos[1]]
                cell_str = str(selected_cell.input_value)
                cell_str = cell_str[:-1]
                if cell_str.isdigit():
                    selected_cell.input_value = int(cell_str)
                else:
                    selected_cell.input_value = 0
            case pygame.KEYDOWN, pygame.K_RETURN | pygame.K_KP_ENTER, False:
                self.mode = (self.mode & GameMode.InputLock) | GameMode.Process
            case pygame.KEYDOWN, pygame.K_ESCAPE, False:
                for r in self.cells:
                    for c in r:
                        c.input_value = 0

    def mouse_handler(self, event: pygame.event):
        match event.type, GameMode.InputLock in self.mode:
            case pygame.MOUSEBUTTONDOWN, False:
                x, y = pygame.mouse.get_pos()
                sx, sy = self.select_pos
                point_pos = list(np.linspace(self.offset, self.dimension - self.offset, self.number + 1))
                for idx, coordinate in enumerate(zip(point_pos[:-1], point_pos[1:])):
                    a0, a1 = coordinate
                    if a0 + 1 < x < a1 - 1:
                        sx = idx

                for idx, coordinate in enumerate(zip(point_pos[:-1], point_pos[1:])):
                    a0, a1 = coordinate
                    if a0 + 1 < y < a1 - 1:
                        sy = idx
                if pygame.mouse.get_pressed()[0]:
                    self.select_pos = [sx, sy]

    def draw(self):
        # Update

        self.game_surface.fill(self.color.background)
        point_idx = list(range(self.number + 1))
        point_pos = list(np.linspace(self.offset, self.dimension - self.offset, len(point_idx)))

        # Draw selection
        if self.selected:
            y, x = self.select_pos
            pygame.draw.rect(self.game_surface, self.color.selected,
                             ((point_pos[x], point_pos[y]),
                              (point_pos[x + 1] - point_pos[x], point_pos[y + 1] - point_pos[y])))

        # Draw frame
        outer_frame = [(point_pos[0], point_pos[0]), (point_pos[-1], point_pos[0]), (point_pos[-1], point_pos[-1]),
                       (point_pos[0], point_pos[-1])]
        pygame.draw.lines(self.game_surface, self.color.frame, True, outer_frame, width=2)
        point_pos_sub = [point_pos[i] for i in range(0, len(point_pos), self.segment)][1:-1]
        sub_frame_line = [*[((point_pos[0], x), (point_pos[-1], x)) for x in point_pos_sub],
                          *[((x, point_pos[0]), (x, point_pos[-1])) for x in point_pos_sub]]
        for st_pt, en_pt in sub_frame_line:
            pygame.draw.line(self.game_surface, self.color.frame, st_pt, en_pt, width=2)

        # Draw subframe
        point_pos_remain = copy(point_pos)
        point_pos_remain.remove(point_pos[0])
        point_pos_remain.remove(point_pos[-1])
        for sub_point in point_pos_sub:
            point_pos_remain.remove(sub_point)

        sub_frame_line = [*[((point_pos[0], x), (point_pos[-1], x)) for x in point_pos_remain],
                          *[((x, point_pos[0]), (x, point_pos[-1])) for x in point_pos_remain]]
        for st_pt, en_pt in sub_frame_line:
            pygame.draw.line(self.game_surface, self.color.lineframe, st_pt, en_pt, width=1)

        # Draw text

        for y, row in enumerate(self.cells):
            for x, cell in enumerate(row):
                if cell.input_value:
                    if self.selected and self.select_pos[0] == y and self.select_pos[1] == x:
                        t_color = self.color.selected_text
                    else:
                        t_color = self.color.text
                    text_img = self._font_cache.render(str(cell.input_value), True, t_color)
                    self.game_surface.blit(text_img, (
                        (point_pos[x] + point_pos[x + 1] - text_img.get_width()) / 2, (point_pos[y] + point_pos[
                            y + 1] - text_img.get_height()) / 2))

        if GameMode.GuessMode in self.mode:
            pygame.draw.rect(self.game_surface, self.color.selected, ((0, 0), (10, 10)))
            # get valid
            sub_point_pos = list(np.linspace(self.offset, self.dimension - self.offset, self.segment * self.number + 1))

            for y, row in enumerate(self.cells):
                for x, cell in enumerate(row):
                    if cell.input_value == 0:
                        if cell.element.value != 0:
                            valid_value = [cell.element.value]
                        else:
                            valid_value = cell.valid_value
                        if len(valid_value) == 1:
                            text_img = self._font_cache.render(str(valid_value[0]), True, self.color.guess_text)
                            self.game_surface.blit(text_img,
                                                   ((point_pos[x] + point_pos[x + 1] - text_img.get_width()) / 2,
                                                    (point_pos[y] + point_pos[y + 1] - text_img.get_height()) / 2))
                        else:
                            for i in range(1, self.number + 1):
                                if i in valid_value:
                                    sy, sx = divmod(i - 1, self.segment)
                                    x_off = x * self.segment + sx
                                    y_off = y * self.segment + sy
                                    text_img = self._small_font_cache.render(str(i), True, self.color.pos_text)
                                    self.game_surface.blit(text_img, (
                                        (sub_point_pos[x_off] + sub_point_pos[x_off + 1] - text_img.get_width()) / 2,
                                        (sub_point_pos[y_off] + sub_point_pos[y_off + 1] - text_img.get_height()) / 2))

        pygame.display.update()

    def model_update(self):
        for y, row in enumerate(self.cells):
            for x, cell in enumerate(row):
                self.sudoku_solver.nodes[y][x].value = cell.input_value
        for y, row in enumerate(self.cells):
            for x, cell in enumerate(row):
                if cell.input_value == 0:
                    cell.valid_value = self.sudoku_solver.nodes[y][x].valid_value()

    def guess(self):
        def get_hash():
            return hash("".join(str(c.element.value) for r in self.cells for c in r))

        def guess():
            for r in self.cells:
                for c in r:
                    c.element.value = c.element.guess()

        def cell_empty():
            return any(c.element.value == 0 and len(c.element.valid_value()) == 0 for r in self.cells for c in r)

        def super_guess(v, u, guess_value):
            if guess_value != 0:
                self.cells[v][u].element.value = guess_value
            p_state = 0
            while p_state != get_hash():
                p_state = get_hash()
                guess()

            if cell_empty():
                self.cells[y][x].element.value = 0
                return False
            else:
                return True

        super_guess(0, 0, 0)

        # Found first unfilled
        for y, row in enumerate(self.cells):
            for x, cell in enumerate(row):
                if cell.element.value == 0:
                    for test_value in cell.element.valid_value():
                        if super_guess(y, x, test_value):
                            return


if __name__ == "__main__":
    a = SuDoKuGame()
    a.setup()
    # if False:
    #     a.test_case(
    #         """
    # 2 0 0 0 1 7 8 0 0
    # 0 0 0 2 0 0 5 0 7
    # 0 9 0 0 4 0 0 0 0
    # 0 0 0 4 0 2 0 0 6
    # 0 0 0 0 7 0 0 9 0
    # 4 3 9 0 0 0 0 0 0
    # 0 6 5 7 0 0 0 0 0
    # 0 0 3 9 0 1 7 0 0
    # 1 2 0 0 0 0 0 5 0""".strip()
    #     )
    a.run()
