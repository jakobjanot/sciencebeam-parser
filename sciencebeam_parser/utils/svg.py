import logging
import re
from typing import Iterable, List, NamedTuple, Optional, Tuple


LOGGER = logging.getLogger(__name__)


class SvgPathCommands:
    MOVE_TO = 'M'
    MOVE_BY = 'm'
    LINE_TO = 'L'
    LINE_BY = 'l'
    HORIZONTAL_LINE_TO = 'H'
    HORIZONTAL_LINE_BY = 'h'
    VERTICAL_LINE_TO = 'V'
    VERTICAL_LINE_BY = 'v'
    CLOSE_PATH = 'Z'
    CUBIC_CURVE_TO = 'C'
    CUBIC_CURVE_BY = 'c'
    SHORTCUT_CUBIC_CURVE_TO = 'S'
    SHORTCUT_CUBIC_CURVE_BY = 's'
    QUADRATIC_CURVE_TO = 'Q'
    QUADRATIC_CURVE_BY = 'q'
    SHORTCUT_QUADRATIC_CURVE_TO = 'T'
    SHORTCUT_QUADRATIC_CURVE_BY = 't'


class SvgPathInstruction(NamedTuple):
    command: str
    x: float
    y: float


def iter_path_split(path_expr: str) -> Iterable[Tuple[str, str]]:
    command: Optional[str] = None
    for item in re.split(r'([A-Za-z])', path_expr):
        if command:
            yield command, item.strip()
            command = None
        if item.isalpha():
            command = item
    if command:
        yield command, ''


def parse_path_values(values_str: str) -> List[float]:
    LOGGER.debug('values_str: %r', values_str)
    if not values_str:
        return []
    return [
        float(item)
        for item in re.split(r'\s+|\s*,\s*', values_str)
    ]


def iter_parse_path(path_expr: str) -> Iterable[SvgPathInstruction]:
    previous_x = 0.0
    previous_y = 0.0
    first_point: Optional[Tuple[float, float]] = None
    for command, values_str in iter_path_split(path_expr):
        values = parse_path_values(values_str)
        command_upper = command.upper()
        if command_upper == SvgPathCommands.CLOSE_PATH:
            assert first_point is not None
            x, y = first_point  # pylint: disable=unpacking-non-sequence
        elif command_upper == SvgPathCommands.HORIZONTAL_LINE_TO:
            x = values[0]
            y = previous_y if command_upper == command else 0.0
        elif command_upper == SvgPathCommands.VERTICAL_LINE_TO:
            x = previous_x if command_upper == command else 0.0
            y = values[0]
        else:
            x = values[-2]
            y = values[-1]
        yield SvgPathInstruction(command=command, x=x, y=y)
        previous_x = x
        previous_y = y
        if first_point is None:
            first_point = (x, y)
