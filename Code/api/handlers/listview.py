from Code.db.models import History, Items
from Code.utils.pg import MAX_QUERY_ARGS
from aiohttp.web import json_response
from sqlalchemy import select

from .base import BaseView


class ListView(BaseView):
    URL_PATH = '/'
    MAX_ITEMS_PER_INSERT = MAX_QUERY_ARGS // 8

    async def get(self):
        body = {}
        all_query = select(Items)
        all_query.parameters = []
        res = await self.pg.fetch(all_query)
        print('ITEMS: ', res)
        res = self.from_records_to_list(res)
        for r in res:
            r['date'] = str(r['date'])
            r['item_id'] = str(r['item_id'])
        body['ITEMS'] = res
        all_query = select(History)
        all_query.parameters = []
        res = await self.pg.fetch(all_query)
        print('HISTORY: ', res)
        res = self.from_records_to_list(res)
        for r in res:
            r['date'] = str(r['date'])
            r['item_id'] = str(r['item_id'])
        body['HISTORY'] = res
        return json_response(body, status=200)
