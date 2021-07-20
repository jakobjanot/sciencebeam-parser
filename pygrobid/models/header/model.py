import logging
from typing import Iterable, Tuple

from pygrobid.document.layout_document import LayoutBlock
from pygrobid.document.semantic_document import SemanticDocument
from pygrobid.models.data import DEFAULT_DOCUMENT_FEATURES_CONTEXT, DocumentFeaturesContext
from pygrobid.models.header.data import HeaderDataGenerator
from pygrobid.models.header.extract import HeaderSemanticExtractor
from pygrobid.models.model import Model


LOGGER = logging.getLogger(__name__)


class HeaderModel(Model):
    def get_data_generator(
        self,
        document_features_context: DocumentFeaturesContext = DEFAULT_DOCUMENT_FEATURES_CONTEXT
    ) -> HeaderDataGenerator:
        return HeaderDataGenerator(
            document_features_context=document_features_context
        )

    def get_semantic_extractor(self) -> HeaderSemanticExtractor:
        return HeaderSemanticExtractor()

    def update_semantic_document_with_entity_blocks(
        self,
        document: SemanticDocument,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]]
    ):
        semantic_content_iterable = (
            self.get_semantic_extractor()
            .iter_semantic_content_for_entity_blocks(entity_tokens)
        )
        front = document.front
        for semantic_content in semantic_content_iterable:
            front.add_content(semantic_content)
