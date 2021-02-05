import argparse
import logging
from pprint import pprint
from typing import List, Dict

import PIL
from PIL import Image
import time
import sys

import mss
from mss import models
from mss.screenshot import ScreenShot

import espixelstick
from mapping import PixelAddress, PixelStrip
from region import ScreenRegion

# def get_combined_bounding_box(region1: str, monitor1: mss.models.Monitor, region2: str, monitor2: mss.models.Monitor):
#     bb1 = get_bounding_box(region1, monitor1)
#     bb2 = get_bounding_box(region2, monitor2)
#

# we just loop over the image in the same pattern as the LEDs are configured
def create_color_data(img: PIL.Image, pixel_strip: PixelStrip, region: ScreenRegion) -> List[int]:
    color_data = []

    # replace this with a loop thru an iterator of the Pixels

    for pixel in iter(pixel_strip.get_pixels_for_region(region)):
        # print(f"getting data for pixel: {pixel.x},{pixel.y}")
        try:
            r, g, b = img.getpixel((pixel.x, pixel.y))
        except IndexError as e:
            print(f"ERROR GETTING PIXEL: {pixel.x}, {pixel.y}")
            print(str(e))
            img.save(f"saved-images/error-log-{region.name}.png")
            raise
        color_data.append(r)
        color_data.append(g)
        color_data.append(b)
        color_data.append(0) # white - should I avg this?

    return color_data
