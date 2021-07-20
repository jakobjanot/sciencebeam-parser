import logging
import re
from typing import Iterable, List, Optional

from pygrobid.document.layout_document import (
    LayoutBlock,
    LayoutDocument,
    LayoutLine,
    LayoutToken
)
from pygrobid.models.data import (
    ContextAwareLayoutTokenFeatures,
    DEFAULT_DOCUMENT_FEATURES_CONTEXT,
    DocumentFeaturesContext,
    ModelDataGenerator,
    LayoutModelData,
    feature_linear_scaling_int,
    _LINESCALE
)


LOGGER = logging.getLogger(__name__)


NBSP = '\u00A0'


def format_feature_text(text: str) -> str:
    return re.sub(" |\t", NBSP, text.strip())


NBBINS_POSITION = 12

EMPTY_LAYOUT_TOKEN = LayoutToken('')
EMPTY_LAYOUT_LINE = LayoutLine([])


def get_block_status(line_index: int, line_count: int) -> str:
    return (
        'BLOCKSTART' if line_index == 0
        else (
            'BLOCKEND'
            if line_index == line_count - 1
            else 'BLOCKIN'
        )
    )


def get_page_status(block_index: int, block_count: int, block_status: str) -> str:
    return (
        'PAGESTART' if block_index == 0 and block_status == 'BLOCKSTART'
        else (
            'PAGEEND'
            if block_index == block_count - 1 and block_status == 'BLOCKEND'
            else 'PAGEIN'
        )
    )


class SegmentationLineFeatures(ContextAwareLayoutTokenFeatures):
    def __init__(self, layout_token: LayoutToken = EMPTY_LAYOUT_TOKEN):
        super().__init__(layout_token, layout_line=EMPTY_LAYOUT_LINE)
        self.line_text = ''
        self.second_token_text = ''
        self.page_blocks: List[LayoutBlock] = []
        self.page_block_index: int = 0
        self.block_lines: List[LayoutLine] = []
        self.block_line_index: int = 0
        self.previous_layout_token: Optional[LayoutToken] = None
        self.max_block_line_text_length = 0
        self.document_token_count = 0
        self.document_token_index = 0

    def get_block_status(self) -> str:
        return get_block_status(self.block_line_index, len(self.block_lines))

    def get_page_status(self) -> str:
        return get_page_status(
            self.page_block_index, len(self.page_blocks), self.get_block_status()
        )

    def get_formatted_whole_line_feature(self) -> str:
        return format_feature_text(self.line_text)

    def get_dummy_str_is_repetitive_pattern(self) -> str:
        return '0'

    def get_dummy_str_is_first_repetitive_pattern(self) -> str:
        return '0'

    def get_dummy_str_is_main_area(self) -> str:
        # whether the block's bounding box intersects with the page bounding box
        return '1'

    def get_str_block_relative_line_length_feature(self) -> str:
        return str(feature_linear_scaling_int(
            len(self.line_text),
            self.max_block_line_text_length,
            _LINESCALE
        ))

    def get_str_relative_document_position(self) -> str:
        return str(feature_linear_scaling_int(
            self.document_token_index,
            self.document_token_count,
            NBBINS_POSITION
        ))


class SegmentationLineFeaturesProvider:
    def iter_line_features(  # pylint: disable=too-many-locals
        self,
        layout_document: LayoutDocument
    ) -> Iterable[SegmentationLineFeatures]:
        segmentation_line_features = SegmentationLineFeatures()
        previous_token: Optional[LayoutToken] = None
        segmentation_line_features.document_token_count = sum(
            len(line.tokens)
            for block in layout_document.iter_all_blocks()
            for line in block.lines
        )
        document_token_index = 0
        for page in layout_document.pages:
            blocks = page.blocks
            segmentation_line_features.page_blocks = blocks
            for block_index, block in enumerate(blocks):
                segmentation_line_features.page_block_index = block_index
                block_lines = block.lines
                segmentation_line_features.block_lines = block_lines
                block_line_texts = [line.text for line in block_lines]
                max_block_line_text_length = max(len(text) for text in block_line_texts)
                for line_index, line in enumerate(block_lines):
                    segmentation_line_features.document_token_index = document_token_index
                    document_token_index += len(line.tokens)
                    segmentation_line_features.layout_line = line
                    segmentation_line_features.block_line_index = line_index
                    segmentation_line_features.max_block_line_text_length = (
                        max_block_line_text_length
                    )
                    line_tokens = line.tokens
                    line_text = block_line_texts[line_index]
                    retokenized_token_texts = re.split(r" |\t|\f|\u00A0", line_text)
                    if not retokenized_token_texts:
                        continue
                    token = line_tokens[0]
                    segmentation_line_features.layout_token = token
                    segmentation_line_features.line_text = line_text
                    segmentation_line_features.concatenated_line_tokens_text = line_text
                    segmentation_line_features.token_text = retokenized_token_texts[0].strip()
                    segmentation_line_features.second_token_text = (
                        retokenized_token_texts[1] if len(retokenized_token_texts) >= 2 else ''
                    )
                    segmentation_line_features.previous_layout_token = previous_token
                    yield segmentation_line_features
                    previous_token = token


class SegmentationDataGenerator(ModelDataGenerator):
    def __init__(
        self,
        document_features_context: DocumentFeaturesContext = DEFAULT_DOCUMENT_FEATURES_CONTEXT
    ):
        self.document_features_context = document_features_context

    def iter_model_data_for_layout_document(
        self,
        layout_document: LayoutDocument,
    ) -> Iterable[LayoutModelData]:
        features_provider = SegmentationLineFeaturesProvider()
        for features in features_provider.iter_line_features(layout_document):
            line_features: List[str] = [
                features.token_text,
                features.second_token_text or features.token_text,
                features.get_lower_token_text(),
                features.get_prefix(1),
                features.get_prefix(2),
                features.get_prefix(3),
                features.get_prefix(4),
                features.get_block_status(),
                features.get_page_status(),
                features.get_token_font_status(),
                features.get_token_font_size_feature(),
                features.get_str_is_bold(),
                features.get_str_is_italic(),
                features.get_capitalisation_status_using_allcap(),
                features.get_digit_status_using_containsdigits(),
                features.get_str_is_single_char(),
                features.get_dummy_str_is_proper_name(),
                features.get_dummy_str_is_common_name(),
                features.get_dummy_str_is_first_name(),
                features.get_dummy_str_is_year(),
                features.get_dummy_str_is_month(),
                features.get_dummy_str_is_email(),
                features.get_dummy_str_is_http(),
                features.get_str_relative_document_position(),
                features.get_dummy_str_relative_page_position(),
                features.get_line_punctuation_profile(),
                features.get_line_punctuation_profile_length_feature(),
                features.get_str_block_relative_line_length_feature(),
                features.get_dummy_str_is_bitmap_around(),
                features.get_dummy_str_is_vector_around(),
                features.get_dummy_str_is_repetitive_pattern(),
                features.get_dummy_str_is_first_repetitive_pattern(),
                features.get_dummy_str_is_main_area(),
                features.get_formatted_whole_line_feature()
            ]

            if len(line_features) != 34:
                raise AssertionError(
                    'expected features to have 34 features, but was=%d (features=%s)' % (
                        len(line_features), line_features
                    )
                )
            yield LayoutModelData(
                layout_line=features.layout_line,
                data_line=' '.join(line_features)
            )
