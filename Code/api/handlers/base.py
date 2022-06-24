import re
from datetime import datetime, timedelta
from random import randint

from Code.api.schema import UUIDSchema
from Code.db.models import Items
from Code.utils.pg import MAX_QUERY_ARGS
from aiohttp.web_urldispatcher import View
from asyncpgsa import PG
from marshmallow import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import aliased


class BaseView(View):
    URL_PATH: str
    MAX_ITEMS_PER_INSERT = MAX_QUERY_ARGS // 9

    @property
    def pg(self) -> PG:
        return self.request.app['pg']

    @staticmethod
    def validate_date(date):
        if date.endswith('+00:00') or date.endswith('-00:00'):
            raise ValidationError('Bad date format')
        pattern = r'([0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.\d\d\d)?(Z|[+-](\d\d):[0-5][0-9])$'
        res = re.match(pattern, date)
        if not res:
            raise ValidationError('Bad date format')

    @staticmethod
    def from_iso_to_datetime_with_tz(date: str) -> tuple:
        '''
        Принимает на вход дату, разделяет на саму дату и часовой пояс, дату переводит к UTC +00:00.
        На выход обновленная дата и сдвиг.
        '''
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
        '''
        На вход принимает дату в UTC +00:00 и сдвиг часового пояса, прибавляет к дате сдвиг часового пояса.
        На выход iso-формат даты.
        '''
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
        '''
        На вход дается запись из БД таблицы History.
        Переводит в Statistic Unit для ответа на запрос.
        '''
        statistic_unit = {
            'id': str(record['item_id']),
            'name': record['name'],
            'parentId': str(record['parent_id']) if record['parent_id'] else None,
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

    # @staticmethod
    # async def create_update_for_items(items, conn):
    #     for item in items:
    #         query = update(Items).where(Items.item_id == item).values(items[item])
    #         query.parameters = []
    #         items[item]['item_id'] = item
    #         await conn.execute(query)
    #     return items

    @staticmethod
    async def create_update_for_items(items, conn):
        '''
        Делает UPDATE запрос в таблицу Items.
        Выодит преобразованный словарь для дальнейшего запрос INSERT в таблицу History.
        '''
        if not items:
            return items
        query = "UPDATE items SET"
        name_values = ""
        price_values = ""
        amount_of_offers_values = ""
        total_price_values = ""
        parent_id_values = ""
        date_values = ""
        timezone_values = ""
        where_statement = " WHERE item_id IN ("
        for item_id, item in items.items():
            name_values += " WHEN '" + item_id + "' THEN '" + item['name'] + "'"
            if item['price'] is not None:
                price_values += " WHEN '" + item_id + "' THEN CAST(" + str(item['price']) + " AS int)"
            else:
                price_values += " WHEN '" + item_id + "' THEN CAST(NULL AS int)"
            amount_of_offers_values += " WHEN '" + item_id + "' THEN " + str(item['amount_of_offers'])
            total_price_values += " WHEN '" + item_id + "' THEN " + str(item['total_price'])
            if item['parent_id'] is not None:
                parent_id_values += " WHEN '" + item_id + "' THEN CAST('" + item['parent_id'] + "' AS uuid)"
            else:
                parent_id_values += " WHEN '" + item_id + "' THEN CAST(NULL AS uuid)"
            date_values += " WHEN '" + item_id + "' THEN CAST('" + str(item['date']) + "' AS timestamp)"
            timezone_values += " WHEN '" + item_id + "' THEN '" + item['timezone'] + "'"
            where_statement += "'" + item_id + "', "
            items[item_id]['item_id'] = item_id
        query += " name = CASE item_id " + name_values + " END,"
        query += " price = CASE item_id " + price_values + " END,"
        query += " amount_of_offers = CASE item_id " + amount_of_offers_values + " END,"
        query += " total_price = CASE item_id " + total_price_values + " END,"
        query += " parent_id = CASE item_id " + parent_id_values + " END,"
        query += " date = CASE item_id " + date_values + " END,"
        query += " timezone = CASE item_id " + timezone_values + " END"
        where_statement = where_statement[:-2] + ')'
        query += where_statement
        await conn.execute(query)
        return items

    @staticmethod
    def from_records_to_list(records):
        '''
        Переводит строки из БД в list.
        '''
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
        '''
        Переводит строки из БД в dict.
        '''
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
        '''
        На вход item_id, составляет рекурсивный SELECT запрос к таблице Items.
        Собирает элемент с id == item_id и всех его родителей до самого верхнего.
        '''
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
        '''
        На вход item_id, составляет рекурсивный SELECT запрос к таблице Items.
        Собирает элемент с id == item_id и всех его детей до самого нижнего.
        '''
        reqursive_query = select(Items). \
            filter(Items.item_id == item_id).cte(name=str(randint(1, 1000000)), recursive=True)
        incl_alias = aliased(reqursive_query, name=str(randint(1, 1000000)) + 'pr')
        parts_alias = aliased(Items, name=str(randint(1, 1000000)) + 'p')
        reqursive_query = reqursive_query.union_all(
            select(parts_alias).filter(parts_alias.parent_id == incl_alias.c.item_id)
        )
        return select(reqursive_query)

    @staticmethod
    def update_info(cur_items: dict, new_info: dict, new_ids=None):
        '''
        cur_items: словарь с текущими состояниями элементов таблицы Items, который должны будут обновиться;
        new_info: информация из запроса /imports или /delete;
        new_ids: id всех элементов из запроса /imports, которых нет в БД (первая вставка);
        Внутри cur_items производит все необходимые изменения.
        На выход: обновленный cur_items, далее будет совершен UPDATE.
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
            if 'parentId' not in item:
                item['parentId'] = None
            if 'price' not in item:
                item['price'] = None
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
                            update_parents_of_offer(new_parent_id, item, kind_of_action=1)
                        else:
                            update_parent_of_category(new_parent_id, item, kind_of_action=1)
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
        '''
        Проверяет, что ни у одного элемента в запросе /imports не указан в качестве родителя OFFER.
        :param import_items: все элементы из запроса /imports
        :param new_ids: id всех элементов из запроса /imports, которых нет в БД (первая вставка);
        :param conn: connect к БД
        '''
        all_types = {}
        parent_ids = set()
        for item in import_items:
            if item['id'] in new_ids:
                all_types[item['id']] = item['type']
            if 'parentId' in item and item['parentId']:
                parent_ids.add(item['parentId'])
        if len(parent_ids) == 0:
            return

        # Getting types of items that are parents in import
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

    async def check_item_id_exists(self, item_uuid: str):
        items = await self.pg.fetch(select(Items.item_id).filter(Items.item_id == item_uuid))
        if len(items) > 0:
            return True
        return False
