from fastapi.testclient import TestClient
from main import app, DB
from pathlib import Path

client = TestClient(app)


def image(name):
    filename = 'public-09.jpg' if name == 'dark.jpg' else 'public-01.jpg'
    data = (Path(__file__).resolve().parents[2] / 'docs/demo-assets/public' / filename).read_bytes()
    return client.post('/api/analyze/image', files={'file': (name, data, 'image/jpeg')})


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


def test_manual_hazards_are_refused_before_diagnosis():
    for text in ['电磁炉内部维修', '锅炉压力阀拆卸', '插座烧焦冒烟', '烤箱内部电线维修']:
        response = client.post('/api/diagnose/manual', json={'brand':'unknown','error_code':text})
        assert response.status_code == 200
        assert response.json()['safety_refused'] is True
        assert response.json()['steps'] == []


def test_image_quality_uses_content_not_filename():
    assets = Path(__file__).resolve().parents[2] / 'docs/demo-assets/public'
    response = client.post('/api/analyze/image', files={'file':('router.jpg', (assets/'public-09.jpg').read_bytes(), 'image/jpeg')})
    assert response.status_code == 422 and '过暗' in response.json()['detail']
    invalid = client.post('/api/analyze/image', files={'file':('router.jpg', b'not an image', 'image/jpeg')})
    assert invalid.status_code == 422 and '无法读取' in invalid.json()['detail']


def test_invalid_feedback_and_language_are_rejected():
    session = image('router.jpg').json()
    url = f'/api/sessions/{session["id"]}'
    feedback = client.post(url+'/steps/'+session['steps'][0]['id']+'/feedback', json={'feedback':'invented'})
    assert feedback.status_code == 422
    assert client.get(url).json()['steps'][0]['feedback'] is None
    assert client.post(url+'/report', json={'lang':'invented'}).status_code == 422
