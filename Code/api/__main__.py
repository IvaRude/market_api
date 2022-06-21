import logging
import os
import sys

from aiohttp.web import run_app

from .app import create_app

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))

API_ADDRESS = '0.0.0.0'
API_PORT = 80


def main():
    logging.basicConfig(filename='app_log.txt', level=logging.INFO)
    fh = logging.FileHandler('app_log.txt')
    log = logging.getLogger(__name__)
    log.addHandler(fh)
    log.setLevel(logging.INFO)
    app = create_app()
    log.info('App created')
    run_app(app, host=API_ADDRESS, port=API_PORT)


if __name__ == '__main__':
    main()
