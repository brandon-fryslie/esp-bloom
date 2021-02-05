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

from region import ScreenRegion, CombineRegion


def signal_handler(sig, frame):
    print('Exiting...')

    # this doesn't turn off the leds for some reason
    # TODO: shut off the LEDs when we exit
    for i in range(1, 3):
        if sender[i] is not None:
            sender[i].dmx_data = (0, 0, 0, 0)

    sender.stop()  # do not forget to stop the sender
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


def send_data(sender, pixel_strips: List[PixelStrip], save_image):
    # Turn off automatic flushing so we can send everything at the same time
    sender.manual_flush = True
    for pixel_strip in pixel_strips:
        pixel_data = []
        for region in pixel_strip.regions:
            img = region.capture_and_resize(pixel_strip.max_row_length, pixel_strip.rows, save_image)
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
# This doesn't use the pixel mapping structure, it just spams solid colors to the DMX
# universes defined in 'pixel_strips'.  Tests the physical LED wiring and controller setup
# ONLY (does not test the pixel mapping)
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

# Turn off the LEDs
def strips_off(pixel_strips):
    print("Turning strips off")
    for pixel_strip in pixel_strips:
        sender[pixel_strip.universe].dmx_data = (0, 0, 0, 0) * 1000
    sender.stop()
    print("Turned strips off.  This doesn't always exit, you might need to press ctrl+c again")


################################################################################################################################################

parser = argparse.ArgumentParser(description='esp-based bias lighting')
parser.add_argument('--debug', dest='debug', action='store_true', default=False, help='debug mode (print debug logs)')
parser.add_argument('--test', dest='test', action='store_true', default=False, help='test mode (spam solid colors)')
parser.add_argument('--slow', dest='slow', action='store_true', default=False, help='slow mode (3 fps)')
parser.add_argument('--save', dest='save', action='store_true', default=False, help='save png image files for debugging')
parser.add_argument('--off', dest='off', action='store_true', default=False, help='turn strips off')
parser.add_argument('--profile', dest='profile', action='store_true', default=False, help='profile (create cProfile profile for debugging performance)')
# parser.add_argument('--fps', dest='fps', action='store', default=30, help='fps')
args = parser.parse_args()

if args.debug:
    print("DEBUG MODE ENABLED")
    logging.basicConfig(level=logging.DEBUG)

frame_rate = 3 if args.debug or args.slow else 30

# I probably don't wanna do the sleep time thing, because this doesn't at all take
# into account how long it took to process the images.  probably responsible
# for some of the choppiness.  replace with asyncio or something like timeloop
# TODO: try out this and see if it helps: https://github.com/sankalpjonn/timeloop
sleep_time = round(1/frame_rate, 3)-.001

### A lot of the code below is very specific to my specific pixel setup.  The setup consists of:
# LED type: these are SK6812 LEDs which are RGBW.  This is what I already had in channels w/ connectors
# I would have preferred to use APA102 LEDs but I didn't have them in channels.  The RGBW LEDs require 4 DMX channels per light
# which reduces the number of LEDs we can have in a DMX Universe.  That's definitely a downside to these LEDs
# (DMX universes can have 512 lights, and each individual LED is RGBW=4x lights).
#
# 3 distinct LED fixtures
# - each fixture uses 1 esp8266 (dev board)
#
# - right monitor
#   - dmx universe 1
#   - 4 rows x 29 pixels in horizontal zigzag pattern starting at lower left
#
# - left monitor
#   - dmx universe 2
#   - 4 rows x 29 pixels in horizontal zigzag pattern starting at lower left
#
# - desk
#   - dmx universe 3+4
#   - 3 rows, horizontal zigzag, starting at upper right
#   - row #1 (dmx universe 3)
#     - back of desk, 75 pixels
#   - row #2 - first part - 53 pixels in universe #3
#   - row #2 - second part - 18 pixels in universe #4
#     - row 2 is split due to universe size limit
#   - row #3 - 71 pixels (dmx universe 4)
#     - row #2 and #3 are in the middle of the desk facing downwards

# function to determine if a specific pixel falls into a specific region
# used for the monitors which have 4x rows of 29 pixels each
# this is how we determine which LEDs should get the top of a screen vs the bottom of a screen
# this functionality should really be refactored to use the newer ScreenRegion class
def _region_fn_monitors(pixel: PixelAddress) -> str:
    if pixel.index < 29*2:
        return "bottom"
    else:
        return "top"

mss_instance = mss.mss()

regionTop3 = ScreenRegion("top", 3, mss_instance)
regionBottom3 = ScreenRegion("bottom", 3, mss_instance)
regionTop1 = ScreenRegion("top", 1, mss_instance)
regionBottom1 = ScreenRegion("bottom", 1, mss_instance)
allBottom = CombineRegion("bottom", 1, mss_instance)

# The list of pixels strips.  The PixelStrip has kind of grown into a catch-all for a bunch of functionality & data
pixel_strips = [
    # 192.168.1.237
    PixelStrip(
        strip_addr="192.168.1.237", universe=1, row_length=[29,29,29,29], rows=4, start_left=True,
        start_bottom=True, region_fn=_region_fn_monitors,
        regions=[regionBottom3, regionTop3],
    ),

    PixelStrip(
        strip_addr="192.168.1.240", universe=2, row_length=[29,29,29,29], rows=4, start_left=True,
        start_bottom=True, region_fn=_region_fn_monitors,
        regions=[regionBottom1, regionTop1],
    ),

    PixelStrip(
        strip_addr="192.168.1.243", universe=3, row_length=[75, 53], rows=2, start_left=False,
        start_bottom=False, region_fn=lambda _: "bottom",
        regions=[allBottom],
    ),

    # # 29 in first channel
    # # 42 in second in 2nd channel
    ## 24 in second channel that are part of universe 3
    # # 29+24 in universe 3, remainder (18) in universe 4
    # # 71 total
    # This one has the most complicated mapping due to the mismatched row lengths and that
    # it actually encompasses multiple DMX universes :/
    # the mapping doesn't work 100% here yet, there's something wrong with the offset calculations
    # in mapping.py.  its a few pixels off.  it could also be that we don't handle matrices with
    # multiple different row_lengths correctly when mapping screen pixels to led pixels
    PixelStrip(
        strip_addr="192.168.1.243", universe=4, row_length=[18, 71], rows=2, start_left=True,
        start_bottom=False, region_fn=lambda _: "bottom",
        regions=[allBottom], first_pixel_offset=53, max_row_length=71,
    ),
]

sender = espixelstick.create_sender(pixel_strips, fps=frame_rate)

if args.profile:
    for i in range(0, 100):
        send_data(sender, pixel_strips, save_image=args.save)
        time.sleep(sleep_time)

    sender.stop()
    sys.exit(0)

if args.test:
    test_strips(pixel_strips)
    sys.exit(0)

if args.off:
    strips_off(pixel_strips)
    sys.exit(0)

# for i in range(0, 1000):
while True:
    send_data(sender, pixel_strips, save_image=args.save)
    time.sleep(sleep_time)

