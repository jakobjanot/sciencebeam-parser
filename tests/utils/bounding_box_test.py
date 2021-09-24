import logging

from sciencebeam_parser.utils.bounding_box import (
    BoundingBox,
    merge_bounding_boxes
)


LOGGER = logging.getLogger(__name__)


class TestBoundingBox:
    def test_should_include_another_bounding_box_to_the_bottom_right(self):
        assert (
            BoundingBox(10, 20, 50, 100).include(BoundingBox(100, 100, 200, 200)) ==
            BoundingBox(10, 20, 100 + 200 - 10, 100 + 200 - 20)
        )

    def test_should_include_another_bounding_box_to_the_top_left(self):
        assert (
            BoundingBox(100, 100, 200, 200).include(BoundingBox(10, 20, 50, 100)) ==
            BoundingBox(10, 20, 100 + 200 - 10, 100 + 200 - 20)
        )


class TestMergeBoundingBoxes:
    def test_should_return_single_bounding_box(self):
        bounding_box = BoundingBox(11, 12, 13, 15)
        assert merge_bounding_boxes([bounding_box]) == bounding_box

    def test_should_merge_two_bounding_boxes(self):
        bounding_boxes = [
            BoundingBox(10, 20, 50, 100),
            BoundingBox(100, 100, 200, 200)
        ]
        expected_bounding_box = BoundingBox(10, 20, 100 + 200 - 10, 100 + 200 - 20)
        result = merge_bounding_boxes(bounding_boxes)
        LOGGER.debug('result: %r', result)
        assert result == expected_bounding_box
