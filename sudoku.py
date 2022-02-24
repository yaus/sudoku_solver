import itertools
from copy import copy


class sudoku:
    def __init__(self, size: int = 9):
        self.pos = [[set(range(1, size + 1)) for _ in range(size)] for _ in range(size)]
        self.size = size
        import math
        self.slice_len = sl = int(math.sqrt(size))
        self._l_iter = set(range(self.size))
        lst = list(range(self.size))
        self._s_iter = [set(lst[i:i + sl]) for i in range(0, self.size, sl)]

        if self.size != self.slice_len ** 2:
            raise ValueError(f"Incorrect {size=}")
        self._load = False

    def __str__(self):
        width = len(str(self.size - 1))
        small_h_seg = "─" * ((width + 1) * self.slice_len - 1)
        h = "┼".join([small_h_seg] * self.slice_len)

        def _(x):
            return str(next(iter(x))) if len(x) == 1 else " "

        result = ""
        for i in range(self.size):
            row = self.pos[i]
            if i % self.slice_len == 0 and i != 0:
                result += "\n" + h
            result += "\n" + "│".join(" ".join(_(t) for t in row[j * 3:j * 3 + 3]) for j in range(self.slice_len))
        return result

    def __getitem__(self, item):
        if isinstance(item, tuple):
            if len(item) == 2:
                x, y = item
                return self.pos[y][x]
            elif len(item) == 4:
                group_x, group_y, x, y = item
                x = group_x * self.slice_len + x
                y = group_y * self.slice_len + y
                return self.pos[y][x]
            else:
                raise IndexError(f"{item=} is not valid index")

    def __setitem__(self, key, value):
        x: int
        y: int
        group_x: int
        group_y: int
        if isinstance(key, tuple):
            if len(key) == 2:
                x, y = key
                group_x, group_y = x // self.slice_len, y // self.slice_len
                if isinstance(value, set):
                    self.pos[y][x] = value
                else:
                    self.pos[y][x] = {value}
            elif len(key) == 4:
                group_x, group_y, x, y = key
                x = group_x * self.slice_len + x
                y = group_y * self.slice_len + y
                self.pos[y][x] = {value}
            else:
                raise IndexError(f"{key=} is not valid type")
            if self._load:
                return
            for ix in self._l_iter:
                if value in self.pos[y][ix] and ix != x:
                    self.pos[y][ix].remove(value)
            for iy in self._l_iter:
                if value in self.pos[iy][x] and iy != y:
                    self.pos[iy][x].remove(value)

            for ix, iy in itertools.product(self._s_iter[group_x], self._s_iter[group_y]):
                if value in self.pos[iy][ix] and (ix != x or iy != y):
                    self.pos[iy][ix].remove(value)

        else:
            raise IndexError(f"{key=} is not valid type")

    def load(self, string):
        self._load = True
        for iy, line in enumerate(string.splitlines()):
            for ix, value in enumerate(line.split(",")):
                value = value.strip()
                if value == "":
                    continue
                else:
                    self[ix, iy] = int(value)
        self._load = False

    def update(self):
        changed = True
        while changed:
            changed = False
            for x, y in itertools.product(self._l_iter, repeat=2):
                if len(self.pos[y][x]) == 1:
                    value = next(iter(self.pos[y][x]))
                    group_x = x // self.slice_len
                    group_y = y // self.slice_len
                    for ix in self._l_iter:
                        if value in self.pos[y][ix] and ix != x:
                            self.pos[y][ix].remove(value)
                            changed = True
                    for iy in self._l_iter:
                        if value in self.pos[iy][x] and iy != y:
                            self.pos[iy][x].remove(value)
                            changed = True

                    for ix, iy in itertools.product(self._s_iter[group_x], self._s_iter[group_y]):
                        if value in self.pos[iy][ix] and (ix != x or iy != y):
                            self.pos[iy][ix].remove(value)
                            changed = True

    def rule0(self):
        for gx, gy in itertools.product(range(len(self._s_iter)), repeat=2):
            k_dict = {}
            for x, y in itertools.product(self._s_iter[gx], self._s_iter[gy]):
                if len(self.pos[y][x]) > 1:
                    for pos in self.pos[y][x]:
                        k_dict.setdefault(pos, [])
                        k_dict[pos].append((y, x))
            for pos in k_dict:
                if len(k_dict[pos]) == 1:
                    y, x = k_dict[pos][0]
                    self.pos[y][x] = {pos}
        self.update()

    def rule1(self):
        for gx, gy in itertools.product(range(len(self._s_iter)), repeat=2):
            for x, y in itertools.product(self._s_iter[gx], self._s_iter[gy]):
                if len(self.pos[y][x]) > 1:
                    for pos in self.pos[y][x]:
                        # check if row only
                        this_row_only = all(pos not in self.pos[dy][dx] for dx, dy in
                                            itertools.product(self._s_iter[gx], self._s_iter[gy]) if (dx != x))
                        if this_row_only:
                            for gyi in range(len(self._s_iter)):
                                if gyi == gy:
                                    continue
                                for yi in self._s_iter[gyi]:
                                    if pos in self.pos[yi][x]:
                                        self.pos[yi][x].remove(pos)

                        this_col_only = all(pos not in self.pos[dy][dx] for dx, dy in
                                            itertools.product(self._s_iter[gx], self._s_iter[gy]) if (dy != y))
                        if this_col_only:
                            for gxi in range(len(self._s_iter)):
                                if gxi == gx:
                                    continue
                                for xi in self._s_iter[gxi]:
                                    if pos in self.pos[y][xi]:
                                        self.pos[y][xi].remove(pos)
                        # remove
        self.update()

    def iterate(self, count=10):
        i = 0
        if self.done:
            return None
        else:
            # print(self)
            while count > 0 and not self.done:
                i += 1
                print(f"Iter #{i}")
                self.update()
                self.rule0()
                self.rule1()
                count -= 1
            # print(self)

    @property
    def done(self):
        return all(all(len(_) == 1 for _ in row) for row in self.pos)
