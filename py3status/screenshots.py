# -*- coding: utf-8 -*-
"""
This file is used for the generation of screenshots for py3status
documentation.

outside of pythons standard library there are the following requirements:

    Pillow==3.4.2
    fonttools

PIL may work if installed but is not supported.
"""

from __future__ import division

import ast
import os
import re

from hashlib import md5

from PIL import Image, ImageFont, ImageDraw
from fontTools.ttLib import TTFont


WIDTH = 650
TOP_BAR_HEIGHT = 5
BAR_HEIGHT = 24
X_OFFSET = 5
PADDING = 4

SEP_PADDING_LEFT = 4
SEP_PADDING_RIGHT = SEP_PADDING_LEFT + 1

SEP_BORDER = 4

FONT = "DejaVuSansMono.ttf"

# Pillow does poor font rendering so we are best off creating huge text and
# then shrinking with anti-aliasing.  SCALE is how many times bigger we render
# the text
SCALE = 8

COLOR = "#FFFFFF"
COLOR_BG = "#000000"
COLOR_PY3STATUS = "#FFFFFF"
COLOR_SEP = "#666666"
COLOR_URGENT = "#FFFFFF"
COLOR_URGENT_BG = "#900000"

FONT_SIZE = BAR_HEIGHT - (PADDING * 2)
HEIGHT = TOP_BAR_HEIGHT + BAR_HEIGHT

# font, glyph_data want caching for performance
font = None
glyph_data = None


def get_color_for_name(module_name):
    """
    Create a custom color for a given string.
    This allows the screenshots to each have a unique color but also for that
    color to be consistent.
    """
    # all screenshots of the same module should be a uniform color
    module_name = module_name.split("-")[0]

    saturation = 0.5
    value = 243.2
    try:
        # we must be bytes to allow the md5 hash to be calculated
        module_name = module_name.encode("utf-8")
    except AttributeError:
        pass
    hue = int(md5(module_name).hexdigest(), 16) / 16 ** 32
    hue *= 6
    hue += 3.708
    r, g, b = (
        (
            value,
            value - value * saturation * abs(1 - hue % 2),
            value - value * saturation,
        )
        * 3
    )[5 ** int(hue) // 3 % 3 :: int(hue) % 2 + 1][:3]
    return "#" + "%02x" * 3 % (int(r), int(g), int(b))


def contains_bad_glyph(glyph_data, data):
    """
    Pillow only looks for glyphs in the font used so we need to make sure our
    font has the glygh.  Although we could substitute a glyph from another font
    eg symbola but this adds more complexity and is of limited value.
    """

    def check_glyph(char):
        for cmap in glyph_data["cmap"].tables:
            if cmap.isUnicode():
                if char in cmap.cmap:
                    return True
        return False

    for part in data:
        text = part.get("full_text", "")
        try:
            # for python 2
            text = text.decode("utf8")
        except AttributeError:
            pass

        for char in text:
            if not check_glyph(ord(char)):
                # we have not found a character in the font
                print(u"%s (%s) missing" % (char, ord(char)))
                return True
    return False


def create_screenshot(name, data, path, font, is_module):
    """
    Create screenshot of py3status output and save to path
    """
    desktop_color = get_color_for_name(name)

    # if this screenshot is for a module then add modules name etc
    if is_module:
        data.append(
            {"full_text": name.split("-")[0], "color": desktop_color, "separator": True}
        )
        data.append(
            {"full_text": "py3status", "color": COLOR_PY3STATUS, "separator": True}
        )

    img = Image.new("RGB", (WIDTH, HEIGHT), COLOR_BG)
    d = ImageDraw.Draw(img)

    # top bar
    d.rectangle((0, 0, WIDTH, TOP_BAR_HEIGHT), fill=desktop_color)
    x = X_OFFSET

    # add text and separators
    for part in reversed(data):
        text = part.get("full_text")
        color = part.get("color", COLOR)
        background = part.get("background")
        separator = part.get("separator")
        urgent = part.get("urgent")

        # urgent background
        if urgent:
            color = COLOR_URGENT
            background = COLOR_URGENT_BG

        size = font.getsize(text)

        if background:
            d.rectangle(
                (
                    WIDTH - x - (size[0] // SCALE),
                    TOP_BAR_HEIGHT + PADDING,
                    WIDTH - x - 1,
                    HEIGHT - PADDING,
                ),
                fill=background,
            )

        x += size[0] // SCALE

        txt = Image.new("RGB", size, background or COLOR_BG)
        d_text = ImageDraw.Draw(txt)
        d_text.text((0, 0), text, font=font, fill=color)
        # resize to actual size wanted and add to image
        txt = txt.resize((size[0] // SCALE, size[1] // SCALE), Image.ANTIALIAS)
        img.paste(txt, (WIDTH - x, TOP_BAR_HEIGHT + PADDING))

        if separator:
            x += SEP_PADDING_RIGHT
            d.line(
                (
                    (WIDTH - x, TOP_BAR_HEIGHT + PADDING),
                    (WIDTH - x, TOP_BAR_HEIGHT + 1 + PADDING + FONT_SIZE),
                ),
                fill=COLOR_SEP,
                width=1,
            )
            x += SEP_PADDING_LEFT

    img.save(os.path.join(path, "%s.png" % name))
    print(" %s.png" % name)


def parse_sample_data(sample_data, module_name):
    """
    Parse sample output definitions and return a dict
    {screenshot_name: sample_output}
    """
    samples = {}
    name = None
    data = ""
    count = 0
    for line in sample_data.splitlines():
        line = line.strip()
        if line == "":
            # blank lines separate screenshots so process the data we have
            if data:
                if name:
                    name = u"%s-%s-%s" % (module_name, count, name)
                else:
                    name = module_name
                try:
                    output = ast.literal_eval(data)
                    samples[name] = output
                except SyntaxError:
                    samples[name] = {
                        "color": "#990000",
                        "background": "#FFFF00",
                        "full_text": " SAMPLE DATA ERROR ",
                    }
                count += 1
            # clear any data
            name = None
            data = ""
        elif name is None and data == "" and not line[0] in ["[", "{"] and count:
            name = line
        else:
            data += line
    return samples


def get_samples():
    """
    Look in all core modules and get any samples from the docstrings.
    return a dict {screenshot_name: sample_output}
    """
    samples = {}
    module_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules")
    for file in sorted(os.listdir(module_dir)):
        if file.endswith(".py") and file != "__init__.py":
            #  remove .py
            module_name = file[:-3]
            with open(os.path.join(module_dir, file), "r") as f:
                try:
                    module = ast.parse(f.read())
                except SyntaxError:
                    continue
                raw_docstring = ast.get_docstring(module)
                if raw_docstring is None:
                    continue
                parts = re.split("^SAMPLE OUTPUT$", raw_docstring, flags=re.M)
                if len(parts) == 1:
                    continue
                sample_data = parts[1]
                samples.update(parse_sample_data(sample_data, module_name))
    return samples


def process(name, data, module=True):
    """
    Process data to create a screenshot which will be saved in
    docs/screenshots/<name>.png
    If module is True the screenshot will include the name and py3status.
    """

    path = "../doc/screenshots"
    # create dir if not exists
    try:
        os.makedirs(path)
    except OSError:
        pass

    global font, glyph_data
    if font is None:
        font = ImageFont.truetype(FONT, FONT_SIZE * SCALE)
    if glyph_data is None:
        glyph_data = TTFont(font.path)

    # make sure that the data is in list form
    if not isinstance(data, list):
        data = [data]

    if contains_bad_glyph(glyph_data, data):
        print("** %s has characters not in %s **" % (name, font.getname()[0]))
    else:
        create_screenshot(name, data, path, font=font, is_module=module)


def create_screenshots(quiet=False):
    """
    create screenshots for all core modules.
    The screenshots directory will have all .png files deleted before new shots
    are created.
    """

    print("Creating screenshots...")
    samples = get_samples()
    for name, data in sorted(samples.items()):
        process(name, data)


if __name__ == "__main__":
    create_screenshots()
