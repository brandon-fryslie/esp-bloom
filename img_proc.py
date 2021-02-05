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


# Get a bounding box for a screen area
def get_bounding_box(area: str, monitor: mss.models.Monitor):
    screen_percent = 25

    # print(f"getting bb for monitor {monitor}")
    # pprint(monitor)

    height = monitor["height"]
    width = monitor["width"]
    top = monitor["top"]
    bottom = top + height
    left = monitor["left"]
    right = left + width

    bounding_boxes = {
        "top": (left, top, right, int(height*screen_percent//100)),
        "bottom": (left, bottom-int(height*screen_percent//100), right, bottom),
        "left": (left, top, left+int((width)*screen_percent//100), bottom),
        "right": (right-int(width*screen_percent//100), 0, right, bottom),
    }
    bb = bounding_boxes[area]

    # pprint(bb)
    return bb

def capture_screen(area: str, monitor_no: int) -> mss.screenshot.ScreenShot:
    with mss.mss() as mss_instance:  # Create a new mss.mss instance
        monitor = mss_instance.monitors[monitor_no]
        bb = get_bounding_box(area, monitor)
        screenshot = mss_instance.grab(bb)  # Take the screenshot
        return screenshot

def capture_and_resize(region: str, monitor_no: int, img_x: int, img_y: int, save_image: bool) -> PIL.Image:
    with mss.mss() as mss_instance:  # Create a new mss.mss instance
        monitor = mss_instance.monitors[monitor_no]
        bb = get_bounding_box(region, monitor)
        screenshot = mss_instance.grab(bb)  # Take the screenshot
        img = PIL.Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")  # Convert to PIL.Image

        if save_image:
            img.save(f"saved-images/monitor-{monitor_no}-{region}.png")

        # Resize to the size of the pixel bounds
        resized = img.resize((img_x, img_y), resample=PIL.Image.BILINEAR)
        if save_image:
            resized.save(f"saved-images/monitor-{monitor_no}-{region}-resized.png")

    return resized


# we just loop over the image in the same pattern as the LEDs are configured
def create_color_data(img: PIL.Image, pixel_strip: PixelStrip, region: str) -> List[int]:
    color_data = []

    # replace this with a loop thru an iterator of the Pixels

    for pixel in iter(pixel_strip.get_pixels_for_region(region)):
        # print(f"getting data for pixel: {pixel.x},{pixel.y}")
        r, g, b = img.getpixel((pixel.x, pixel.y))
        color_data.append(r)
        color_data.append(g)
        color_data.append(b)
        color_data.append(0) # white - should I avg this?

    return color_data
