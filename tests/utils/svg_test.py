import logging

from sciencebeam_parser.utils.svg import (
    SvgPathCommands,
    SvgPathInstruction,
    iter_parse_path,
    iter_path_split,
    parse_path_values
)


LOGGER = logging.getLogger(__name__)


class TestIterPathSplit:
    def test_should_split_simple_move_to_path(self):
        result = list(iter_path_split('M10 10'))
        LOGGER.debug('result: %r', result)
        assert result == [('M', '10 10')]

    def test_should_split_simple_move_to_path_and_close_path(self):
        result = list(iter_path_split('M10 10 Z'))
        LOGGER.debug('result: %r', result)
        assert result == [('M', '10 10'), ('Z', '')]


class TestIterParsePathValues:
    def test_should_parse_empty_str(self):
        result = parse_path_values('')
        LOGGER.debug('result: %r', result)
        assert result == []

    def test_should_parse_two_space_separated_values(self):
        result = parse_path_values('10 10')
        LOGGER.debug('result: %r', result)
        assert result == [10.0, 10.0]


class TestIterParsePath:  # pylint: disable=too-many-public-methods
    def test_should_parse_simple_move_to(self):
        result = list(iter_parse_path('M10 10'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10)
        ]

    def test_should_parse_move_to_line_to(self):
        result = list(iter_parse_path('M10 10 L20 20'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.LINE_TO, x=20, y=20)
        ]

    def test_should_parse_move_to_line_to_with_more_spacing(self):
        result = list(iter_parse_path(' M  10  10  L  20  20  '))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.LINE_TO, x=20, y=20)
        ]

    def test_should_parse_move_to_line_to_with_comma(self):
        result = list(iter_parse_path('M10,10 L20,20'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.LINE_TO, x=20, y=20)
        ]

    def test_should_parse_move_to_line_to_with_comma_and_dot(self):
        result = list(iter_parse_path('M10.5,10.5 L20.5,20.5'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10.5, y=10.5),
            SvgPathInstruction(command=SvgPathCommands.LINE_TO, x=20.5, y=20.5)
        ]

    def test_should_parse_move_to_line_by(self):
        result = list(iter_parse_path('M10 10 l20 20'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.LINE_BY, x=20, y=20)
        ]

    def test_should_parse_move_to_horizontal_line_to(self):
        result = list(iter_parse_path('M10 10 H20'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.HORIZONTAL_LINE_TO, x=20, y=10)
        ]

    def test_should_parse_move_to_horizontal_line_by(self):
        result = list(iter_parse_path('M10 10 h20'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.HORIZONTAL_LINE_BY, x=20, y=0)
        ]

    def test_should_parse_move_to_vertical_line_to(self):
        result = list(iter_parse_path('M10 10 V20'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.VERTICAL_LINE_TO, x=10, y=20)
        ]

    def test_should_parse_move_to_vertical_line_by(self):
        result = list(iter_parse_path('M10 10 v20'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.VERTICAL_LINE_BY, x=0, y=20)
        ]

    def test_should_parse_move_to_line_to_close_path(self):
        result = list(iter_parse_path('M10 10 L20 20 Z'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.LINE_TO, x=20, y=20),
            SvgPathInstruction(command=SvgPathCommands.CLOSE_PATH, x=10, y=10)
        ]

    def test_should_parse_bezier_cubic_curve_to(self):
        result = list(iter_parse_path('M10 10 C 20 20, 40 20, 50 10'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.CUBIC_CURVE_TO, x=50, y=10),
        ]

    def test_should_parse_bezier_cubic_curve_by(self):
        result = list(iter_parse_path('M10 10 c 20 20, 40 20, 50 10'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.CUBIC_CURVE_BY, x=50, y=10),
        ]

    def test_should_parse_shortcut_cubic_curve_to(self):
        result = list(iter_parse_path('M10 10 S 40 20, 50 10'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.SHORTCUT_CUBIC_CURVE_TO, x=50, y=10),
        ]

    def test_should_parse_shortcut_cubic_curve_by(self):
        result = list(iter_parse_path('M10 10 s 40 20, 50 10'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.SHORTCUT_CUBIC_CURVE_BY, x=50, y=10),
        ]

    def test_should_parse_quadratic_curve_to(self):
        result = list(iter_parse_path('M10 10 Q 40 20, 50 10'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.QUADRATIC_CURVE_TO, x=50, y=10),
        ]

    def test_should_parse_quadratic_curve_by(self):
        result = list(iter_parse_path('M10 10 q 40 20, 50 10'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.QUADRATIC_CURVE_BY, x=50, y=10),
        ]

    def test_should_parse_shortcut_quadratic_curve_to(self):
        result = list(iter_parse_path('M10 10 T 50 10'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.SHORTCUT_QUADRATIC_CURVE_TO, x=50, y=10),
        ]

    def test_should_parse_shortcut_quadratic_curve_by(self):
        result = list(iter_parse_path('M10 10 t 50 10'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.SHORTCUT_QUADRATIC_CURVE_BY, x=50, y=10),
        ]

    def test_should_parse_arc_to(self):
        result = list(iter_parse_path('M10 10 A 30 50 0 0 1 162.55 162.45'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.ARC_TO, x=162.55, y=162.45),
        ]

    def test_should_parse_arc_by(self):
        result = list(iter_parse_path('M10 10 a 30 50 0 0 1 162.55 162.45'))
        LOGGER.debug('result: %r', result)
        assert result == [
            SvgPathInstruction(command=SvgPathCommands.MOVE_TO, x=10, y=10),
            SvgPathInstruction(command=SvgPathCommands.ARC_BY, x=162.55, y=162.45),
        ]
