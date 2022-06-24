## market_api
Приложение упаковано в Docker-контейнер. 
Используется: 
- БД Postgres
- aiohttp
- SQLAlchemy

Swagger-документация доступна по адресу 0.0.0.0:80/api/doc.
### Команды
Приложение запускается по адресу 0.0.0.0:80 командой: `docker-compose up`.

Тесты запускаются командой: `python3 -m Code.tests`. Для корректного завершения тестирования
необходимо, чтобы приложение работало на адресе 0.0.0.0:80 и БД была пустой.
### Описание БД
Было создано 2 таблицы. В таблице Items хранится вся актуальная информация (после последнего обновления) о товарах и категориях, 
в таблице History - все записи об обновлениях элементов. Чтобы корректно высчитывать среднюю цену категорий, принято хранить количество (amount_of_offers)
и сумму (total_price) всех её товаров. Не получилось записать в БД дату вместе с часовым поясом, поэтому решил хранить их раздельно (date, timezone).
###### Таблица Items
1. item_id: UUID, PRIMARY KEY
2. parent_id: UUID, FOREIGN KEY (Items.item_id)
3. type: STRING
4. name: STRING
5. date: TIMESTAMP
6. timezone: STRING
7. price: INTEGER
8. total_price: INTEGER
9. amount_of_offers: INTEGER
###### Таблица History
1. history_id: INTEGER, PRIMARY KEY
2. item_id: UUID, FOREIGN KEY (Items.item_id)
3. parent_id: UUID
4. type: STRING
5. name: STRING
6. date: TIMESTAMP
7. timezone: STRING
8. price: INTEGER
9. total_price: INTEGER
10. amount_of_offers: INTEGER

Миграции производятся с помощью alembic.
### Дополнительные запросы
Для удобства были добавлены 2 запроса: '/', '/deleteall'. Они нужны для просмотра и удаления соответственно всей информации, хранящейся в БД.
