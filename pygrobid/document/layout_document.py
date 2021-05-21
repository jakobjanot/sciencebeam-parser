import logging
from dataclasses import dataclass
from functools import partial
from typing import Callable, List, Iterable, NamedTuple, Optional, Tuple

from pygrobid.utils.tokenizer import get_tokenized_tokens


LOGGER = logging.getLogger(__name__)


@dataclass
class LayoutFont:
    font_id: str
    font_family: Optional[str] = None
    font_size: Optional[float] = None
    is_bold: Optional[bool] = None
    is_italics: Optional[bool] = None


EMPTY_FONT = LayoutFont(font_id='_EMPTY')


class LayoutCoordinates(NamedTuple):
    x: float
    y: float
    width: float
    height: float


@dataclass
class LayoutToken:
    text: str
    font: LayoutFont = EMPTY_FONT
    whitespace: str = ' '
    coordinates: Optional[LayoutCoordinates] = None


T_FlatMapLayoutTokensFn = Callable[[LayoutToken], List[LayoutToken]]


def default_get_tokenized_tokens_keep_whitespace(text: str) -> List[str]:
    return get_tokenized_tokens(text, keep_whitespace=True)


def get_relative_coordinates(
    coordinates: Optional[LayoutCoordinates],
    text: str,
    text_character_offset: int,
    total_text_length: int
) -> Optional[LayoutCoordinates]:
    if not coordinates:
        return None
    return LayoutCoordinates(
        x=(
            coordinates.x
            + coordinates.width * text_character_offset / total_text_length
        ),
        y=coordinates.y,
        width=(
            coordinates.width
            * len(text) / total_text_length
        ),
        height=coordinates.height
    )


def retokenize_layout_token(
    layout_token: LayoutToken,
    tokenize_fn: Optional[Callable[[str], List[str]]] = None
) -> List[LayoutToken]:
    if not layout_token.text.strip():
        return []
    if tokenize_fn is None:
        tokenize_fn = default_get_tokenized_tokens_keep_whitespace
    token_texts = tokenize_fn(layout_token.text)
    if token_texts == [layout_token.text]:
        return [layout_token]
    total_text_length = sum(len(token_text) for token_text in token_texts)
    texts_with_whitespace: List[Tuple[str, str, int]] = []
    pending_token_text = ''
    pending_whitespace = ''
    text_character_offset = 0
    pending_text_character_offset = 0
    for token_text in token_texts:
        if not token_text.strip():
            pending_whitespace += token_text
            text_character_offset += len(token_text)
            continue
        if pending_token_text:
            texts_with_whitespace.append((
                pending_token_text,
                pending_whitespace,
                pending_text_character_offset
            ))
        pending_token_text = token_text
        pending_whitespace = ''
        pending_text_character_offset = text_character_offset
        text_character_offset += len(token_text)
    pending_whitespace += layout_token.whitespace
    if pending_token_text:
        texts_with_whitespace.append((
            pending_token_text,
            pending_whitespace,
            pending_text_character_offset
        ))
    return [
        LayoutToken(
            text=token_text,
            font=layout_token.font,
            whitespace=whitespace,
            coordinates=get_relative_coordinates(
                layout_token.coordinates,
                pending_token_text,
                text_character_offset,
                total_text_length
            )
        )
        for token_text, whitespace, text_character_offset in texts_with_whitespace
    ]


def join_layout_tokens(layout_tokens: List[LayoutToken]) -> str:
    return ''.join([
        (
            token.text + token.whitespace
            if index < len(layout_tokens) - 1
            else token.text
        )
        for index, token in enumerate(layout_tokens)
    ])


@dataclass
class LayoutLine:
    tokens: List[LayoutToken]

    def flat_map_layout_tokens(self, fn: T_FlatMapLayoutTokensFn) -> 'LayoutLine':
        return LayoutLine(tokens=[
            tokenized_token
            for token in self.tokens
            for tokenized_token in fn(token)
        ])


@dataclass
class LayoutBlock:
    lines: List[LayoutLine]

    def flat_map_layout_tokens(self, fn: T_FlatMapLayoutTokensFn) -> 'LayoutBlock':
        return LayoutBlock(lines=[
            line.flat_map_layout_tokens(fn)
            for line in self.lines
        ])

    def remove_empty_lines(self) -> 'LayoutBlock':
        return LayoutBlock(lines=[
            line
            for line in self.lines
            if line.tokens
        ])


@dataclass
class LayoutPage:
    blocks: List[LayoutBlock]

    def flat_map_layout_tokens(self, fn: T_FlatMapLayoutTokensFn) -> 'LayoutPage':
        return LayoutPage(blocks=[
            block.flat_map_layout_tokens(fn)
            for block in self.blocks
        ])

    def remove_empty_blocks(self) -> 'LayoutPage':
        blocks: List[LayoutBlock] = [
            block.remove_empty_lines()
            for block in self.blocks
        ]
        return LayoutPage(blocks=[
            block
            for block in blocks
            if block.lines
        ])


@dataclass
class LayoutDocument:
    pages: List[LayoutPage]

    def iter_all_blocks(self) -> Iterable[LayoutBlock]:
        return (
            block
            for page in self.pages
            for block in page.blocks
        )

    def iter_all_tokens(self) -> Iterable[LayoutToken]:
        return (
            token
            for block in self.iter_all_blocks()
            for line in block.lines
            for token in line.tokens
        )

    def flat_map_layout_tokens(
        self, fn: T_FlatMapLayoutTokensFn, **kwargs
    ) -> 'LayoutDocument':
        if kwargs:
            fn = partial(fn, **kwargs)
        return LayoutDocument(pages=[
            page.flat_map_layout_tokens(fn)
            for page in self.pages
        ])

    def retokenize(self, **kwargs) -> 'LayoutDocument':
        return self.flat_map_layout_tokens(retokenize_layout_token, **kwargs)

    def remove_empty_blocks(self) -> 'LayoutDocument':
        pages: List[LayoutPage] = [
            page.remove_empty_blocks()
            for page in self.pages
        ]
        return LayoutDocument(pages=[
            page
            for page in pages
            if page.blocks
        ])


def flat_map_layout_document_tokens(
    layout_document: LayoutDocument,
    fn: T_FlatMapLayoutTokensFn,
    **kwargs
) -> LayoutDocument:
    return layout_document.flat_map_layout_tokens(fn, **kwargs)


def retokenize_layout_document(
    layout_document: LayoutDocument,
    **kwargs
) -> LayoutDocument:
    return layout_document.retokenize(**kwargs)


def remove_empty_blocks(layout_document: LayoutDocument) -> LayoutDocument:
    return layout_document.remove_empty_blocks()
