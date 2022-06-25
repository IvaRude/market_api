from functools import partial

from aiohttp.web_app import Application
from aiohttp_apispec import setup_aiohttp_apispec

from Code.utils.pg import setup_pg
from .handlers import HANDLERS

MEGABYTE = 1024 ** 2
MAX_REQUEST_SIZE = 70 * MEGABYTE

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "Code")))

def create_app():
    '''
    Создает приложение
    '''
    app = Application(client_max_size=MAX_REQUEST_SIZE)
    app.cleanup_ctx.append(partial(setup_pg, args=None))

    # Добавляет документацию по адресу /api/doc
    setup_aiohttp_apispec(app=app, title="My Documentation", version="v1", swagger_path='/api/doc')

    for handler in HANDLERS:
        app.router.add_route('*', handler.URL_PATH, handler)
    return app
