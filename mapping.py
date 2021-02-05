
# Format of the pixel mapping
# We need to turn an XY coordinate in an image into a pixel address
# Pixel address:
# - strip # (dmx universe, etc, eventually)
# - LED # (on the strip)
from typing import List, Callable, Optional, Union

from region import ScreenRegion


class PixelAddress:
    def __init__(self, strip_addr: str, index: int, x: int, y: int, region: Optional[str] = None):
        self.index = index
        self.strip_addr = strip_addr
        self.x = x
        self.y = y
        self.id = f"{x}_{y}"
        self.region = region

    def __str__(self):
        return f"PixelAddress[{self.strip_addr},index={self.index},x={self.x},y={self.y},region={self.region}]"

    def __repr__(self):
        return self.__str__()

class PixelStrip:
    def __init__(self, strip_addr: str, universe: int,
                 row_length: Union[int, List[int]], rows: int, start_left: bool,
                 start_bottom: bool, region_fn: Callable[[PixelAddress], str],
                 regions: List[ScreenRegion],
                 first_pixel_offset: int = 0, max_row_length: Optional[int] = None,
        ):

        # Keep track of max row length to avoid index out of bound issues
        # with the way we handle the image data
        self.row_length = row_length
        if max_row_length is not None:
            self.max_row_length = max_row_length
        else:
            self.max_row_length = max(row_length)

        self.strip_addr = strip_addr
        self.universe = universe
        self.rows = rows
        self.start_left = start_left
        self.start_bottom = start_bottom
        self.region_fn = region_fn
        self.regions = regions
        self.first_pixel_offset = first_pixel_offset

        self.pixels = self.generate_pixel_mapping(start_left, start_bottom)

    def __str__(self):
        return f"PixelStrip[{self.strip_addr},row_length={self.row_length},rows={self.rows},y={self.start_left},start_bottom={self.start_bottom}]"

    def __repr__(self):
        return self.__str__()

    def get_pixels_for_region(self, region: ScreenRegion):
        res = [pixel for pixel in self.pixels if pixel.region == region.name]
        # print(f"got pixel for region {region}")
        # print(res)
        return res

    # Generates a list of 'Pixel' objects that correspond to a pixel on a strip
    # The order of the list corresponds to the order of the pixels on the led strip
    # Each pixel knows its own X, Y coordinate in the grid (horizontal zigzag pattern)
    # which we use later to grab image data for the correct pixel
    # This is probably the most complex part of the application
    def generate_pixel_mapping(self, start_left: bool, start_bottom: bool) -> List[PixelAddress]:
        pixels = []

        # zig = left -> right
        # zag = right -> left

        # We run 2 loops. the outer loop is by row, the inner by LED (which
        # could be considered a 'column' if every strip has the same # of pixels)
        # We have a bunch of complicated logic to run the loops in the actual order of the
        # leds in zigzag pattern, which makes using everything later in our draw loop
        # very simple

        if start_bottom is True:
            row_idx_start = self.rows-1
            row_idx_end = -1
            row_idx_step = -1
        else:
            row_idx_start = 0
            row_idx_end = self.rows
            row_idx_step = 1

        strip_idx = 0
        # print(f"generating pixel mapping for y {row_idx_start}, {row_idx_end}, {row_idx_step}")
        for y in range(row_idx_start, row_idx_end, row_idx_step):
            if start_bottom:
                row_number = self.rows - y - 1
            else:
                row_number = y

            if start_left:
                is_zig = row_number % 2 == 1
            else:
                is_zig = row_number % 2 == 0

            # Handle pixel offset, only applies to the first row in a fixture
            if y == row_idx_start:
                row_length = self.row_length[y] + self.first_pixel_offset
                # print(f"first row: y:{y} == row_idx_start, row_length: {self.row_length[y]}, offset: {self.first_pixel_offset}, total row_length {row_length}")
            else:
                row_length = self.row_length[y]

            # print(f"MAPPING ROW: is_zig: {is_zig}, length: {row_length}")

            if is_zig and start_left is True:
                col_idx_start = 0
                col_idx_end = row_length
                col_idx_step = 1
            elif not is_zig and start_left is True:
                col_idx_start = row_length-1
                col_idx_end = -1
                col_idx_step = -1
            elif is_zig and start_left is False:
                col_idx_start = row_length-1
                col_idx_end = -1
                col_idx_step = -1
            elif not is_zig and start_left is False:
                col_idx_start = 0
                col_idx_end = row_length
                col_idx_step = 1
            else:
                raise ValueError("ERROR: could not generate pixel mapping")

            # print(f"generating pixel mapping for x {col_idx_start}, {col_idx_end}, {col_idx_step}")
            # offset first row if needed
            # if y == row_idx_start:
            #     print(f"first_row")
            #     col_idx_start += self.first_pixel_offset

            for x in range(col_idx_start, col_idx_end, col_idx_step):
                # print(f" creating pixel x:{x} y:{y}")
                pixel = PixelAddress(self.strip_addr, strip_idx, x, y)

                # determine which region a pixel belongs to, used later
                # so we can have some pixels on a strip correspond to the
                # top of the screen and some to the bottom
                pixel.region = self.region_fn(pixel)

                pixels.append(pixel)

                # prolly a better way to track the index
                strip_idx += 1

        return pixels


