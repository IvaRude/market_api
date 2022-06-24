import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

from .unit_test import request, deep_sort_children, print_diff

# all ids for items
CATEGORY_UUIDS = [str(uuid.uuid4()) for _ in range(9)]
OFFER_UUIDS = [str(uuid.uuid4()) for _ in range(7)]

INITIAL_IMPORT_DATA = {
    'items': [
        {
            'id': CATEGORY_UUIDS[0],
            'type': 'CATEGORY',
            'name': 'category_0',
        },
        {
            'id': CATEGORY_UUIDS[1],
            'type': 'CATEGORY',
            'name': 'category_1',
            'parentId': CATEGORY_UUIDS[0]
        },
        {
            'id': CATEGORY_UUIDS[8],
            'type': 'CATEGORY',
            'name': 'category_8',
            'parentId': CATEGORY_UUIDS[0]
        },
        {
            'id': CATEGORY_UUIDS[2],
            'type': 'CATEGORY',
            'name': 'category_2',
            'parentId': CATEGORY_UUIDS[1]
        },
        {
            'id': CATEGORY_UUIDS[3],
            'type': 'CATEGORY',
            'name': 'category_3',
        },
        {
            'id': CATEGORY_UUIDS[4],
            'type': 'CATEGORY',
            'name': 'category_4',
            'parentId': CATEGORY_UUIDS[3]
        },
        {
            'id': OFFER_UUIDS[0],
            'type': 'OFFER',
            'name': 'offer_0',
            'parentId': CATEGORY_UUIDS[2],
            'price': 1
        },
        {
            'id': OFFER_UUIDS[6],
            'type': 'OFFER',
            'name': 'offer_6',
            'parentId': CATEGORY_UUIDS[8],
            'price': 5
        },
        {
            'id': OFFER_UUIDS[3],
            'type': 'OFFER',
            'name': 'offer_3',
            'parentId': CATEGORY_UUIDS[4],
            'price': 3
        },
    ],
    'updateDate': '2022-02-02T12:00:00.000Z'
}

# Changing parent of category_8
UPDATE_CATEGORY_8 = {
    'items': [
        {
            'id': CATEGORY_UUIDS[8],
            'type': 'CATEGORY',
            'name': 'category_8',
            'parentId': CATEGORY_UUIDS[2]
        }, ],
    'updateDate': '2022-02-02T13:00:00.000Z'
}
SECOND_UPDATE_CATEGORY_8 = {
    'items': [
        {
            'id': CATEGORY_UUIDS[8],
            'type': 'CATEGORY',
            'name': 'category_8',
            'parentId': None
        }, ],
    'updateDate': '2022-02-02T13:00:00.000Z'
}

ADD_CATEGORY_5 = {
    'items': [
        {
            'id': CATEGORY_UUIDS[5],
            'type': 'CATEGORY',
            'name': 'category_5',
            'parentId': CATEGORY_UUIDS[2]
        },
        {
            'id': OFFER_UUIDS[1],
            'type': 'OFFER',
            'name': 'offer_1',
            'parentId': CATEGORY_UUIDS[5],
            'price': 2
        },
        {
            'id': OFFER_UUIDS[2],
            'type': 'OFFER',
            'name': 'offer_2',
            'parentId': CATEGORY_UUIDS[5],
            'price': 2
        },
    ],
    'updateDate': '2022-02-03T13:00:00.001Z'
}


def initial_import():
    '''
    Вставка многих элементов
    '''
    status, _ = request("/imports", method="POST", data=INITIAL_IMPORT_DATA)
    assert status == 200, f"Expected HTTP status code 200, got {status}"
    print('Initial import made.')


def change_parent_of_category_8():
    '''
    Меняем отца одной из категорий на сына её брата.
    Проверяем, что у изначального отца не изменилась цена, но обновилась дата.
    Затем делаем эту категорию без отца.
    '''
    # First changing parent from category_0 to category_3,
    # then checking statistic of category_0: it's price must be the same
    status, _ = request("/imports", method="POST", data=UPDATE_CATEGORY_8)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    params = urllib.parse.urlencode({
        "dateStart": "2022-02-02T13:00:00.000Z",
    })
    status, response = request(
        f"/node/{CATEGORY_UUIDS[0]}/statistic?{params}", json_response=True)
    expected_response = {
        'items': [{
            'id': CATEGORY_UUIDS[0],
            'name': 'category_0',
            'type': 'CATEGORY',
            'parentId': None,
            'price': 3,
            # 'date': '2022-02-02T21:00:00.000Z',
            'date': '2022-02-02T13:00:00.000Z'
        }]
    }
    assert status == 200, f"Expected HTTP status code 200, got {status}"
    assert response == expected_response, "Wrong statistic for category_0"
    # Now category_8 has no parent
    status, _ = request("/imports", method="POST", data=SECOND_UPDATE_CATEGORY_8)
    assert status == 200, f"Expected HTTP status code 200, got {status}"
    print('Category_8 changed parent to None.')


def add_category_5():
    '''
    Проверяем краевой случай в запросах /sales: чтобы не попали лишние элементы во временной отрезок.
    '''
    # Adding new category with time == first import time + 24h + 1ms
    status, _ = request("/imports", method="POST", data=ADD_CATEGORY_5)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    # Checking the statistic of new category: must be only one note
    params = urllib.parse.urlencode({})
    status, response = request(
        f"/node/{CATEGORY_UUIDS[5]}/statistic?{params}", json_response=True)
    expected_response = {
        'items': [{
            'id': CATEGORY_UUIDS[5],
            'type': 'CATEGORY',
            'name': 'category_5',
            'parentId': CATEGORY_UUIDS[2],
            'price': 2,
            # 'date': '2022-02-03T21:00:00.001Z'
            'date': '2022-02-03T13:00:00.001Z'
        }
        ]
    }
    assert status == 200, f"Expected HTTP status code 200, got {status}"
    assert response == expected_response, "Wrong statistic for category_5"

    # Cheking sales request with time == last adding time: must be only two new offers
    params = urllib.parse.urlencode({
        'date': '2022-02-03T13:00:00.001Z'
    })
    status, response = request(f"/sales?{params}", json_response=True)
    expected_response = {
        'items': [
            {
                'id': OFFER_UUIDS[1],
                'type': 'OFFER',
                'name': 'offer_1',
                'parentId': CATEGORY_UUIDS[5],
                'price': 2,
                # 'date': '2022-02-03T21:00:00.001Z'
                'date': '2022-02-03T13:00:00.001Z'
            },
            {
                'id': OFFER_UUIDS[2],
                'type': 'OFFER',
                'name': 'offer_2',
                'parentId': CATEGORY_UUIDS[5],
                'price': 2,
                # 'date': '2022-02-03T21:00:00.001Z'
                'date': '2022-02-03T13:00:00.001Z'
            },
        ]
    }
    response['items'].sort(key=lambda x: x['id'])
    expected_response['items'].sort(key=lambda x: x['id'])
    assert status == 200, f"Expected HTTP status code 200, got {status}"
    assert response == expected_response, "Wrong sales response"
    print("Category 5 added correctly.")


def change_parent_of_category_5():
    '''
    Сначала проверяем запрос /nodes для категории, затем переставляем одну из её категорий-поддетей к другой категории.
    Проверяем, что корректно изменилась информация у изначального и нового отцов.
    '''
    # Firstly make nodes request for category_0
    expected_response = {
        'id': CATEGORY_UUIDS[0],
        'name': 'category_0',
        'type': 'CATEGORY',
        'parentId': None,
        'price': 1,
        'date': '2022-02-03T13:00:00.001Z',
        # 'date': '2022-02-03T21:00:00.001Z',
        'children': [
            {'id': CATEGORY_UUIDS[1],
             'name': 'category_1',
             'type': 'CATEGORY',
             'parentId': CATEGORY_UUIDS[0],
             'price': 1,
             'date': '2022-02-03T13:00:00.001Z',
             # 'date': '2022-02-03T21:00:00.001Z',
             'children': [
                 {'id': CATEGORY_UUIDS[2],
                  'name': 'category_2',
                  'type': 'CATEGORY',
                  'parentId': CATEGORY_UUIDS[1],
                  'price': 1,
                  'date': '2022-02-03T13:00:00.001Z',
                  # 'date': '2022-02-03T21:00:00.001Z',
                  'children': [
                      {'id': OFFER_UUIDS[0],
                       'name': 'offer_0',
                       'type': 'OFFER',
                       'parentId': CATEGORY_UUIDS[2],
                       'price': 1,
                       'date': '2022-02-02T12:00:00.000Z',
                       # 'date': '2022-02-02T20:00:00.000Z',
                       'children': None
                       },
                      {
                          'id': CATEGORY_UUIDS[5],
                          'name': 'category_5',
                          'type': 'CATEGORY',
                          'parentId': CATEGORY_UUIDS[2],
                          'price': 2,
                          'date': '2022-02-03T13:00:00.001Z',
                          # 'date': '2022-02-03T21:00:00.001Z',
                          'children': [
                              {'id': OFFER_UUIDS[1],
                               'name': 'offer_1',
                               'type': 'OFFER',
                               'parentId': CATEGORY_UUIDS[5],
                               'price': 2,
                               'date': '2022-02-03T13:00:00.001Z',
                               # 'date': '2022-02-03T21:00:00.001Z',
                               'children': None
                               },
                              {'id': OFFER_UUIDS[2],
                               'name': 'offer_2',
                               'type': 'OFFER',
                               'parentId': CATEGORY_UUIDS[5],
                               'price': 2,
                               'date': '2022-02-03T13:00:00.001Z',
                               # 'date': '2022-02-03T21:00:00.001Z',
                               'children': None
                               },
                          ]
                      },
                  ]}
             ]}
        ]
    }
    status, response = request(f"/nodes/{CATEGORY_UUIDS[0]}", json_response=True)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    deep_sort_children(response)
    deep_sort_children(expected_response)
    if response != expected_response:
        print_diff(expected_response, response)
        print("Response tree doesn't match expected tree for category_0")
        sys.exit(1)

    # Change parent from category_2 to category_4
    UPDATE_CATEGORY_5 = {
        'items': [
            {
                'id': CATEGORY_UUIDS[5],
                'type': 'CATEGORY',
                'name': 'category_5',
                'parentId': CATEGORY_UUIDS[4]
            },
        ],
        'updateDate': '2022-02-03T14:00:00.000Z'
    }
    status, _ = request("/imports", method="POST", data=UPDATE_CATEGORY_5)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    # Again nodes request for category_0: category_5 must gone
    expected_response['children'][0]['children'][0]['children'] = [{'id': OFFER_UUIDS[0],
                                                                    'name': 'offer_0',
                                                                    'type': 'OFFER',
                                                                    'parentId': CATEGORY_UUIDS[2],
                                                                    'price': 1,
                                                                    'date': '2022-02-02T12:00:00.000Z',
                                                                    # 'date': '2022-02-02T20:00:00.000Z',
                                                                    'children': None
                                                                    }, ]
    expected_response['date'] = '2022-02-03T14:00:00.000Z'
    # expected_response['date'] = '2022-02-03T22:00:00.000Z'
    expected_response['children'][0]['date'] = '2022-02-03T14:00:00.000Z'
    # expected_response['children'][0]['date'] = '2022-02-03T22:00:00.000Z'
    expected_response['children'][0]['children'][0]['date'] = '2022-02-03T14:00:00.000Z'
    # expected_response['children'][0]['children'][0]['date'] = '2022-02-03T22:00:00.000Z'
    status, response = request(f"/nodes/{CATEGORY_UUIDS[0]}", json_response=True)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    deep_sort_children(response)
    deep_sort_children(expected_response)
    if response != expected_response:
        print_diff(expected_response, response)
        print("Response tree doesn't match expected tree for category_0 second time")
        sys.exit(1)

    # Finally making nodes requests for category_3: category_5 must appear in tree
    expected_response = {
        'id': CATEGORY_UUIDS[3],
        'name': 'category_3',
        'type': 'CATEGORY',
        'parentId': None,
        'price': 2,
        'date': '2022-02-03T14:00:00.000Z',
        # 'date': '2022-02-03T22:00:00.000Z',
        'children': [
            {'id': CATEGORY_UUIDS[4],
             'name': 'category_4',
             'type': 'CATEGORY',
             'parentId': CATEGORY_UUIDS[3],
             'price': 2,
             'date': '2022-02-03T14:00:00.000Z',
             # 'date': '2022-02-03T22:00:00.000Z',
             'children': [
                 {'id': OFFER_UUIDS[3],
                  'name': 'offer_3',
                  'type': 'OFFER',
                  'parentId': CATEGORY_UUIDS[4],
                  'price': 3,
                  'date': '2022-02-02T12:00:00.000Z',
                  # 'date': '2022-02-02T20:00:00.000Z',
                  'children': None
                  },
                 {
                     'id': CATEGORY_UUIDS[5],
                     'name': 'category_5',
                     'type': 'CATEGORY',
                     'parentId': CATEGORY_UUIDS[4],
                     'price': 2,
                     'date': '2022-02-03T14:00:00.000Z',
                     # 'date': '2022-02-03T22:00:00.000Z',
                     'children': [
                         {'id': OFFER_UUIDS[1],
                          'name': 'offer_1',
                          'type': 'OFFER',
                          'parentId': CATEGORY_UUIDS[5],
                          'price': 2,
                          'date': '2022-02-03T13:00:00.001Z',
                          # 'date': '2022-02-03T21:00:00.001Z',
                          'children': None
                          },
                         {'id': OFFER_UUIDS[2],
                          'name': 'offer_2',
                          'type': 'OFFER',
                          'parentId': CATEGORY_UUIDS[5],
                          'price': 2,
                          'date': '2022-02-03T13:00:00.001Z',
                          # 'date': '2022-02-03T21:00:00.001Z',
                          'children': None
                          },
                     ]
                 },
             ]
             },
        ]
    }
    status, response = request(f"/nodes/{CATEGORY_UUIDS[3]}", json_response=True)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    deep_sort_children(response)
    deep_sort_children(expected_response)
    if response != expected_response:
        print_diff(expected_response, response)
        print("Response tree doesn't match expected tree for category_3")
        sys.exit(1)
    print('Category_5 changed parent from category_2 to category_4')


def statistic_category_5():
    '''
    У одной из категорий удаляем товар.
    Проверяем, что в статистике появляется новая запись после удаления и с датой,
    совпадающей с предыдущим последним обновлением.
    '''
    # In statistic request for category_5 must be two notes
    params = urllib.parse.urlencode({
        'dateEnd': '2022-02-03T14:00:00.001Z'
    })
    status, response = request(
        f"/node/{CATEGORY_UUIDS[5]}/statistic?{params}", json_response=True)
    expected_response = {
        'items': [
            {
                'id': CATEGORY_UUIDS[5],
                'type': 'CATEGORY',
                'name': 'category_5',
                'parentId': CATEGORY_UUIDS[2],
                'price': 2,
                # 'date': '2022-02-03T21:00:00.001Z'
                'date': '2022-02-03T13:00:00.001Z'
            },
            {
                'id': CATEGORY_UUIDS[5],
                'type': 'CATEGORY',
                'name': 'category_5',
                'parentId': CATEGORY_UUIDS[4],
                'price': 2,
                # 'date': '2022-02-03T22:00:00.000Z'
                'date': '2022-02-03T14:00:00.000Z'
            }
        ]
    }
    assert status == 200, f"Expected HTTP status code 200, got {status}"
    assert response == expected_response, "Wrong statistic for category_5"

    # Deleting offer_1
    status, _ = request(f"/delete/{OFFER_UUIDS[1]}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    # Again checking statistic of category_5: must be 3 notes
    expected_response['items'].append(expected_response['items'][1])
    status, response = request(
        f"/node/{CATEGORY_UUIDS[5]}/statistic?{params}", json_response=True)
    assert status == 200, f"Expected HTTP status code 200, got {status}"
    assert response == expected_response, "Wrong statistic for category_5"
    print('Statistic for category_5 is correct')


def delete_category_5():
    '''
    Вставляем новый товар с id, совпадающим с id удаленного ранее товара.
    Проверяем, что на запрос /statistic с этим id выводится только информация по новому товару,
    а про старый ничего не выводится.
    '''
    # Import new children for category_4
    # Offer_5 have the same id that had offer_1 before its deletion
    IMPORT_CATEGORY_6 = {
        'items': [
            {
                'id': CATEGORY_UUIDS[6],
                'type': 'CATEGORY',
                'name': 'category_6',
                'parentId': CATEGORY_UUIDS[4]
            },
            {
                'id': CATEGORY_UUIDS[7],
                'type': 'CATEGORY',
                'name': 'category_7',
                'parentId': CATEGORY_UUIDS[6]
            },
            {
                'id': OFFER_UUIDS[1],
                'type': 'OFFER',
                'name': 'offer_5',
                'parentId': CATEGORY_UUIDS[7],
                'price': 5
            },
            {
                'id': OFFER_UUIDS[4],
                'type': 'OFFER',
                'name': 'offer_4',
                'parentId': CATEGORY_UUIDS[6],
                'price': 4
            },
        ],
        'updateDate': '2022-02-03T14:01:00.000Z'
    }
    status, _ = request("/imports", method="POST", data=IMPORT_CATEGORY_6)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    # Statistic request for offer_5: must be only one note
    params = urllib.parse.urlencode({})
    status, response = request(
        f"/node/{OFFER_UUIDS[1]}/statistic?{params}", json_response=True)

    expected_response = {
        'items': [
            {
                'id': OFFER_UUIDS[1],
                'type': 'OFFER',
                'name': 'offer_5',
                'parentId': CATEGORY_UUIDS[7],
                'price': 5,
                # 'date': '2022-02-03T22:01:00.000Z'
                'date': '2022-02-03T14:01:00.000Z'
            }
        ]
    }
    assert status == 200, f"Expected HTTP status code 200, got {status}"
    assert response == expected_response, "Wrong statistic for offer_5"

    # Deleting category_4
    status, _ = request(f"/delete/{CATEGORY_UUIDS[4]}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    # Nodes request for category_3: now it has no children, so price must be equal None
    expected_response = {
        'id': CATEGORY_UUIDS[3],
        'name': 'category_3',
        'type': 'CATEGORY',
        'parentId': None,
        'price': None,
        # 'date': '2022-02-03T22:01:00.000Z',
        'date': '2022-02-03T14:01:00.000Z',
        'children': []
    }
    status, response = request(f"/nodes/{CATEGORY_UUIDS[3]}", json_response=True)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    deep_sort_children(response)
    deep_sort_children(expected_response)
    if response != expected_response:
        print_diff(expected_response, response)
        print("Response tree doesn't match expected tree for category_3")
        sys.exit(1)
    print('Category_5 deleted correctly.')


def make_zero_price_for_offer_0():
    '''
    У категории есть только один товар.
    Меняем цену товара на 0, проверяем, что цена категории стала равной 0.
    '''
    # Updating price of offer_0 to 0
    UPDATE_OFFER_0 = {
        'items': [
            {
                'id': OFFER_UUIDS[0],
                'type': 'OFFER',
                'name': 'offer_0',
                'parentId': CATEGORY_UUIDS[2],
                'price': 0,
            }
        ],
        'updateDate': '2022-02-03T14:05:00.000Z'
    }
    status, _ = request("/imports", method="POST", data=UPDATE_OFFER_0)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    # Nodes request for category_0: its price must be equal 0
    expected_response = {
        'id': CATEGORY_UUIDS[0],
        'name': 'category_0',
        'type': 'CATEGORY',
        'parentId': None,
        'price': 0,
        # 'date': '2022-02-03T22:05:00.000Z',
        'date': '2022-02-03T14:05:00.000Z',
        'children': [{
            'id': CATEGORY_UUIDS[1],
            'name': 'category_1',
            'type': 'CATEGORY',
            'parentId': CATEGORY_UUIDS[0],
            'price': 0,
            # 'date': '2022-02-03T22:05:00.000Z',
            'date': '2022-02-03T14:05:00.000Z',
            'children': [{
                'id': CATEGORY_UUIDS[2],
                'name': 'category_2',
                'type': 'CATEGORY',
                'parentId': CATEGORY_UUIDS[1],
                'price': 0,
                # 'date': '2022-02-03T22:05:00.000Z',
                'date': '2022-02-03T14:05:00.000Z',
                'children': [{
                    'id': OFFER_UUIDS[0],
                    'name': 'offer_0',
                    'type': 'OFFER',
                    'parentId': CATEGORY_UUIDS[2],
                    'price': 0,
                    # 'date': '2022-02-03T22:05:00.000Z',
                    'date': '2022-02-03T14:05:00.000Z',
                    'children': None
                }]}]
        }]
    }
    status, response = request(f"/nodes/{CATEGORY_UUIDS[0]}", json_response=True)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    deep_sort_children(response)
    deep_sort_children(expected_response)
    if response != expected_response:
        print_diff(expected_response, response)
        print("Response tree doesn't match expected tree for category_0")
        sys.exit(1)
    print('Updated price of offer_0 to 0.')


def delete_all_categories():
    '''
    Удаляем все категории, пытаемся сделать запросы /delete, /statistic, /nodes по этим удаленным категориям, и получаем
    соответствующие ошибки.
    '''
    # Deleting category_0
    status, _ = request(f"/delete/{CATEGORY_UUIDS[0]}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    # Trying to get info about category_0
    status, _ = request(f"/nodes/{CATEGORY_UUIDS[0]}", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"

    # Trying to get statistic of category_0
    params = urllib.parse.urlencode({})
    status, _ = request(
        f"/node/{OFFER_UUIDS[0]}/statistic?{params}", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"

    # Trying to delete category_0 second time
    status, _ = request(f"/delete/{CATEGORY_UUIDS[0]}", method="DELETE")
    assert status == 404, f"Expected HTTP status code 404, got {status}"

    # Deleting category_3
    status, _ = request(f"/delete/{CATEGORY_UUIDS[3]}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    # Deleting category_8
    status, _ = request(f"/delete/{CATEGORY_UUIDS[8]}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    print('All categories are deleted.')


def complex_test():
    initial_import()
    change_parent_of_category_8()
    add_category_5()
    change_parent_of_category_5()
    statistic_category_5()
    delete_category_5()
    make_zero_price_for_offer_0()
    delete_all_categories()
    print('Complex test passed.')


if __name__ == '__main__':
    complex_test()
