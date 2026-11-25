#!/usr/bin/env python3
"""news-image-20261124 v2 — 'The World by the Numbers'.

A one-page front page summing up Tuesday 24 November 2026.
Hero: five big verified numbers. Below: 32 dated stories, 10 regions.
Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).

Pure Python 3.13 standard library. No network, no file reads, no fonts:
every glyph is a hand-built single-stroke vector on a 10x14 grid, drawn
fresh in this session. Deterministic: same bytes every run.
"""

import os
import struct
import sys
import zlib

W, H = 1024, 1024

PAPER = (250, 246, 236)
INK = (26, 26, 26)
RED = (178, 34, 34)
SOFT = (110, 105, 95)
GREY = (200, 192, 180)
CARD = (255, 253, 247)
WHITE = (255, 255, 255)

REGION_COLORS = {
    "UKRAINE": (30, 90, 200),
    "MIDEAST": (0, 130, 120),
    "IRAN": (150, 70, 20),
    "EUROPE": (120, 60, 200),
    "MARKETS": (170, 120, 0),
    "TECH": (40, 110, 180),
    "ASIA": (0, 140, 90),
    "USA": (150, 40, 60),
    "CHINA": (200, 30, 30),
    "AFRICA": (140, 90, 0),
}


def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def encode_png(rgb, w, h):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + _chunk(b"IEND", b""))


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def dot(self, x, y, color, t):
        r = t // 2
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                self.set(x + dx, y + dy, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.dot(x, y, color, t)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def polyline(self, pts, color, t=1):
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1], color, t)

    def hline(self, x0, x1, y, color, t=1):
        for x in range(x0, x1 + 1):
            self.dot(x, y, color, t)

    def vline(self, x, y0, y1, color, t=1):
        for y in range(y0, y1 + 1):
            self.dot(x, y, color, t)

    def rect(self, x, y, w, h, color, t=1):
        self.hline(x, x + w, y, color, t)
        self.hline(x, x + w, y + h, color, t)
        self.vline(x, y, y + h, color, t)
        self.vline(x + w, y, y + h, color, t)

    def fill_rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def circle(self, cx, cy, r, color, filled=False, t=1):
        if filled:
            for yy in range(-r, r + 1):
                span = int((r * r - yy * yy) ** 0.5)
                for xx in range(-span, span + 1):
                    self.set(cx + xx, cy + yy, color)
            return
        x, y, d = 0, r, 3 - 2 * r
        while x <= y:
            for px, py in ((x, y), (y, x), (-x, y), (-y, x),
                           (x, -y), (y, -x), (-x, -y), (-y, -x)):
                self.dot(cx + px, cy + py, color, t)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

# Single-stroke vector font, 10 wide x 14 tall. Each glyph is a list of
# polylines in grid units; drawn scaled to the requested pixel size.
FONT = {
    "A": [[(1, 13), (5, 1), (9, 13)], [(3, 9), (7, 9)]],
    "B": [[(1, 1), (1, 13)],
          [(1, 1), (7, 1), (9, 3), (9, 6), (7, 7), (1, 7)],
          [(1, 7), (7, 7), (9, 9), (9, 12), (7, 13), (1, 13)]],
    "C": [[(9, 2), (7, 1), (3, 1), (1, 3), (1, 11), (3, 13), (7, 13), (9, 11)]],
    "D": [[(1, 1), (1, 13)], [(1, 1), (7, 1), (9, 4), (9, 10), (7, 13), (1, 13)]],
    "E": [[(1, 1), (1, 13)], [(1, 1), (9, 1)], [(1, 7), (7, 7)], [(1, 13), (9, 13)]],
    "F": [[(1, 1), (1, 13)], [(1, 1), (9, 1)], [(1, 7), (7, 7)]],
    "G": [[(9, 3), (7, 1), (3, 1), (1, 3), (1, 11), (3, 13), (7, 13),
           (9, 11), (9, 7), (5, 7)]],
    "H": [[(1, 1), (1, 13)], [(9, 1), (9, 13)], [(1, 7), (9, 7)]],
    "I": [[(2, 1), (8, 1)], [(5, 1), (5, 13)], [(2, 13), (8, 13)]],
    "J": [[(9, 1), (9, 11), (7, 13), (3, 13), (1, 11)]],
    "K": [[(1, 1), (1, 13)], [(9, 1), (1, 7), (9, 13)]],
    "L": [[(1, 1), (1, 13)], [(1, 13), (9, 13)]],
    "M": [[(1, 13), (1, 1), (5, 6), (9, 1), (9, 13)]],
    "N": [[(1, 13), (1, 1), (9, 13), (9, 1)]],
    "O": [[(2, 1), (8, 1), (9, 3), (9, 11), (8, 13), (2, 13), (1, 11),
           (1, 3), (2, 1)]],
    "P": [[(1, 1), (1, 13)], [(1, 1), (8, 1), (9, 3), (9, 6), (7, 7), (1, 7)]],
    "Q": [[(2, 1), (8, 1), (9, 3), (9, 11), (8, 13), (2, 13), (1, 11),
           (1, 3), (2, 1)], [(6, 9), (9, 13)]],
    "R": [[(1, 1), (1, 13)], [(1, 1), (8, 1), (9, 3), (9, 6), (7, 7), (1, 7)],
          [(5, 7), (9, 13)]],
    "S": [[(9, 2), (7, 1), (3, 1), (1, 3), (1, 6), (3, 7), (8, 7), (9, 9),
           (9, 12), (7, 13), (3, 13), (1, 11)]],
    "T": [[(1, 1), (9, 1)], [(5, 1), (5, 13)]],
    "U": [[(1, 1), (1, 12), (3, 13), (7, 13), (9, 12), (9, 1)]],
    "V": [[(1, 1), (5, 13), (9, 1)]],
    "W": [[(1, 1), (3, 13), (5, 7), (7, 13), (9, 1)]],
    "X": [[(1, 1), (9, 13)], [(9, 1), (1, 13)]],
    "Y": [[(1, 1), (5, 7), (9, 1)], [(5, 7), (5, 13)]],
    "Z": [[(1, 1), (9, 1), (1, 13), (9, 13)]],
}

FONT.update({
    "0": [[(2, 1), (8, 1), (9, 3), (9, 11), (8, 13), (2, 13), (1, 11),
           (1, 3), (2, 1)]],
    "1": [[(3, 4), (6, 1), (6, 13)], [(3, 13), (9, 13)]],
    "2": [[(1, 3), (2, 1), (8, 1), (9, 3), (9, 6), (1, 13), (9, 13)]],
    "3": [[(1, 2), (7, 1), (9, 3), (9, 6), (6, 7), (9, 8), (9, 12),
           (7, 13), (1, 13)]],
    "4": [[(8, 1), (1, 9), (9, 9)], [(6, 1), (6, 13)]],
    "5": [[(9, 1), (1, 1), (1, 6), (8, 6), (9, 8), (9, 12), (8, 13), (1, 13)]],
    "6": [[(8, 1), (3, 1), (1, 4), (1, 12), (3, 13), (8, 13), (9, 11),
           (9, 8), (7, 7), (1, 7)]],
    "7": [[(1, 1), (9, 1), (4, 13)]],
    "8": [[(3, 1), (7, 1), (9, 3), (9, 6), (7, 7), (3, 7), (1, 6), (1, 3),
           (3, 1)],
          [(3, 7), (7, 7), (9, 9), (9, 12), (7, 13), (3, 13), (1, 12),
           (1, 9), (3, 7)]],
    "9": [[(2, 13), (8, 13), (9, 11), (9, 3), (8, 1), (2, 1), (1, 3),
           (1, 7), (9, 7)]],
    "%": [[(2, 2), (4, 2), (4, 5), (2, 5), (2, 2)],
          [(6, 9), (8, 9), (8, 12), (6, 12), (6, 9)],
          [(1, 13), (9, 1)]],
    "$": [[(5, 0), (5, 14)], [(8, 3), (3, 3), (3, 7), (8, 7), (8, 11), (3, 11)]],
    "+": [[(5, 3), (5, 11)], [(1, 7), (9, 7)]],
    ",": [[(4, 11), (3, 14)]],
    ".": [[(4, 12), (4, 13)]],
    "-": [[(2, 7), (8, 7)]],
    ":": [[(4, 4), (4, 5)], [(4, 9), (4, 10)]],
    "/": [[(8, 13), (2, 1)]],
    "'": [[(5, 1), (4, 4)]],
    "!": [[(5, 1), (5, 9)], [(5, 12), (5, 13)]],
})


def _adv(size):
    return size * 13 // 10


def text_width(text, size):
    if not text:
        return 0
    return len(text) * _adv(size) - size * 3 // 10


def draw_text(cv, x, y, text, size, color):
    t = max(1, size // 7)
    cx = x
    for ch in text:
        strokes = FONT.get(ch)
        if strokes:
            for pts in strokes:
                scaled = [(cx + gx * size // 10, y + gy * size // 14)
                          for gx, gy in pts]
                cv.polyline(scaled, color, t)
        cx += _adv(size)
    return cx


def wrap_text(text, size, max_w):
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, size) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, x, y, text, size, color, max_w, leading, max_lines):
    lines = wrap_text(text, size, max_w)[:max_lines]
    for i, line in enumerate(lines):
        draw_text(cv, x, y + i * leading, line, size, color)
    return y + len(lines) * leading


def draw_kicker(cv, x, y, region, size):
    color = REGION_COLORS.get(region, INK)
    cv.circle(x + 4, y + size // 2 - 1, 3, color, filled=True)
    draw_text(cv, x + 11, y, region, size, color)

# Five verified numbers from Tuesday 24 November 2026. Each card shows
# the big figure plus the exact fact in small lines underneath.
# (region, big number, label line 1, label line 2, label line 3)
HERO_STATS = [
    ("MARKETS", "8.99%", "TAIEX RECORD", "CLOSE 40,122", "TSMC LIMIT-UP"),
    ("MARKETS", "$41B", "SANOFI BUYS", "INSMED", "$175 A SHARE"),
    ("UKRAINE", "700K", "RUSSIAN DEAD", "700,000", "STUDY SAYS"),
    ("AFRICA", "1-0", "SENEGAL WINS", "AFCON TITLE", "CAS RESTORES"),
    ("UKRAINE", "40", "WOUNDED IN", "ZAPORIZHZHIA", "2 DEAD"),
]

# 32 dated stories, 10 regions. Every headline + deck was checked
# against live reporting of 24 Nov 2026 (see NEWS.md).
# (region, headline, one-line deck, max 17 chars)
STORIES = [
    ("UKRAINE", "KYIV DRONES HIT RUSSIAN SHIP IN LIBYA", "HIT AT BENGHAZI"),
    ("MIDEAST", "GAZA STRIKES KILL HAMAS SECURITY CHIEF", "SEVEN DEAD IN GAZA"),
    ("IRAN", "TEHRAN VOWS TO FIGHT US NAVAL BLOCKADE", "USE ALL TOOLS"),
    ("IRAN", "VANCE AND RUBIO MEET QATAR PM AT WHITE HOUSE", "QATAR PM IN DC"),
    ("EUROPE", "NATO VOWS TO DEFEND SPACE", "DEFENDS SPACE"),
    ("EUROPE", "SEVEN STATES URGE EU TO CURB RUSSIAN TRAVEL", "VISA CURBS URGED"),
    ("UKRAINE", "BERLIN FIRST TO TAP KYIV SYSTEM", "DELTA DEAL SIGNED"),
    ("UKRAINE", "ZELENSKY: ADMIT UKRAINE TO NATO", "PLEA IN BERLIN"),
    ("TECH", "HUANG BACK AS NVIDIA CEO", "SHARES UP 31.5%"),
    ("TECH", "US BLACKLISTS SINGAPORE CLOUD FIRM", "ENTITY LISTED"),
    ("TECH", "HUAWEI CONVICTED IN US ESPIONAGE TRIAL", "ESPIONAGE VERDICT"),
    ("TECH", "CHINA AI CAMPAIGN TARGETS TAIWAN VOTE", "AI INFLUENCE PUSH"),
    ("ASIA", "KOREA REWARDS AI EXAM CHEAT TIPS", "UP TO $375,000"),
    ("MARKETS", "UK ENERGY BILLS SET TO RISE 26%", "443 MORE A YEAR"),
    ("USA", "PENTAGON: CANADA FALLS SHORT ON DEFENCE", "OTTAWA REBUKED"),
    ("EUROPE", "POLAND: PEACE DEAL WON'T END SABOTAGE", "SABOTAGE WARNING"),
    ("EUROPE", "LATVIA: WAR MAY TIP TOWARD RUSSIAN DEFEAT", "DEFEAT POSSIBLE"),
    ("AFRICA", "DR CONGO FIGHTING TRAPS EBOLA TEAMS", "TEAMS TAKE COVER"),
    ("ASIA", "IRAQ PM TAKES KURDISH OILFIELDS", "OILFIELDS SEIZED"),
    ("AFRICA", "AMNESTY: TIGRAY STRIKES MAY BE WAR CRIMES", "WAR CRIMES PROBE"),
    ("ASIA", "HASINA PLANS RETURN TO BANGLADESH", "RETURN SET DEC 16"),
    ("ASIA", "JAPAN TO PAY ICC BILL EARLY", "ICC PAID EARLY"),
    ("USA", "TRUMP ORDERS DOJ TO SPEED DEATH SENTENCES", "DEATH ROW SPEED-UP"),
    ("USA", "CIA AND ODNI HIT BY CYBERATTACK", "BREACH REPORTED"),
    ("EUROPE", "UK SANCTIONS FIVE MYANMAR GENERALS", "GENOCIDE RULING"),
    ("UKRAINE", "RUSSIAN DRONE PROBED POLISH AIRSPACE", "FIRE WITHHELD"),
    ("MARKETS", "TSMC HITS LIMIT-UP AT NT$2,230", "CHIP RALLY"),
    ("MIDEAST", "US TO TRAIN SYRIAN SOLDIERS IN DEMINING", "DEMINING TRAINING"),
    ("CHINA", "SHANGHAI CHIEF FALLS IN XI PURGE", "CHEN JINING PROBED"),
    ("MIDEAST", "HUCKABEE DOUBTS END OF ISRAEL AID", "AID LIKELY STAYS"),
    ("USA", "ILHAN OMAR SEARCH FILES UNSEALED", "PROBE BACK TO 1980"),
    ("USA", "US CITIZEN DEPORTED BY ICE ERROR", "WRONGFUL REMOVAL"),
]

def draw_masthead(cv):
    draw_text(cv, 24, 14, "THE WORLD", 46, INK)
    draw_text(cv, 24, 62, "BY THE NUMBERS", 34, INK)
    right = "TUESDAY"
    draw_text(cv, 1000 - text_width(right, 22), 18, right, 22, RED)
    right2 = "24 NOV 2026"
    draw_text(cv, 1000 - text_width(right2, 22), 50, right2, 22, INK)
    cv.hline(24, 1000, 122, INK, 3)


def draw_strip(cv):
    draw_text(cv, 24, 132, "SHANGHAI PURGE - TAIEX +8.99% - SENEGAL CROWNED",
              13, RED)


def draw_hero(cv):
    y0, card_h = 162, 124
    for i, (region, big, l1, l2, l3) in enumerate(HERO_STATS):
        x = 24 + i * 196
        cv.fill_rect(x, y0, 190, card_h, CARD)
        cv.fill_rect(x, y0, 190, 3, RED)
        cv.rect(x, y0, 190, card_h, INK, 1)
        draw_kicker(cv, x + 10, y0 + 10, region, 9)
        draw_text(cv, x + 8, y0 + 28, big, 28, RED)
        draw_text(cv, x + 10, y0 + 66, l1, 10, INK)
        draw_text(cv, x + 10, y0 + 78, l2, 10, INK)
        draw_text(cv, x + 10, y0 + 90, l3, 10, SOFT)


def draw_grid(cv):
    draw_text(cv, 24, 298, "THE DAY IN BRIEF", 24, INK)
    right = "32 STORIES"
    draw_text(cv, 1000 - text_width(right, 13), 304, right, 13, SOFT)
    cv.hline(24, 1000, 330, INK, 3)
    y0, col_w, gap, per_col = 338, 232, 16, 8
    item_h = 77
    for c in range(4):
        cx = 24 + c * (col_w + gap)
        for ri in range(per_col):
            idx = c * per_col + ri
            if idx >= len(STORIES):
                break
            region, headline, deck = STORIES[idx]
            iy = y0 + ri * item_h
            draw_kicker(cv, cx, iy + 2, region, 10)
            draw_para(cv, cx, iy + 15, headline, 11, INK, col_w, 12, 3)
            draw_para(cv, cx, iy + 55, deck, 10, SOFT, col_w, 12, 1)
            if ri < per_col - 1:
                cv.hline(cx, cx + col_w, iy + item_h - 1, GREY, 1)


def draw_footer(cv):
    cv.hline(24, 1000, 966, INK, 3)
    draw_text(cv, 24, 976, "ALL 32 STORIES: TUESDAY 24 NOVEMBER 2026", 16, INK)
    draw_text(cv, 24, 998, "NOTHING HERE IS FROM BEFORE 13 NOVEMBER 2026.",
              13, SOFT)


def main():
    cv = Canvas(W, H, PAPER)
    draw_masthead(cv)
    draw_strip(cv)
    draw_hero(cv)
    draw_grid(cv)
    draw_footer(cv)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(encode_png(bytes(cv.buf), W, H))
    print(f"wrote {path} ({os.path.getsize(path)} bytes)")


if __name__ == "__main__":
    main()
