from aiohttp.web import json_response

from .base import BaseWithIDView


class DeleteView(BaseWithIDView):
    URL_PATH = r'/delete/{item_id:[\w-]+}'

    async def delete(self):
        try:
            async with self.pg.transaction() as conn:
                if self.item_id is None:
                    return json_response({'code': 400, 'message': 'Validation failed'}, status=400)
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
                await self.create_update_for_items(items_need_to_update, conn)

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
