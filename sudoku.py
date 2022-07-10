from dataclasses import dataclass


class Sudoku:
    def __init__(self, size: int, nodes: list[list["SudokuElement"]]):
        self.nodes = nodes
        self.size = size
        import math
        self.sub_par_size = math.isqrt(size)
        for r in nodes:
            for e in r:
                e._root = self

    @staticmethod
    def create_classic(size: int):
        import math
        test_sqrt = math.isqrt(size) ** 2
        if test_sqrt != size:
            raise ValueError(f"{size=} is not valid square number")

        db = [[SudokuElement(x, y, [], 0) for x in range(size)] for y in range(size)]

        # create list of trigger
        # x dir
        for r in db:
            for x in r:
                trigger_list_clone = r.copy()
                trigger_list_clone.remove(x)
                x.trigger_group.append(trigger_list_clone)

        # y dir
        for c in [list(element) for element in zip(*db)]:
            for y in c:
                trigger_list_clone = c.copy()
                trigger_list_clone.remove(y)
                y.trigger_group.append(trigger_list_clone)

        # Same Sub partition
        sub_par_size = math.isqrt(size)
        sub_list = [list(range(i * sub_par_size, (i + 1) * sub_par_size)) for i in range(sub_par_size)]
        import itertools
        for gx, gy in itertools.product(sub_list, repeat=2):
            # ref_list = [db[y][x] for y in gy for x in gx]
            for x, y in itertools.product(gx, gy):
                # sub_group = ref_list.copy()
                # sub_group.remove(db[y][x])
                db[y][x].trigger_group.append(list(db[sy][sx] for sy in gy for sx in gx if sy != y or sx != x))
        return Sudoku(size, db)

    def __getitem__(self, item):
        if isinstance(item, tuple):
            if len(item) == 2:
                x, y = item
                return self.nodes[y][x].value

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            if len(key) == 2:
                x, y = key
                self.nodes[y][x].value = value


@dataclass
class SudokuElement:
    x: int
    y: int

    trigger_group: list[list["SudokuElement"]]
    value: int = 0
    _root: Sudoku = None

    def __repr__(self):
        return f"x:{self.x} y:{self.y} value:{self.value}"

    def valid_value(self) -> list[int]:
        z = self._root.size
        h = list(range(1, z + 1))
        for e in self.trigger_element():
            if e.value != 0 and e.value in h:
                h.remove(e.value)
        return h

    def guess(self):
        if self.value == 0:
            v = self.valid_value()
            if len(v) == 1:
                return v[0]
            for stg in self.trigger_group:
                number = []
                for e in stg:
                    if e.value != 0:
                        number.append(e.value)
                    else:
                        number.extend(e.valid_value())
                number = set(number)
                remain = set(range(1, self._root.size + 1)) - number
                if len(remain) == 1:
                    e = next(iter(remain))
                    if e in v:
                        return e

        return self.value

    def trigger_element(self):
        yield from set(j for i in self.trigger_group for j in i)

    def __hash__(self):
        return hash(self.y * self._root.size + self.x)
