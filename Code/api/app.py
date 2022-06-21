from functools import partial

from Code.utils.pg import setup_pg
from aiohttp.web_app import Application
from aiohttp_apispec import setup_aiohttp_apispec

from .handlers import HANDLERS

MEGABYTE = 1024 ** 2
MAX_REQUEST_SIZE = 70 * MEGABYTE


def create_app():
    app = Application(client_max_size=MAX_REQUEST_SIZE)
    app.cleanup_ctx.append(partial(setup_pg, args=None))
    setup_aiohttp_apispec(app=app, title="My Documentation", version="v1")
    for handler in HANDLERS:
        app.router.add_route('*', handler.URL_PATH, handler)
    return app
