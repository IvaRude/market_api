from datetime import datetime

from Code.api.schema import StatisticSchema
from Code.db.models import History
from aiohttp.web import json_response
from aiohttp_apispec import docs, request_schema
from sqlalchemy import and_
from sqlalchemy import select

from .base import BaseWithIDView


class StatisticView(BaseWithIDView):
    URL_PATH = r'/node/{item_id:[\w-]+}/statistic'

    @docs(
        summary='Получить информацию обо всех обновлениях элемента с id == item_id в полуинтервале [dateStart, dateEnd).')
    @request_schema(StatisticSchema())
    async def get(self):
        # Валидация входных данных
        try:
            content = self.request.rel_url.query
            if 'dateStart' in content:
                self.validate_date(content['dateStart'])
            if 'dateEnd' in content:
                self.validate_date(content['dateEnd'])
            StatisticSchema().load(content)
            # Проверка, что dateStart <= dateEnd
            try:
                date_start = datetime.fromisoformat(self.from_iso_to_datetime_with_tz(content['dateStart'])[0])
            except Exception as e:
                date_start = None
            try:
                date_end = datetime.fromisoformat(self.from_iso_to_datetime_with_tz(content['dateEnd'])[0])
            except Exception as e:
                date_end = None
            if date_start and date_end and date_end < date_start:
                return json_response({'code': 400, 'message': 'Validation failed'}, status=400)
        except Exception as e:
            return json_response({'code': 400, 'message': 'Validation failed'}, status=400)
        if self.item_id is None:
            return json_response({'code': 400, 'message': 'Validation failed'}, status=400)

        # Выполнение запроса
        item_id = self.item_id
        if not await self.check_item_id_exists(item_id):
            return json_response({'code': 404, 'message': 'Item not found'}, status=404)
        try:
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
            return json_response({'items': statistic_units}, status=200)
        except Exception as e:
            return json_response({'code': 404, 'message': 'Item not found'}, status=404)
