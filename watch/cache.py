import json
import logging
import random

from base64 import urlsafe_b64encode
from datetime import datetime
from pathlib import Path


logger = logging.getLogger(__name__)


class Cache:
    def __init__(self, storage: Path, mapping: Path, expired: int = 3600) -> None:
        if not storage.exists():
            storage.mkdir(parents=True)
            logger.info("New directory created: %s", storage)

        self.storage = storage

        if mapping.suffix != ".json":
            raise ValueError(f"Mapping must be a JSON: {mapping}")

        self.mapping_file = mapping

        if expired < 0:
            raise ValueError(f"Cache must expire greater or equal 0 seconds")

        self.expired = expired

    def __enter__(self) -> "Cache":
        self.mapping = {}

        if self.mapping_file.exists():
            content = self.mapping_file.read_text()
            data = json.loads(content)
        else:
            data = []

        for item in data:
            url = item["url"]
            path = Path(item["path"])
            updated = datetime.fromisoformat(item["updated"])
            self.mapping[url] = (path, updated)

        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        data = []
        for key, value in self.mapping.items():
            url = key
            path, updated = value
            item = {
                "url": url,
                "path": str(path),
                "updated": updated.isoformat(),
            }
            data.append(item)

        content = json.dumps(data, indent=2)
        self.mapping_file.write_text(content)

    def set(self, url: str, content: str) -> None:
        item = self.mapping.pop(url, None)

        if item:
            path, updated = item
            path = Path(path)
            path.unlink()
            logger.warning("Removed cache item: %s", path.stem)

        name = get_file_name()
        path = self.storage / f"{name}.html"
        if path.is_file():
            raise Exception("Collision on file name generation")

        path.write_text(content)
        self.mapping[url] = (path, datetime.utcnow())
        logger.info("Added new cache item: %s", path.stem)

    def get(self, url: str) -> str | None:
        item = self.mapping.get(url)

        if not item:
            return

        path, updated = item
        delta = datetime.utcnow() - updated

        if delta.total_seconds() > self.expired:
            logger.info("Cache expired for item %s", path.stem)
            return

        content = Path(path).read_text()
        logger.debug("Retrieved cache item: %s", path.stem)
        return content


def get_file_name() -> str:
    """Return random file name"""
    # Choose multipe of 3 for number of bytes to avoid
    # padding when converting as urlsafe b64
    bytes = random.randbytes(6)
    name = urlsafe_b64encode(bytes)
    return name.decode()
