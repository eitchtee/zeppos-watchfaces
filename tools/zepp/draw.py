"""Drawing primitives for LCD / retro style watchface assets.

All functions return RGBA Pillow images. Sizes are given as specs
(w, h, thickness) where relevant.
"""
from PIL import Image, ImageDraw

SS = 4  # supersampling for anti-aliased edges
CLEAR = (0, 0, 0, 0)
SKEW = 0.06  # default italic lean for 7-segment glyphs

SEGMENTS = {
    "0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc",
    "5": "afgcd", "6": "afgedc", "7": "fabc", "8": "abcdefg", "9": "abcdfg",
    "-": "g", " ": "",
}

def seg_polys(w, h, t, gap):
    """Hexagonal-ended segment polygons in an upright w x h box."""
    ht = t / 2
    xl, xr = ht, w - ht
    yt, ym, yb = ht, h / 2, h - ht

    def hseg(x0, x1, y):
        return [(x0, y), (x0 + ht, y - ht), (x1 - ht, y - ht),
                (x1, y), (x1 - ht, y + ht), (x0 + ht, y + ht)]

    def vseg(x, y0, y1):
        return [(x, y0), (x + ht, y0 + ht), (x + ht, y1 - ht),
                (x, y1), (x - ht, y1 - ht), (x - ht, y0 + ht)]

    return {
        "a": hseg(xl + gap, xr - gap, yt),
        "g": hseg(xl + gap, xr - gap, ym),
        "d": hseg(xl + gap, xr - gap, yb),
        "f": vseg(xl, yt + gap, ym - gap),
        "b": vseg(xr, yt + gap, ym - gap),
        "e": vseg(xl, ym + gap, yb - gap),
        "c": vseg(xr, ym + gap, yb - gap),
    }

def skewed(poly, h, skew=SKEW):
    return [(x + (h - y) * skew, y) for x, y in poly]

def img_w(w, h, skew=SKEW):
    """Image width of a glyph box once the skew is applied."""
    return int(round(w + h * skew))

def seg_char(ch, w, h, t, color, ghost=None, skew=SKEW):
    gap = max(1.0, t * 0.12)
    iw = img_w(w, h, skew)
    big = Image.new("RGBA", (iw * SS, h * SS), CLEAR)
    d = ImageDraw.Draw(big)
    polys = seg_polys(w, h, t, gap)
    on = SEGMENTS[ch]
    for name, poly in polys.items():
        fill = color if name in on else ghost
        if fill is None:
            continue
        d.polygon([(x * SS, y * SS) for x, y in skewed(poly, h, skew)], fill=fill)
    return big.resize((iw, h), Image.LANCZOS)

def ttf_glyphs(font_path, cap_h, color, chars="0123456789", ghost=None,
               fixed=True, stroke=0, skew=SKEW, xscale=1.0, cell_char="8",
               align="right"):
    """One image per char, all cap_h tall (cap_char's ink height), sharing a
    baseline. Positions use the glyphs' real ink, not the font's metrics.

    fixed=True:  every image as wide as cell_char's ink. align="right" puts a
                 narrow glyph on the cell's right segments (LCD style, use with
                 ghost); align="center" centres it (tabular figures).
    fixed=False: tight ink width per glyph (punctuation, units).
    ghost:       colour of cell_char drawn underneath (unlit segments).
    stroke > 0 thickens thin fonts but closes the gaps between segments.
    """
    from PIL import ImageFont
    probe = ImageFont.truetype(font_path, 100)
    _, t, _, b = probe.getbbox(cell_char)
    font = ImageFont.truetype(font_path, int(round(100 * cap_h * SS / (b - t))))
    sw = int(round(stroke * SS))

    def ink(ch):
        size = font.size * 3
        m = Image.new("L", (size, size), 0)
        ImageDraw.Draw(m).text((size // 3, size // 3), ch, font=font, fill=255,
                               stroke_width=sw, stroke_fill=255)
        x0, y0, x1, y1 = m.getbbox()
        return x0 - size // 3, y0 - size // 3, x1 - size // 3, y1 - size // 3

    cx0, top, cx1, bottom = ink(cell_char)
    cell_w, h = cx1 - cx0, bottom - top

    def draw(d, ch, left, fill):
        x0 = ink(ch)[0]
        d.text((left - x0, -top), ch, font=font, fill=fill,
               stroke_width=sw, stroke_fill=fill)

    out = {}
    for ch in chars:
        x0, _, x1, _ = ink(ch)
        gw = x1 - x0
        w = cell_w if fixed else gw
        big = Image.new("RGBA", (w, h), CLEAR)
        d = ImageDraw.Draw(big)
        if fixed and ghost is not None:
            draw(d, cell_char, 0, ghost)
        left = 0
        if fixed:
            left = cell_w - gw if align == "right" else (cell_w - gw) // 2
        draw(d, ch, left, color)
        sheared = big.transform((w + int(h * skew) + 1, h), Image.AFFINE,
                                (1, skew, -h * skew, 0, 1, 0), Image.BICUBIC)
        out[ch] = sheared.resize(
            (max(1, round(sheared.width * xscale * cap_h / h)), cap_h), Image.LANCZOS)
    return out


def ttf_word(text, font_path, cap_h, color, stroke=0, skew=SKEW):
    """Render text with a TTF font, scaled so capitals are cap_h px tall,
    slanted like the 7-segment glyphs. stroke thickens thin fonts (px)."""
    from PIL import ImageFont
    probe = ImageFont.truetype(font_path, 100)
    l, t, r, b = probe.getbbox("H")
    size = 100 * cap_h * SS / (b - t)
    font = ImageFont.truetype(font_path, int(round(size)))
    sw = int(round(stroke * SS))
    l, t, r, b = font.getbbox(text, stroke_width=sw)
    big = Image.new("RGBA", (r - l, b - t), CLEAR)
    ImageDraw.Draw(big).text((-l, -t), text, font=font, fill=color,
                             stroke_width=sw, stroke_fill=color)
    h = big.height
    sheared = big.transform((big.width + int(h * skew) + 1, h), Image.AFFINE,
                            (1, skew, -h * skew, 0, 1, 0), Image.BICUBIC)
    return sheared.resize((max(1, round(sheared.width / SS)), cap_h), Image.LANCZOS)


def colon(w, h, dot, color, skew=SKEW):
    """Two square dots, positioned on the skewed axis like the digits."""
    iw = img_w(w, h, skew)
    big = Image.new("RGBA", (iw * SS, h * SS), CLEAR)
    d = ImageDraw.Draw(big)
    for cy in (h * 0.32, h * 0.70):
        x0 = (w - dot) / 2
        y0 = cy - dot / 2
        sq = [(x0, y0), (x0 + dot, y0), (x0 + dot, y0 + dot), (x0, y0 + dot)]
        d.polygon([(x * SS, y * SS) for x, y in skewed(sq, h, skew)], fill=color)
    return big.resize((iw, h), Image.LANCZOS)

def slash(w, h, t, color):
    big = Image.new("RGBA", (w * SS, h * SS), CLEAR)
    d = ImageDraw.Draw(big)
    d.line([(w * 0.85 * SS, 1 * SS), (w * 0.15 * SS, (h - 1) * SS)],
           fill=color, width=int(t * SS))
    return big.resize((w, h), Image.LANCZOS)

def pixel(grid, scale, color):
    rows = [r for r in grid]
    gh, gw = len(rows), max(len(r) for r in rows)
    im = Image.new("RGBA", (gw * scale, gh * scale), CLEAR)
    d = ImageDraw.Draw(im)
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c == "X":
                d.rectangle([x * scale, y * scale,
                             (x + 1) * scale - 1, (y + 1) * scale - 1], fill=color)
    return im

def compose(grids, w, h):
    """Layer pixel grids: each entry (grid, dx, dy, outline). Outline erases a
    1-px border around the layer so overlapping shapes stay readable."""
    canvas = [["." for _ in range(w)] for _ in range(h)]
    for grid, dx, dy, outline in grids:
        cells = [(x + dx, y + dy) for y, r in enumerate(grid)
                 for x, c in enumerate(r) if c == "X"]
        if outline:
            for cx, cy in cells:
                for ox in (-1, 0, 1):
                    for oy in (-1, 0, 1):
                        if 0 <= cx + ox < w and 0 <= cy + oy < h:
                            canvas[cy + oy][cx + ox] = "."
        for cx, cy in cells:
            if 0 <= cx < w and 0 <= cy < h:
                canvas[cy][cx] = "X"
    return ["".join(r) for r in canvas]

FONT5x7 = {
    "A": [".XXX.", "X...X", "X...X", "XXXXX", "X...X", "X...X", "X...X"],
    "B": ["XXXX.", "X...X", "X...X", "XXXX.", "X...X", "X...X", "XXXX."],
    "D": ["XXXX.", "X...X", "X...X", "X...X", "X...X", "X...X", "XXXX."],
    "E": ["XXXXX", "X....", "X....", "XXXX.", "X....", "X....", "XXXXX"],
    "G": [".XXX.", "X...X", "X....", "X.XXX", "X...X", "X...X", ".XXXX"],
    "I": [".XXX.", "..X..", "..X..", "..X..", "..X..", "..X..", ".XXX."],
    "M": ["X...X", "XX.XX", "X.X.X", "X.X.X", "X...X", "X...X", "X...X"],
    "O": [".XXX.", "X...X", "X...X", "X...X", "X...X", "X...X", ".XXX."],
    "Q": [".XXX.", "X...X", "X...X", "X...X", "X.X.X", "X..X.", ".XX.X"],
    "R": ["XXXX.", "X...X", "X...X", "XXXX.", "X.X..", "X..X.", "X...X"],
    "S": [".XXXX", "X....", "X....", ".XXX.", "....X", "....X", "XXXX."],
    "T": ["XXXXX", "..X..", "..X..", "..X..", "..X..", "..X..", "..X.."],
    "U": ["X...X", "X...X", "X...X", "X...X", "X...X", "X...X", ".XXX."],
    "X": ["X...X", "X...X", ".X.X.", "..X..", ".X.X.", "X...X", "X...X"],
}

DOT, PITCH = 4, 5  # dot size and spacing of the 5x7 matrix font

def dot_word(word, color, ghost=None):
    cols = len(word) * 5 + (len(word) - 1)
    im = Image.new("RGBA", (cols * PITCH - 1, 7 * PITCH - 1), CLEAR)
    d = ImageDraw.Draw(im)
    for i, ch in enumerate(word):
        glyph = FONT5x7[ch]
        for y in range(7):
            for x in range(5):
                fill = color if glyph[y][x] == "X" else ghost
                if fill is None:
                    continue
                px_ = (i * 6 + x) * PITCH
                py_ = y * PITCH
                d.rectangle([px_, py_, px_ + DOT - 1, py_ + DOT - 1], fill=fill)
    return im

def battery(level, bars, color, ghost):
    w, h = 46, 22
    im = Image.new("RGBA", (w, h), CLEAR)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 5, h - 1], outline=color, width=2)
    d.rectangle([w - 4, 6, w - 1, h - 7], fill=color)
    bw = (w - 5 - 4 - 2 - (bars - 1) * 2) // bars
    for i in range(bars):
        x0 = 4 + i * (bw + 2)
        d.rectangle([x0, 4, x0 + bw - 1, h - 5],
                    fill=color if i < level else ghost)
    return im

def font_set(spec, color, ghost=None, skew=SKEW):
    """Digits 0-9 and "-" as 7-segment images (ghost = colour of unlit segments)."""
    return {ch: seg_char(ch, *spec, color, ghost, skew) for ch in "0123456789-"}

def degree(size, t, color):
    im = Image.new("RGBA", (size * SS, size * SS), CLEAR)
    d = ImageDraw.Draw(im)
    d.ellipse([t * SS / 2, t * SS / 2, (size - t / 2) * SS, (size - t / 2) * SS],
              outline=color, width=int(t * SS))
    return im.resize((size, size), Image.LANCZOS)

def degree_unit(spec, color):
    """Degree sign on a canvas as tall as the digits, sitting at the top."""
    w, h, t = spec
    s = max(6, int(h * 0.28))
    im = Image.new("RGBA", (s + 2, h), CLEAR)
    im.alpha_composite(degree(s, max(2, t * 0.6), color), (2, 0))
    return im

def percent_unit(spec, color):
    w, h, t = spec
    big = Image.new("RGBA", (w * SS, h * SS), CLEAR)
    d = ImageDraw.Draw(big)
    r = w * 0.18
    lw = max(1.5, t * 0.6) * SS
    d.ellipse([(w * 0.05) * SS, (h * 0.12) * SS, (w * 0.05 + 2 * r) * SS,
               (h * 0.12 + 2 * r) * SS], outline=color, width=int(lw))
    d.ellipse([(w * 0.95 - 2 * r) * SS, (h * 0.88 - 2 * r) * SS, (w * 0.95) * SS,
               (h * 0.88) * SS], outline=color, width=int(lw))
    d.line([(w * 0.9 * SS, h * 0.1 * SS), (w * 0.1 * SS, h * 0.9 * SS)],
           fill=color, width=int(lw))
    return big.resize((w, h), Image.LANCZOS)

def dot_img(spec, color):
    w, h, t = spec
    s = max(3, t)
    im = Image.new("RGBA", (s + 4, h), CLEAR)
    ImageDraw.Draw(im).rectangle([2, h - s - 1, 2 + s - 1, h - 2], fill=color)
    return im

def text_img(canvas, x, y, digits, imgs, space=3, w=None, align="left"):
    parts = [imgs[c] for c in digits]
    tw = sum(p.width for p in parts) + space * (len(parts) - 1)
    if w is not None and align == "center":
        x += (w - tw) // 2
    elif w is not None and align == "right":
        x += w - tw
    for p in parts:
        canvas.alpha_composite(p, (x, y)); x += p.width + space

def mask_screen(im, r=64):
    """Approximate the Bip 6 rounded display for previews."""
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], r, fill=255)
    out = Image.new("RGBA", im.size, (40, 40, 40, 255))
    out.paste(im, (0, 0), m)
    return out


def dot_word_width(n_chars):
    return (n_chars * 6 - 1) * PITCH - 1
