from Code.db.models import History, Items
from aiohttp.web import json_response
from sqlalchemy import delete

from .base import BaseView


class DeleteAllView(BaseView):
    '''
    Удаляет все строки из таблиц Items и History.
    '''
    URL_PATH = '/deleteall'

    async def get(self):
        try:
            async with self.pg.transaction() as conn:
                query = delete(History)
                query.parameters = []
                await conn.execute(query)
                query = delete(Items)
                query.parameters = []
                await conn.execute(query)
            return json_response({'code': 200, 'message': 'Deleted Successfully'})
        except Exception as e:
            return json_response({'code': 404, 'message': 'Deletion aborted'}, status=404)