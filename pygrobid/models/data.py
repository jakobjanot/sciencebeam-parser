import logging
import math
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, List, Optional

from lxml import etree

from pygrobid.document.layout_document import LayoutDocument, LayoutToken,  LayoutLine
from pygrobid.external.pdfalto.parser import parse_alto_root


LOGGER = logging.getLogger(__name__)


@dataclass
class LayoutModelData:
    data_line: str
    layout_line: Optional[LayoutLine] = None
    layout_token: Optional[LayoutToken] = None

    @property
    def label_token_text(self):
        return self.data_line.split(' ')[0]


class ModelDataGenerator(ABC):
    def iter_data_lines_for_xml_root(
        self,
        root: etree.ElementBase
    ) -> Iterable[str]:
        return self.iter_data_lines_for_layout_document(
            parse_alto_root(root)
        )

    @abstractmethod
    def iter_model_data_for_layout_document(
        self,
        layout_document: LayoutDocument
    ) -> Iterable[LayoutModelData]:
        pass

    def iter_data_lines_for_layout_document(  # pylint: disable=too-many-locals
        self,
        layout_document: LayoutDocument
    ) -> Iterable[str]:
        return (
            model_data.data_line
            for model_data in self.iter_model_data_for_layout_document(layout_document)
        )

    def iter_data_lines_for_layout_documents(  # pylint: disable=too-many-locals
        self,
        layout_documents: Iterable[LayoutDocument]
    ) -> Iterable[str]:
        for index, layout_document in enumerate(layout_documents):
            LOGGER.debug('generating data lines for document: index=%d', index)
            if index > 0:
                LOGGER.debug('adding document separator')
                yield from ['\n']
            yield from (
                model_data.data_line
                for model_data in self.iter_model_data_for_layout_document(layout_document)
            )


def feature_linear_scaling_int(pos: int, total: int, bin_count: int) -> int:
    """
    Given an integer value between 0 and total, discretized into nbBins following a linear scale
    Adapted from:
    grobid-core/src/main/java/org/grobid/core/features/FeatureFactory.java
    """
    if pos >= total:
        return bin_count
    if pos <= 0:
        return 0
    return math.floor((pos / total) * bin_count)


def get_token_font_status(previous_token: Optional[LayoutToken], current_token: LayoutToken):
    if not previous_token:
        return 'NEWFONT'
    return (
        'SAMEFONT' if current_token.font.font_family == previous_token.font.font_family
        else 'NEWFONT'
    )


def get_token_font_size_feature(
    previous_token: Optional[LayoutToken],
    current_token: LayoutToken
):
    if not previous_token:
        return 'HIGHERFONT'
    previous_font_size = previous_token.font.font_size
    current_font_size = current_token.font.font_size
    if not previous_font_size or not current_font_size:
        return 'HIGHERFONT'
    if previous_font_size < current_font_size:
        return 'HIGHERFONT'
    if previous_font_size > current_font_size:
        return 'LOWERFONT'
    return 'SAMEFONTSIZE'


def get_digit_feature(text: str) -> str:
    if text.isdigit():
        return 'ALLDIGIT'
    for c in text:
        if c.isdigit():
            return 'CONTAINSDIGITS'
    return 'NODIGIT'


def get_capitalisation_feature(text: str) -> str:
    if text and all(not c.islower() for c in text):
        return 'ALLCAP'
    if text and text[0].isupper():
        return 'INITCAP'
    return 'NOCAPS'


class PunctuationProfileValues:
    OPENBRACKET = 'OPENBRACKET'
    ENDBRACKET = 'ENDBRACKET'
    DOT = 'DOT'
    COMMA = 'COMMA'
    HYPHEN = 'HYPHEN'
    QUOTE = 'QUOTE'
    PUNCT = 'PUNCT'
    NOPUNCT = 'NOPUNCT'


PUNCTUATION_PROFILE_MAP = {
    '(': PunctuationProfileValues.OPENBRACKET,
    '[': PunctuationProfileValues.OPENBRACKET,
    ')': PunctuationProfileValues.ENDBRACKET,
    ']': PunctuationProfileValues.ENDBRACKET,
    '.': PunctuationProfileValues.DOT,
    ',': PunctuationProfileValues.COMMA,
    '-': PunctuationProfileValues.HYPHEN,
    '–': PunctuationProfileValues.HYPHEN,
    '"': PunctuationProfileValues.QUOTE,
    '\'': PunctuationProfileValues.QUOTE,
    '`': PunctuationProfileValues.QUOTE,
    '’': PunctuationProfileValues.QUOTE
}


IS_PUNCT_PATTERN = r"^[\,\:;\?\.]+$"


PUNCTUATION_PROFILE_CHARACTERS = (
    "(（[ •*,:;?.!/)）-−–‐«»„\"“”‘’'`$#@]*\u2666\u2665\u2663\u2660\u00A0"
)


def get_line_status(token_index: int, token_count: int) -> str:
    return (
        'LINEEND' if token_index == token_count - 1
        else (
            'LINESTART' if token_index == 0
            else 'LINEIN'
        )
    )


def get_block_status(
    line_index: int,
    line_count: int,
    line_status: str
) -> str:
    return (
        'BLOCKEND'
        if line_index == line_count - 1 and line_status == 'LINEEND'
        else (
            'BLOCKSTART'
            if line_index == 0 and line_status == 'LINESTART'
            else 'BLOCKIN'
        )
    )


class RelativeFontSizeFeature:
    def __init__(self, layout_tokens: Iterable[LayoutToken]):
        font_sizes = [
            layout_token.font.font_size
            for layout_token in layout_tokens
            if layout_token.font.font_size
        ]
        self.largest_font_size = max(font_sizes) if font_sizes else 0.0
        self.smallest_font_size = min(font_sizes) if font_sizes else 0.0
        self.mean_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 0.0

    def is_largest_font_size(self, layout_token: LayoutToken):
        return layout_token.font.font_size == self.largest_font_size

    def is_smallest_font_size(self, layout_token: LayoutToken):
        return layout_token.font.font_size == self.smallest_font_size

    def is_larger_than_average_font_size(self, layout_token: LayoutToken):
        if not layout_token.font.font_size:
            return False
        return layout_token.font.font_size > self.mean_font_size


class LineIndentationStatusFeature:
    def __init__(self):
        self._line_start_x = None
        self._is_new_line = True
        self._is_indented = False

    def on_new_line(self):
        self._is_new_line = True

    def get_is_indented_and_update(self, layout_token: LayoutToken):
        if self._is_new_line and layout_token.coordinates and layout_token.text:
            previous_line_start_x = self._line_start_x
            self._line_start_x = layout_token.coordinates.x
            character_width = layout_token.coordinates.width / len(layout_token.text)
            if previous_line_start_x is not None:
                if self._line_start_x - previous_line_start_x > character_width:
                    self._is_indented = True
                if previous_line_start_x - self._line_start_x > character_width:
                    self._is_indented = False
        self._is_new_line = False
        return self._is_indented


def get_punctuation_type_feature(text: str) -> str:
    result = PUNCTUATION_PROFILE_MAP.get(text)
    if not result and re.match(IS_PUNCT_PATTERN, text):
        return PunctuationProfileValues.PUNCT
    if not result:
        return PunctuationProfileValues.NOPUNCT
    return result


def get_punctuation_profile_feature(text: str) -> str:
    if not text:
        return ''
    return ''.join((
        c
        for c in text
        if not c.isspace() and c in PUNCTUATION_PROFILE_CHARACTERS
    ))


def get_punctuation_profile_length_for_punctuation_profile_feature(
    punctuation_profile: str
) -> str:
    if not punctuation_profile:
        return 'no'
    return str(min(10, len(punctuation_profile)))


def get_char_shape_feature(ch: str) -> str:
    if ch.isdigit():
        return 'd'
    if ch.isalpha():
        if ch.isupper():
            return 'X'
        return 'x'
    return ch


def get_word_shape_feature(text: str) -> str:
    shape = [
        get_char_shape_feature(ch)
        for ch in text
    ]
    prefix = shape[:1]
    middle = shape[1:-2]
    suffix = shape[1:][-2:]
    middle_without_consequitive_duplicates = middle[:1].copy()
    for ch in middle[1:]:
        if ch != middle_without_consequitive_duplicates[-1]:
            middle_without_consequitive_duplicates.append(ch)
    return ''.join(prefix + middle_without_consequitive_duplicates + suffix)


def get_str_bool_feature_value(value: Optional[bool]) -> str:
    return '1' if value else '0'


class CommonLayoutTokenFeatures(ABC):  # pylint: disable=too-many-public-methods
    def __init__(self, layout_token: LayoutToken) -> None:
        self.layout_token = layout_token
        self.token_text = layout_token.text or ''

    def get_lower_token_text(self) -> str:
        return self.token_text.lower()

    def get_prefix(self, n: int) -> str:
        return self.token_text[:n]

    def get_suffix(self, n: int) -> str:
        return self.token_text[-n:]

    def get_str_is_bold(self) -> str:
        return get_str_bool_feature_value(self.layout_token.font.is_bold)

    def get_str_is_italic(self) -> str:
        return get_str_bool_feature_value(self.layout_token.font.is_italics)

    def get_str_is_single_char(self) -> str:
        return get_str_bool_feature_value(len(self.token_text) == 1)

    def get_digit_status(self) -> str:
        return get_digit_feature(self.token_text)

    def get_capitalisation_status(self) -> str:
        if self.get_digit_status() == 'ALLDIGIT':
            return 'NOCAPS'
        return get_capitalisation_feature(self.token_text)

    def get_punctuation_type_feature(self) -> str:
        return get_punctuation_type_feature(self.token_text)

    def get_word_shape_feature(self) -> str:
        return get_word_shape_feature(self.token_text)

    def get_dummy_str_is_proper_name(self) -> str:
        return '0'

    def get_dummy_str_is_common_name(self) -> str:
        return '0'

    def get_dummy_str_is_first_name(self) -> str:
        return '0'

    def get_dummy_str_is_last_name(self) -> str:
        return '0'

    def get_dummy_str_is_known_title(self) -> str:
        return '0'

    def get_dummy_str_is_known_suffix(self) -> str:
        return '0'

    def get_dummy_str_is_location_name(self) -> str:
        return '0'

    def get_dummy_str_is_country_name(self) -> str:
        return '0'

    def get_dummy_str_is_year(self) -> str:
        return '0'

    def get_dummy_str_is_month(self) -> str:
        return '0'

    def get_dummy_str_is_email(self) -> str:
        return '0'

    def get_dummy_str_is_http(self) -> str:
        return '0'

    def get_dummy_str_is_known_collaboration(self) -> str:
        return '0'

    def get_dummy_str_is_known_journal_title(self) -> str:
        return '0'

    def get_dummy_str_is_known_conference_title(self) -> str:
        return '0'

    def get_dummy_str_is_known_publisher(self) -> str:
        return '0'

    def get_dummy_str_is_known_identifier(self) -> str:
        return '0'

    def get_dummy_label(self) -> str:
        return '0'


_LINESCALE = 10


class ContextAwareLayoutTokenFeatures(CommonLayoutTokenFeatures):
    def __init__(
        self,
        layout_token: LayoutToken,
        layout_line: LayoutLine,
        previous_layout_token: Optional[LayoutToken],
        token_index: int,
        token_count: int,
        document_token_index: int,
        document_token_count: int,
        line_index: int,
        line_count: int,
        concatenated_line_tokens_text: str,
        max_concatenated_line_tokens_length: int,
        line_token_position: int,
        relative_font_size_feature: RelativeFontSizeFeature,
        line_indentation_status_feature: LineIndentationStatusFeature
    ) -> None:
        super().__init__(layout_token)
        self.layout_line = layout_line
        self.previous_layout_token = previous_layout_token
        self.token_index = token_index
        self.token_count = token_count
        self.document_token_index = document_token_index
        self.document_token_count = document_token_count
        self.line_index = line_index
        self.line_count = line_count
        self.concatenated_line_tokens_text = concatenated_line_tokens_text
        self.max_concatenated_line_tokens_length = max_concatenated_line_tokens_length
        self.line_token_position = line_token_position
        self.relative_font_size_feature = relative_font_size_feature
        self.line_indentation_status_feature = line_indentation_status_feature

    def get_layout_model_data(self, features: List[str]) -> LayoutModelData:
        return LayoutModelData(
            layout_line=self.layout_line,
            layout_token=self.layout_token,
            data_line=' '.join(features)
        )

    def get_line_status(self) -> str:
        return get_line_status(token_index=self.token_index, token_count=self.token_count)

    def get_block_status(self) -> str:
        return get_block_status(
            line_index=self.line_index,
            line_count=self.line_count,
            line_status=self.get_line_status()
        )

    def get_dummy_page_status(self) -> str:
        return 'PAGEIN'

    def get_is_indented_and_update(self) -> bool:
        return self.line_indentation_status_feature.get_is_indented_and_update(
            self.layout_token
        )

    def get_alignment_status(self) -> str:
        indented = self.get_is_indented_and_update()
        return 'LINEINDENT' if indented else 'ALIGNEDLEFT'

    def get_token_font_status(self) -> str:
        return get_token_font_status(self.previous_layout_token, self.layout_token)

    def get_token_font_size_feature(self) -> str:
        return get_token_font_size_feature(self.previous_layout_token, self.layout_token)

    def get_str_is_largest_font_size(self) -> str:
        return get_str_bool_feature_value(
            self.relative_font_size_feature.is_largest_font_size(
                self.layout_token
            )
        )

    def get_str_is_smallest_font_size(self) -> str:
        return get_str_bool_feature_value(
            self.relative_font_size_feature.is_smallest_font_size(
                self.layout_token
            )
        )

    def get_str_is_larger_than_average_font_size(self) -> str:
        return get_str_bool_feature_value(
            self.relative_font_size_feature.is_larger_than_average_font_size(
                self.layout_token
            )
        )

    def get_line_punctuation_profile(self) -> str:
        return get_punctuation_profile_feature(self.concatenated_line_tokens_text)

    def get_line_punctuation_profile_length_feature(self) -> str:
        return get_punctuation_profile_length_for_punctuation_profile_feature(
            self.get_line_punctuation_profile()
        )

    def get_str_line_token_relative_position(self) -> str:
        return str(feature_linear_scaling_int(
            self.line_token_position,
            len(self.concatenated_line_tokens_text),
            _LINESCALE
        ))

    def get_str_line_relative_length(self) -> str:
        return str(feature_linear_scaling_int(
            len(self.concatenated_line_tokens_text),
            self.max_concatenated_line_tokens_length,
            _LINESCALE
        ))

    def get_str_sentence_token_relative_position(self) -> str:
        return str(feature_linear_scaling_int(
            # the document is currently the sentence view
            self.document_token_index,
            self.document_token_count,
            12
        ))

    def get_dummy_str_relative_document_position(self):
        # position within whole document
        return '0'

    def get_dummy_str_relative_page_position(self):
        return '0'

    def get_dummy_str_is_bitmap_around(self) -> str:
        return '0'

    def get_dummy_str_is_vector_around(self) -> str:
        return '0'


class ContextAwareLayoutTokenModelDataGenerator(ModelDataGenerator):
    @abstractmethod
    def iter_model_data_for_context_layout_token_features(
        self,
        token_features: ContextAwareLayoutTokenFeatures
    ) -> Iterable[LayoutModelData]:
        pass

    def iter_model_data_for_layout_document(  # pylint: disable=too-many-locals
        self,
        layout_document: LayoutDocument
    ) -> Iterable[LayoutModelData]:
        relative_font_size_feature = RelativeFontSizeFeature(
            layout_document.iter_all_tokens()
        )
        line_indentation_status_feature = LineIndentationStatusFeature()
        previous_layout_token: Optional[LayoutToken] = None
        concatenated_line_tokens_length_by_line_id = {
            id(line): sum((len(token.text) for token in line.tokens))
            for block in layout_document.iter_all_blocks()
            for line in block.lines
        }
        max_concatenated_line_tokens_length = max(
            concatenated_line_tokens_length_by_line_id.values()
        )
        document_token_count = sum((
            1
            for _ in layout_document.iter_all_tokens()
        ))
        document_token_index = 0
        for block in layout_document.iter_all_blocks():
            block_lines = block.lines
            line_count = len(block_lines)
            for line_index, line in enumerate(block_lines):
                line_indentation_status_feature.on_new_line()
                line_tokens = line.tokens
                token_count = len(line_tokens)
                concatenated_line_tokens_text = ''.join([
                    token.text for token in line_tokens
                ])
                line_token_position = 0
                for token_index, token in enumerate(line_tokens):
                    yield from self.iter_model_data_for_context_layout_token_features(
                        ContextAwareLayoutTokenFeatures(
                            token,
                            layout_line=line,
                            previous_layout_token=previous_layout_token,
                            token_index=token_index,
                            token_count=token_count,
                            document_token_index=document_token_index,
                            document_token_count=document_token_count,
                            line_index=line_index,
                            line_count=line_count,
                            concatenated_line_tokens_text=concatenated_line_tokens_text,
                            max_concatenated_line_tokens_length=max_concatenated_line_tokens_length,
                            line_token_position=line_token_position,
                            relative_font_size_feature=relative_font_size_feature,
                            line_indentation_status_feature=line_indentation_status_feature
                        )
                    )
                    previous_layout_token = token
                    line_token_position += len(token.text)
                    document_token_index += 1
