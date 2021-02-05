
import mss
from mss import models
from mss.base import MSSBase
from mss.screenshot import ScreenShot

class ScreenRegion:
    def __init__(self, name: str, monitor_no: int, mss: MSSBase):
        self.name = name
        self.monitor_no = monitor_no
        self.mss = mss
        self.monitor = mss.monitors[monitor_no]

    # Get a bounding box for a screen area
    def get_bounding_box(self):
        screen_percent = 25

        # print(f"getting bb for monitor {monitor}")
        # pprint(monitor)

        height = self.monitor["height"]
        width = self.monitor["width"]
        top = self.monitor["top"]
        bottom = top + height
        left = self.monitor["left"]
        right = left + width

        bounding_boxes = {
            "top": (left, top, right, int(height*screen_percent//100)),
            "bottom": (left, bottom-int(height*screen_percent//100), right, bottom),
            "left": (left, top, left+int((width)*screen_percent//100), bottom),
            "right": (right-int(width*screen_percent//100), 0, right, bottom),
        }
        bb = bounding_boxes[self.name]

        # pprint(bb)
        return bb

    def screenshot(self):
        bb = self.get_bounding_box()
        screenshot = self.mss.grab(bb)  # Take the screenshot
        return screenshot

