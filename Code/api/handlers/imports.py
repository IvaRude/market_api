from datetime import datetime

from Code.db.models import Items, History
from Code.utils.pg import MAX_QUERY_ARGS
from aiohttp.web import json_response
from aiohttp_apispec import docs, request_schema
from aiomisc import chunk_list
from sqlalchemy import insert, union, select

from .base import BaseImportView
from Code.api.schema import ImportSchema


class ImportView(BaseImportView):
    URL_PATH = '/imports'
    MAX_ITEMS_PER_INSERT = MAX_QUERY_ARGS // 8

    @docs(summary='Inserting new items and updating old items')
    @request_schema(ImportSchema())
    async def post(self):
        try:
            content = await self.request.json()
            self.validate_date(content['updateDate'])
            ImportSchema().load(content)
            update_date, time_zone = self.from_iso_to_datetime_with_tz(content['updateDate'])
            # print('update_date', update_date)
            content['updateDate'] = update_date
            content['timezone'] = time_zone
            all_import_ids = set([item['id'] for item in content['items']])
            if len(all_import_ids) == 0:
                return json_response({'code': 200, 'message': 'Imported Successfully'}, status=200)
            async with self.pg.transaction() as conn:

                # inserting new items
                query = "SELECT item_id FROM items WHERE item_id IN ("
                for id in all_import_ids:
                    query += "'" + id + "', "
                query = query[:-2] + ')'
                record_ids = await conn.fetch(query)
                old_ids = set([str(rec_id['item_id']) for rec_id in record_ids])
                new_ids = all_import_ids.difference(old_ids)

                # Checking the validation
                await self.check_parents_are_categories(content['items'], new_ids, conn)

                insert_items = []
                update_items = []
                for item in content['items']:
                    if item['id'] in new_ids:
                        insert_items.append({
                            'item_id': item['id'],
                            'name': item['name'],
                            'parent_id': item['parentId'] if 'parentId' in item else None,
                            'type': item['type'],
                            'price': item['price'] if 'price' in item else None,
                            'date': datetime.fromisoformat(update_date),
                            'timezone': time_zone,
                            'total_price': 0,
                            'amount_of_offers': 0
                        })
                    else:
                        update_items.append(
                            {'item_id': item['id']})
                        if 'parentId' in item:
                            update_items.append({'item_id': item['parentId']})
                chunked_insert_values = chunk_list(insert_items, self.MAX_ITEMS_PER_INSERT)
                for chunk in chunked_insert_values:
                    query = insert(Items).values(list(chunk))
                    query.parameters = []
                    await conn.execute(query)
                # collecting all items that will be updated
                all_queries = [self.reqursive_up(item['item_id']) for item in insert_items + update_items]
                query = union(*all_queries)
                items_need_to_update = self.from_records_to_dict(await conn.fetch(query))
                items_need_to_update = self.update_info(items_need_to_update, content, new_ids)
                for item in items_need_to_update:
                    items_need_to_update[item]['date'] = datetime.fromisoformat(update_date)
                    items_need_to_update[item]['timezone'] = time_zone
                # Making big update query in Items table
                insert_history_values = await self.create_update_for_items(items_need_to_update, conn)

                dates = select(Items.date)
                print(await conn.fetch(dates))

                # Making insert query in History table
                chunked_insert_history_values = chunk_list(insert_history_values.values(), self.MAX_ITEMS_PER_INSERT)
                for chunk in chunked_insert_history_values:
                    query = insert(History).values(list(chunk))
                    query.parameters = []
                    await conn.execute(query)
            return json_response({'code': 200, 'message': 'Imported Successfully'}, status=200)
        except Exception as e:
            return json_response({'code': 400, 'message': 'Validation Failed'}, status=400)
