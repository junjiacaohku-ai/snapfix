from io import BytesIO
from types import SimpleNamespace
import base64

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image
import pytest

from ui_api import install_ui_api, UiStore, LEARNING


@pytest.fixture
def client(tmp_path):
    app = FastAPI()
    install_ui_api(app, lambda: SimpleNamespace(path=tmp_path/'ui.db'))
    with TestClient(app) as client:
        yield client


def image():
    output = BytesIO()
    Image.new('RGB',(128,128),(90,130,180)).save(output,format='PNG')
    return output.getvalue()


def create(client, scenario='e24'):
    result=client.post('/api/fe2/demo',json={'scenario':scenario})
    assert result.status_code==200, result.text
    return result.json()


def test_regular_photo_never_filename_routes_to_demo(client):
    result=client.post('/api/fe2/diagnose/photo',files={'file':('microwave_e24.png',image(),'image/png')})
    assert result.status_code==200
    s=result.json()
    assert s['mode']=='live' and s['model'] is None
    assert s['revisions'][0]['explanation']==LEARNING
    assert s['revisions'][0]['steps']==[]
    assert s['primary_image'].startswith('data:image/png;base64,')
    assert len(client.get('/api/fe2/sessions').json())==1
    assert client.get('/api/fe2/sessions?mode=demo').json()==[]


def test_e24_preview_uses_original_four_step_case(client):
    session=create(client)
    assert len(session['revisions'][0]['steps'])==4
    assert not session['revisions'][0]['is_high_risk']
    assert session['revisions'][0]['suggestion']=='self_check'
    assert 'SMI46MS00E' in session['model']


def test_invalid_photo_and_empty_inputs_do_not_create_records(client):
    assert client.post('/api/fe2/diagnose/photo',files={'file':('fake.png',b'not an image','image/png')}).status_code==422
    assert client.post('/api/fe2/diagnose',json={}).status_code==422
    assert client.post('/api/fe2/diagnose/photo',files={'file':('big.png',b'x'*(5*1024*1024+1),'image/png')}).status_code==413
    assert client.get('/api/fe2/sessions').json()==[]


@pytest.mark.parametrize('scenario',['e24','router','billy','microwave'])
def test_demo_scenarios_explicit_and_isolated(client,scenario):
    a=create(client,scenario);b=create(client,scenario)
    assert a['id']!=b['id'] and a['mode']=='demo'
    assert len(client.get('/api/fe2/sessions?mode=demo').json())==2
    assert client.get('/api/fe2/sessions').json()==[]
    if scenario=='microwave':
        assert a['category']=='微波炉' and a['revisions'][0]['is_high_risk']
        assert a['revisions'][0]['steps']==[]


def test_feedback_reports_status_survive_reopen_and_delete(client):
    s=create(client);sid=s['id'];path='/api/fe2/sessions/'+sid
    steps=s['revisions'][0]['steps']
    for step,feedback in zip(steps,['done','not_useful','skipped']):
        response=client.post(path+'/steps/'+step['id']+'/feedback',json={'feedback':feedback})
        assert response.status_code==200
    draft='师傅您好，请检查，预约时间另议。'
    for who in ['landlord','technician','after_sales']:
        for lang in ['zh','en']:
            assert client.post(path+f'/reports/{who}/{lang}').status_code==200
            assert client.put(path+f'/reports/{who}/{lang}',json={'content':draft+who+lang}).status_code==200
    assert client.get(path).json()['status']=='investigating'
    assert client.patch(path+'/status',json={'status':'awaiting_repair'}).status_code==200
    reopened=UiStore(client.app.state.fe2_store.path).get(sid)
    assert reopened['revisions'][0]['steps'][2]['feedback']=='skipped'
    assert reopened['reports']['technician_en']['content']==draft+'technicianen'
    assert reopened['status']=='awaiting_repair'
    assert client.delete(path).status_code==200
    assert client.get(path).status_code==404
    assert client.put(path+'/reports/landlord/zh',json={'content':draft}).status_code==404


def test_follow_up_retains_feedback_and_photo_without_fabricating_steps(client):
    s=create(client);path='/api/fe2/sessions/'+s['id']
    first=s['revisions'][0]['steps'][0]
    client.post(path+'/steps/'+first['id']+'/feedback',json={'feedback':'not_useful'})
    data_url='data:image/png;base64,'+base64.b64encode(image()).decode()
    updated=client.post(path+'/follow-ups',json={'note':'仍有异响','photoUrl':data_url}).json()
    assert len(updated['revisions'])==2
    assert updated['revisions'][0]['steps'][0]['feedback']=='not_useful'
    assert updated['revisions'][1]['supplementary_image']==data_url
    assert updated['revisions'][1]['steps']==[]
    report=client.post(path+'/reports/technician/zh').json()['content']
    assert first['title'] in report and '未改善' in report and '仍有异响' in report


def test_safety_persists_across_follow_up_and_no_feedback_allowed(client):
    s=create(client,'microwave');path='/api/fe2/sessions/'+s['id']
    assert client.post(path+'/steps/fake/feedback',json={'feedback':'done'}).status_code==409
    result=client.post(path+'/follow-ups',json={'note':'我想拆开看看'}).json()
    assert result['revisions'][1]['is_high_risk'] and result['revisions'][1]['steps']==[]


def test_cases_readonly_and_same_code_not_proof_of_compatibility(client):
    cases=client.get('/api/fe2/cases?q=e24').json();assert cases
    assert client.get('/api/fe2/sessions').json()==[]
    check=client.post('/api/fe2/cases/'+cases[0]['id']+'/checks',json={'errorCode':'E24'}).json()
    assert check['confidence']=='low' and check['isMatch'] is False
    assert client.post('/api/fe2/cases/missing/checks',json={}).status_code==404


def test_validation_no_silent_state_changes(client):
    s=create(client);path='/api/fe2/sessions/'+s['id']
    assert client.patch(path+'/status',json={'status':'sent'}).status_code==422
    assert client.post(path+'/follow-ups',json={'note':' '}).status_code==422
    assert client.post(path+'/follow-ups',json={'photoUrl':'https://example.com/false.png'}).status_code==422
    assert client.put(path+'/reports/landlord/zh',json={'content':' '}).status_code==422
    assert client.get(path).json()['status']=='investigating'


def test_english_demo_descriptions_are_translated_without_api_key(client):
    s=create(client);path='/api/fe2/sessions/'+s['id'];step=s['revisions'][0]['steps'][0]
    client.post(path+'/steps/'+step['id']+'/feedback',json={'feedback':'done'})
    text=client.post(path+'/reports/technician/en').json()['content']
    assert 'water was not draining properly' in text
    assert 'Unplug the dishwasher' in text
    assert 'Original text (not translated)' not in text


def test_v1_mock_results_cannot_enter_the_normal_workflow(client):
    assert client.post('/api/fe2/import/legacy-mock-id').status_code==409
    assert client.get('/api/fe2/sessions').json()==[]


def test_reset_template_does_not_overwrite_a_saved_draft(client):
    session=create(client);path='/api/fe2/sessions/'+session['id']+'/reports/landlord/zh'
    client.put(path,json={'content':'我的已保存修改'})
    template=client.get(path+'/template').json()['content']
    assert template!='我的已保存修改'
    assert client.get('/api/fe2/sessions/'+session['id']).json()['reports']['landlord_zh']['content']=='我的已保存修改'


def test_v1_bridge_keeps_session_and_does_not_reset_saved_work(tmp_path):
    class LegacyStore:
        path=tmp_path/'bridge.db'
        def __getitem__(self, sid):
            return SimpleNamespace(model_dump=lambda:dict(id=sid,brand='Test',model='ABC-1',device_category='router',
                error_code=None,decision='diy',decision_reason='Check external cables.',safety_refused=False,
                created_at='2026-11-05T00:00:00Z',steps=[dict(id='step-1',idx=1,content='Check cable.',
                    citation_manual='User guide',citation_section='Connections',feedback=None)]))
    app=FastAPI();install_ui_api(app,lambda:LegacyStore(),lambda:False)
    with TestClient(app) as client:
        imported=client.post('/api/fe2/import/original').json();path='/api/fe2/sessions/'+imported['id']
        assert imported['mode']=='live' and imported['model']=='ABC-1'
        assert imported['revisions'][0]['steps'][0]['source']['snippet'] is None
        client.patch(path+'/status',json={'status':'resolved'})
        assert client.post('/api/fe2/import/original').json()['status']=='resolved'
