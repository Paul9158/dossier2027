#!/usr/bin/env python3
"""Génère les icônes (écran d'accueil, onglet) et l'image d'aperçu des liens. À lancer une seule fois."""
import pathlib
from PIL import Image, ImageDraw, ImageFont

OUT = pathlib.Path(__file__).resolve().parent.parent / "docs"
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
FONT_MED = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
TOP, BOT = (10, 132, 255), (0, 64, 221)


def gradient(w, h):
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = (x / w * 0.35 + y / h * 0.65)
            px[x, y] = tuple(round(a + (b - a) * t) for a, b in zip(TOP, BOT))
    return img


def centered(draw, text, font, cx, cy, fill):
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    draw.text((cx - (r - l) / 2 - l, cy - (b - t) / 2 - t), text, font=font, fill=fill)


def icon(size=1024):
    img = gradient(size, size)
    d = ImageDraw.Draw(img, "RGBA")
    centered(d, "Dossier", ImageFont.truetype(FONT_MED, round(size * .135)), size / 2, size * .36, (255, 255, 255, 205))
    centered(d, "2027", ImageFont.truetype(FONT, round(size * .30)), size / 2, size * .58, (255, 255, 255, 255))
    return img


def rounded(img, radius):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.size[0] - 1, img.size[1] - 1), radius=radius, fill=255)
    out = img.convert("RGBA")
    out.putalpha(mask)
    return out


big = icon(1024)
for s in (180, 192, 512):
    big.resize((s, s), Image.LANCZOS).save(OUT / f"icon-{s}.png", optimize=True)
rounded(big, 230).resize((64, 64), Image.LANCZOS).save(OUT / "favicon-64.png", optimize=True)

# Image d'aperçu quand on partage le lien (WhatsApp, iMessage...) : 1200 x 630
W, H = 1200, 630
og = gradient(W, H)
d = ImageDraw.Draw(og, "RGBA")
d.text((80, 150), "Dossier", font=ImageFont.truetype(FONT_MED, 64), fill=(255, 255, 255, 205))
d.text((76, 225), "Présidentielle 2027", font=ImageFont.truetype(FONT, 104), fill=(255, 255, 255, 255))
d.text((80, 390), "Candidats · programmes · vrai / faux · débats · sondages", font=ImageFont.truetype(FONT_MED, 38), fill=(255, 255, 255, 220))
d.text((80, 450), "Mis à jour chaque matin", font=ImageFont.truetype(FONT_MED, 38), fill=(255, 255, 255, 170))
og.save(OUT / "og.png", optimize=True)
print("icônes écrites dans", OUT)
