from fastapi.testclient import TestClient
from main import app, DB

client = TestClient(app)


def image(name):
    return client.post('/api/analyze/image', files={'file': (name, b'mock', 'image/jpeg')})


def test_six_scenarios():
    DB.clear()
    router = image('router.jpg').json()
    assert router['brand'] == 'TP-Link' and router['steps']
    manual = client.post('/api/diagnose/manual', json={'brand': '博世', 'error_code': ' e24 '}).json()
    assert manual['error_code'] == 'E24' and manual['device_category'] == 'dishwasher'
    assert manual['decision'] == 'professional'
    for code in ['E:24', ' E：24 ', 'e24']:
        normalized = client.post('/api/diagnose/manual', json={'brand': ' Bosch ', 'error_code': code})
        assert normalized.status_code == 200 and normalized.json()['error_code'] == 'E24'
    billy = image('billy.jpg').json()
    assert billy['brand'] == 'IKEA' and '工具' in billy['decision_reason']
    refused = image('microwave.jpg').json()
    assert refused['safety_refused'] and refused['steps'] == []
    assert image('dark.jpg').status_code == 422
    session = image('report.jpg').json()
    step = session['steps'][0]['id']
    url = f'/api/sessions/{session["id"]}'
    assert client.post(f'{url}/steps/{step}/feedback', json={'feedback': 'done'}).status_code == 200
    zh = client.post(url + '/report', json={'lang': 'zh'}).json()['content']
    en = client.post(url + '/report', json={'lang': 'en'}).json()['content']
    assert '步骤1' in zh and 'step 1' in en
    assert '照片' in zh and 'photo' in en


def test_unknown_manual_does_not_invent_e24():
    assert client.post('/api/diagnose/manual', json={'brand': 'unknown', 'error_code': 'X'}).status_code == 404


def test_health_and_session_lifecycle():
    assert client.get('/api/health').status_code == 200
    session = image('router.jpg').json()
    url = '/api/sessions/' + session['id']
    assert client.get(url).status_code == 200
    assert client.delete(url).status_code == 200
    assert client.get(url).status_code == 404


def test_unknown_images_do_not_invent_diagnosis():
    assert image('random.jpg').status_code == 422


def test_reports_do_not_claim_nonexistent_attachment():
    session = image('report.jpg').json()
    result = client.post(f'/api/sessions/{session["id"]}/report', json={'lang':'en'}).json()
    assert 'Photos attached' not in result['content']
    assert 'attach a photo' in result['content']
