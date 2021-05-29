# -*- coding: utf-8 -*-
import colormath
import colormath.color_conversions
import colormath.color_objects

for h in range(0, 360, 4):
    color = colormath.color_objects.LCHabColor(100 * 0.5, 132 * 0.6, h)
    rgb_color = colormath.color_conversions.convert_color(
        color, colormath.color_objects.sRGBColor
    )
    hex_color = rgb_color.get_rgb_hex()
    print(f".label_color_h{h:02d}{{color:{hex_color};}}")
