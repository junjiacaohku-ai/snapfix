"""FE-2 mobile/web contract. Additive to the team's v1 API.

UI revisions and recipient drafts use their own table, leaving BE-2 tables intact.
Only an explicit demo request may load the AI Studio scenario fixtures.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import copy
import json
import sqlite3
import uuid

from fastapi import HTTPException, UploadFile
from pydantic import BaseModel, Field

LEARNING = "还在学习该维修技能中！"
MAX_IMAGE = 5 * 1024 * 1024

# Reviewed offline translations for the explicit classroom fixtures only.
DEMO_EN = {
    '洗碗机工作中断，报警提示 E24 错误代码，腔体底部排水不畅。': 'The dishwasher stopped with error E24 and water was not draining properly.',
    '洗碗程序运行到最后15分钟时报警停机，面板频繁显示 E24 错误代码，腔体底部积水未排出。': 'The dishwasher stopped with error E24 during the final 15 minutes of its program and water was not draining properly.',
    '拔掉电源断电并吸出底部积水': 'Unplug the dishwasher and remove standing water from the bottom',
    '逆时针旋转取出圆柱微孔滤网': 'Turn anticlockwise to remove the cylindrical fine filter',
    '打开排水泵白色护盖，检查叶轮转动': 'Open the white drain-pump cover and check impeller movement',
    '重新卡紧白色护盖（听到咔哒声）并复位滤网': 'Secure the white cover until it clicks and reinstall the filter',
    '拔掉洗碗机主电源插头': 'Unplug the dishwasher from the mains power supply',
    '逆时针拧出滤网组件并刷洗': 'Turn the filter assembly anticlockwise to remove it and brush it clean',
    '检查左侧排水泵白色护盖与叶轮': 'Check the white drain-pump cover and impeller on the left',
    '路由器外部检查': 'External router checks',
    'IKEA BILLY 组装检查': 'IKEA BILLY assembly checks',
    '微波炉加热时打火并有异响': 'The microwave sparks and makes unusual noises when heating.',
    '检查外置电源与网线是否插牢，不拆机。': 'Check the external power and network cable connections without opening the device.',
    '按设备用户指南重启，等待启动完成；不要恢复出厂设置。': 'Restart according to the user guide and wait for startup; do not perform a factory reset.',
    '如仍无法联网，记录指示灯状态并联系网络运营商。': 'If the connection is still unavailable, record the indicator-light status and contact the network provider.',
    '先确认实际型号，阅读并遵循该型号说明书的每一步要求。': 'Confirm the exact model and follow every step in its instructions.',
    '使用说明书要求的防倾倒连接件；墙体固定螺钉和膨胀件须适配墙体。': 'Use the specified anti-tip fittings, with screws and plugs suitable for the wall.',
    '无法确定墙体材料或固定方法时，请寻求专业人员建议。': 'Seek professional advice if the wall material or fixing method is uncertain.',
}


def now():
    return datetime.now(timezone.utc).isoformat()


class DiagnoseInput(BaseModel):
    brand: str = Field(default="", max_length=100)
    category: str = Field(default="", max_length=100)
    model: str = Field(default="", max_length=100)
    error_code: str = Field(default="", max_length=50)
    note: str = Field(default="", max_length=3000)


class DemoInput(BaseModel):
    scenario: Literal['e24', 'router', 'billy', 'microwave'] = 'e24'


class FeedbackInput(BaseModel):
    feedback: Literal['done', 'not_useful', 'skipped']


class StatusInput(BaseModel):
    status: Literal['investigating', 'awaiting_repair', 'resolved']


class FollowUpInput(BaseModel):
    note: str = Field(default='', max_length=3000)
    photoUrl: str | None = Field(default=None, max_length=7_100_000)


class DraftInput(BaseModel):
    content: str = Field(min_length=1, max_length=20000)


class CheckInput(BaseModel):
    errorCode: str = Field(default='', max_length=50)
    brand: str = Field(default='', max_length=100)
    model: str = Field(default='', max_length=100)


def validate_image(data_url):
    """Validate attachments as pixels, not just a user supplied data URL."""
    import base64
    from io import BytesIO
    from PIL import Image, UnidentifiedImageError
    if not data_url:
        return
    try:
        if not data_url.startswith(('data:image/jpeg;base64,', 'data:image/png;base64,', 'data:image/webp;base64,')):
            raise ValueError()
        raw = base64.b64decode(data_url.split(',', 1)[1], validate=True)
        if len(raw) > MAX_IMAGE:
            raise ValueError()
        with Image.open(BytesIO(raw)) as image:
            image.verify()
    except (ValueError, UnidentifiedImageError, OSError):
        raise HTTPException(422, '请选择不超过 5MB 的有效 JPG、PNG 或 WebP 照片。')


def pending(data, image=None):
    stamp = now()
    danger = any(word in (data.category + data.note).lower() for word in ('微波炉', '高压', '燃气', 'microwave', 'gas leak'))
    return dict(id=str(uuid.uuid4()), created_at=stamp, updated_at=stamp,
        device_name=' '.join(filter(None, [data.brand, data.category])) or '设备待确认',
        brand=data.brand or None, category=data.category or '待确认设备', model=data.model or None,
        error_code=data.error_code or None, primary_image=image, status='investigating',
        current_revision_index=0, reports={}, mode='live', diagnosis_status='unsupported',
        revisions=[dict(revision_id=str(uuid.uuid4()), revision_number=1, created_at=stamp,
            problem_summary=data.note or (f'错误码：{data.error_code}' if data.error_code else '已提交设备照片'),
            explanation=LEARNING, suggestion='contact_professional', confidence='low',
            is_high_risk=danger, high_risk_reason='请勿自行拆解高风险设备，请联系专业人员。' if danger else None,
            steps=[])])


class UiStore:
    def __init__(self, path):
        self.path = path
        with self.connection() as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS fe2_sessions (id TEXT PRIMARY KEY, mode TEXT NOT NULL, data TEXT NOT NULL, updated_at TEXT NOT NULL)')

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            yield db
        finally:
            db.close()

    def load(self, db, sid):
        row = db.execute('SELECT data FROM fe2_sessions WHERE id=?', (sid,)).fetchone()
        if row is None:
            raise HTTPException(404, '维修记录不存在或已删除。')
        return json.loads(row['data'])

    def write(self, db, session):
        db.execute('INSERT INTO fe2_sessions VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data, updated_at=excluded.updated_at',
            (session['id'], session['mode'], json.dumps(session, ensure_ascii=False), session['updated_at']))

    def create(self, session):
        with self.connection() as db, db:
            self.write(db, session)
        return session

    def get(self, sid):
        with self.connection() as db:
            return self.load(db, sid)

    def update(self, sid, change):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                session = self.load(db, sid)
                change(session)
                session['updated_at'] = now()
                self.write(db, session)
                db.commit()
                return session
            except Exception:
                db.rollback()
                raise


def report_text(session, recipient, lang):
    revision = session['revisions'][session['current_revision_index']]
    attempts = [s for rev in session['revisions'] for s in rev['steps'] if s.get('feedback') in ('done', 'not_useful')]
    # Model output and Chinese step text are not silently labelled a translation.
    if lang == 'en':
        greet = {'landlord': 'Dear Landlord,', 'technician': 'Hello,', 'after_sales': 'Dear After-Sales Support,'}[recipient]
        def english(text):
            if session['mode'] == 'demo' and text in DEMO_EN:
                return DEMO_EN[text]
            if any('\u4e00' <= char <= '\u9fff' for char in text):
                return 'Original text (not translated): ' + text
            return text
        if session['mode'] == 'live' and len(session['revisions']) == 1 and session.get('error_code'):
            issue = 'Reported error code: ' + session['error_code']
        elif session['mode'] == 'live' and len(session['revisions']) == 1 and session.get('primary_image'):
            issue = 'A device photo has been submitted. Identification and diagnosis are not yet available.'
        else:
            issue = english(revision['problem_summary'])
        actions = '\n'.join(f"- Step {s['step_number']}: {'performed' if s['feedback'] == 'done' else 'attempted, no improvement'}; {english(s['title'])}" for s in attempts) or '- None recorded'
        return f"{greet}\nRepair request\nBrand: {session.get('brand') or 'Not confirmed'}\nModel: {session.get('model') or 'Not confirmed'}\nError code: {session.get('error_code') or 'Not provided'}\nProblem description: {issue}\nTroubleshooting record:\n{actions}\nPlease advise on inspection and availability. Appointment time to be agreed.\nPlease attach actual device photos."
    greet = {'landlord': '房东您好，希望协助安排检查维修。', 'technician': '师傅您好，希望咨询设备检查维修。', 'after_sales': '售后您好，希望核对设备故障与服务安排。'}[recipient]
    actions = '\n'.join(f"- {s['title']}（{'已执行' if s['feedback'] == 'done' else '未改善'}）" for s in attempts) or '暂无已记录操作。'
    return f"{greet}\n设备：{session.get('brand') or '品牌待确认'} {session['category']}\n型号：{session.get('model') or '尚未确认'}\n错误码：{session.get('error_code') or '未提供'}\n问题描述：{revision['problem_summary']}\n已尝试操作：\n{actions}\n烦请提供建议或安排检查，预约时间由双方另行确认。\n发送时请另附实际设备照片。"


def install_ui_api(app, get_legacy_store, legacy_is_mock=lambda: True):
    store = UiStore(get_legacy_store().path)
    app.state.fe2_store = store
    fixtures = json.loads((Path(__file__).parent / 'data/ui_demo.json').read_text(encoding='utf-8'))

    @app.get('/api/fe2/capabilities')
    def capabilities():
        return {'real_vision_connected': False, 'unsupported_message': LEARNING,
                'persistence': 'sqlite', 'draft_recipients': ['landlord', 'technician', 'after_sales']}

    @app.get('/api/fe2/cases')
    def cases(q: str = '', brand: str = '', appliance: str = ''):
        result = fixtures['cases']
        for key, value in [('brand', brand), ('appliance', appliance)]:
            if value and value != '全部':
                result = [row for row in result if value.lower() in row[key].lower()]
        if q.strip():
            result = [row for row in result if q.lower().strip() in ' '.join(str(row.get(k, '')) for k in ['title','brand','appliance','error_code','problem_description']).lower()]
        return result

    @app.post('/api/fe2/cases/{case_id}/checks')
    def check(case_id: str, req: CheckInput):
        item = next((row for row in fixtures['cases'] if row['id'] == case_id), None)
        if not item:
            raise HTTPException(404, '案例不存在。')
        code_same = bool(req.errorCode) and req.errorCode.upper().strip() == (item.get('error_code') or '').upper()
        return dict(isMatch=False, confidence='low', matchedPoints=['错误码相同'] if code_same else [],
                    unmatchedPoints=['实际设备型号尚未核实'], advice='请核对实际品牌、完整型号和适用说明书。错误码相同不能单独确认适用。')

    @app.post('/api/fe2/diagnose')
    def diagnose(req: DiagnoseInput):
        if not any([req.error_code.strip(), req.note.strip()]):
            raise HTTPException(422, '请输入错误码或问题描述。')
        # This integrated snapshot has no live provider. Never route names/codes to demo.
        return store.create(pending(req))

    @app.post('/api/fe2/diagnose/photo')
    async def photo(file: UploadFile):
        import base64
        from io import BytesIO
        from PIL import Image, UnidentifiedImageError
        raw = await file.read(MAX_IMAGE + 1)
        await file.close()
        if len(raw) > MAX_IMAGE:
            raise HTTPException(413, '照片不能超过 5MB。')
        try:
            with Image.open(BytesIO(raw)) as image:
                fmt = image.format
                if fmt not in ('JPEG','PNG','WEBP'):
                    raise ValueError()
                image.verify()
        except (ValueError, UnidentifiedImageError, OSError):
            raise HTTPException(422, '请选择有效的 JPG、PNG 或 WebP 照片。')
        mime = {'JPEG':'jpeg','PNG':'png','WEBP':'webp'}[fmt]
        url = f'data:image/{mime};base64,' + base64.b64encode(raw).decode()
        return store.create(pending(DiagnoseInput(), url))

    @app.post('/api/fe2/demo')
    def demo(req: DemoInput):
        if req.scenario == 'e24':
            session = copy.deepcopy(fixtures['sessions'][0])
            original = next(row for row in fixtures['cases'] if row['id'] == 'case_bosch_e24')
            session.update(brand=original['brand'], model=original['model'], category=original['appliance'],
                error_code=original['error_code'], primary_image=original['image_url'])
            session['revisions'][0].update(problem_summary=original['problem_description'],
                explanation=original['cause_analysis'], suggestion='self_check', confidence='high',
                is_high_risk=False, steps=copy.deepcopy(original['steps']))
        elif req.scenario == 'microwave':
            session = pending(DiagnoseInput(category='微波炉', note='微波炉加热时打火并有异响'))
            session['device_name'] = '微波炉打火与异响'
            session['revisions'][0].update(explanation='微波炉内部有高压部件，请勿自行拆解。', is_high_risk=True,
                high_risk_reason='断电后高压电容仍可能储能，请联系专业人员。')
        else:
            legacy = next(row for row in json.loads((Path(__file__).parent / 'data/demo_sessions.json').read_text(encoding='utf-8')) if row['id'] == 'demo-' + req.scenario)
            session = pending(DiagnoseInput(category={'router':'路由器','billy':'家具'}[req.scenario]))
            session['device_name'] = {'router':'路由器外部检查','billy':'IKEA BILLY 组装检查'}[req.scenario]
            rev = session['revisions'][0]
            rev.update(problem_summary=session['device_name'], explanation=legacy['decision_reason'], suggestion='self_check',
                       steps=[dict(id=str(uuid.uuid4()), step_number=i+1, title=s['content'],description=s['content'],
                                   source=dict(manual_title=s['citation_manual'], chapter=s['citation_section'],is_verified=False)) for i,s in enumerate(legacy['steps'])])
        session.update(id=str(uuid.uuid4()), mode='demo', status='investigating', reports={}, diagnosis_status='demo', created_at=now(), updated_at=now())
        session['current_revision_index'] = 0
        session['revisions'] = session['revisions'][:1]
        for rev in session['revisions']:
            rev['revision_id'] = str(uuid.uuid4())
            if req.scenario == 'microwave':
                rev.update(is_high_risk=True, steps=[], suggestion='contact_professional')
            for step in rev['steps']:
                step['id'] = str(uuid.uuid4())
                step.pop('feedback', None)
                if step.get('source'):
                    step['source']['is_verified'] = False
        return store.create(session)

    @app.get('/api/fe2/sessions')
    def sessions(mode: Literal['live','demo'] = 'live'):
        with store.connection() as db:
            return [json.loads(row['data']) for row in db.execute('SELECT data FROM fe2_sessions WHERE mode=? ORDER BY updated_at DESC', (mode,))]

    @app.get('/api/fe2/sessions/{sid}')
    def get_session(sid: str):
        return store.get(sid)

    @app.post('/api/fe2/import/{legacy_id}')
    def import_legacy(legacy_id: str):
        # FE-1 can hand over a real v1 diagnosis without synthesizing a UI session.
        if legacy_is_mock():
            raise HTTPException(409, '当前诊断服务仍是预设模式，请从预览使用流程入口体验。')
        sid = 'legacy-' + legacy_id
        try:
            return store.get(sid)
        except HTTPException as exc:
            if exc.status_code != 404:
                raise
        try:
            data = get_legacy_store()[legacy_id].model_dump()
        except KeyError:
            raise HTTPException(404, '诊断记录不存在。')
        session = pending(DiagnoseInput(brand=data.get('brand') or '', model=data.get('model') or '',
            category=data['device_category'], error_code=data.get('error_code') or ''))
        session.update(id=sid, legacy_session_id=legacy_id, diagnosis_status='available', created_at=data['created_at'])
        rev = session['revisions'][0]
        refused = data.get('safety_refused') or data['decision'] == 'refused'
        rev.update(explanation=data['decision_reason'], is_high_risk=bool(refused), high_risk_reason=data['decision_reason'] if refused else None,
            suggestion={'diy':'self_check','landlord':'contact_landlord'}.get(data['decision'],'contact_professional'),
            problem_summary=data['decision_reason'], confidence='low' if not data.get('model') else 'medium',
            steps=[] if refused else [dict(id=row['id'],step_number=row['idx'],title=row['content'],description=row['content'],
                feedback=row.get('feedback'),source=dict(manual_title=row['citation_manual'],chapter=row['citation_section'],
                snippet=row.get('citation_text'),is_verified=False)) for row in data['steps']])
        return store.create(session)

    @app.delete('/api/fe2/sessions/{sid}')
    def delete_session(sid: str):
        with store.connection() as db, db:
            if not db.execute('DELETE FROM fe2_sessions WHERE id=?', (sid,)).rowcount:
                raise HTTPException(404, '维修记录不存在或已删除。')
        return {'deleted': True}

    @app.patch('/api/fe2/sessions/{sid}/status')
    def status(sid: str, req: StatusInput):
        return store.update(sid, lambda s: s.update(status=req.status))

    @app.post('/api/fe2/sessions/{sid}/steps/{step_id}/feedback')
    def feedback(sid: str, step_id: str, req: FeedbackInput):
        def change(session):
            rev = session['revisions'][session['current_revision_index']]
            if rev['is_high_risk']:
                raise HTTPException(409, '高风险问题不提供自行操作步骤。')
            step = next((s for s in rev['steps'] if s['id'] == step_id), None)
            if not step:
                raise HTTPException(404, '步骤不存在。')
            step.update(feedback=req.feedback, feedback_at=now())
        return store.update(sid, change)

    @app.post('/api/fe2/sessions/{sid}/follow-ups')
    def follow_up(sid: str, req: FollowUpInput):
        if not req.note.strip() and not req.photoUrl:
            raise HTTPException(422, '请补充照片或描述。')
        validate_image(req.photoUrl)
        def change(session):
            previous = session['revisions'][session['current_revision_index']]
            rev = dict(revision_id=str(uuid.uuid4()), revision_number=len(session['revisions'])+1,
                created_at=now(), problem_summary=req.note.strip() or '已补充照片', explanation=LEARNING,
                suggestion='contact_professional',confidence='low', is_high_risk=previous['is_high_risk'],
                high_risk_reason=previous.get('high_risk_reason'), steps=[], user_note=req.note,
                supplementary_image=req.photoUrl)
            session['revisions'].append(rev)
            session['current_revision_index'] = len(session['revisions'])-1
            session['diagnosis_status'] = 'unsupported'
            session['status'] = 'investigating'
        return store.update(sid, change)

    def report(session, recipient, lang, content):
        session['reports'][f'{recipient}_{lang}'] = dict(recipient_type=recipient, language=lang,
            title='报修说明', content=content, updated_at=now(), is_customized=True)

    @app.post('/api/fe2/sessions/{sid}/reports/{recipient}/{lang}')
    def generate(sid: str, recipient: Literal['landlord','technician','after_sales'], lang: Literal['zh','en']):
        def change(session):
            key = f'{recipient}_{lang}'
            if key not in session['reports']:
                report(session, recipient, lang, report_text(session, recipient, lang))
        return store.update(sid, change)['reports'][f'{recipient}_{lang}']

    @app.put('/api/fe2/sessions/{sid}/reports/{recipient}/{lang}')
    def save(sid: str, recipient: Literal['landlord','technician','after_sales'], lang: Literal['zh','en'], req: DraftInput):
        if not req.content.strip():
            raise HTTPException(422, '报修内容不能为空。')
        return store.update(sid, lambda s: report(s, recipient, lang, req.content))['reports'][f'{recipient}_{lang}']

    @app.get('/api/fe2/sessions/{sid}/reports/{recipient}/{lang}/template')
    def template(sid: str, recipient: Literal['landlord','technician','after_sales'], lang: Literal['zh','en']):
        return {'content': report_text(store.get(sid), recipient, lang)}
