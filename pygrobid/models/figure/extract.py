import logging
from typing import Iterable, Mapping, Optional, Tuple

from pygrobid.document.semantic_document import (
    SemanticCaption,
    SemanticContentFactoryProtocol,
    SemanticContentWrapper,
    SemanticFigure,
    SemanticLabel
)
from pygrobid.document.layout_document import LayoutBlock
from pygrobid.models.extract import SimpleModelSemanticExtractor


LOGGER = logging.getLogger(__name__)


SIMPLE_SEMANTIC_CONTENT_CLASS_BY_TAG: Mapping[str, SemanticContentFactoryProtocol] = {
    '<label>': SemanticLabel,
    '<figDesc>': SemanticCaption
}


class FigureSemanticExtractor(SimpleModelSemanticExtractor):
    def __init__(self):
        super().__init__(semantic_content_class_by_tag=SIMPLE_SEMANTIC_CONTENT_CLASS_BY_TAG)

    def iter_semantic_content_for_entity_blocks(  # pylint: disable=arguments-differ
        self,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]],
        **kwargs
    ) -> Iterable[SemanticContentWrapper]:
        entity_tokens = list(entity_tokens)
        LOGGER.debug('entity_tokens: %s', entity_tokens)
        figure: Optional[SemanticFigure] = None
        for name, layout_block in entity_tokens:
            if not figure:
                figure = SemanticFigure()
            semantic_content = self.get_semantic_content_for_entity_name(
                name, layout_block=layout_block
            )
            figure.add_content(semantic_content)
        if figure:
            yield figure
