#!/usr/bin/env python3
"""shisen-sho 四川省连连看: 8x12 牌面, 最多三线段(两次转弯)连接同对消除."""

import argparse
import copy
import random
import sys

ROWS, COLS = 8, 12
# 棋牌用数字代表花色(1-9), 每种 8 张(4 对), 8*12=96 格正好 12 种
TILES = list(range(1, 13))


class IllegalMove(Exception):
    pass


class ShisenSho:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.grid = [[None] * COLS for _ in range(ROWS)]
        self.deal()

    def deal(self):
        cards = []
        for t in TILES:
            cards.extend([t] * 8)
        self.rng.shuffle(cards)
        it = iter(cards)
        for r in range(ROWS):
            for c in range(COLS):
                self.grid[r][c] = next(it)
        self.remaining = ROWS * COLS

    def _in(self, r, c):
        return 0 <= r < ROWS and 0 <= c < COLS

    def clearable_path(self, a, b):
        """a,b 为 (r,c); 返回连接线段点列, 不能连返回 None.
        允许绕到棋盘外一圈(虚拟边框), 最多 3 段(两次转弯)."""
        if a == b:
            return None
        (r1, c1), (r2, c2) = a, b
        if not (self._in(r1, c1) and self._in(r2, c2)):
            return None
        if self.grid[r1][c1] is None or self.grid[r2][c2] is None:
            return None
        if self.grid[r1][c1] != self.grid[r2][c2]:
            return None

        def empty(r, c):
            if (r, c) == a or (r, c) == b:
                return True
            if not self._in(r, c):
                return True  # 虚拟边框
            return self.grid[r][c] is None

        # BFS: (r, c, 方向, 转弯数), 方向 0=上,1=下,2=左,3=右,4=起点
        from collections import deque
        DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        dq = deque()
        dq.append((r1, c1, 4, 0, [(r1, c1)]))
        seen = {}
        while dq:
            r, c, d, turns, path = dq.popleft()
            for nd, (dr, dc) in enumerate(DIRS):
                nt = turns + (0 if d == 4 or d == nd else 1)
                if nt > 2:
                    continue
                nr, nc = r + dr, c + dc
                # 允许进入虚拟边框一圈
                if not (-1 <= nr <= ROWS and -1 <= nc <= COLS):
                    continue
                if not empty(nr, nc):
                    continue
                if (nr, nc) == (r2, c2):
                    return path + [(nr, nc)]
                key = (nr, nc, nd)
                if seen.get(key, 99) <= nt:
                    continue
                seen[key] = nt
                dq.append((nr, nc, nd, nt, path + [(nr, nc)]))
        return None

    def legal_moves(self):
        moves = []
        pos = {}
        for r in range(ROWS):
            for c in range(COLS):
                t = self.grid[r][c]
                if t is not None:
                    pos.setdefault(t, []).append((r, c))
        for t, cells in pos.items():
            n = len(cells)
            for i in range(n):
                for j in range(i + 1, n):
                    a, b = cells[i], cells[j]
                    path = self.clearable_path(a, b)
                    if path:
                        moves.append((a, b, path))
        return moves

    def remove(self, a, b):
        path = self.clearable_path(a, b)
        if path is None:
            raise IllegalMove("这两张牌连不起来")
        self.grid[a[0]][a[1]] = None
        self.grid[b[0]][b[1]] = None
        self.remaining -= 2
        return path

    def is_cleared(self):
        return self.remaining == 0

    def greedy_move(self):
        moves = self.legal_moves()
        if not moves:
            return None
        return self.rng.choice(moves)

    def solve_auto(self, verbose=False):
        steps = 0
        while self.remaining > 0:
            m = self.greedy_move()
            if m is None:
                break
            a, b, path = m
            self.remove(a, b)
            steps += 1
            if verbose:
                print(f"消除 {self.grid and ''}第{steps}对: {a}->{b} ({len(path)-1}段)")
        return steps, self.remaining

    def render(self):
        lines = []
        head = "    " + " ".join(f"{c:2d}" for c in range(COLS))
        lines.append(head)
        for r in range(ROWS):
            row = []
            for c in range(COLS):
                v = self.grid[r][c]
                row.append(" ." if v is None else f"{v:2d}")
            lines.append(f"{r:2d}  " + " ".join(row))
        return "\n".join(lines)


def play_interactive(seed=None):
    if not sys.stdin.isatty():
        print("交互模式需要终端, 请用 --auto 自动演示。")
        sys.exit(2)
    g = ShisenSho(seed=seed)
    print("=== 四川省连连看 ===")
    print("输入如 '1 2 1 5' 表示连接 (1,2) 与 (1,5), q 退出。")
    while not g.is_cleared():
        print(g.render())
        print(f"剩余 {g.remaining} 张")
        s = input("> ").strip()
        if s.lower() == "q":
            break
        try:
            r1, c1, r2, c2 = map(int, s.split())
        except ValueError:
            print("格式: r1 c1 r2 c2")
            continue
        try:
            path = g.remove((r1, c1), (r2, c2))
            print(f"消除! 线段数 {len(path)-1}")
        except IllegalMove as e:
            print("连不上:", e)
    if g.is_cleared():
        print("全部消除, 通关!")


def play_auto(games, seed, verbose):
    rng = random.Random(seed)
    cleared = 0
    total_pairs = 0
    for i in range(games):
        g = ShisenSho(seed=rng.randrange(1 << 30))
        steps, remaining = g.solve_auto(verbose=verbose)
        total_pairs += steps
        if remaining == 0:
            cleared += 1
        if verbose:
            print(f"第{i+1}局: {'通关' if remaining == 0 else f'剩余{remaining}张'}")
    print(f"共 {games} 局: 通关 {cleared}, 未通关 {games-cleared}, 共消除 {total_pairs} 对")


def main():
    ap = argparse.ArgumentParser(description="四川省连连看")
    ap.add_argument("--auto", action="store_true", help="自动求解演示")
    ap.add_argument("--games", type=int, default=10)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    if args.auto:
        play_auto(args.games, args.seed, args.verbose)
    else:
        play_interactive(seed=args.seed)


if __name__ == "__main__":
    main()
