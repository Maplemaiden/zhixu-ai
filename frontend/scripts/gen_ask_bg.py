from PIL import Image, ImageDraw, ImageFilter
import math
import random

W, H = 1920, 1080
rng = random.Random(42)

img = Image.new("RGB", (W, H), (18, 38, 63))
px = img.load()

for y in range(H):
    t = y / (H - 1)
    r = int(18 + (12 - 18) * t)
    g = int(38 + (58 - 38) * t)
    b = int(63 + (72 - 63) * t)
    for x in range(W):
        hx = abs(x - W / 2) / (W / 2)
        rr = max(0, min(255, int(r - 8 * hx + 18 * (1 - t))))
        gg = max(0, min(255, int(g + 22 * (1 - hx * 0.4) + 30 * (1 - t) * 0.3)))
        bb = max(0, min(255, int(b + 10 * (1 - hx * 0.3))))
        px[x, y] = (rr, gg, bb)


def soft_orb(cx, cy, radius, color, alpha=90):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for i in range(8, 0, -1):
        a = int(alpha * (i / 8) ** 2)
        rad = int(radius * (i / 8))
        ld.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=(*color, a))
    return layer.filter(ImageFilter.GaussianBlur(radius=max(18, radius // 6)))


wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
for cx, cy, rad, col, a in [
    (280, 160, 420, (160, 220, 200), 70),
    (1600, 820, 480, (100, 180, 160), 55),
    (980, 200, 260, (200, 230, 220), 35),
    (1200, 400, 300, (40, 90, 110), 40),
]:
    wash = Image.alpha_composite(wash, soft_orb(cx, cy, rad, col, a))

base = Image.alpha_composite(img.convert("RGBA"), wash)

grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(grid)
for i in range(18):
    y = 420 + i * 36
    alpha = max(10, 42 - i * 2)
    inset = int(80 + i * 18)
    gd.line([(inset, y), (W - inset, y)], fill=(180, 220, 210, alpha), width=1)
for i in range(28):
    x0 = 80 + i * 66
    gd.line([(x0, 430), (int(W / 2 + (x0 - W / 2) * 0.15), H - 40)], fill=(170, 210, 200, 16), width=1)

for _ in range(140):
    x = rng.randint(0, W - 1)
    y = rng.randint(0, H - 1)
    r = rng.choice([1, 1, 2, 2, 3])
    a = rng.randint(30, 110)
    gd.ellipse((x - r, y - r, x + r, y + r), fill=(210, 240, 230, a))

for _ in range(10):
    x1 = rng.randint(100, W - 100)
    y1 = rng.randint(80, H - 80)
    length = rng.randint(120, 320)
    ang = rng.uniform(-0.6, 0.6)
    x2 = int(x1 + length * math.cos(ang))
    y2 = int(y1 + length * math.sin(ang))
    gd.line([(x1, y1), (x2, y2)], fill=(190, 230, 215, rng.randint(18, 40)), width=2)

out = Image.alpha_composite(base, grid.filter(ImageFilter.GaussianBlur(radius=0.6)))

edge = Image.new("RGBA", (W, H), (10, 22, 36, 0))
ed = ImageDraw.Draw(edge)
for i, a in enumerate(range(90, 0, -12)):
    m = i * 14
    ed.rectangle([0, 0, W, m], fill=(10, 22, 36, a // 3))
    ed.rectangle([0, H - m, W, H], fill=(10, 22, 36, a // 3))
    ed.rectangle([0, 0, m, H], fill=(10, 22, 36, a // 4))
    ed.rectangle([W - m, 0, W, H], fill=(10, 22, 36, a // 4))
out = Image.alpha_composite(out, edge.filter(ImageFilter.GaussianBlur(24)))

path = r"c:\Users\yoimi\Desktop\数字人项目\frontend\public\ask-space-bg.png"
out.convert("RGB").save(path, "PNG", optimize=True)
print("saved", path, out.size)
