"""Draw the garden picture with Pillow.

Sky and grass are simple shapes; weather and flowers are macOS emoji
(☀️☁️⚡ 🌻🌹🌷🌱🥀) rendered big and pasted on top. Rain lines are
hand-drawn with Pillow.
"""
import random

from PIL import Image, ImageDraw, ImageFont

W, H = 1000, 600
GROUND_Y = int(H * 0.64)          # y where the grass hill starts

SKY = {
    "sunny":  ((96, 165, 250), (224, 242, 254)),
    "cloudy": ((148, 163, 184), (241, 245, 249)),
    "rainy":  ((71, 85, 105), (148, 163, 184)),
    "stormy": ((30, 41, 59), (71, 85, 105)),
}

# stage -> (emoji, size); grow/bloom show the habit's own flower instead
STAGE = {
    "seed": ("🌰", 34),
    "sprout": ("🌱", 54),
    "grow": (None, 62),
    "bloom": (None, 82),
    "wilt": ("🥀", 68),
}

# weather -> [(emoji, size, x, y), ...]
WEATHER = {
    "sunny":  [("☀️", 110, 790, 105)],
    "cloudy": [("☁️", 130, 250, 100), ("☁️", 100, 730, 175)],
    "rainy":  [("☁️", 130, 250, 100), ("☁️", 100, 730, 175)],
    "stormy": [("☁️", 130, 250, 100), ("☁️", 100, 730, 175),
               ("⚡", 70, 500, 260)],
}

TAG_ICON = {"seed": "🌰", "sprout": "🌱", "grow": "🌿",
            "bloom": "🌸", "wilt": "🥀"}

_emoji_font = None
_text_font = None


# load the two fonts once (apple emoji + helvetica)
def _fonts():
    global _emoji_font, _text_font
    if _emoji_font is None:
        _emoji_font = ImageFont.truetype(
            "/System/Library/Fonts/Apple Color Emoji.ttc", 160)
        _text_font = ImageFont.truetype(
            "/System/Library/Fonts/Helvetica.ttc", 13)
    return _emoji_font, _text_font


# render one emoji into a picture of the given size
def emoji_img(emoji, size):
    ef, _ = _fonts()
    tile = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((90, 96), emoji, font=ef,
                              embedded_color=True, anchor="mm")
    return tile.resize((size, size), Image.LANCZOS)


# pick which emoji to show for this stage and how big
def flower_img(flower_emoji, stage):
    emoji, size = STAGE[stage]
    if emoji is None:                   # grow / bloom: the habit's flower
        emoji = flower_emoji
    if emoji == "🌹":                   # the rose glyph looks too big
        size = int(size * 0.82)
    return emoji_img(emoji, size)


# paint the sky as a vertical gradient, line by line
def sky(weather):
    top, bottom = SKY[weather]
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t)
                      for i in range(3))
        d.line((0, y, W, y), fill=color)
    return img


# paste the weather emoji into the sky, plus rain if needed
def add_weather(img, weather):
    for emoji, size, x, y in WEATHER[weather]:
        tile = emoji_img(emoji, size)
        img.alpha_composite(tile, (int(x - size / 2), int(y - size / 2)))
    if weather in ("rainy", "stormy"):
        rain(img, 90 if weather == "rainy" else 140)


# hand-draw n short slanted lines to look like rain
def rain(img, n):
    d = ImageDraw.Draw(img)
    rnd = random.Random(7)      # fixed seed so the rain looks the same
    for _ in range(n):
        x = rnd.randint(0, W)
        y = rnd.randint(0, H - 30)
        d.line((x, y, x - 3, y + 16), fill=(255, 255, 255, 130), width=2)


# draw the grass hill as two big ellipses
def ground(img):
    d = ImageDraw.Draw(img)
    d.ellipse((-100, GROUND_Y, W + 100, H * 1.7), fill=(74, 222, 128))
    d.ellipse((-100, GROUND_Y + 60, W + 100, H * 1.8), fill=(34, 197, 94))


# scan down one column of pixels to find where the grass starts
def grass_height(img, x):
    px = img.load()
    for y in range(H):
        r, g, b = px[x, y][:3]
        # clearly green means grass (cloud edges are grey-blue, not green)
        if g > 150 and g - r > 40 and g - b > 30:
            return y
    return H - 1


# draw the small pill under a flower: short name + stage icon
def name_tag(img, x, y, short, stage):
    _, f = _fonts()
    d = ImageDraw.Draw(img)
    tw = d.textlength(short, font=f)
    icon = emoji_img(TAG_ICON[stage], 18)
    w = int(tw) + icon.width + 24
    tag = Image.new("RGBA", (w, 24), (0, 0, 0, 0))
    td = ImageDraw.Draw(tag)
    td.rounded_rectangle((0, 0, w - 1, 23), radius=12,
                         fill=(255, 255, 255, 130))   # semi-transparent
    td.text((12, 5), short, font=f, fill=(31, 41, 55))
    tag.alpha_composite(icon, (w - icon.width - 6, 3))
    img.alpha_composite(tag, (int(x - w / 2), int(y)))


# draw the whole garden, and remember each flower's box for the hover card
def render(habits, weather, flower_emojis):
    img = sky(weather).convert("RGBA")
    add_weather(img, weather)
    ground(img)
    boxes = []      # (x1, y1, x2, y2, habit), used by the hover feature
    for h in habits:
        x = int(h.pos["left"] / 100 * W)
        gy = grass_height(img, x)
        base_y = gy + (h.pos["top"] - 60)
        base_y = min(max(base_y, gy - 6), gy + 30)
        tile = flower_img(flower_emojis.get(h.flower_symbol, "🌸"),
                          h.stage())
        top_y = int(base_y - tile.height + 20)
        img.alpha_composite(tile, (int(x - tile.width / 2), top_y))
        name_tag(img, x, base_y + 12, h.short, h.stage())
        boxes.append((x - tile.width // 2, top_y,
                      x + tile.width // 2, int(base_y + 40), h))
    return img.convert("RGB"), boxes
