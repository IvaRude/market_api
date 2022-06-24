from datetime import datetime, timedelta

from Code.db.models import Items
from aiohttp.web import json_response
from sqlalchemy import and_
from sqlalchemy import select

from .base import BaseView
from Code.api.schema import SalesSchema


class SalesView(BaseView):
    URL_PATH = '/sales'

    async def get(self):
        # Валидация входных данных
        try:
            content = self.request.rel_url.query
            self.validate_date(content['date'])
            SalesSchema().load(content)
        except Exception as e:
            return json_response({'code': 400, 'message': 'Validation failed'}, status=400)

        sales_date, _ = self.from_iso_to_datetime_with_tz(content['date'])
        sales_date = datetime.fromisoformat(sales_date)
        try:
            date_start = sales_date - timedelta(days=1)
            records = await self.pg.fetch(select(Items).filter(
                and_(Items.type == 'OFFER', Items.date >= date_start, Items.date <= sales_date)))
            statistic_units = [self.from_record_to_statistic_unit(record) for record in records]
            return json_response({'items': statistic_units}, status=200)
        except Exception as e:
            return json_response({'code': 400, 'message': 'Validation Failed'}, status=400)
