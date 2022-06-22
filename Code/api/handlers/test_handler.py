import uuid
from datetime import datetime, timezone, timedelta

from Code.db.models import History, Items
from Code.utils.pg import MAX_QUERY_ARGS
from aiohttp.web import json_response
from sqlalchemy import select, insert, delete, bindparam, union
from sqlalchemy.types import TIMESTAMP

from .base import BaseView




class TestView(BaseView):
    URL_PATH = '/'
    MAX_ITEMS_PER_INSERT = MAX_QUERY_ARGS // 8

    async def delete_all(self):
        query = delete(History)
        query.parameters = []
        await self.pg.execute(query)
        query = delete(Items)
        query.parameters = []
        await self.pg.execute(query)

    async def get(self):
        body = {'body': 'Everything is OK'}
        print(body)

        # query = delete(History).filter(History.item_id.in_(select(Items.item_id)))
        # date = isoparse(date)
        # date = date.replace(tzinfo=None)
        # date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        # date = datetime.timestamp(date)
        # await self.delete_all()
        all_query = union(*[select(Items), select(Items), select(Items)])
        all_query.parameters = []
        res = await self.pg.fetch(all_query)
        print('ITEMS: ', res)
        res = self.from_records_to_list(res)
        for r in res:
            r['date'] = str(r['date'])

            # r.pop('date')
            r['item_id'] = str(r['item_id'])
        body['ITEMS'] = res
        all_query = select(History)
        all_query.parameters = []
        res = await self.pg.fetch(all_query)
        print('HISTORY: ', res)
        res = self.from_records_to_list(res)
        for r in res:
            r['date'] = str(r['date'])
            # r.pop('date')
            r['item_id'] = str(r['item_id'])

        body['HISTORY'] = res

        return json_response(body)
