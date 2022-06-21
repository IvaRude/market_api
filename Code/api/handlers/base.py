from random import randint

from aiohttp.web_urldispatcher import View
from asyncpgsa import PG
from marshmallow import ValidationError
from sqlalchemy import select, update
from sqlalchemy.orm import aliased

from Code.db.models import Items
from .schema import UUIDSchema
from datetime import datetime, timedelta

import logging
logging.basicConfig(filename='app_log.txt', level=logging.INFO)
fh = logging.FileHandler('app_log.txt')
log = logging.getLogger(__name__)
log.addHandler(fh)
log.setLevel(logging.INFO)

class BaseView(View):
    URL_PATH: str

    logger = log

    @property
    def pg(self) -> PG:
        return self.request.app['pg']

    @staticmethod
    def from_iso_to_datetime_with_tz(date: str) -> tuple:
        date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        tz = str(date.tzinfo)[3:]
        if tz == '':
            tz = '+00:00'
        final_tz = tz
        date = date.replace(tzinfo=None)
        symb, tz = tz[0], datetime.strptime(tz[1:], '%H:%M')
        delta = timedelta(hours=tz.hour, minutes=tz.minute)
        if symb == '+':
            date -= delta
        else:
            date += delta
        return str(date), final_tz

    @staticmethod
    def from_datetime_with_tz_to_iso(data: tuple) -> str:
        date, tz = data
        final_tz = 'Z' if tz == '+00:00' else tz
        date = datetime.fromisoformat(date)
        symb, tz = tz[0], datetime.strptime(tz[1:], '%H:%M')
        delta = timedelta(hours=tz.hour, minutes=tz.minute)
        if symb == '+':
            date += delta
        else:
            date -= delta
        return date.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + final_tz

    def from_record_to_statistic_unit(self, record):
        statistic_unit = {
            'id': str(record['item_id']),
            'name': record['name'],
            'parentId': str(record['parent_id']),
            'date': self.from_datetime_with_tz_to_iso((str(record['date']), record['timezone'])),
            'type': record['type'],
            'price': record['price'],
        }
        if record['type'] == 'CATEGORY':
            if record['amount_of_offers'] != 0:
                statistic_unit['price'] = record['total_price'] // record['amount_of_offers']
            else:
                statistic_unit['price'] = None
        return statistic_unit

    @staticmethod
    async def create_update_for_items(items, conn):
        for item in items:
            query = update(Items).where(Items.item_id == item).values(items[item])
            query.parameters = []
            items[item]['item_id'] = item
            await conn.execute(query)
        return items

    @staticmethod
    def from_records_to_list(records):
        ans = []
        for record in records:
            ans.append({
                'item_id': record['item_id'],
                'parent_id': str(record['parent_id']) if record['parent_id'] else None,
                'name': record['name'],
                'type': record['type'],
                'total_price': record['total_price'],
                'amount_of_offers': record['amount_of_offers'],
                'price': record['price'],
                'date': record['date'],
                'timezone': record['timezone']
            })
        return ans

    @staticmethod
    def from_records_to_dict(records):
        ans = {}
        for record in records:
            ans[str(record['item_id'])] = {
                'parent_id': str(record['parent_id']) if record['parent_id'] else None,
                'name': record['name'],
                'type': record['type'],
                'total_price': record['total_price'],
                'amount_of_offers': record['amount_of_offers'],
                'price': record['price'],
                'date': record['date'],
                'timezone': record['timezone']
            }
        return ans

    @staticmethod
    def reqursive_up(item_id):
        reqursive_query = select(Items). \
            filter(Items.item_id == item_id).cte(name=str(randint(1, 1000000)), recursive=True)
        incl_alias = aliased(reqursive_query, name=str(randint(1, 1000000)) + 'pr')
        parts_alias = aliased(Items, name=str(randint(1, 1000000)) + 'p')
        reqursive_query = reqursive_query.union_all(
            select(parts_alias).filter(parts_alias.item_id == incl_alias.c.parent_id)
        )
        return select(reqursive_query)

    @staticmethod
    def reqursive_down(item_id):
        reqursive_query = select(Items). \
            filter(Items.item_id == item_id).cte(name=str(randint(1, 1000000)), recursive=True)
        incl_alias = aliased(reqursive_query, name=str(randint(1, 1000000)) + 'pr')
        parts_alias = aliased(Items, name=str(randint(1, 1000000)) + 'p')
        reqursive_query = reqursive_query.union_all(
            select(parts_alias).filter(parts_alias.parent_id == incl_alias.c.item_id)
        )
        return select(reqursive_query)

    @staticmethod
    def update_info(cur_items, new_info, new_ids=None):
        '''
        Makes all updates for items inside Python.
        Returns dict with correct data for all items after all inserts, updates, deletes.
        '''

        if new_ids is None:
            new_ids = list()

        def update_parents_of_offer(start_id, item, kind_of_action):
            '''
            kind_of_action is in [-1, 0, 1],
            if it equals -1, then item's gone from this category,
            if it equals 1, then item's gone in this category,
            if it equals 0, then item just has changed its price, or other info, not parent
            '''
            nonlocal cur_items, new_info
            cur_id = start_id
            while cur_id:
                if kind_of_action == 1:
                    cur_items[cur_id]['amount_of_offers'] += 1
                    cur_items[cur_id]['total_price'] += item['price']
                elif kind_of_action == -1:
                    cur_items[cur_id]['amount_of_offers'] -= 1
                    cur_items[cur_id]['total_price'] -= item['price']
                else:
                    cur_items[cur_id]['total_price'] += item['price'] - cur_items[item['id']]['price']
                cur_id = cur_items[cur_id]['parent_id']

        def update_parent_of_category(start_id, item, kind_of_action):
            nonlocal cur_items, new_info
            cur_id = start_id
            while cur_id:
                if kind_of_action == 1:
                    cur_items[cur_id]['amount_of_offers'] += cur_items[item['id']]['amount_of_offers']
                    cur_items[cur_id]['total_price'] += cur_items[item['id']]['total_price']
                elif kind_of_action == -1:
                    cur_items[cur_id]['amount_of_offers'] -= cur_items[item['id']]['amount_of_offers']
                    cur_items[cur_id]['total_price'] -= cur_items[item['id']]['total_price']
                else:
                    break
                cur_id = cur_items[cur_id]['parent_id']

        for item in new_info['items']:
            if item['type'] != cur_items[item['id']]['type']:
                raise ValidationError('Type may not be changed')
            if item['id'] in new_ids:
                if item['type'] == 'OFFER':
                    update_parents_of_offer(item['parentId'], item, kind_of_action=1)
            else:
                old_parent_id = cur_items[item['id']]['parent_id']
                new_parent_id = item['parentId']
                if old_parent_id != new_parent_id:
                    if old_parent_id is not None:
                        if item['type'] == 'OFFER':
                            update_parents_of_offer(old_parent_id, item, kind_of_action=-1)
                        else:
                            update_parent_of_category(old_parent_id, item, kind_of_action=-1)
                    if new_parent_id is not None:
                        if item['type'] == 'OFFER':
                            update_parents_of_offer(old_parent_id, item, kind_of_action=1)
                        else:
                            update_parent_of_category(old_parent_id, item, kind_of_action=1)
                elif new_parent_id is not None and item['type'] == 'OFFER' and \
                        cur_items[item['id']]['price'] != item['price']:
                    update_parents_of_offer(new_parent_id, item, kind_of_action=0)
            cur_items[item['id']]['date'] = new_info['updateDate']
            cur_items[item['id']]['timezone'] = new_info['timezone']
            cur_items[item['id']]['name'] = item['name']
            cur_items[item['id']]['parent_id'] = item['parentId']
            if item['type'] == 'OFFER':
                cur_items[item['id']]['price'] = item['price']
        return cur_items


class BaseImportView(BaseView):
    async def check_parents_are_categories(self, import_items, new_ids, conn):
        all_types = {}
        parent_ids = set()
        for item in import_items:
            if item['id'] in new_ids:
                all_types[item['id']] = item['type']
            if item['parentId']:
                parent_ids.add(item['parentId'])
        if len(parent_ids) == 0:
            return
        query = "SELECT item_id, type FROM items WHERE item_id IN ("
        for parent_id in parent_ids:
            query += "'" + str(parent_id) + "', "
        query = query[:-2] + ')'
        items_from_db_records = await conn.fetch(query)
        for record in items_from_db_records:
            all_types[str(record['item_id'])] = record['type']

        for parent_id in parent_ids:
            if all_types[parent_id] == 'OFFER':
                raise ValidationError('An offer may not be a parent')


class BaseWithIDView(BaseView):
    @property
    def item_id(self):
        try:
            id = {'id': self.request.match_info.get('item_id')}
            UUIDSchema().load(id)
            return str(self.request.match_info.get('item_id'))
        except Exception as e:
            return None
