from datetime import datetime

from Code.db.models import History
from aiohttp.web import json_response
from sqlalchemy import and_
from sqlalchemy import select

from .base import BaseWithIDView
from .schema import StatisticSchema


class StatisticView(BaseWithIDView):
    URL_PATH = r'/node/{item_id:[\w-]+}/statistic'

    async def get(self):
        try:
            content = self.request.rel_url.query
            StatisticSchema().load(content)
        except Exception as e:
            return json_response({'code': 400, 'message': 'Validation failed'}, status=400)
        if self.item_id is None:
            return json_response({'code': 400, 'message': 'Validation failed'}, status=400)
        try:
            try:
                date_start = datetime.fromisoformat(self.from_iso_to_datetime_with_tz(content['dateStart'])[0])
            except Exception as e:
                date_start = None
            try:
                date_end = datetime.fromisoformat(self.from_iso_to_datetime_with_tz(content['dateEnd'])[0])
            except Exception as e:
                date_end = None
            if date_start and date_end:
                records = await self.pg.fetch(select(History).filter(
                    and_(History.item_id == self.item_id, History.date >= date_start, History.date < date_end)))
            elif date_start:
                records = await self.pg.fetch(select(History).filter(
                    and_(History.item_id == self.item_id, History.date >= date_start)))
            elif date_end:
                records = await self.pg.fetch(select(History).filter(
                    and_(History.item_id == self.item_id, History.date < date_end)))
            else:
                records = await self.pg.fetch(select(History).filter(
                    and_(History.item_id == self.item_id)))
            statistic_units = [self.from_record_to_statistic_unit(record) for record in records]
            return json_response(statistic_units, status=200)
        except Exception as e:
            return json_response({'code': 404, 'message': 'Item not found'}, status=404)
