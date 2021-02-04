import argparse
import itertools
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
import img_proc

import signal
import sys

def signal_handler(sig, frame):
    print('Exiting...')
    sender.stop()  # do not forget to stop the sender
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


def get_pixel_data(monitor_num: int, region: str, rows, row_length, save_image):
    bottom_img = img_proc.capture_and_resize(region, monitor_num, row_length, rows, save_image)
    pixel_data = img_proc.create_color_data(bottom_img, pixel_strip, "bottom")
    return pixel_data



def send_data(sender, pixel_strips: List[PixelStrip], save_image):
    # Turn off automatic flushing so we can send everything at the same time
    sender.manual_flush = True
    for pixel_strip in pixel_strips:
        pixel_data = []
        for region in pixel_strip.regions:
            img = img_proc.capture_and_resize(region, pixel_strip.monitor, pixel_strip.row_length, pixel_strip.rows, save_image)
            pixel_data += img_proc.create_color_data(img, pixel_strip, region)

        # Set pixel data for the universe
        sender[pixel_strip.universe].dmx_data = pixel_data

    # Flush all data
    sender.flush()

    # Reenable automatic flushing
    sender.manual_flush = False


def flatten(l: List) -> List:
    return list(itertools.chain.from_iterable(l))

# Send a solid color that changes every 2s
def test_strips(pixel_strips):
    sample_data = (255, 0, 0, 0) * 300
    sample_data = {
        "red": (255, 0, 0, 0) * 300,
        "green": (0, 255, 0, 0) * 300,
        "blue": (0, 0, 255, 0) * 300,
    }
    color_iter = itertools.cycle(sample_data.values())

    for i in range(20):
        color_data = next(color_iter)

        for pixel_strip in pixel_strips:
            sender[pixel_strip.universe].dmx_data = color_data

        time.sleep(1)

    time.sleep(10)
    sender.stop()


################################################################################################################################################

parser = argparse.ArgumentParser(description='esp-based bias lighting')
parser.add_argument('--debug', dest='debug', action='store_true', default=False, help='debug mode')
parser.add_argument('--test', dest='test', action='store_true', default=False, help='test mode')
parser.add_argument('--slow', dest='slow', action='store_true', default=False, help='slow + save images mode')
# parser.add_argument('--fps', dest='fps', action='store', default=30, help='fps')
args = parser.parse_args()

if args.debug:
    print("DEBUG MODE ENABLED")
    logging.basicConfig(level=logging.DEBUG)

rows = 4
row_length = 29

frame_rate = 3 if args.debug or args.slow else 30
sleep_time = round(1/frame_rate, 3)-.001

# function to determine if a specific pixel falls into a specific region
def _region_fn_universe_1(pixel: PixelAddress) -> str:
    if pixel.index < 29*2:
        return "bottom"
    else:
        return "top"

pixel_strip1 = PixelStrip(
    "universe-1", 1, row_length=29, rows=4, start_left=True,
    start_bottom=True, region_fn=_region_fn_universe_1,
    monitor=3, regions=["bottom", "top"],
)

pixel_strip2 = PixelStrip(
    "universe-2", 2, row_length=29, rows=1, start_left=True,
    start_bottom=True, region_fn=_region_fn_universe_1,
    monitor=1, regions=["bottom"],
)

pixel_strips = [
    pixel_strip1,
    pixel_strip2,
]

sender = espixelstick.create_sender(fps=frame_rate)
# if args.debug:
#     send_data(sender, pixel_strip, rows, row_length, True)
#     sender.stop()
#     sys.exit(0)

if args.test:
    test_strips(pixel_strips)
    sys.exit(0)

# for i in range(0, 1000):
while True:
    send_data(sender, pixel_strips, save_image=args.slow)
    time.sleep(sleep_time)

