from typing import List

import sacn

from mapping import PixelStrip


def create_sender(pixel_strips: List[PixelStrip], **kwargs):
    sender = sacn.sACNsender(**kwargs)  # provide an IP-Address to bind to if you are using Windows and want to use multicast
    sender.start()  # start the sending thread

    for i, pixel_strip in enumerate(pixel_strips):
        universe = pixel_strip.universe
        sender.activate_output(universe)
        # multicast is not working for whatever reason
        sender[universe].multicast = False
        sender[universe].destination = pixel_strip.strip_addr

    return sender
