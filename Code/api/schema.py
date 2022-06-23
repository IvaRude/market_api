from marshmallow import Schema, ValidationError, validates_schema
from marshmallow.fields import Nested, Str, UUID, DateTime, Integer
from marshmallow.validate import OneOf


class UUIDSchema(Schema):
    id = UUID(required=True)


class SalesSchema(Schema):
    date = DateTime(required=True, format='iso')


class StatisticSchema(Schema):
    dateStart = DateTime(required=False, format='iso')
    dateEnd = DateTime(required=False, format='iso')


class ItemSchema(Schema):
    id = UUID(required=True)
    name = Str(required=True)
    type = Str(validate=OneOf(['OFFER', 'CATEGORY']), required=True)
    parentId = UUID(required=False, allow_none=True)
    price = Integer(required=False, strict=True, allow_none=True)

    @validates_schema
    def validate_price(self, item, **_):
        if item['type'] == 'OFFER' and 'price' in item and (item['price'] is None or item['price'] < 0):
            raise ValidationError("Offer's price must be >= 0")
        elif item['type'] == 'CATEGORY' and 'price' in item and item['price'] is not None:
            raise ValidationError("Category's price must be None")
        elif item['type'] == 'OFFER' and 'price' not in item:
            raise ValidationError('Offer must have price')


class ImportSchema(Schema):
    items = Nested(ItemSchema, many=True, required=True)
    updateDate = DateTime(required=True, format='iso')

    @validates_schema
    def validate_unique_item_id(self, data, **_):
        items = data['items']
        unique_item_ids = set()
        for item in items:
            if item['id'] in unique_item_ids:
                raise ValidationError('Ids must be unique')
            unique_item_ids.add(item['id'])
