REGISTER_URL = '/api/v1/auth/register'
LOGIN_URL = '/api/v1/auth/login'
ME_URL = '/api/v1/auth/me'


def test_register_and_login_and_me(client):
    payload = {'username': 'testuser', 'password': 'secret'}
    resp = client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert 'access_token' in data
    assert data['token_type'] == 'bearer'
    assert 'bot_token' in data

    resp_login = client.post(LOGIN_URL, json=payload)
    assert resp_login.status_code == 200
    login_data = resp_login.json()
    assert 'access_token' in login_data

    token = login_data['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    resp_me = client.get(ME_URL, headers=headers)
    assert resp_me.status_code == 200
    me_data = resp_me.json()
    assert me_data['username'] == 'testuser'
    assert me_data['balance'] == 0
    assert me_data['status'] == 'bronze'
    assert me_data['status_date_end'] is None


def test_login_with_invalid_credentials(client):
    client.post(REGISTER_URL, json={'username': 'u2', 'password': 'p2'})

    resp = client.post(LOGIN_URL, json={'username': 'u2', 'password': 'wrong'})
    assert resp.status_code == 401
    assert 'detail' in resp.json()
