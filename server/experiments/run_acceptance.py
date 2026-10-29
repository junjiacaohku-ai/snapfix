"""Record bounded mock API responses and latency; never claim live vision or UI coverage."""
import json
import sys
import time
import os
from tempfile import TemporaryDirectory
from pathlib import Path
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
_temp_database = TemporaryDirectory(prefix='snapfix-acceptance-')
os.environ['SNAPFIX_DB'] = str(Path(_temp_database.name)/'acceptance.db')
from main import app, DB

root=Path(__file__).resolve().parents[1]
client=TestClient(app)
DB.clear()
results=[]
for scenario,name in [('S1','router.jpg'),('S2','e24.jpg'),('S3','billy.jpg'),('S4','microwave.jpg'),('S5','dark.jpg'),('S6','router.jpg')]:
    start=time.perf_counter()
    if scenario=='S2':
        response=client.post('/api/diagnose/manual',json={'brand':'博世','error_code':'E:24'})
    else:
        source_name={'S1':'public-01.jpg','S3':'public-03.jpg','S4':'public-05.jpg','S5':'public-09.jpg','S6':'public-01.jpg'}[scenario]
        picture=(root.parent/'docs/demo-assets/public'/source_name).read_bytes()
        response=client.post('/api/analyze/image',files={'file':(name,picture,'image/jpeg')})
    data=response.json()
    extra={}
    if scenario=='S6' and response.status_code==200:
        url=f'/api/sessions/{data["id"]}'
        client.post(f'{url}/steps/{data["steps"][0]["id"]}/feedback',json={'feedback':'done'})
        extra={lang:client.post(url+'/report',json={'lang':lang}).json() for lang in ['zh','en']}
    expected=422 if scenario=='S5' else 200
    checks={'http_status':response.status_code==expected}
    if scenario=='S1':
        checks['router_steps']=data.get('brand')=='TP-Link' and bool(data.get('steps'))
    elif scenario=='S2':
        checks['model_uncertainty']=data.get('model') is None
        checks['e24_referral']=data.get('device_category')=='dishwasher' and data.get('decision')=='professional' and data.get('error_code')=='E24'
    elif scenario=='S3':
        checks['billy_guidance']=data.get('brand')=='IKEA' and '防倾倒' in str(data.get('steps'))
    elif scenario=='S4':
        checks['refusal']=data.get('safety_refused') is True and data.get('steps')==[]
    elif scenario=='S5':
        checks['retake']='重拍' in data.get('detail','')
    elif scenario=='S6':
        checks['reports']=('步骤1' in extra.get('zh',{}).get('content','') and
                           'step 1' in extra.get('en',{}).get('content','') and
                           'attach a photo' in extra.get('en',{}).get('content',''))
    results.append(dict(scenario=scenario,input='manual Bosch E:24' if scenario=='S2' else name,status=response.status_code,
                        checks=checks,passed=all(checks.values()),elapsed_ms=round((time.perf_counter()-start)*1000,2),
                        response=data,reports=extra))
(root/'experiments/acceptance-results.json').write_text(json.dumps(dict(scope='Real image quality and safety checks; offline diagnosis selected by filename; no live vision or mobile UI test',cases=results),ensure_ascii=False,indent=2)+'\n')
print(f'{sum(r["passed"] for r in results)}/6 mock response checks completed')
if not all(r['passed'] for r in results):
    raise SystemExit(1)
