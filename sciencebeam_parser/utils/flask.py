import logging
from typing import NamedTuple, Optional, Sequence

from flask import request
from werkzeug.exceptions import BadRequest

from sciencebeam_parser.utils.media_types import (
    get_first_matching_media_type,
    guess_extension_for_media_type,
    guess_media_type_for_filename
)


LOGGER = logging.getLogger(__name__)


DEFAULT_FILENAME = 'file'


class SourceDataWrapper(NamedTuple):
    data: bytes
    media_type: str
    filename: Optional[str] = None


def get_optional_post_data_wrapper() -> SourceDataWrapper:
    if not request.files:
        return SourceDataWrapper(
            data=request.data,
            media_type=request.mimetype,
            filename=request.args.get('filename')
        )
    supported_file_keys = ['file', 'input']
    for name in supported_file_keys:
        if name not in request.files:
            continue
        uploaded_file = request.files[name]
        data = uploaded_file.stream.read()
        return SourceDataWrapper(
            data=data,
            media_type=uploaded_file.mimetype,
            filename=uploaded_file.filename
        )
    raise BadRequest(
        f'missing file named one pf "{supported_file_keys}", found: {request.files.keys()}'
    )


def get_data_wrapper_with_improved_media_type_or_filename(
    data_wrapper: SourceDataWrapper
) -> SourceDataWrapper:
    if not data_wrapper.filename:
        return data_wrapper._replace(filename='%s%s' % (
            DEFAULT_FILENAME, guess_extension_for_media_type(data_wrapper.media_type) or ''
        ))
    if data_wrapper.media_type == 'application/octet-stream':
        media_type = guess_media_type_for_filename(data_wrapper.filename)
        if media_type:
            return data_wrapper._replace(media_type=media_type)
    return data_wrapper


def get_required_post_data_wrapper() -> SourceDataWrapper:
    data_wrapper = get_optional_post_data_wrapper()
    if not data_wrapper.data:
        raise BadRequest('no contents')
    return data_wrapper


def get_required_post_data() -> bytes:
    return get_required_post_data_wrapper().data


def get_request_accept_media_types() -> Sequence[str]:
    accept_media_types = list(request.accept_mimetypes.values())
    LOGGER.info('accept_media_types: %s', accept_media_types)
    return accept_media_types


def assert_and_get_first_matching_media_type(
    accept_media_types: Sequence[str],
    available_media_types: Sequence[str]
) -> str:
    media_type = get_first_matching_media_type(
        accept_media_types,
        available_media_types
    )
    if not media_type:
        raise BadRequest(
            f'unsupported accept media types: {accept_media_types},'
            f' supported types are: {available_media_types}'
        )
    LOGGER.info('resolved media type: %r', media_type)
    return media_type


def assert_and_get_first_accept_matching_media_type(
    available_media_types: Sequence[str]
) -> str:
    return assert_and_get_first_matching_media_type(
        get_request_accept_media_types(),
        available_media_types
    )
