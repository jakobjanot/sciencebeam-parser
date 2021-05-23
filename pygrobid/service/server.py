import argparse
import logging
import os
from logging.config import dictConfig
from pathlib import Path

import yaml
from flask import Flask

from pygrobid.service.blueprints.index import IndexBlueprint
from pygrobid.service.blueprints.api import ApiBlueprint


LOGGER = logging.getLogger(__name__)


def create_app(config: dict):
    app = Flask(__name__)

    index = IndexBlueprint()
    app.register_blueprint(index, url_prefix='/')

    api = ApiBlueprint(config)
    app.register_blueprint(api, url_prefix='/api')

    return app


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--host', required=False,
        help='Host to bind server to.'
    )
    parser.add_argument(
        '--port', type=int, default=8080,
        help='The port to listen to.'
    )
    parsed_args = parser.parse_args(argv)
    return parsed_args


def main(argv=None):
    args = parse_args(argv)
    config = yaml.safe_load(Path('config.yml').read_text())
    logging_config = config.get('logging')
    if logging_config:
        for handler_config in logging_config.get('handlers', {}).values():
            filename = handler_config.get('filename')
            if not filename:
                continue
            dirname = os.path.dirname(filename)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
        try:
            dictConfig(logging_config)
        except ValueError:
            LOGGER.info('logging_config: %r', logging_config)
            raise
    LOGGER.info('config: %s', config)
    app = create_app(config)
    app.run(port=args.port, host=args.host, threaded=True)


if __name__ == "__main__":
    logging.basicConfig(level='INFO')
    main()
