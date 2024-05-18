import functools
import logging
import requests
import time

from pathlib import Path
from requests.exceptions import ConnectionError

from watch import __version__ as VERSION, __name__ as NAME
from watch.cache import Cache

logger = logging.getLogger(__name__)


def get_content(cache: Cache, url: str) -> str | None:
    content = cache.get(url)
    if content:
        return content

    content = get_page(url)
    if content:
        cache.set(url, content)
        return content


class Throttle:
    def __init__(self, func, seconds: int = 300) -> None:
        functools.update_wrapper(self, func)
        self.func = func
        self.time = None
        self.seconds = seconds

    def __call__(self, *args, **kwargs):
        if self.time:
            delta = time.time() - self.time
            if delta < self.seconds:
                time_to_wait = self.seconds - max(delta, 0)
                logging.warning("Waiting another %d seconds (throttle)", time_to_wait)
                time.sleep(time_to_wait)

        self.time = time.time()
        return self.func(*args, **kwargs)


HEADERS = {
    "Accept": "text/html",
    "User-Agent": f"{NAME}/{VERSION}",
}


@Throttle
def get_page(url: str, headers: dict = HEADERS) -> str | None:
    try:
        response = requests.get(url=url, headers=headers)
    except ConnectionError:
        logger.error("Connection failed")
        return

    logger.info("GET: %s", url)

    if response.status_code != 200:
        logger.error("Failed to retrieve page (code: %d)", response.status_code)
        return

    return response.text
