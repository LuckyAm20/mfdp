import pytest

TOP_UP_URL = '/api/v1/balance/top_up'
PURCHASE_URL = '/api/v1/balance/purchase'
HISTORY_URL = '/api/v1/balance/history'
AUTH_REGISTER = '/api/v1/auth/register'
AUTH_LOGIN = '/api/v1/auth/login'


@pytest.fixture
def auth_headers(client):
    client.post(AUTH_REGISTER, json={'username': 'baluser', 'password': 'pw'})
    resp = client.post(AUTH_LOGIN, json={'username': 'baluser', 'password': 'pw'})
    token = resp.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def test_top_up_balance_success(client, auth_headers):
    payload = {'amount': 100}
    resp = client.post(TOP_UP_URL, json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data['amount'] == 100

    bad_resp = client.post(TOP_UP_URL, json={'amount': -50}, headers=auth_headers)
    assert bad_resp.status_code == 400
    assert 'detail' in bad_resp.json()


def test_purchase_status_and_history(client, auth_headers):
    client.post(TOP_UP_URL, json={'amount': 300}, headers=auth_headers)

    payload = {'status': 'silver'}
    resp = client.post(PURCHASE_URL, json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'silver'
    assert 'status_date_end' in data
    assert data['remaining_balance'] < 300

    hist_resp = client.post(HISTORY_URL, json={}, headers=auth_headers)
    assert hist_resp.status_code == 200
    history = hist_resp.json()['history']

    assert len(history) == 2
    amounts = [item['amount'] for item in history]
    assert 300 in amounts
    assert any(a < 0 for a in amounts)


def test_purchase_status_insufficient(client, auth_headers):
    resp = client.post(PURCHASE_URL, json={'status': 'diamond'}, headers=auth_headers)
    assert resp.status_code == 400
    assert 'detail' in resp.json()
