from Code.db.models import History
from aiohttp.web import json_response
from aiohttp_apispec import docs
from aiomisc import chunk_list
from sqlalchemy import insert

from .base import BaseWithIDView


@docs(summary='Удаляет элемент c id == item_id и всех его детей из всех таблиц.')
class DeleteView(BaseWithIDView):
    URL_PATH = r'/delete/{item_id:[\w-]+}'

    async def delete(self):
        try:
            async with self.pg.transaction() as conn:
                if self.item_id is None:
                    return json_response({'code': 400, 'message': 'Validation failed'}, status=400)
                if not self.check_item_id_exists(self.item_id):
                    return json_response({'code': 404, 'message': 'Item not found'}, status=404)
                # Finding all parents of this item
                items = await conn.fetch(self.reqursive_up(self.item_id))
                item = self.from_records_to_list([items[0]])[0]

                # Updating information for parents
                item['parentId'] = None
                item['id'] = self.item_id
                items = self.from_records_to_dict(items)
                items_need_to_update = self.update_info(items, {'items': [item], 'updateDate': None, 'timezone': None})
                items_need_to_update.pop(self.item_id)

                # Update query for Items table
                insert_history_values = await self.create_update_for_items(items_need_to_update, conn)

                # Making insert query in History table
                chunked_insert_history_values = chunk_list(insert_history_values.values(), self.MAX_ITEMS_PER_INSERT)
                for chunk in chunked_insert_history_values:
                    query = insert(History).values(list(chunk))
                    query.parameters = []
                    await conn.execute(query)

                # Delete from Items and History tables
                items_need_to_delete = await conn.fetch(self.reqursive_down(self.item_id))
                item_ids_need_to_delete = set(str(record['item_id']) for record in items_need_to_delete)

                query = "DELETE FROM history WHERE item_id IN ("
                for id in item_ids_need_to_delete:
                    query += "'" + id + "'" + ', '
                query = query[:-2] + ')'
                await conn.execute(query)

                query = 'DELETE FROM items' + query[19:]
                await conn.execute(query)
                return json_response({'code': 200, 'message': 'Deleted Successfully'})
        except Exception as e:
            return json_response({'code': 404, 'message': 'Item not found'}, status=404)
