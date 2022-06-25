import urllib.parse
import uuid

from .unit_test import request


def import_request(data, expected_status):
    status, _ = request("/imports", method="POST", data=data)
    assert status == expected_status, f"Expected HTTP status code 400, got {status}"


def test_bad_uuid():
    data = {"items": [
        {
            "type": "CATEGORY",
            "name": "Товары",
            "id": "fake-uuid-asdasd",
        }
    ],
        "updateDate": "2022-02-01T12:00:00.000Z"
    }
    import_request(data, 400)
    print("Test bad_uuid passed.")


def test_null_name():
    data = {"items": [
        {
            "type": "CATEGORY",
            "name": None,
            "id": str(uuid.uuid4()),
        }
    ],
        "updateDate": "2022-02-01T12:00:00.000Z"
    }
    import_request(data, 400)
    print("Test null_name passed.")


def test_bad_type():
    data = {"items": [
        {
            "type": "CATEGORIES",
            "name": '',
            "id": str(uuid.uuid4()),
        }
    ],
        "updateDate": "2022-02-01T12:00:00.000Z"
    }
    import_request(data, 400)
    print("Test bad_type passed.")


def test_bad_date():
    data = {"items": [],
            "updateDate": "2022-02-01 12:00:00.001Z"
            }
    import_request(data, 400)
    print("Test bad_date passed.")


def test_offer_has_bad_price():
    # offer has no price
    data = {"items": [
        {
            "type": "OFFER",
            "name": '',
            "id": str(uuid.uuid4()),
        }
    ],
        "updateDate": "2022-02-01T12:00:00.001Z"
    }
    import_request(data, 400)
    # offer's price is None
    data['items'][0]['price'] = None
    import_request(data, 400)
    # offer's price < 0
    data['items'][0]['price'] = -1
    import_request(data, 400)
    # offer's price is float
    data['items'][0]['price'] = 1.2
    import_request(data, 400)
    print("Test offer_has_bad_price passed.")


def test_category_has_price():
    data = {"items": [
        {
            "type": "CATEGORY",
            "name": '',
            "id": str(uuid.uuid4()),
            'price': 0
        }
    ],
        "updateDate": "2022-02-01T12:00:00.001Z"
    }
    import_request(data, 400)
    print("Test category_has_price passed.")


def test_bad_parent_id():
    parent_id = str(uuid.uuid4())
    # parent is an offer
    data = {"items": [
        {
            "type": "OFFER",
            "name": 'child',
            "id": str(uuid.uuid4()),
            'price': 0,
            'parentId': parent_id
        },
        {
            "type": "OFFER",
            "name": 'parent',
            "id": parent_id,
            'price': 0
        }
    ],
        "updateDate": "2022-02-01T12:00:00.001Z"
    }
    import_request(data, 400)
    # no such parentId in database or in import
    data['items'][0]['parentId'] = str(uuid.uuid4())
    import_request(data, 400)
    print("Test bad_parent_id passed.")


def test_two_same_ids():
    item_id = str(uuid.uuid4())
    data = {"items": [
        {
            "type": "OFFER",
            "name": 'child',
            "id": item_id,
            'price': 0,
        },
        {
            "type": "OFFER",
            "name": 'parent',
            "id": item_id,
            'price': 0
        }
    ],
        "updateDate": "2022-02-01T12:00:00.001Z"
    }
    import_request(data, 400)
    print("Test two same ids passed.")


def test_try_change_type():
    item_id = str(uuid.uuid4())
    data = {"items": [
        {
            "type": "OFFER",
            "name": 'child',
            "id": item_id,
            'price': 0,
        },
    ],
        "updateDate": "2022-02-01T12:00:00.001Z"
    }
    status, _ = request("/imports", method="POST", data=data)
    data = {"items": [
        {
            "type": "CATEGORY",
            "name": 'child',
            "id": item_id,
        },
    ],
        "updateDate": "2022-02-01T12:00:00.001Z"
    }
    try:
        import_request(data, 400)
    finally:
        status, _ = request(f"/delete/{item_id}", method="DELETE")
        assert status == 200, f"Expected HTTP status code 200, got {status}"
    print('Test changing type passed.')


def test_bad_id_delete_request():
    item_id = str(uuid.uuid4())
    status, _ = request(f"/delete/{item_id}", method="DELETE")
    assert status == 404, f"Expected HTTP status code 404, got {status}"

    item_id = '1'
    status, _ = request(f"/delete/{item_id}", method="DELETE")
    assert status == 400, f"Expected HTTP status code 400, got {status}"
    print('Test bad id in /delete request passed.')


def test_bad_id_nodes_request():
    item_id = str(uuid.uuid4())
    status, _ = request(f"/nodes/{item_id}", method="GET")
    assert status == 404, f"Expected HTTP status code 404, got {status}"

    item_id = '1'
    status, _ = request(f"/nodes/{item_id}", method="GET")
    assert status == 400, f"Expected HTTP status code 400, got {status}"
    print('Test bad id in /nodes request passed.')


def test_bad_date_sales_request():
    params = urllib.parse.urlencode({
        "date": "2022-02-04 00:00:00.000Z"
    })
    status, response = request(f"/sales?{params}", json_response=True)
    assert status == 400, f"Expected HTTP status code 400, got {status}"

    params = urllib.parse.urlencode({
        "date": "2022-02-04T00:00:00.000+00:00"
    })
    status, response = request(f"/sales?{params}", json_response=True)
    assert status == 400, f"Expected HTTP status code 400, got {status}"
    print('Test bad date in /sales request passed.')


def test_bad_id_statistic_request():
    item_id = str(uuid.uuid4())
    params = urllib.parse.urlencode({
        "dateStart": "2022-02-01T00:00:00.000Z",
        "dateEnd": "2022-02-03T00:00:00.000Z"
    })
    status, response = request(
        f"/node/{item_id}/statistic?{params}", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"

    item_id = '1'
    status, response = request(
        f"/node/{item_id}/statistic?{params}", json_response=True)
    assert status == 400, f"Expected HTTP status code 400, got {status}"

    print('Test bad id in /statistic request passed.')


def test_bad_date_statistic_request():
    item_id = str(uuid.uuid4())
    # Wrong format
    date_variants = ["2022-02-01 00:00:00.000Z", "2022-02-03T00:00:00.000+00:00"]
    for date_variant in date_variants:
        params = urllib.parse.urlencode({
            "dateStart": date_variant,
        })
        status, response = request(
            f"/node/{item_id}/statistic?{params}", json_response=True)
        assert status == 400, f"Expected HTTP status code 400, got {status}"

        params = urllib.parse.urlencode({
            "dateEnd": date_variant
        })
        status, response = request(
            f"/node/{item_id}/statistic?{params}", json_response=True)
        assert status == 400, f"Expected HTTP status code 400, got {status}"

    # Wrong format
    params = urllib.parse.urlencode({
        "dateStart": "2022-02-01 00:00:00.000Z",
        "dateEnd": "2022-02-03T00:00:00.000+00:00"
    })
    status, response = request(
        f"/node/{item_id}/statistic?{params}", json_response=True)
    assert status == 400, f"Expected HTTP status code 400, got {status}"

    # dateEnd < dateStart
    params = urllib.parse.urlencode({
        "dateStart": "2022-02-01T01:00:00.000Z",
        "dateEnd": "2022-02-01T00:00:00.000Z"
    })
    status, response = request(
        f"/node/{item_id}/statistic?{params}", json_response=True)
    assert status == 400, f"Expected HTTP status code 400, got {status}"
    print('Test bad date in /statistic request passed.')


def test_all_validators():
    test_bad_uuid()
    test_null_name()
    test_bad_type()
    test_bad_date()
    test_offer_has_bad_price()
    test_category_has_price()
    test_bad_parent_id()
    test_two_same_ids()
    test_try_change_type()
    test_bad_id_delete_request()
    test_bad_id_nodes_request()
    test_bad_date_sales_request()
    test_bad_id_statistic_request()
    test_bad_date_statistic_request()


if __name__ == '__main__':
    test_all_validators()
