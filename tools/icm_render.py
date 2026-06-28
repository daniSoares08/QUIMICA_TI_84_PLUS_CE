#!/usr/bin/env python3
"""Shared plot/draw primitives for the ICM app.

A page "body" is a list of "ops" (tuples). Each op maps 1:1 to a g_* helper in
src/ui.c. The SAME op list emits C and renders a 320x240 PNG preview, so every
graph (stress-strain curve, phase diagram, crystal cell) can be checked for
off-screen / overlap before building.
"""

from PIL import Image, ImageDraw, ImageFont

SCREEN_W = 320
SCREEN_H = 240

COLORS = {
    "w": (255, 255, 255),
    "k": (0, 0, 0),
    "gr": (145, 145, 145),
    "lt": (228, 236, 244),
    "b": (35, 76, 150),
    "r": (190, 36, 36),
    "g": (34, 128, 82),
}
COL_C = {
    "w": "COL_WHITE", "k": "COL_BLACK", "gr": "COL_GRAY", "lt": "COL_LIGHT",
    "b": "COL_BLUE", "r": "COL_RED", "g": "COL_GREEN",
}
CHAR_W = 8


def _load_font():
    for name in ("consola.ttf", "cour.ttf", "lucon.ttf"):
        try:
            return ImageFont.truetype("C:/Windows/Fonts/" + name, 11)
        except OSError:
            continue
    return ImageFont.load_default()


_FONT = _load_font()


def text_w(s):
    return CHAR_W * len(s)


def _s(v):
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


_C_EMIT = {
    "line": lambda a: "g_line(%d, %d, %d, %d, %s);" % (a[0], a[1], a[2], a[3], COL_C[a[4]]),
    "dash": lambda a: "g_dash(%d, %d, %d, %d, %s);" % (a[0], a[1], a[2], a[3], COL_C[a[4]]),
    "dot": lambda a: "g_dot(%d, %d, %s);" % (a[0], a[1], COL_C[a[2]]),
    "circ": lambda a: "g_circ(%d, %d, %d, %s);" % (a[0], a[1], a[2], COL_C[a[3]]),
    "disc": lambda a: "g_disc(%d, %d, %d, %s);" % (a[0], a[1], a[2], COL_C[a[3]]),
    "text": lambda a: "g_text(%s, %d, %d, %s);" % (_s(a[0]), a[1], a[2], COL_C[a[3]]),
    "axes": lambda a: "g_axes(%d, %d, %d, %d);" % a,
}


def emit_body_c(name, ops):
    body = ["static void %s(void) {" % name]
    for op in ops:
        body.append("    " + _C_EMIT[op[0]](op[1:]))
    body.append("}")
    return "\n".join(body)


# --------------------------------------------------------------------------
# PIL rendering (mirror of src/ui.c g_* helpers)
# --------------------------------------------------------------------------

class _R:
    def __init__(self, draw):
        self.d = draw

    def text(self, s, x, y, col="k"):
        c = COLORS[col]
        for i, ch in enumerate(str(s)):
            self.d.text((x + i * CHAR_W, y - 1), ch, font=_FONT, fill=c)

    def line(self, x1, y1, x2, y2, col="k"):
        self.d.line((x1, y1, x2, y2), fill=COLORS[col], width=1)

    def dash(self, x1, y1, x2, y2, col="k"):
        dx, dy = x2 - x1, y2 - y1
        steps = max(abs(dx), abs(dy))
        if steps == 0:
            return
        for i in range(steps + 1):
            if (i // 3) % 2 == 0:
                px = x1 + dx * i // steps
                py = y1 + dy * i // steps
                self.d.point((px, py), fill=COLORS[col])

    def disc(self, x, y, r, col):
        self.d.ellipse((x - r, y - r, x + r, y + r), fill=COLORS[col],
                       outline=COLORS["k"])

    def circ(self, x, y, r, col):
        self.d.ellipse((x - r, y - r, x + r, y + r), outline=COLORS[col])

    def dot(self, x, y, col):
        self.d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=COLORS[col])


def _draw_op(r, op):
    k = op[0]
    a = op[1:]
    if k == "line":
        r.line(a[0], a[1], a[2], a[3], a[4])
    elif k == "dash":
        r.dash(a[0], a[1], a[2], a[3], a[4])
    elif k == "dot":
        r.dot(a[0], a[1], a[2])
    elif k == "circ":
        r.circ(a[0], a[1], a[2], a[3])
    elif k == "disc":
        r.disc(a[0], a[1], a[2], a[3])
    elif k == "text":
        r.text(a[0], a[1], a[2], a[3])
    elif k == "axes":
        x0, y0, x1, y1 = a
        r.line(x0, y0, x0, y1)
        r.line(x0, y1, x1, y1)
        r.line(x0, y0, x0 - 3, y0 + 6)
        r.line(x0, y0, x0 + 3, y0 + 6)
        r.line(x1, y1, x1 - 6, y1 - 3)
        r.line(x1, y1, x1 - 6, y1 + 3)
    else:
        raise ValueError("unknown op %r" % (op,))


def render_ops(draw, ops):
    r = _R(draw)
    for op in ops:
        _draw_op(r, op)


def render_page(page, topic="", ex_meta="", ex_title=""):
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), COLORS["w"])
    d = ImageDraw.Draw(img)
    r = _R(d)
    if topic:
        r.text(topic, 2, 2)
        if ex_meta:
            r.text(ex_meta, 190, 2)
        r.line(0, 14, SCREEN_W, 14)
        if ex_title:
            r.text(ex_title, 8, 18, "gr")
    if page.get("title"):
        t = page["title"]
        r.text(t, (SCREEN_W - text_w(t)) // 2, 30)
    if page.get("subtitle"):
        s = page["subtitle"]
        r.text(s, (SCREEN_W - text_w(s)) // 2, 44, "gr")
    if page.get("body"):
        render_ops(d, page["body"])
    for (text, x, y, color) in page.get("lines", []):
        r.text(text, x, y, color)
    if page.get("result"):
        y = page.get("result_y", 186)
        d.rectangle((24, y, 24 + 272, y + 30), outline=COLORS["b"])
        d.rectangle((25, y + 1, 25 + 270, y + 1 + 28), outline=COLORS["b"])
        t = page["result"]
        r.text(t, (SCREEN_W - text_w(t)) // 2, y + 10, "b")
    r.line(0, 224, SCREEN_W, 224, "gr")
    r.text("UP/DN ex  </> pg  CLEAR volta ON sair", 2, 229)
    return img
