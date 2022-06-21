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

    async def get(self):
        body = {'body': 'Everything is OK'}
        print(body)
        self.logger.info('GET request for / at ' + str(datetime.now().strftime('%H:%M:%S')))

        # query = delete(History).filter(History.item_id.in_(select(Items.item_id)))
        date = '2022-02-01T12:00:00.010-07:10'
        res = self.from_iso_to_datetime_with_tz(date)
        final_date = self.from_datetime_with_tz_to_iso(res)
        print(date == final_date)
        # date = isoparse(date)
        # date = date.replace(tzinfo=None)
        # date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        date = '2022-02-01T12:00:00.010+01:00'
        date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        tz = date.tzinfo
        str_tz = str(tz)
        date += timedelta(days=-1)
        # date = datetime.timestamp(date)
        query = insert(Items).values(item_id=str(uuid.uuid4()), type='OFFER',
                                     date=bindparam('date', datetime.utcnow().replace(tzinfo=timezone.utc),
                                                    type_=TIMESTAMP(timezone=True)), name='asdasd')
        query = insert(Items).values(item_id=str(uuid.uuid4()), type='OFFER', date=date, name='asdasd')
        query.parameters = []
        # await self.pg.execute(query)
        # query = delete(History)
        query = delete(Items)
        query.parameters = []
        # await self.pg.execute(query)
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
