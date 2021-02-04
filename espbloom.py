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

import signal
import sys

def signal_handler(sig, frame):
    print('Exiting...')
    sender.stop()  # do not forget to stop the sender
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

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

def capture_and_resize(area: str, monitor_no: int, img_x: int, img_y: int, save_image: bool) -> PIL.Image:
    with mss.mss() as mss_instance:  # Create a new mss.mss instance
        monitor = mss_instance.monitors[monitor_no]
        bb = get_bounding_box(area, monitor)
        screenshot = mss_instance.grab(bb)  # Take the screenshot
        img = PIL.Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")  # Convert to PIL.Image
        # img.save(f"{area}-bb.png")

        # Resize to the size of the pixel bounds
        resized = img.resize((img_x, img_y), resample=PIL.Image.BILINEAR)
        if save_image:
            resized.save(f"{area}-resized.png")

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

def send_data(sender, pixel_strip: PixelStrip, rows, row_length, save_image):
    bottom_img = capture_and_resize("bottom", 3, row_length, rows, save_image)
    pixel_data = create_color_data(bottom_img, pixel_strip, "bottom")

    # print(f"sending pixel data {len(pixel_data)/4}")
    # print(pixel_data)

    top_img = capture_and_resize("top", 3, row_length, rows, save_image)
    pixel_data += create_color_data(top_img, pixel_strip, "top")

    sender[1].dmx_data = pixel_data
    # sender[1].preview_data = True
    # print("Sending pixel data")

################################################################################################################################################

parser = argparse.ArgumentParser(description='esp-based bias lighting')
parser.add_argument('--debug', dest='debug', action='store_true', default=False, help='debug mode')
# parser.add_argument('--fps', dest='fps', action='store', default=30, help='fps')
args = parser.parse_args()

if args.debug:
    print("DEBUG MODE ENABLED")
    logging.basicConfig(level=logging.DEBUG)

rows = 4
row_length = 29

frame_rate = 3 if args.debug else 30
sleep_time = round(1/frame_rate, 2)

# function to determine if a specific pixel falls into a specific region
def _region_fn(pixel: PixelAddress) -> str:
    if pixel.index < 29*2:
        return "bottom"
    else:
        return "top"

pixel_strip = PixelStrip("test", row_length=row_length, rows=rows, start_left=True, start_bottom=True, region_fn=_region_fn)

sender = espixelstick.create_sender(fps=frame_rate)
if args.debug:
    send_data(sender, pixel_strip, rows, row_length, True)
    sender.stop()
    sys.exit(0)

# for i in range(0, 1000):
while True:
    send_data(sender, pixel_strip, rows, row_length, save_image=args.debug)
    time.sleep(sleep_time)




