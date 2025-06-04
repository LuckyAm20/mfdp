import pytest

NYC_FREE_URL = '/api/v1/prediction/nyc_free'
NYC_COST_URL = '/api/v1/prediction/nyc_cost'
HISTORY_URL = '/api/v1/prediction/history'
GET_URL_BASE = '/api/v1/prediction'

AUTH_REGISTER = '/api/v1/auth/register'
AUTH_LOGIN = '/api/v1/auth/login'


@pytest.fixture
def auth_headers_with_balance(client):
    client.post(AUTH_REGISTER, json={'username': 'preduser', 'password': 'pw'})
    resp = client.post(AUTH_LOGIN, json={'username': 'preduser', 'password': 'pw'})
    token = resp.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    client.post('/api/v1/balance/top_up', json={'amount': 1000}, headers=headers)
    return headers


def test_prediction_history_and_get_by_id(db_session, client, auth_headers_with_balance, monkeypatch):
    from services.user_manager import UserManager

    token = auth_headers_with_balance['Authorization'].split()[1]
    user_manager = UserManager(db_session)
    user = user_manager.authenticate('preduser', 'pw')
    user_manager.user = user
    for idx in range(3):
        user_manager.prediction.create_prediction(
            city='NYC',
            district=idx,
            model='lstm',
            cost=0,
            hour=1
        )

    resp_hist = client.post(HISTORY_URL, json={}, headers=auth_headers_with_balance)
    assert resp_hist.status_code == 200
    history = resp_hist.json()['history']
    assert len(history) == 3

    first_id = history[0]['id']
    resp_get = client.get(f'{GET_URL_BASE}/{first_id}', headers=auth_headers_with_balance)
    assert resp_get.status_code == 200
    pred_data = resp_get.json()
    assert pred_data['id'] == first_id
    assert pred_data['city'] == 'NYC'

    resp_404 = client.get(f'{GET_URL_BASE}/9999', headers=auth_headers_with_balance)
    assert resp_404.status_code == 404
