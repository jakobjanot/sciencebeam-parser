import logging
from typing import List, Optional, Sequence, Tuple

import PIL.Image

from layoutparser.elements.layout import Layout
from layoutparser.models.auto_layoutmodel import AutoLayoutModel
from layoutparser.models.base_layoutmodel import BaseLayoutModel

from sciencebeam_parser.utils.bounding_box import BoundingBox
from sciencebeam_parser.cv_models.cv_model import (
    ComputerVisionModel,
    ComputerVisionModelInstance,
    ComputerVisionModelResult
)


LOGGER = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = 'lp://efficientdet/PubLayNet'

DEFAULT_SCORE_THRESHOLD = 0.0


def load_model(model_path: str) -> BaseLayoutModel:
    LOGGER.info('loading model: %r', model_path)
    return AutoLayoutModel(model_path)


def get_bounding_box_for_layout_parser_coordinates(
    coordinates: Tuple[float, float, float, float]
) -> BoundingBox:
    x1, y1, x2, y2 = coordinates
    return BoundingBox(x=x1, y=y1, width=x2 - x1, height=y2 - y1)


def is_bounding_box_overlapping_with_any_bounding_boxes(
    bounding_box: BoundingBox,
    other_bounding_boxes: Sequence[BoundingBox],
    max_overlap_ratio: float = 0.1
) -> bool:
    bounding_box_area = bounding_box.area
    for other_bounding_box in other_bounding_boxes:
        intersection_bounding_box = bounding_box.intersection(
            other_bounding_box
        )
        if not intersection_bounding_box:
            continue
        if intersection_bounding_box.area / bounding_box_area >= max_overlap_ratio:
            return True
    return False


class LayoutParserComputerVisionModelInstance(ComputerVisionModelInstance):
    def __init__(self, bounding_box: BoundingBox):
        super().__init__()
        self.bounding_box = bounding_box

    def get_bounding_box(self) -> BoundingBox:
        return self.bounding_box


class LayoutParserComputerVisionModelResult(ComputerVisionModelResult):
    def __init__(
        self,
        layout: Layout,
        score_threshold: float,
        avoid_overlapping: bool,
        max_overlap_ratio: float = 0.1
    ):
        super().__init__()
        self.layout = layout
        self.score_threshold = score_threshold
        self.avoid_overlapping = avoid_overlapping
        self.max_overlap_ratio = max_overlap_ratio
        LOGGER.debug('layout: %r', layout)

    def get_instances_by_type_name(self, type_name: str) -> Sequence[ComputerVisionModelInstance]:
        instances = [
            LayoutParserComputerVisionModelInstance(
                get_bounding_box_for_layout_parser_coordinates(block.coordinates)
            )
            for block in self.layout
            if (
                block.type == type_name
                and block.score >= self.score_threshold
            )
        ]
        if self.avoid_overlapping:
            _instances = instances
            instances = []
            prev_bounding_boxes: List[BoundingBox] = []
            for instance in _instances:
                bounding_box = instance.get_bounding_box()
                if is_bounding_box_overlapping_with_any_bounding_boxes(
                    bounding_box,
                    prev_bounding_boxes,
                    max_overlap_ratio=self.max_overlap_ratio
                ):
                    LOGGER.debug(
                        'bounding box overlapping with prev: %r ~ %r',
                        bounding_box, prev_bounding_boxes
                    )
                    continue
                instances.append(instance)
                prev_bounding_boxes.append(bounding_box)
        return instances


class LayoutParserComputerVisionModel(ComputerVisionModel):
    def __init__(
        self,
        config: dict,
        model_path: str = DEFAULT_MODEL_PATH,
    ):
        super().__init__()
        self.score_threshold = float(config.get('score_threshold', DEFAULT_SCORE_THRESHOLD))
        self.avoid_overlapping = bool(config.get('avoid_overlapping', True))
        self.model_path = model_path
        self._layout_model: Optional[BaseLayoutModel] = None

    @property
    def layout_model(self) -> BaseLayoutModel:
        if self._layout_model is None:
            self._layout_model = load_model(self.model_path)
        return self._layout_model

    def predict_single(self, image: PIL.Image.Image) -> ComputerVisionModelResult:
        return LayoutParserComputerVisionModelResult(
            self.layout_model.detect(image),
            score_threshold=self.score_threshold,
            avoid_overlapping=self.avoid_overlapping
        )
