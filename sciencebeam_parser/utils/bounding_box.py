from functools import reduce
from typing import Iterable, NamedTuple


class BoundingBox(NamedTuple):
    x: float
    y: float
    width: float
    height: float

    def is_empty(self):
        return not self.width or not self.height

    def include(self, other: 'BoundingBox'):
        if other.is_empty():
            return self
        if self.is_empty():
            return other
        x = min(self.x, other.x)
        y = min(self.y, other.y)
        w = max(self.x + self.width, other.x + other.width) - x
        h = max(self.y + self.height, other.y + other.height) - y
        return BoundingBox(x, y, w, h)


EMPTY_BOUNDING_BOX = BoundingBox(0, 0, 0, 0)


def merge_bounding_boxes(
    bounding_box_iterable: Iterable[BoundingBox]
) -> BoundingBox:
    return reduce(BoundingBox.include, bounding_box_iterable)
