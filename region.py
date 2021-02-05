from typing import Tuple

import mss
from mss import models
from mss.base import MSSBase
from mss.screenshot import ScreenShot

import PIL
from PIL import Image

class ScreenRegion:
    def __init__(self, name: str, monitor_no: int, mss: MSSBase):
        self.name = name
        self.monitor_no = monitor_no
        self.mss = mss
        self.monitor = mss.monitors[monitor_no]

    # Get a bounding box for a screen area
    # should be refactored, moved this in here from outside the class
    def get_bounding_box(self, region_name: str, monitor):
        # Capture 50% of the screen
        screen_percent = 50

        # print(f"getting bb for monitor {monitor}")
        # pprint(monitor)

        height = monitor["height"]
        width = monitor["width"]
        top = monitor["top"]
        bottom = top + height
        left = monitor["left"]
        right = left + width

        # things look better if we exclude menu bars / status bars on the edges of the screen
        # your brain focuses on the center of the screen so that's what it expects the ambient
        # lights reflect.  TODO: use a percentage instead
        edge_offset = 50

        bounding_boxes = {
            "top": (left, top+edge_offset, right, int(height*screen_percent//100)),
            "bottom": (left, bottom-int(height*screen_percent//100), right, bottom-edge_offset),
            "left": (left, top, left+int((width)*screen_percent//100), bottom), # unused
            "right": (right-int(width*screen_percent//100), 0, right, bottom), # unused
        }
        bb = bounding_boxes[region_name]

        # pprint(bb)
        return bb

    # Take a screenshot of the screen region
    def screenshot(self, bb: Tuple):
        return self.mss.grab(bb)  # Take the screenshot

    # Capture a screenshot and resize it to the low-res of the LEDs
    def capture_and_resize(self, img_x: int, img_y: int, save_image: bool) -> PIL.Image:
        bb = self.get_bounding_box(self.name, self.monitor)
        screenshot = self.screenshot(bb)
        img = PIL.Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")  # Convert to PIL.Image

        if save_image:
            img.save(f"saved-images/monitor-{self.monitor_no}-{self.name}.png")

        # Resize to the size of the pixel bounds
        resized = img.resize((img_x, img_y), resample=PIL.Image.BILINEAR)
        if save_image:
            resized.save(f"saved-images/monitor-{self.monitor_no}-{self.name}-resized.png")

        return resized

# Hacky class to define a 'combined region' which is both the bottom regions from 2 separate monitors
# This was the final fixture I implemented and is my desk.  The LEDs span the entire length of my desk
# so I needed a way to put both monitors into 1 'region' in the code.  The existing abstractions
# can't really handle that case so this was an OK way to hack it in
class CombineRegion(ScreenRegion):
    # monitor data:
    # [{'height': 2130, 'left': 0, 'top': 0, 'width': 4480},
    #  {'height': 1440, 'left': 0, 'top': 0, 'width': 2560},
    #  {'height': 1050, 'left': 2560, 'top': 1080, 'width': 1680},
    #  {'height': 1080, 'left': 2560, 'top': 0, 'width': 1920}]

    # Grab both bounding boxes and take 2 separate screenshots.  We then resize them,
    # giving half the horizontal resolution to the left side monitor and the remainder
    # to the right side monitor.  When we stich them together, we have a single image in
    # the correct resolution for the single LED fixture that contains color data from
    # both monitors in (roughly) the correct proportions
    def capture_and_resize(self, img_x: int, img_y: int, save_image: bool) -> PIL.Image:
        # capture monitor 1 bottom and monitor 3 bottom
        #
        # do it for 2 monitors here:  just hardcode the shtuff.  its hackathon :D

        bb_mon_1 = self.get_bounding_box("bottom", self.mss.monitors[1])
        ss_mon_1 = self.screenshot(bb_mon_1)
        img_mon_1 = PIL.Image.frombytes("RGB", ss_mon_1.size, ss_mon_1.bgra, "raw", "BGRX")  # Convert to PIL.Image
        img_mon_1_resized = img_mon_1.resize((img_x//2, img_y), resample=PIL.Image.BILINEAR)
        if save_image:
            img_mon_1_resized.save(f"saved-images/monitor-bottom-combined-left-resized.png")

        bb_mon_2 = self.get_bounding_box("bottom", self.mss.monitors[3])
        ss_mon_2 = self.screenshot(bb_mon_2)
        img_mon_2 = PIL.Image.frombytes("RGB", ss_mon_2.size, ss_mon_2.bgra, "raw", "BGRX")  # Convert to PIL.Image
        img_mon_2_resized = img_mon_2.resize((img_x-(img_x//2), img_y), resample=PIL.Image.BILINEAR)
        if save_image:
            img_mon_2_resized.save(f"saved-images/monitor-bottom-combined-right-resized.png")

        # stitch the images together
        img_concat = self.get_concat_h(img_mon_1_resized, img_mon_2_resized)

        if save_image:
            img_concat.save(f"saved-images/monitor-bottom-combined-resized.png")

        return img_concat


    def get_concat_h(self, im1, im2):
        dst = Image.new('RGB', (im1.width + im2.width, im1.height))
        dst.paste(im2, (im1.width, 0))
        dst.paste(im1, (0, 0))
        return dst
