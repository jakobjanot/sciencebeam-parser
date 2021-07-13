from typing import Iterable

from pygrobid.models.data import (
    ContextAwareLayoutTokenFeatures,
    ContextAwareLayoutTokenModelDataGenerator,
    LayoutModelData
)


class AffiliationAddressDataGenerator(ContextAwareLayoutTokenModelDataGenerator):
    def iter_model_data_for_context_layout_token_features(
        self,
        token_features: ContextAwareLayoutTokenFeatures
    ) -> Iterable[LayoutModelData]:
        yield token_features.get_layout_model_data([
            token_features.token_text,
            token_features.get_lower_token_text(),
            token_features.get_prefix(1),
            token_features.get_prefix(2),
            token_features.get_prefix(3),
            token_features.get_prefix(4),
            token_features.get_suffix(1),
            token_features.get_suffix(2),
            token_features.get_suffix(3),
            token_features.get_suffix(4),
            token_features.get_line_status_with_lineend_for_single_token(),
            token_features.get_capitalisation_status(),
            token_features.get_digit_status(),
            token_features.get_str_is_single_char(),
            token_features.get_dummy_str_is_proper_name(),
            token_features.get_dummy_str_is_common_name(),
            token_features.get_dummy_str_is_first_name(),
            token_features.get_dummy_str_is_location_name(),
            token_features.get_dummy_str_is_country_name(),
            token_features.get_punctuation_type_feature(),
            token_features.get_word_shape_feature(),
            token_features.get_dummy_label()
        ])
