import logging

from sciencebeam_parser.utils.svg import (
    SvgPathCommands,
    SvgPathInstruction,
    iter_parse_path
)


LOGGER = logging.getLogger(__name__)


class TestIterParsePath:
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
