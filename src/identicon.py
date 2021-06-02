# -*- coding: utf-8 -*-
import zlib

from gi.repository import GdkPixbuf
from gi.repository import GLib
from PIL import Image
from PIL import ImageDraw

from . import colors


def name_to_color_class(name):
    hue = zlib.crc32(name.encode("utf-8")) * 90 // 0xFFFFFFFF * 4
    return f"label_color_h{hue:02d}"


def name_to_color(name):
    hue = zlib.crc32(name.encode("utf-8")) * 90 // 0xFFFFFFFF * 4
    return colors.name[hue]


def image_to_pixbuf(img):
    gbytes = GLib.Bytes(img.tobytes())
    width, height = img.size
    return GdkPixbuf.Pixbuf.new_from_bytes(
        gbytes, GdkPixbuf.Colorspace.RGB, True, 8, width, height, width * 4
    )


# TODO: limit identicon cache size
_identicon_cache = {}


def get_identicon(name):
    number = zlib.crc32(name.encode("utf-8")) * (194481) // 0xFFFFFFFF
    if number in _identicon_cache:
        return _identicon_cache[number]

    rest = number
    bottom_number = rest % 21 + 1
    number = rest // 21
    face_number = rest % 21 + 1
    number = rest // 21
    side_number = rest % 21 + 1
    number = rest // 21
    top_number = rest % 21 + 1

    result = Image.new("RGBA", (32, 32))
    draw = ImageDraw.Draw(result)
    draw.ellipse((8, 8, 24, 24), fill=name_to_color(name))

    bottom = Image.open(f"identicon/bottom/bottom_{bottom_number:02d}.png").convert(
        "RGBA"
    )
    face = Image.open(f"identicon/face/face_{face_number:02d}.png").convert("RGBA")
    side = Image.open(f"identicon/side/side_{side_number:02d}.png").convert("RGBA")
    top = Image.open(f"identicon/top/top_{top_number:02d}.png").convert("RGBA")

    result.paste(bottom, mask=bottom)
    result.paste(face, mask=face)
    result.paste(side, mask=side)
    result.paste(top, mask=top)

    pixbuf = image_to_pixbuf(result)

    _identicon_cache[number] = pixbuf
    return pixbuf
