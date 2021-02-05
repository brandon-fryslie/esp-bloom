
# Format of the pixel mapping
# We need to turn an XY coordinate in an image into a pixel address
# Pixel address:
# - strip # (dmx universe, etc, eventually)
# - LED # (on the strip)
from typing import List, Callable, Optional

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
                 row_length: int, rows: int, start_left: bool,
                 start_bottom: bool, region_fn: Callable[[PixelAddress], str],
                 regions: List[ScreenRegion],
        ):
        self.strip_addr = strip_addr
        self.universe = universe
        self.row_length = row_length
        self.rows = rows
        self.start_left = start_left
        self.start_bottom = start_bottom
        self.region_fn = region_fn
        self.regions = regions

        self.pixels = self.generate_pixel_mapping()

    def __str__(self):
        return f"PixelStrip[{self.strip_addr},row_length={self.row_length},rows={self.rows},y={self.start_left},start_bottom={self.start_bottom}]"

    def __repr__(self):
        return self.__str__()

    def get_pixels_for_region(self, region: ScreenRegion):
        res = [pixel for pixel in self.pixels if pixel.region == region.name]
        # print(f"got pixel for region {region}")
        # print(res)
        return res

    def generate_pixel_mapping(self, start_left: bool = True, start_bottom: bool = True) -> List[PixelAddress]:
        pixels = []

        # zig = left -> right
        # zag = right -> left

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
                row_number = self.rows - y
            else:
                row_number = y

            is_zig = row_number % 2 == 1

            if is_zig and start_left is True:
                col_idx_start = 0
                col_idx_end = self.row_length
                col_idx_step = 1
            elif not is_zig and start_left is True:
                col_idx_start = self.row_length-1
                col_idx_end = -1
                col_idx_step = -1
            elif is_zig and start_left is False:
                col_idx_start = self.row_length-1
                col_idx_end = -1
                col_idx_step = -1
            elif not is_zig and start_left is False:
                col_idx_start = 0
                col_idx_end = self.row_length
                col_idx_step = 1
            else:
                raise ValueError("ERROR: could not generate pixel mapping")

            # print(f"generating pixel mapping for x {col_idx_start}, {col_idx_end}, {col_idx_step}")

            for x in range(col_idx_start, col_idx_end, col_idx_step):
                # print(f"creating pixel x:{x} y:{y}")
                pixel = PixelAddress(self.strip_addr, strip_idx, x, y)

                pixel.region = self.region_fn(pixel)

                pixels.append(pixel)

                # prolly a better way to track the index
                strip_idx += 1

        return pixels


