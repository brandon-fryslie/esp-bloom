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

from region import ScreenRegion


def signal_handler(sig, frame):
    print('Exiting...')
    sender.stop()  # do not forget to stop the sender
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


def send_data(sender, pixel_strips: List[PixelStrip], save_image):
    # Turn off automatic flushing so we can send everything at the same time
    sender.manual_flush = True
    for pixel_strip in pixel_strips:
        pixel_data = []
        for region in pixel_strip.regions:
            img = img_proc.capture_and_resize(region, pixel_strip.row_length, pixel_strip.rows, save_image)
            pixel_data += img_proc.create_color_data(img, pixel_strip, region)

        # print number of pixels
        # print(len(pixel_data)/4)

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
parser.add_argument('--slow', dest='slow', action='store_true', default=False, help='slow mode')
parser.add_argument('--save', dest='save', action='store_true', default=False, help='save images')
parser.add_argument('--profile', dest='profile', action='store_true', default=False, help='profile')
# parser.add_argument('--fps', dest='fps', action='store', default=30, help='fps')
args = parser.parse_args()

if args.debug:
    print("DEBUG MODE ENABLED")
    logging.basicConfig(level=logging.DEBUG)

frame_rate = 3 if args.debug or args.slow else 30
sleep_time = round(1/frame_rate, 3)-.001

# function to determine if a specific pixel falls into a specific region
def _region_fn_universe_1(pixel: PixelAddress) -> str:
    if pixel.index < 29*2:
        return "bottom"
    else:
        return "top"

# function to determine if a specific pixel falls into a specific region
def _region_fn_universe_3(pixel: PixelAddress) -> str:
    return "bottom"

mss_instance = mss.mss()

regionTop3 = ScreenRegion("top", 3, mss_instance)
regionBottom3 = ScreenRegion("bottom", 3, mss_instance)
regionTop1 = ScreenRegion("top", 1, mss_instance)
regionBottom1 = ScreenRegion("bottom", 1, mss_instance)

# 192.168.1.237
pixel_strip1 = PixelStrip(
    strip_addr="192.168.1.237", universe=1, row_length=29, rows=4, start_left=True,
    start_bottom=True, region_fn=_region_fn_universe_1,
    regions=[regionBottom3, regionTop3],
)

pixel_strip2 = PixelStrip(
    strip_addr="192.168.1.240", universe=2, row_length=29, rows=4, start_left=True,
    start_bottom=True, region_fn=_region_fn_universe_1,
    regions=[regionBottom1, regionTop1],
)

pixel_strip3 = PixelStrip(
    strip_addr="192.168.1.243", universe=3, row_length=75, rows=1, start_left=True,
    start_bottom=True, region_fn=_region_fn_universe_3,
    regions=[regionBottom1],
)

pixel_strips = [
    pixel_strip1,
    pixel_strip2,
    pixel_strip3,
]

sender = espixelstick.create_sender(pixel_strips, fps=frame_rate)
# if args.debug:
#     send_data(sender, pixel_strip, rows, row_length, True)
#     sender.stop()
#     sys.exit(0)

if args.profile:
    for i in range(0, 100):
        send_data(sender, pixel_strips, save_image=args.save)
        time.sleep(sleep_time)

    sender.stop()
    sys.exit(0)

if args.test:
    test_strips(pixel_strips)
    sys.exit(0)

# for i in range(0, 1000):
while True:
    send_data(sender, pixel_strips, save_image=args.save)
    time.sleep(sleep_time)

