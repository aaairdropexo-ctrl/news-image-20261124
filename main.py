#!/usr/bin/env python3
"""news-image-20261124 v3 — "The World in One Day" (ATM rebuild).

Front page for Tuesday 24 November 2026: 38 stories, 9 regions.
Structure copied from the live top 10 (ATM): black top bar, huge
serif-style masthead, sub-deck, region bar, UTC strip, numbers
strip, 3 illustrated heroes, 10 illustrated cards, numbered ALSO
list, world map with pins, DATE CHECK box, badge legend.

Stdlib only. Deterministic: same bytes on every run. No network.
Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).
"""
import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
CREAM = (250, 246, 236)
PAPER = (255, 252, 244)
INK = (24, 24, 22)
BLACK = (12, 12, 12)
RED = (178, 34, 28)
DARKRED = (140, 22, 18)
BLUE = (28, 68, 128)
NAVY = (16, 32, 64)
GOLD = (176, 132, 32)
GREEN = (28, 96, 48)
TEAL = (14, 110, 110)
GREY = (110, 108, 100)
LGREY = (206, 202, 190)
MGREY = (168, 164, 150)
WHITE = (255, 255, 255)
SKY = (172, 206, 230)
SEA = (86, 132, 178)
SAND = (226, 208, 172)
ORANGE = (214, 110, 28)
PURPLE = (96, 52, 128)

REGION_COLORS = {
    "Europe": (28, 68, 168),
    "Middle East": (178, 34, 28),
    "Asia": (28, 96, 48),
    "Americas": (96, 52, 128),
    "Africa": (214, 110, 28),
    "Oceania": (14, 110, 110),
    "South Asia": (176, 132, 32),
    "SE Asia": (120, 90, 40),
    "World": (70, 70, 70),
}

BADGE_COLORS = {
    "CONFIRMED": (28, 96, 48),
    "OFFICIAL": (176, 132, 32),
    "REPORTED": (28, 68, 168),
    "CLAIM": (178, 34, 28),
    "ONGOING": (96, 52, 128),
}


# ---------------------------------------------------------------- PNG
def _chunk(kind, data):
    c = struct.pack(">I", len(data)) + kind + data
    return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write_png(path, cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw.extend(cv.px[y * cv.w * 3:(y + 1) * cv.w * 3])
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def dot(self, x, y, c, r=0):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                self.set(x + dx, y + dy, c)

    def line(self, x0, y0, x1, y1, c, wd=1):
        dx, dy = x1 - x0, y1 - y0
        n = max(abs(dx), abs(dy), 1)
        r = wd // 2
        for i in range(n + 1):
            x = x0 + dx * i // n
            y = y0 + dy * i // n
            if wd <= 1:
                self.set(x, y, c)
            else:
                for oy in range(-r, r + 1):
                    for ox in range(-r, r + 1):
                        self.set(x + ox, y + oy, c)

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def rect_outline(self, x, y, w, h, c, wd=1):
        self.line(x, y, x + w - 1, y, c, wd)
        self.line(x, y + h - 1, x + w - 1, y + h - 1, c, wd)
        self.line(x, y, x, y + h - 1, c, wd)
        self.line(x + w - 1, y, x + w - 1, y + h - 1, c, wd)

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.set(xx, yy, c)
                else:
                    if abs(d2 - r * r) <= r:
                        self.set(xx, yy, c)

    def poly(self, pts, c):
        # scanline fill for a simple polygon
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            for i in range(len(pts)):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % len(pts)]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                for x in range(int(xs[j]), int(xs[j + 1]) + 1):
                    self.set(x, y, c)
        for i in range(len(pts)):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % len(pts)]
            self.line(x0, y0, x1, y1, c, 1)


# ---------------------------------------------------------------- font
# Single-stroke vector glyphs on a 9x14 grid. Caps y1..11, lowercase
# x-height y5..11, ascenders y1..11, descenders y11..13. Each glyph is
# a list of polylines written as "x,y x,y ...".
FONT = {
    "A": ["0,11 4,1 8,11", "2,8 6,8"],
    "B": ["0,1 0,11", "0,1 6,1 8,3 8,5 6,6 0,6", "0,6 6,6 8,8 8,10 6,11 0,11"],
    "C": ["8,3 6,1 2,1 0,3 0,9 2,11 6,11 8,9"],
    "D": ["0,1 0,11 6,11 8,9 8,3 6,1 0,1"],
    "E": ["8,1 0,1 0,11 8,11", "0,6 5,6"],
    "F": ["0,1 0,11", "0,1 8,1", "0,6 5,6"],
    "G": ["8,3 6,1 2,1 0,3 0,9 2,11 6,11 8,9 8,6 5,6"],
    "H": ["0,1 0,11", "8,1 8,11", "0,6 8,6"],
    "I": ["4,1 4,11", "2,1 6,1", "2,11 6,11"],
    "J": ["2,1 7,1", "6,1 6,9 4,11 1,11 0,9"],
    "K": ["0,1 0,11", "8,1 0,6", "2,8 8,11"],
    "L": ["0,1 0,11 8,11"],
    "M": ["0,11 0,1 4,7 8,1 8,11"],
    "N": ["0,11 0,1 8,11 8,1"],
    "O": ["2,1 6,1 8,3 8,9 6,11 2,11 0,9 0,3 2,1"],
    "P": ["0,1 0,11", "0,1 6,1 8,3 8,5 6,6 0,6"],
    "Q": ["2,1 6,1 8,3 8,9 6,11 2,11 0,9 0,3 2,1", "5,8 8,11"],
    "R": ["0,1 0,11", "0,1 6,1 8,3 8,5 6,6 0,6", "3,6 8,11"],
    "S": ["7,3 5,1 2,1 0,3 0,5 2,6 6,6 8,8 8,10 6,11 3,11 1,9"],
    "T": ["0,1 8,1", "4,1 4,11"],
    "U": ["0,1 0,9 2,11 6,11 8,9 8,1"],
    "V": ["0,1 4,11 8,1"],
    "W": ["0,1 2,11 4,5 6,11 8,1"],
    "X": ["0,1 8,11", "8,1 0,11"],
    "Y": ["0,1 4,6 8,1", "4,6 4,11"],
    "Z": ["0,1 8,1 0,11 8,11"],
    "a": ["8,5 8,11", "1,6 1,10 3,11 6,11 8,9 8,6 6,5 3,5 1,6"],
    "b": ["0,1 0,11", "0,6 6,6 8,8 8,10 6,11 0,11"],
    "c": ["8,6 6,5 2,5 0,7 0,9 2,11 6,11 8,10"],
    "d": ["8,1 8,11", "8,6 2,6 0,8 0,10 2,11 6,11 8,10"],
    "e": ["7,8 8,9 6,11 2,11 0,9 0,6 2,5 6,5 8,7", "0,8 8,8"],
    "f": ["7,1 5,2 4,4 4,11", "2,5 6,5"],
    "g": ["0,6 0,10 2,11 6,11 8,9 8,5", "8,9 8,12 6,13 3,13 1,12"],
    "h": ["0,1 0,11", "0,6 2,5 6,5 8,7 8,11"],
    "i": ["4,5 4,11", "4,2 4,2"],
    "j": ["6,5 6,12 4,13 2,13", "6,2 6,2"],
    "k": ["0,1 0,11", "7,5 1,8", "2,9 7,11"],
    "l": ["4,1 4,11"],
    "m": ["0,5 0,11", "0,6 2,5 4,6 4,11", "4,6 6,5 8,7 8,11"],
    "n": ["0,5 0,11", "0,6 2,5 6,5 8,7 8,11"],
    "o": ["2,5 6,5 8,7 8,9 6,11 2,11 0,9 0,7 2,5"],
    "p": ["0,5 0,13", "0,6 6,6 8,8 8,10 6,11 0,11"],
    "q": ["8,5 8,13", "8,6 2,6 0,8 0,10 2,11 6,11 8,10"],
    "r": ["0,5 0,11", "0,6 3,5 6,5 7,6"],
    "s": ["7,6 5,5 2,5 0,7 0,8 2,9 6,9 8,10 6,11 3,11 1,10"],
    "t": ["4,2 4,11", "2,6 6,6", "3,11 5,11"],
    "u": ["0,5 0,9 2,11 6,11 8,9 8,5"],
    "v": ["0,5 4,11 8,5"],
    "w": ["0,5 2,11 4,7 6,11 8,5"],
    "x": ["0,5 8,11", "8,5 0,11"],
    "y": ["0,5 4,11 8,5", "4,11 4,13 2,13"],
    "z": ["0,5 8,5 0,11 8,11"],
    "0": ["2,1 6,1 8,3 8,9 6,11 2,11 0,9 0,3 2,1"],
    "1": ["5,1 5,11", "3,3 5,1", "2,11 7,11"],
    "2": ["1,3 3,1 6,1 8,3 8,5 0,11 8,11"],
    "3": ["1,2 3,1 6,1 8,3 7,5 5,6 7,7 8,9 6,11 3,11 1,10"],
    "4": ["5,1 0,8 6,8", "6,1 6,11"],
    "5": ["8,1 0,1 0,6 6,6 8,8 8,10 6,11 2,11 0,9"],
    "6": ["8,3 6,1 2,1 0,3 0,9 0,10 2,11 6,11 8,9 8,7 6,6 2,6 0,8"],
    "7": ["0,1 8,1 4,11"],
    "8": ["2,1 6,1 8,3 8,5 6,6 2,6 0,5 0,3 2,1",
          "2,6 6,6 8,8 8,10 6,11 2,11 0,9 0,7 2,6"],
    "9": ["8,9 8,3 6,1 2,1 0,3 0,5 2,6 6,6 8,8 8,10 6,11 2,11 0,9"],
    ".": ["4,11 4,11"],
    ",": ["4,11 3,13"],
    ":": ["4,4 4,4", "4,10 4,10"],
    ";": ["4,4 4,4", "4,10 3,13"],
    "!": ["4,1 4,8", "4,11 4,11"],
    "?": ["1,3 3,1 6,1 8,3 8,5 6,6 4,7 4,9", "4,11 4,11"],
    "'": ["4,1 3,3"],
    "\u2019": ["4,1 3,3"],
    "-": ["1,7 7,7"],
    "\u2013": ["0,7 8,7"],
    "\u2014": ["0,7 8,7"],
    "(": ["6,1 3,3 3,9 6,11"],
    ")": ["2,1 5,3 5,9 2,11"],
    "%": ["0,2 8,10", "2,1 2,3 0,3 0,1 2,1", "6,9 6,11 8,11 8,9 6,9"],
    "$": ["4,0 4,13", "7,3 5,1 2,1 0,3 0,5 2,6 6,6 8,8 8,10 6,11 3,11 1,9"],
    "/": ["7,1 1,11"],
    "+": ["4,3 4,9", "1,6 7,6"],
    '"': ["2,1 2,3", "6,1 6,3"],
    "\u00b7": ["4,6 4,6"],
    "\u00d7": ["1,4 7,10", "7,4 1,10"],
    "=": ["1,4 7,4", "1,8 7,8"],
    " ": [],
}

ADV = 10  # advance width in grid units per glyph


def _draw_glyph(cv, x, y, ch, s, color, bold):
    strokes = FONT.get(ch)
    if not strokes:
        return
    wd = max(1, round(s * (0.55 if bold else 0.34)))
    for stroke in strokes:
        pts = [tuple(map(int, p.split(","))) for p in stroke.split()]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            cv.line(x + round(ax * s), y + round(ay * s),
                    x + round(bx * s), y + round(by * s), color, wd)
            if len(pts) == 1:
                cv.dot(x + round(ax * s), y + round(ay * s), color, wd // 2)
    if bold:
        # second pass, one pixel over, for a heavier face
        off = max(1, round(s * 0.22))
        for stroke in strokes:
            pts = [tuple(map(int, p.split(","))) for p in stroke.split()]
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                cv.line(x + off + round(ax * s), y + round(ay * s),
                        x + off + round(bx * s), y + round(by * s), color, wd)


def text_w(s, scale):
    w = 0
    for ch in s:
        w += (5 if ch == " " else ADV) * scale
    return w


def draw_text(cv, x, y, s, scale, color, bold=False):
    cx = int(x)
    for ch in s:
        if ch != " ":
            _draw_glyph(cv, int(cx), y, ch, scale, color, bold)
        cx += (5 if ch == " " else ADV) * scale
    return cx


def draw_text_center(cv, cx, y, s, scale, color, bold=False):
    draw_text(cv, int(cx - text_w(s, scale) // 2), y, s, scale, color, bold)


def wrap(s, scale, max_w):
    """Greedy word wrap. Returns a list of lines that fit max_w."""
    words = s.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, x, y, s, scale, color, max_w, bold=False, leading=None):
    lh = leading if leading is not None else round(14 * scale)
    for line in wrap(s, scale, max_w):
        draw_text(cv, x, y, line, scale, color, bold)
        y += lh
    return y


# ---------------------------------------------------------------- badges
def badge(cv, x, y, text, scale=1):
    w = int(text_w(text, scale)) + 8
    h = int(round(13 * scale)) + 4
    col = BADGE_COLORS.get(text, GREY)
    cv.rect(int(x), y, w, h, col)
    draw_text(cv, int(x) + 4, y + 2, text, scale, WHITE, True)
    return w


def kicker(cv, x, y, region, field, scale=1):
    rc = REGION_COLORS.get(region, GREY)
    cv.rect(x, y + 1, 8, 8, rc)
    draw_text(cv, x + 12, y, region.upper() + " \u00b7 " + field.upper(),
              scale, rc, True)


# ---------------------------------------------------------------- map
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-120, 72), (-95, 80), (-80, 73), (-70, 62),
     (-75, 45), (-80, 32), (-90, 21), (-97, 16), (-105, 20), (-115, 30),
     (-125, 40), (-125, 49), (-140, 60), (-155, 58)],
    # South America
    [(-80, 10), (-60, 8), (-50, 0), (-40, -5), (-35, -10), (-40, -20),
     (-48, -28), (-58, -35), (-65, -45), (-70, -55), (-75, -40),
     (-80, -20), (-80, 0)],
    # Europe
    [(-10, 36), (-10, 44), (0, 48), (-5, 50), (5, 58), (10, 58),
     (18, 56), (21, 55), (28, 60), (30, 70), (40, 68), (45, 60),
     (40, 50), (30, 46), (28, 40), (23, 36), (15, 38), (8, 44),
     (3, 43), (-2, 37)],
    # Africa
    [(-18, 15), (-10, 30), (0, 36), (10, 37), (20, 32), (30, 31),
     (35, 28), (43, 12), (51, 11), (48, 0), (40, -10), (35, -20),
     (30, -30), (20, -35), (15, -27), (12, -18), (8, -2), (9, 4),
     (-8, 5)],
    # Asia
    [(30, 70), (45, 68), (60, 70), (75, 73), (90, 75), (110, 76),
     (130, 72), (150, 70), (170, 66), (180, 65), (170, 60), (160, 55),
     (140, 40), (130, 33), (120, 25), (110, 20), (105, 10), (100, 5),
     (95, 15), (90, 22), (80, 20), (75, 10), (70, 25), (60, 25),
     (55, 30), (50, 30), (45, 30), (40, 35), (35, 36), (30, 42),
     (30, 60)],
    # Australia
    [(110, -12), (125, -15), (140, -18), (145, -25), (150, -37),
     (140, -38), (130, -32), (115, -35), (110, -22)],
    # New Zealand
    [(166, -34), (178, -38), (174, -41), (166, -46)],
]


def _in_poly(lon, lat, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > lat) != (y1 > lat):
            xin = x0 + (lat - y0) * (x1 - x0) / (y1 - y0)
            if lon < xin:
                inside = not inside
    return inside


def _on_land(lon, lat):
    return any(_in_poly(lon, lat, p) for p in CONTINENTS)


def draw_map(cv, x, y, w, h, pins):
    cv.rect(x, y, w, h, (232, 228, 214))
    cv.rect_outline(x, y, w, h, MGREY, 1)
    step_lon, step_lat = 4, 4
    for lat in range(-54, 84, step_lat):
        for lon in range(-180, 180, step_lon):
            if _on_land(lon, lat):
                px = x + int((lon + 180) / 360 * w)
                py = y + int((85 - lat) / 140 * h)
                cv.dot(px, py, (150, 142, 122), 1)
    for pin in pins:
        num, lon, lat, col = pin[:4]
        ox, oy = (pin[4], pin[5]) if len(pin) > 5 else (0, 0)
        px = x + int((lon + 180) / 360 * w) + ox
        py = y + int((85 - lat) / 140 * h) + oy
        cv.circle(px, py, 7, col, True)
        cv.circle(px, py, 7, INK, False)
        draw_text(cv, px - 3 if num < 10 else px - 6, py - 4,
                  str(num), 1, WHITE, True)


# ---------------------------------------------------------------- scenes
def _sky(cv, x, y, w, h, col=SKY):
    cv.rect(x, y, w, h, col)


def _building(cv, x, y, w, h, col, lit=True):
    cv.rect(x, y, w, h, col)
    if lit:
        for wy in range(y + 5, y + h - 4, 8):
            for wx in range(x + 3, x + w - 3, 7):
                if (wx * 7 + wy * 3) % 11 < 4:
                    cv.rect(wx, wy, 2, 3, (255, 220, 120))


def scene_riyadh(cv, x, y, w, h):
    _sky(cv, x, y, w, h)
    cv.circle(x + w - 26, y + 18, 11, (255, 214, 120))
    _building(cv, x + 8, y + h - 58, 34, 58, (120, 110, 96))
    _building(cv, x + 48, y + h - 78, 30, 78, (96, 88, 78))
    # PIF tower: tall, tapering, lit crown
    cv.poly([(x + w // 2 - 14, y + h), (x + w // 2 - 9, y + 14),
             (x + w // 2 + 9, y + 14), (x + w // 2 + 14, y + h)],
            (52, 52, 58))
    cv.rect(x + w // 2 - 9, y + 14, 18, 8, (255, 220, 120))
    for wy in range(y + 30, y + h - 6, 10):
        cv.rect(x + w // 2 - 5, wy, 3, 4, (255, 220, 120))
        cv.rect(x + w // 2 + 2, wy + 5, 3, 4, (255, 220, 120))
    # smoke + drone
    cv.circle(x + w // 2 + 22, y + 22, 7, (150, 150, 150))
    cv.circle(x + w // 2 + 32, y + 16, 9, (170, 170, 170))
    cv.circle(x + w // 2 + 42, y + 24, 6, (150, 150, 150))
    cv.line(x + 18, y + 26, x + 34, y + 22, INK, 2)
    cv.line(x + 18, y + 22, x + 34, y + 26, INK, 2)
    cv.circle(x + 26, y + 24, 2, INK)
    cv.rect(x, y + h - 6, w, 6, (90, 82, 70))


def scene_hormuz(cv, x, y, w, h):
    _sky(cv, x, y, w, h)
    cv.circle(x + w - 24, y + 16, 10, (255, 214, 120))
    sea_y = y + h * 2 // 3
    cv.rect(x, sea_y, w, h - h * 2 // 3, SEA)
    for i in range(3):
        tx = x + 12 + i * (w // 3)
        # tanker hull
        cv.poly([(tx, sea_y + 12), (tx + w // 3 - 14, sea_y + 12),
                 (tx + w // 3 - 20, sea_y + 24), (tx + 6, sea_y + 24)],
                (140, 40, 30) if i == 1 else (60, 60, 66))
        cv.rect(tx + 8, sea_y + 2, 12, 10, (220, 180, 60))
        cv.rect(tx + 24, sea_y + 4, 12, 8, (200, 200, 200))
    # fire + smoke on the middle tanker
    cv.circle(x + w // 2, sea_y + 2, 6, ORANGE)
    cv.circle(x + w // 2 + 8, sea_y - 4, 5, (230, 180, 40))
    cv.circle(x + w // 2 + 16, sea_y - 12, 7, (150, 150, 150))
    cv.circle(x + w // 2 + 26, sea_y - 18, 9, (170, 170, 170))
    # mine spikes
    mx, my = x + w - 34, sea_y + 30
    cv.circle(mx, my, 5, INK)
    for dx, dy in ((-7, 0), (7, 0), (0, -7), (0, 7), (-5, -5), (5, -5),
                   (-5, 5), (5, 5)):
        cv.line(mx, my, mx + dx, my + dy, INK, 2)


def scene_dow(cv, x, y, w, h):
    cv.rect(x, y, w, h, NAVY)
    cv.line(x + 14, y + h - 22, x + w - 12, y + h - 22, (120, 130, 150), 1)
    cv.line(x + 14, y + 12, x + 14, y + h - 22, (120, 130, 150), 1)
    pts = [(x + 16, y + h - 40), (x + w // 4, y + h - 52),
           (x + w // 2, y + h - 34), (x + 3 * w // 4, y + h - 58),
           (x + w - 16, y + 22)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        cv.line(ax, ay, bx, by, (80, 200, 120), 3)
    # Nasdaq falling line
    pts2 = [(x + 16, y + h - 66), (x + w // 3, y + h - 60),
            (x + 2 * w // 3, y + h - 44), (x + w - 16, y + h - 30)]
    for (ax, ay), (bx, by) in zip(pts2, pts2[1:]):
        cv.line(ax, ay, bx, by, (230, 90, 80), 2)
    cv.circle(x + w - 16, y + 22, 4, (80, 200, 120))
    cv.rect(x + 14, y + 12, 4, 4, (80, 200, 120))


def scene_shanghai(cv, x, y, w, h):
    _sky(cv, x, y, w, h, (238, 228, 200))
    _building(cv, x + 6, y + h - 44, 22, 44, (110, 100, 88))
    _building(cv, x + 32, y + h - 62, 24, 62, (90, 82, 74))
    _building(cv, x + 60, y + h - 36, 20, 36, (120, 110, 96))
    # magnifier
    cx, cy, r = x + w - 26, y + 26, 16
    cv.circle(cx, cy, r, WHITE, False)
    cv.circle(cx, cy, r, INK, False)
    cv.line(cx + 11, cy + 11, cx + 22, cy + 22, INK, 3)
    cv.circle(cx, cy, 3, RED)


def scene_huawei(cv, x, y, w, h):
    _sky(cv, x, y, w, h, (228, 226, 214))
    # courthouse pediment + columns
    cv.poly([(x + 8, y + 22), (x + w // 2, y + 6), (x + w - 8, y + 22)],
            (210, 204, 186))
    for cx in (x + 16, x + w // 2 - 4, x + w - 24):
        cv.rect(cx, y + 24, 7, h - 30, (232, 228, 214))
    cv.rect(x + 6, y + h - 8, w - 12, 6, (180, 172, 150))
    # gavel
    cv.line(x + w - 34, y + h - 26, x + w - 12, y + h - 38, (90, 60, 30), 4)
    cv.rect(x + w - 40, y + h - 30, 12, 6, (90, 60, 30))


def scene_zaporizhzhia(cv, x, y, w, h):
    _sky(cv, x, y, w, h, (210, 214, 224))
    _building(cv, x + 10, y + h - 52, 40, 52, (140, 132, 118))
    _building(cv, x + 56, y + h - 40, 30, 40, (120, 112, 100))
    # damaged corner + smoke
    cv.rect(x + 34, y + h - 52, 16, 14, (60, 56, 50))
    cv.circle(x + 42, y + h - 58, 7, (120, 120, 120))
    cv.circle(x + 52, y + h - 66, 9, (140, 140, 140))
    cv.circle(x + 64, y + h - 72, 6, (160, 160, 160))
    for dx in (18, 44, 70):
        cv.line(x + dx, y + 12, x + dx + 12, y + 10, INK, 1)
        cv.line(x + dx, y + 10, x + dx + 12, y + 12, INK, 1)


def scene_senegal(cv, x, y, w, h):
    _sky(cv, x, y, w, h, (238, 232, 210))
    # flag stripes + star
    fx, fy, fw, fh = x + 8, y + 8, 30, 20
    cv.rect(fx, fy, fw // 3, fh, GREEN)
    cv.rect(fx + fw // 3, fy, fw // 3, fh, (240, 210, 40))
    cv.rect(fx + 2 * fw // 3, fy, fw // 3, fh, RED)
    cv.circle(fx + fw // 2, fy + fh // 2, 4, GREEN)
    # trophy
    tx, ty = x + w - 42, y + 8
    cv.poly([(tx, ty), (tx + 22, ty), (tx + 18, ty + 18),
             (tx + 4, ty + 18)], GOLD)
    cv.line(tx - 4, ty + 4, tx, ty + 10, GOLD, 2)
    cv.line(tx + 26, ty + 4, tx + 22, ty + 10, GOLD, 2)
    cv.rect(tx + 8, ty + 18, 6, 6, GOLD)
    cv.rect(tx + 2, ty + 24, 18, 4, GOLD)
    cv.circle(x + w // 2, y + h - 16, 9, WHITE)
    cv.poly([(x + w // 2, y + h - 24), (x + w // 2 + 3, y + h - 15),
             (x + w // 2 + 9, y + h - 14), (x + w // 2 + 4, y + h - 10),
             (x + w // 2 + 6, y + h - 4), (x + w // 2, y + h - 8),
             (x + w // 2 - 6, y + h - 4), (x + w // 2 - 4, y + h - 10),
             (x + w // 2 - 9, y + h - 14), (x + w // 2 - 3, y + h - 15)],
            INK)


def scene_sanofi(cv, x, y, w, h):
    _sky(cv, x, y, w, h, (232, 238, 244))
    # big capsule, diagonal
    cx, cy = x + w // 2, y + h // 2
    cv.poly([(cx - 26, cy + 4), (cx - 10, cy - 12), (cx + 26, cy - 4),
             (cx + 10, cy + 12)], (220, 60, 80))
    cv.poly([(cx - 26, cy + 4), (cx - 2, cy - 8), (cx + 2, cy + 8),
             (cx - 10, cy + 12)], (240, 240, 240))
    cv.circle(cx - 30, cy + 18, 5, (120, 170, 220))
    cv.circle(cx + 32, cy - 16, 4, (120, 170, 220))
    cv.circle(cx + 30, cy + 20, 4, GOLD)


def scene_gaza(cv, x, y, w, h):
    _sky(cv, x, y, w, h, (240, 222, 190))
    _building(cv, x + 8, y + h - 40, 26, 40, (130, 118, 100))
    _building(cv, x + 40, y + h - 30, 22, 30, (110, 100, 86))
    # explosion burst
    bx, by = x + w - 28, y + 22
    for dx, dy in ((-12, 0), (12, 0), (0, -12), (0, 12), (-9, -9),
                   (9, -9), (-9, 9), (9, 9)):
        cv.line(bx, by, bx + dx, by + dy, ORANGE, 3)
    cv.circle(bx, by, 6, (250, 200, 60))
    cv.circle(bx - 16, by + 8, 6, (150, 150, 150))
    cv.circle(bx - 24, by - 2, 8, (170, 170, 170))


def scene_taiex(cv, x, y, w, h):
    _sky(cv, x, y, w, h, (226, 238, 226))
    cv.line(x + 10, y + h - 16, x + w - 8, y + h - 16, MGREY, 1)
    pts = [(x + 10, y + h - 24), (x + w // 3, y + h - 34),
           (x + w // 2, y + h - 30), (x + 2 * w // 3, y + h - 48),
           (x + w - 10, y + 12)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        cv.line(ax, ay, bx, by, GREEN, 3)
    cv.line(x + w - 22, y + 12, x + w - 10, y + 12, GREEN, 3)
    cv.line(x + w - 10, y + 12, x + w - 10, y + 24, GREEN, 3)
    cv.circle(x + w - 10, y + 12, 3, GREEN)


def scene_heat(cv, x, y, w, h):
    _sky(cv, x, y, w, h, (250, 232, 190))
    cv.circle(x + 22, y + 20, 12, (250, 190, 60))
    for dx, dy in ((-16, 0), (16, 0), (0, -16), (0, 16), (-11, -11),
                   (11, -11), (-11, 11), (11, 11)):
        cv.line(x + 22, y + 20, x + 22 + dx, y + 20 + dy, (250, 190, 60), 2)
    # thermometer
    tx = x + w - 26
    cv.rect(tx, y + 12, 8, h - 24, WHITE)
    cv.rect_outline(tx, y + 12, 8, h - 24, INK, 1)
    cv.rect(tx + 2, y + h - 26, 4, 14, RED)
    cv.circle(tx + 4, y + h - 12, 6, RED)
    _building(cv, x + 8, y + h - 22, w - 16, 22, (150, 130, 100), lit=False)


def scene_tiangong(cv, x, y, w, h):
    cv.rect(x, y, w, h, (18, 24, 48))
    for sx, sy in ((12, 10), (30, 22), (w - 16, 12), (w - 34, 26),
                   (w // 2, 8), (16, 34), (w - 12, 40)):
        cv.dot(x + sx, y + sy, WHITE, 1)
    # rocket
    rx, ry = x + w // 2 - 5, y + 12
    cv.poly([(rx, ry + 22), (rx + 2, ry + 6), (rx + 5, ry),
             (rx + 8, ry + 6), (rx + 10, ry + 22)], WHITE)
    cv.circle(rx + 5, ry + 12, 2, SKY)
    cv.poly([(rx, ry + 22), (rx - 4, ry + 30), (rx + 2, ry + 26)], ORANGE)
    cv.poly([(rx + 10, ry + 22), (rx + 14, ry + 30), (rx + 8, ry + 26)],
            ORANGE)
    cv.circle(rx + 5, ry + 34, 4, (250, 200, 60))
    # station: hub + panels
    cv.rect(x + 8, y + h - 18, 14, 6, (140, 160, 190))
    cv.rect(x + w - 22, y + h - 18, 14, 6, (140, 160, 190))
    cv.circle(x + w // 2, y + h - 15, 5, (180, 200, 220))


def scene_korea(cv, x, y, w, h):
    _sky(cv, x, y, w, h, (210, 224, 238))
    cx, cy, r = x + 24, y + h // 2, 18
    cv.circle(cx, cy, r, (20, 60, 40), True)
    cv.circle(cx, cy, r, (80, 200, 120), False)
    cv.circle(cx, cy, r // 2, (80, 200, 120), False)
    cv.line(cx, cy, cx + 14, cy - 10, (80, 200, 120), 2)
    cv.dot(cx + 8, cy + 6, (120, 255, 150), 1)
    cv.dot(cx - 6, cy - 4, (120, 255, 150), 1)
    # jets
    for jx in (x + w - 46, x + w - 26):
        cv.poly([(jx, y + 16), (jx + 16, y + 22), (jx, y + 28),
                 (jx + 4, y + 22)], (70, 70, 78))
    cv.line(x + w - 46, y + 34, x + w - 20, y + 40, GREY, 1)
    cv.line(x + w - 46, y + 40, x + w - 20, y + 46, GREY, 1)


# ---------------------------------------------------------------- data
HEROES = [
    dict(num=1, region="Middle East", field="War", badge="CONFIRMED",
         headline="Houthi drone hits Riyadh tower",
         deck="Eleven hurt, two of them Saudi, in the second strike "
              "on the financial district in a week.",
         source="AL JAZEERA \u00b7 SPA \u00b7 REUTERS", scene=scene_riyadh),
    dict(num=2, region="Middle East", field="Shipping", badge="REPORTED",
         headline="Three ships hit in Hormuz",
         deck="Unknown projectiles strike vessels in the strait; Brent "
              "closes at $91.40, up $2.03.",
         source="UKMTO \u00b7 REUTERS", scene=scene_hormuz),
    dict(num=3, region="World", field="Markets", badge="CONFIRMED",
         headline="Dow closes back above 50,000",
         deck="The index ends at 50,018.70, up 423, as the Nasdaq "
              "falls 1.5% and Nvidia slides 5.9%.",
         source="REUTERS \u00b7 WSJ", scene=scene_dow),
]

CARDS = [
    dict(num=4, region="Asia", field="Politics", badge="OFFICIAL",
         headline="Shanghai party chief under probe",
         source="CCDI \u00b7 XINHUA", scene=scene_shanghai),
    dict(num=5, region="Americas", field="Courts", badge="CONFIRMED",
         headline="Huawei guilty on 10 of 12 counts",
         source="BBC \u00b7 CNBC", scene=scene_huawei),
    dict(num=6, region="Europe", field="War", badge="CONFIRMED",
         headline="Zaporizhzhia: 2 dead, 48 hurt",
         source="REUTERS", scene=scene_zaporizhzhia),
    dict(num=7, region="Africa", field="Sport", badge="OFFICIAL",
         headline="Senegal's AFCON title restored",
         source="CAS \u00b7 CNN", scene=scene_senegal),
    dict(num=8, region="Europe", field="Business", badge="OFFICIAL",
         headline="Sanofi to buy Insmed for $41bn",
         source="REUTERS", scene=scene_sanofi),
    dict(num=9, region="Middle East", field="War", badge="REPORTED",
         headline="Hamas security chief killed",
         source="REUTERS \u00b7 BBC", scene=scene_gaza),
    dict(num=10, region="Asia", field="Markets", badge="CONFIRMED",
         headline="Taiex soars 9% to a record close",
         source="FOCUS TAIWAN \u00b7 CNA", scene=scene_taiex),
    dict(num=11, region="Europe", field="Climate", badge="OFFICIAL",
         headline="England heat deaths: 5,258",
         source="UKHSA \u00b7 BBC", scene=scene_heat),
    dict(num=12, region="Asia", field="Space", badge="OFFICIAL",
         headline="First foreign astronaut",
         source="XINHUA \u00b7 REUTERS", scene=scene_tiangong),
    dict(num=13, region="Asia", field="Security", badge="CONFIRMED",
         headline="Ulleung alert as Russian jets near",
         source="AP \u00b7 YONHAP", scene=scene_korea),
]

ALSO = [
    (14, "Solomons to end China pact", "REUTERS", "Oceania", "Diplomacy"),
    (15, "UAE bus crash kills 13", "KHALEEJ TIMES", "Middle East", "Disaster"),
    (16, "Nepal quake M5.3, no deaths", "REUTERS", "South Asia", "Disaster"),
    (17, "Hanoi gas blast kills 6", "VNEXPRESS", "SE Asia", "Disaster"),
    (18, "Cartagena gunmen hold 25 hostages", "AP", "Americas", "Crime"),
    (19, "Cikande toll rises to 26", "CNA", "SE Asia", "Disaster"),
    (20, "Sarkozy trial set for 2027", "EURONEWS", "Europe", "Courts"),
    (21, "Microsoft declares 'Code Red'", "REUTERS", "Americas", "Technology"),
    (22, "Ariane 6 lofts 36 Amazon satellites", "ESA", "Americas", "Space"),
    (23, "US drone caught El Chapo Isidro", "FRANCE24", "Americas", "Cartels"),
    (24, "UN: 47,000 women killed by kin", "UNODC", "World", "Rights"),
    (25, "Gavi to buy 1.5m Ebola doses", "REUTERS", "Africa", "Health"),
    (26, "Ukraine seeks 115bn euros in aid", "FRANCE24", "Europe", "Aid"),
    (27, "Houthis near Aden, 60 km away", "FRANCE24", "Middle East", "Conflict"),
    (28, "Hasina plans return, Dec 16", "REUTERS", "South Asia", "Politics"),
    (29, "Iraq PM takes Kurdish oilfields", "REUTERS", "Middle East", "Energy"),
    (30, "Japan to pay ICC bill early", "JUST SECURITY", "Asia", "Justice"),
    (31, "NATO vows to defend space", "REUTERS", "World", "Defence"),
    (32, "US blacklists Singapore firm", "COMMERCE", "SE Asia", "Technology"),
    (33, "Australia inflation hits 4.9%", "GUARDIAN", "Oceania", "Economy"),
    (34, "DR Congo plane missing", "BBC", "Africa", "Conflict"),
    (35, "Commanders beat Bengals 22-20", "GUARDIAN", "Americas", "Sport"),
    (36, "Poland: peace won't end sabotage", "POLAND", "Europe", "Diplomacy"),
    (37, "China AI targets Taiwan vote", "VANDERBILT", "Asia", "Technology"),
    (38, "CIA, ODNI hit by cyberattack", "JUST SECURITY", "Americas", "Cyber"),
]

NUMBERS = [
    ("11", "hurt in Riyadh tower strike"),
    ("50,018", "Dow closes back above"),
    ("$91.40", "Brent after Hormuz hit"),
    ("5,258", "heat deaths, England record"),
    ("+8.99%", "Taiex record gain"),
    ("47,000", "women killed by partners"),
]

UTC_STRIP = [
    ("01:00", "Hanoi blast"),
    ("01:32", "Nepal quake"),
    ("05:30", "Sanofi deal"),
    ("08:14", "Ariane 6"),
    ("21:00", "Dow 50,000"),
]

DATE_CHECK = [
    "COP31 ended Sun 22 Nov, no deal \u00b7 Huang back at Nvidia Mon 23 Nov "
    "\u00b7 EU sanctions only proposed Mon 23 Nov",
    "Corvette Merkury blast Sun 22 Nov \u00b7 Shenzhou-24 launch Wed 25 Nov "
    "\u00b7 Solomons signing Wed 25 Nov",
    "Hormuz mines 9/13/14 Nov \u00b7 Cikande fire Sat 21 Nov "
    "\u00b7 El Chapo held Fri 20 Nov",
    "Microsoft outage 12-13 Nov \u00b7 Dow first topped 50,000 on 6 Feb 2026",
]

PINS = [
    (1, 46.7, 24.7, REGION_COLORS["Middle East"]),
    (2, 56.5, 26.5, REGION_COLORS["Middle East"]),
    (3, -74.0, 40.7, REGION_COLORS["World"]),
    (4, 121.5, 31.2, REGION_COLORS["Asia"]),
    (5, -74.0, 40.7, REGION_COLORS["Americas"], 14, -10),
    (6, 35.2, 47.8, REGION_COLORS["Europe"]),
    (7, -17.5, 14.7, REGION_COLORS["Africa"]),
    (8, 2.3, 48.9, REGION_COLORS["Europe"]),
    (9, 34.5, 31.5, REGION_COLORS["Middle East"]),
    (10, 121.6, 25.0, REGION_COLORS["Asia"]),
    (11, 0.0, 51.5, REGION_COLORS["Europe"]),
    (12, 98.5, 39.8, REGION_COLORS["Asia"]),
    (13, 130.9, 37.5, REGION_COLORS["Asia"]),
]


# ---------------------------------------------------------------- layout
def draw_top_bar(cv, n, nreg, nfield):
    cv.rect(0, 0, W, 26, BLACK)
    draw_text(cv, 24, 7, "THE WORLD IN ONE DAY", 1, WHITE, True)
    right = ("%d STORIES \u00b7 %d REGIONS \u00b7 %d FIELDS \u00b7 ALL FROM "
             "TUESDAY 24 NOVEMBER 2026" % (n, nreg, nfield))
    draw_text(cv, W - 24 - text_w(right, 1), 7, right, 1, WHITE, True)


def draw_region_bar(cv, counts):
    y = 108
    parts = []
    total = 0
    for region in ["Europe", "Middle East", "Asia", "Americas", "Africa",
                   "Oceania", "South Asia", "SE Asia", "World"]:
        if counts.get(region):
            parts.append((region, counts[region]))
            total += int(text_w(region.upper() + " " + str(counts[region]), 1)) + 12
    x = (W - total) // 2
    for region, cnt in parts:
        rc = REGION_COLORS[region]
        cv.rect(x, y + 1, 9, 9, rc)
        draw_text(cv, x + 13, y, region.upper() + " " + str(cnt), 1, INK, True)
        x += int(text_w(region.upper() + " " + str(cnt), 1)) + 12


def draw_utc_strip(cv):
    y = 128
    cv.line(16, y - 2, W - 16, y - 2, LGREY, 1)
    draw_text(cv, 16, y + 3, "THE DAY IN UTC", 1, RED, True)
    x = 170
    slot = (W - 16 - x) // len(UTC_STRIP)
    for t, ev in UTC_STRIP:
        draw_text(cv, x, y + 3, t, 1, RED, True)
        draw_text(cv, x + text_w(t, 1) + 5, y + 3, ev, 1, INK)
        x += slot
    cv.line(16, y + 17, W - 16, y + 17, LGREY, 1)


def draw_numbers(cv):
    y = 146
    colw = (W - 32) // len(NUMBERS)
    for i, (big, label) in enumerate(NUMBERS):
        x = 16 + i * colw
        draw_text(cv, x, y + 2, big, 2.0, RED, True)
        draw_para(cv, x, y + 26, label, 1, INK, colw - 8, leading=12)
    cv.line(16, y + 50, W - 16, y + 50, LGREY, 1)


def draw_hero(cv, h, x, y, w, ht):
    cv.rect_outline(x, y, w, ht, LGREY, 1)
    h["scene"](cv, x + 1, y + 1, w - 2, 118)
    ky = y + 126
    kicker(cv, x + 8, ky, h["region"], h["field"], 1)
    bw = badge(cv, x + w - 8 - (text_w(h["badge"], 1) + 8), ky - 1, h["badge"], 1)
    hy = y + 146
    hy_end = draw_para(cv, x + 8, hy, h["headline"], 1.75, INK, w - 16,
                       bold=True, leading=26)
    dy = hy_end + 2
    draw_para(cv, x + 8, dy, h["deck"], 1, INK, w - 16, leading=13)
    draw_text(cv, x + 8, y + ht - 16, h["source"], 1, GREY)


def draw_card(cv, c, x, y, w, ht):
    cv.rect_outline(x, y, w, ht, LGREY, 1)
    c["scene"](cv, x + 1, y + 1, w - 2, 58)
    bw = int(text_w(c["badge"], 1)) + 8
    badge(cv, x + w - 1 - bw, y + 1, c["badge"], 1)
    kicker(cv, x + 8, y + 64, c["region"], c["field"], 1)
    draw_para(cv, x + 8, y + 80, c["headline"], 1.1, INK, w - 16,
              bold=True, leading=16)
    draw_text(cv, x + 8, y + ht - 14, c["source"], 1, GREY)


def draw_also(cv, x, y, colw, items):
    yy = y + 18
    for num, head, src, _r, _f in items:
        line = "%d %s \u2014 %s" % (num, head, src)
        sc = min(0.9, colw / max(1, text_w(line, 1)))
        sc = max(sc, 0.65)
        draw_text(cv, x, yy, str(num), sc, RED, True)
        rest = " %s \u2014 %s" % (head, src)
        draw_text(cv, x + text_w(str(num) + " ", sc), yy, rest, sc, INK)
        yy += 12
    return yy


def draw_date_check(cv):
    y = 914
    draw_text(cv, 16, y, "DATE CHECK \u2014 LEFT OFF AS EARLIER NEWS",
              1, RED, True)
    yy = y + 16
    for line in DATE_CHECK:
        draw_text(cv, 16, yy, line, 0.9, INK)
        yy += 11


def draw_footer(cv):
    y = 974
    cv.line(16, y - 2, W - 16, y - 2, LGREY, 1)
    x = 16
    legend = [("CONFIRMED", "2+ outlets"), ("OFFICIAL", "on the record"),
              ("REPORTED", "one outlet"), ("CLAIM", "one side"),
              ("ONGOING", "unfolding")]
    for name, desc in legend:
        col = BADGE_COLORS[name]
        cv.rect(x, y + 2, 8, 8, col)
        txt = name + " " + desc
        draw_text(cv, x + 11, y, txt, 0.9, INK, True)
        x += int(text_w(txt, 0.9)) + 18
    draw_text(cv, 16, y + 16,
              "Every story happened or was first reported on Tuesday "
              "24 November 2026 \u00b7 Original drawings, not photographs",
              0.9, GREY)


def main():
    all_stories = [(h["region"], h["field"]) for h in HEROES]
    all_stories += [(c["region"], c["field"]) for c in CARDS]
    all_stories += [(r, f) for (_n, _h, _s, r, f) in ALSO]
    regions = {}
    fields = set()
    for r, f in all_stories:
        regions[r] = regions.get(r, 0) + 1
        fields.add(f)
    n = len(all_stories)

    cv = Canvas(W, H, CREAM)
    draw_top_bar(cv, n, len(regions), len(fields))
    draw_text_center(cv, W // 2, 30, "Tuesday 24 November 2026", 3.5, INK, True)
    draw_text_center(cv, W // 2, 88,
                     "Riyadh tower hit \u00b7 Shanghai chief probed "
                     "\u00b7 Dow back above 50,000", 1.25, RED, True)
    draw_region_bar(cv, regions)
    draw_utc_strip(cv)
    draw_numbers(cv)
    # heroes: y 198..464
    hx = [16, 349, 682]
    for h, x in zip(HEROES, hx):
        draw_hero(cv, h, x, 198, 325, 266)
    # cards: 2 rows x 5 cols, y 464..736
    cx = [16, 216, 416, 616, 816]
    for row in range(2):
        for col in range(5):
            c = CARDS[row * 5 + col]
            draw_card(cv, c, cx[col], 464 + row * 136, 192, 136)
    # also + map: y 736..914
    draw_text(cv, 16, 736, "ALSO ON TUESDAY 24 NOVEMBER", 1, RED, True)
    draw_also(cv, 16, 736, 336, ALSO[:13])
    draw_also(cv, 360, 736, 336, ALSO[13:])
    draw_text(cv, 700, 736, "WHERE IT HAPPENED", 1, RED, True)
    draw_map(cv, 700, 754, 308, 160, PINS)
    draw_date_check(cv)
    draw_footer(cv)

    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    write_png(path, cv)
    print("wrote", path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
