import logging
from pathlib import Path
from typing import Sequence, Tuple
from unittest.mock import MagicMock

import pytest

import PIL.Image

from sciencebeam_parser.document.layout_document import (
    LayoutBlock,
    LayoutGraphic,
    LayoutPageCoordinates,
    LayoutToken
)
from sciencebeam_parser.document.semantic_document import (
    SemanticContentWrapper,
    SemanticFigure,
    SemanticGraphic,
    SemanticLabel,
    SemanticMixedContentWrapper
)
from sciencebeam_parser.processors.graphic_matching import (
    BoundingBoxDistanceGraphicMatcher,
    GraphicRelatedBlockTextGraphicMatcher,
    OpticalCharacterRecognitionGraphicMatcher,
    get_bounding_box_list_distance
)


LOGGER = logging.getLogger(__name__)


COORDINATES_1 = LayoutPageCoordinates(
    x=10,
    y=100,
    width=200,
    height=100,
    page_number=1
)


GRAPHIC_ABOVE_FIGURE_COORDINATES_1 = LayoutPageCoordinates(
    x=10,
    y=100,
    width=200,
    height=100,
    page_number=1
)

FIGURE_BELOW_GRAPHIC_COORDINATES_1 = LayoutPageCoordinates(
    x=10,
    y=GRAPHIC_ABOVE_FIGURE_COORDINATES_1.y + GRAPHIC_ABOVE_FIGURE_COORDINATES_1.height + 10,
    width=200,
    height=20,
    page_number=1
)

FAR_AWAY_COORDINATES_1 = LayoutPageCoordinates(
    x=10,
    y=10,
    width=200,
    height=20,
    page_number=10
)

FAR_AWAY_COORDINATES_2 = LayoutPageCoordinates(
    x=10,
    y=10,
    width=200,
    height=20,
    page_number=11
)


@pytest.fixture(name='ocr_model_mock')
def _ocr_model_mock() -> MagicMock:
    return MagicMock(name='ocr_model')


def _get_semantic_content_for_page_coordinates(
    coordinates: LayoutPageCoordinates
) -> SemanticContentWrapper:
    return SemanticFigure(
        layout_block=LayoutBlock.for_tokens([
            LayoutToken(
                text='dummy',
                coordinates=coordinates
            )
        ])
    )


def _get_bounding_box_list_distance_sort_key(
    bounding_box_list_1: Sequence[LayoutPageCoordinates],
    bounding_box_list_2: Sequence[LayoutPageCoordinates]
) -> Tuple[float, ...]:
    return get_bounding_box_list_distance(
        bounding_box_list_1, bounding_box_list_2
    )


class TestGetBoundingBoxListDistance:
    def test_should_return_distance_between_vertical_adjacent_bounding_boxes(self):
        bounding_box_distance = get_bounding_box_list_distance(
            [COORDINATES_1],
            [COORDINATES_1.move_by(dy=COORDINATES_1.height)]
        )
        assert bounding_box_distance.page_number_diff == 0
        assert bounding_box_distance.delta_x == 0
        assert bounding_box_distance.delta_y == 0
        assert bounding_box_distance.euclidean_distance == 0

    def test_should_return_distance_between_horizontal_adjacent_bounding_boxes(self):
        bounding_box_distance = get_bounding_box_list_distance(
            [COORDINATES_1],
            [COORDINATES_1.move_by(dx=COORDINATES_1.width)]
        )
        assert bounding_box_distance.page_number_diff == 0
        assert bounding_box_distance.delta_x == 0
        assert bounding_box_distance.delta_y == 0
        assert bounding_box_distance.euclidean_distance == 0

    def test_should_return_delta_x_for_bounding_box_left_right(self):
        bounding_box_distance = get_bounding_box_list_distance(
            [COORDINATES_1],
            [COORDINATES_1.move_by(dx=COORDINATES_1.width + 10)]
        )
        assert bounding_box_distance.page_number_diff == 0
        assert bounding_box_distance.delta_x == 10
        assert bounding_box_distance.delta_y == 0
        assert bounding_box_distance.euclidean_distance == 10

    def test_should_return_delta_x_for_bounding_box_right_left(self):
        bounding_box_distance = get_bounding_box_list_distance(
            [COORDINATES_1.move_by(dx=COORDINATES_1.width + 10)],
            [COORDINATES_1]
        )
        assert bounding_box_distance.page_number_diff == 0
        assert bounding_box_distance.delta_x == 10
        assert bounding_box_distance.delta_y == 0
        assert bounding_box_distance.euclidean_distance == 10

    def test_should_return_delta_y_for_bounding_box_above_below(self):
        bounding_box_distance = get_bounding_box_list_distance(
            [COORDINATES_1],
            [COORDINATES_1.move_by(dy=COORDINATES_1.height + 10)]
        )
        assert bounding_box_distance.page_number_diff == 0
        assert bounding_box_distance.delta_x == 0
        assert bounding_box_distance.delta_y == 10
        assert bounding_box_distance.euclidean_distance == 10

    def test_should_return_delta_y_for_bounding_box_below_above(self):
        bounding_box_distance = get_bounding_box_list_distance(
            [COORDINATES_1.move_by(dy=COORDINATES_1.height + 10)],
            [COORDINATES_1]
        )
        assert bounding_box_distance.page_number_diff == 0
        assert bounding_box_distance.delta_x == 0
        assert bounding_box_distance.delta_y == 10
        assert bounding_box_distance.euclidean_distance == 10


class TestBoundingBoxDistanceGraphicMatcher:
    def test_should_return_empty_list_with_empty_list_of_graphics(self):
        result = BoundingBoxDistanceGraphicMatcher().get_graphic_matches(
            semantic_graphic_list=[],
            candidate_semantic_content_list=[SemanticMixedContentWrapper()]
        )
        assert not result

    def test_should_match_graphic_above_semantic_content(self):
        semantic_graphic_1 = SemanticGraphic(layout_graphic=LayoutGraphic(
            coordinates=GRAPHIC_ABOVE_FIGURE_COORDINATES_1
        ))
        candidate_semantic_content_1 = _get_semantic_content_for_page_coordinates(
            coordinates=FIGURE_BELOW_GRAPHIC_COORDINATES_1
        )
        result = BoundingBoxDistanceGraphicMatcher().get_graphic_matches(
            semantic_graphic_list=[semantic_graphic_1],
            candidate_semantic_content_list=[
                _get_semantic_content_for_page_coordinates(
                    coordinates=FAR_AWAY_COORDINATES_1
                ),
                candidate_semantic_content_1,
                _get_semantic_content_for_page_coordinates(
                    coordinates=FAR_AWAY_COORDINATES_2
                )
            ]
        )
        LOGGER.debug('result: %r', result)
        assert len(result) == 1
        first_match = result.graphic_matches[0]
        assert first_match.semantic_graphic == semantic_graphic_1
        assert first_match.candidate_semantic_content == candidate_semantic_content_1

    def test_should_not_match_further_away_graphic_to_same_semantic_content(self):
        semantic_graphic_1 = SemanticGraphic(layout_graphic=LayoutGraphic(
            coordinates=GRAPHIC_ABOVE_FIGURE_COORDINATES_1
        ))
        candidate_semantic_content_1 = _get_semantic_content_for_page_coordinates(
            coordinates=FIGURE_BELOW_GRAPHIC_COORDINATES_1
        )
        further_away_graphic_1 = SemanticGraphic(layout_graphic=LayoutGraphic(
            coordinates=FIGURE_BELOW_GRAPHIC_COORDINATES_1.move_by(dy=500)
        ))
        further_away_graphic_2 = SemanticGraphic(layout_graphic=LayoutGraphic(
            coordinates=FIGURE_BELOW_GRAPHIC_COORDINATES_1.move_by(dy=1000)
        ))
        result = BoundingBoxDistanceGraphicMatcher().get_graphic_matches(
            semantic_graphic_list=[
                further_away_graphic_1,
                semantic_graphic_1,
                further_away_graphic_2
            ],
            candidate_semantic_content_list=[
                candidate_semantic_content_1
            ]
        )
        LOGGER.debug('result: %r', result)
        assert len(result) == 1
        first_match = result.graphic_matches[0]
        assert first_match.semantic_graphic == semantic_graphic_1
        assert first_match.candidate_semantic_content == candidate_semantic_content_1

    def test_should_not_match_empty_graphic(self):
        empty_semantic_graphic_1 = SemanticGraphic(layout_graphic=LayoutGraphic(
            coordinates=COORDINATES_1._replace(
                width=0, height=0
            )
        ))
        candidate_semantic_content_1 = _get_semantic_content_for_page_coordinates(
            coordinates=COORDINATES_1
        )
        result = BoundingBoxDistanceGraphicMatcher().get_graphic_matches(
            semantic_graphic_list=[empty_semantic_graphic_1],
            candidate_semantic_content_list=[
                candidate_semantic_content_1
            ]
        )
        LOGGER.debug('result: %r', result)
        assert not result

    def test_should_not_match_graphic_on_another_page(self):
        semantic_graphic_1 = SemanticGraphic(layout_graphic=LayoutGraphic(
            coordinates=COORDINATES_1._replace(
                page_number=COORDINATES_1.page_number + 1
            )
        ))
        candidate_semantic_content_1 = _get_semantic_content_for_page_coordinates(
            coordinates=COORDINATES_1
        )
        result = BoundingBoxDistanceGraphicMatcher().get_graphic_matches(
            semantic_graphic_list=[semantic_graphic_1],
            candidate_semantic_content_list=[
                candidate_semantic_content_1
            ]
        )
        LOGGER.debug('result: %r', result)
        assert not result.graphic_matches
        assert result.unmatched_graphics == [semantic_graphic_1]

    @pytest.mark.parametrize(
        "graphic_type,should_match",
        [("svg", False), ("bitmap", True)]
    )
    def test_should_match_graphic_of_specific(
        self,
        graphic_type: str,
        should_match: bool
    ):
        semantic_graphic_1 = SemanticGraphic(layout_graphic=LayoutGraphic(
            coordinates=GRAPHIC_ABOVE_FIGURE_COORDINATES_1,
            graphic_type=graphic_type
        ))
        candidate_semantic_content_1 = _get_semantic_content_for_page_coordinates(
            coordinates=FIGURE_BELOW_GRAPHIC_COORDINATES_1
        )
        result = BoundingBoxDistanceGraphicMatcher().get_graphic_matches(
            semantic_graphic_list=[semantic_graphic_1],
            candidate_semantic_content_list=[
                candidate_semantic_content_1
            ]
        )
        LOGGER.debug('result: %r', result)
        if should_match:
            assert len(result) == 1
            first_match = result.graphic_matches[0]
            assert first_match.semantic_graphic == semantic_graphic_1
        else:
            assert not result.graphic_matches
            assert result.unmatched_graphics == [semantic_graphic_1]


class TestGraphicRelatedBlockTextGraphicMatcher:
    @pytest.mark.parametrize(
        "related_text,figure_label,should_match",
        [
            ("Figure 1", "Figure 1", True),
            ("Figure 1", "Figure 2", False),
            ("Fig 1", "Figure 1", True),
            ("F 1", "Figure 1", False),
            ("Fug 1", "Figure 1", False),
            ("Other\nFigure 1\nMore", "Figure 1", True)
        ]
    )
    def test_should_match_based_on_figure_label(
        self,
        related_text: str,
        figure_label: str,
        should_match: bool
    ):
        semantic_graphic_1 = SemanticGraphic(layout_graphic=LayoutGraphic(
            coordinates=FAR_AWAY_COORDINATES_1,
            related_block=LayoutBlock.for_text(related_text)
        ))
        candidate_semantic_content_1 = SemanticFigure([
            SemanticLabel(layout_block=LayoutBlock.for_text(figure_label))
        ])
        result = GraphicRelatedBlockTextGraphicMatcher().get_graphic_matches(
            semantic_graphic_list=[semantic_graphic_1],
            candidate_semantic_content_list=[
                candidate_semantic_content_1
            ]
        )
        LOGGER.debug('result: %r', result)
        if should_match:
            assert len(result) == 1
            first_match = result.graphic_matches[0]
            assert first_match.semantic_graphic == semantic_graphic_1
        else:
            assert not result.graphic_matches
            assert result.unmatched_graphics == [semantic_graphic_1]

    def test_should_ignore_layout_graphic_without_related_block(
        self
    ):
        semantic_graphic_1 = SemanticGraphic(layout_graphic=LayoutGraphic(
            coordinates=FAR_AWAY_COORDINATES_1,
            related_block=None
        ))
        candidate_semantic_content_1 = SemanticFigure([
            SemanticLabel(layout_block=LayoutBlock.for_text('Figure 1'))
        ])
        result = GraphicRelatedBlockTextGraphicMatcher().get_graphic_matches(
            semantic_graphic_list=[semantic_graphic_1],
            candidate_semantic_content_list=[
                candidate_semantic_content_1
            ]
        )
        LOGGER.debug('result: %r', result)
        assert not result.graphic_matches
        assert result.unmatched_graphics == [semantic_graphic_1]


class TestOpticalCharacterRecognitionGraphicMatcher:
    @pytest.mark.parametrize(
        "ocr_text,figure_label,should_match",
        [
            ("Figure 1", "Figure 1", True),
            ("Figure 1", "Figure 2", False),
            ("Fig 1", "Figure 1", True),
            ("F 1", "Figure 1", False),
            ("Fug 1", "Figure 1", False),
            ("Other\nFigure 1\nMore", "Figure 1", True)
        ]
    )
    def test_should_match_based_on_figure_label(
        self,
        ocr_model_mock: MagicMock,
        ocr_text: str,
        figure_label: str,
        should_match: bool,
        tmp_path:  Path
    ):
        local_graphic_path = tmp_path / 'image.png'
        PIL.Image.new('RGB', (10, 10), (0, 1, 2)).save(local_graphic_path)
        ocr_model_mock.predict_single.return_value.get_text.return_value = ocr_text
        semantic_graphic_1 = SemanticGraphic(layout_graphic=LayoutGraphic(
            coordinates=FAR_AWAY_COORDINATES_1,
            local_file_path=str(local_graphic_path)
        ))
        candidate_semantic_content_1 = SemanticFigure([
            SemanticLabel(layout_block=LayoutBlock.for_text(figure_label))
        ])
        result = OpticalCharacterRecognitionGraphicMatcher(
            ocr_model=ocr_model_mock
        ).get_graphic_matches(
            semantic_graphic_list=[semantic_graphic_1],
            candidate_semantic_content_list=[
                candidate_semantic_content_1
            ]
        )
        LOGGER.debug('result: %r', result)
        if should_match:
            assert len(result) == 1
            first_match = result.graphic_matches[0]
            assert first_match.semantic_graphic == semantic_graphic_1
        else:
            assert not result.graphic_matches
            assert result.unmatched_graphics == [semantic_graphic_1]

    def test_should_ignore_layout_graphic_without_local_path(
        self,
        ocr_model_mock: MagicMock
    ):
        ocr_model_mock.predict_single.return_value.get_text.side_effect = RuntimeError
        semantic_graphic_1 = SemanticGraphic(layout_graphic=LayoutGraphic(
            coordinates=FAR_AWAY_COORDINATES_1,
            local_file_path=None
        ))
        candidate_semantic_content_1 = SemanticFigure([
            SemanticLabel(layout_block=LayoutBlock.for_text('Figure 1'))
        ])
        result = OpticalCharacterRecognitionGraphicMatcher(
            ocr_model=ocr_model_mock
        ).get_graphic_matches(
            semantic_graphic_list=[semantic_graphic_1],
            candidate_semantic_content_list=[
                candidate_semantic_content_1
            ]
        )
        LOGGER.debug('result: %r', result)
        assert not result.graphic_matches
        assert result.unmatched_graphics == [semantic_graphic_1]
