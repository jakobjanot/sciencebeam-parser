import re
from typing import Iterable, NamedTuple, Optional, Tuple


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


class SvgPathInstruction(NamedTuple):
    command: str
    x: float
    y: float


SVG_PATH_PATTERN = r'([A-Za-z])\s*(?:(\d+\.?\d?)(?:(?:\s+|\s*,\s*)(\d+\.?\d?))?)?'


def iter_parse_path(path_expr: str) -> Iterable[SvgPathInstruction]:
    previous_x = 0.0
    previous_y = 0.0
    first_point: Optional[Tuple[float, float]] = None
    for m in re.finditer(SVG_PATH_PATTERN, path_expr):
        command = m.group(1)
        command_upper = command.upper()
        if command_upper == 'Z':
            assert first_point is not None
            x, y = first_point  # pylint: disable=unpacking-non-sequence
        elif command_upper == 'H':
            x = float(m.group(2))
            y = previous_y if command_upper == command else 0.0
        elif command_upper == 'V':
            x = previous_x if command_upper == command else 0.0
            y = float(m.group(2))
        else:
            x = float(m.group(2))
            y = float(m.group(3))
        yield SvgPathInstruction(command=command, x=x, y=y)
        previous_x = x
        previous_y = y
        if first_point is None:
            first_point = (x, y)
