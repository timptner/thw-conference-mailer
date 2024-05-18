#! /usr/bin/env python3

import logging
import tomllib

from pathlib import Path
from urllib.parse import urljoin

from watch.cache import Cache
from watch.parse import parse
from watch.scrape import get_content

BASE_DIR = Path(__file__).parent.parent

logger = logging.getLogger(__name__)


def main() -> None:
    config = get_config()

    storage = BASE_DIR / config["cache"]["directory"]
    mapping = BASE_DIR / config["cache"]["mapping"]

    courses = []
    with Cache(storage, mapping) as cache:
        base_url = config["target"]["base_url"]
        next_page = config["target"]["entry_point"]
        while next_page:
            url = urljoin(base_url, next_page)
            content = get_content(cache, url)
            if not content:
                break
            data = parse(content)
            next_page = data["next_page"]
            courses += data["courses"]

    print(courses)


def get_config() -> dict:
    config_file = BASE_DIR / "config.toml"
    with open(config_file, "rb") as file:
        config = tomllib.load(file)
    return config


if __name__ == "__main__":
    main()
