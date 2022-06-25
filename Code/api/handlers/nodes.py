from aiohttp.web import json_response
from aiohttp_apispec import docs

from .base import BaseWithIDView


class NodesView(BaseWithIDView):
    URL_PATH = r'/nodes/{item_id:[\w-]+}'

    def from_records_to_dict(self, records: list):
        '''
        Переводит строки из БД в dict, добавляет поле children.
        '''
        ans = {}
        for record in records:
            record_id = str(record['item_id'])
            parent_id = str(record['parent_id']) if record['parent_id'] else None
            ans[record_id] = {
                'parentId': parent_id,
                'name': record['name'],
                'type': record['type'],
                'price': record['price'],
                'date': self.from_datetime_with_tz_to_iso((str(record['date']), record['timezone']))
            }
            if record['type'] == 'CATEGORY':
                if record['amount_of_offers'] != 0:
                    ans[record_id]['price'] = record['total_price'] // record['amount_of_offers']
                else:
                    ans[record_id]['price'] = None
            ans[record_id]['children'] = []
            if parent_id and parent_id in ans:
                if 'children' in ans[parent_id]:
                    ans[parent_id]['children'].append(record_id)
                else:
                    ans[parent_id]['children'] = [record_id]
        return ans

    def make_json_answer(self, items: dict):
        '''
        Составляет итоговый json-ответ.
        :param items: все элементы с полем children
        '''

        def make_shop_unit(item_id):
            nonlocal items, shop_units
            shop_unit = {
                'id': item_id,
                'name': items[item_id]['name'],
                'parentId': items[item_id]['parentId'],
                'date': str(items[item_id]['date']),
                'type': items[item_id]['type'],
                'price': items[item_id]['price'],
            }
            if shop_unit['type'] == 'OFFER':
                shop_unit['children'] = None
            else:
                shop_unit['children'] = [shop_units.pop(id) for id in items[item_id]['children']]
            return shop_unit

        shop_units = {}
        stack = []
        cur_ind = self.item_id
        while cur_ind or stack:
            if cur_ind:
                stack.append(cur_ind)
                for child in items[cur_ind]['children'][:-1]:
                    stack.append(child)
                items[cur_ind]['visited'] = None
                if items[cur_ind]['children']:
                    cur_ind = items[cur_ind]['children'][-1]
                else:
                    cur_ind = None
            else:
                cur_item_ind = stack.pop()
                if 'visited' in items[cur_item_ind]:
                    shop_unit = make_shop_unit(cur_item_ind)
                    shop_units[cur_item_ind] = shop_unit
                else:
                    cur_ind = cur_item_ind
        return shop_units[self.item_id]

    @docs(summary='Показывает последнюю актуальную информацию об элементе и его детях.')
    async def get(self):
        try:
            if not self.check_item_id_exists(self.item_id):
                return json_response({'code': 404, 'message': 'Item not found'}, status=404)
            if self.item_id is None:
                return json_response({'code': 400, 'message': 'Validation failed'}, status=400)
            items = await self.pg.fetch(self.reqursive_down(self.item_id))
            items = self.from_records_to_dict(items)
            json_answer = self.make_json_answer(items)
            return json_response(json_answer, status=200)
        except Exception as e:
            return json_response({'code': 404, 'message': 'Item not found'}, status=404)
