import logging
import os
from datetime import datetime
from pathlib import Path

from aiohttp.web_app import Application
from asyncpgsa import PG
from configargparse import Namespace
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DATABASE_HOST')

CENSORED = '***'
DEFAULT_PG_URL = 'postgresql://admin:admin@0.0.0.0:5432/apiDB'
# DEFAULT_PG_URL = 'postgresql://admin:admin@0.0.0.0:54321/testDB3'

if DB_HOST:
    # DEFAULT_PG_URL = 'postgresql://admin:admin@' + DB_HOST + ':5432/testDB2'
    DEFAULT_PG_URL = 'postgresql://admin:admin@' + DB_HOST + ':5432/apiDB'

MAX_QUERY_ARGS = 32767
MAX_INTEGER = 2147483647

PROJECT_PATH = Path(__file__).parent.parent.resolve()
logging.basicConfig(filename='test_log.txt')
log = logging.getLogger(__name__)


async def setup_pg(app: Application, args: Namespace) -> PG:
    logging.basicConfig(filename='app_log.txt', level=logging.INFO)
    fh = logging.FileHandler('app_log.txt')
    log = logging.getLogger(__name__)
    log.addHandler(fh)
    log.setLevel(logging.INFO)
    log.info('Connecting to database at ' + str(datetime.now().strftime('%H:%M:%S')))
    app['pg'] = PG()
    await app['pg'].init(
        DEFAULT_PG_URL,
    )
    await app['pg'].fetchval('SELECT 1')
    log.info('Connected to database')

    try:
        yield
    finally:
        log.info('Disconnecting from database')
        await app['pg'].pool.close()
        log.info('Disconnected from database')
