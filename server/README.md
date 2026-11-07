# SnapFix Server · FastAPI 后端

本文描述三条后端分支集成后的实际行为。图片诊断目前仍是带质量门的离线场景；手动错误码检索、SQLite、反馈和报修使用真实实现。

## 1. 环境要求

- Python 3.11 或以上；已在 macOS、Python 3.14 复测，Windows 实机复测待完成。
- SQLite 使用 Python 标准库，无需安装数据库服务器。
- 首次安装依赖需要网络；安装后，检索、档案、图片 mock 和基础报修不需要 key。
- 英文步骤正文在线翻译是可选增强；无 key 或翻译失败仍生成基础英文报告。

## 2. 安装与启动

在 `server` 目录执行。

macOS：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
python -X utf8 corpus_store.py --database data/snapfix.db
python -m uvicorn main:app --reload
```

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
python -X utf8 corpus_store.py --database data/snapfix.db
python -m uvicorn main:app --reload
```

PowerShell 禁止激活脚本时，直接使用 `.\.venv\Scripts\python.exe` 替代 `python`。语料导入预期输出：

```json
{"manuals": 16, "chunks": 2032}
```

启动后打开：

- [Swagger UI](http://127.0.0.1:8000/docs)
- [健康接口](http://127.0.0.1:8000/api/health)

`GET /api/health` 当前返回 `mock: true`、`provider: "mock"`，因为真实图片识别尚未接入。该状态不代表可选报修翻译是否调用了 Gemini。

## 3. 数据库与语料

默认数据库为 `data/snapfix.db`，可通过 `SNAPFIX_DB` 改路径。语料导入和后端必须指向同一数据库；更新语料时先停止服务，导入后重启以刷新索引缓存。

| 表 | 用途 |
|---|---|
| `manuals` | 说明书名称、来源和设备类别 |
| `manual_chunks` | 切块正文及所属说明书 |
| `chunk_metadata` | 页码、品牌、来源等元数据 |
| `sessions` | 诊断记录、设备信息、决策和创建时间 |
| `steps` | 诊断步骤、引用和反馈 |
| `reports` | 报修语言、正文和关联诊断 |

`corpus_store.py` 读取 `data/manuals.json` 和 `data/chunks.json`。重复导入会更新本批手册并保留其他手册。诊断、反馈和报修草稿会保存；删除诊断会级联删除步骤和草稿。上传的原始照片不持久化，测试使用临时数据库。

## 4. API 行为

| 方法 | 路径 | 当前行为 |
|---|---|---|
| GET | `/api/health` | 图片诊断的 mock 状态 |
| POST | `/api/manuals/search` | BM25 候选片段、来源和加权分数 |
| POST | `/api/diagnose/manual` | 品牌/错误码归一化、安全检查、真实语料检索和存储；目前不生成维修步骤 |
| POST | `/api/analyze/image` | 图片内容质量检查后按文件名返回六场景 mock |
| GET | `/api/sessions` | 从 SQLite 读取诊断列表 |
| GET | `/api/sessions/{id}` | 从 SQLite 读取详情 |
| POST | `/api/sessions/{id}/steps/{step_id}/feedback` | 保存 `done`/`not_useful`/`skipped` |
| POST | `/api/sessions/{id}/report` | 生成并保存中英报告；英文翻译失败时降级 |
| DELETE | `/api/sessions/{id}` | 删除诊断并级联清除步骤和报告 |

完整字段以 `docs/api-contract.md` 和运行中的 `/docs` 为准。

### 手动检索

```json
{
  "query": "Bosch E24 排水",
  "category": "",
  "category_hint": "dishwasher",
  "brand": "Bosch",
  "error_code": "E24",
  "limit": 3
}
```

`POST /api/manuals/search` 的 Top3 应包含 `bosch-dishwasher-9001014024`、PDF 第 35 页。`category` 是严格筛选，`category_hint` 是加权提示。未知错误码返回空 `matches`，不会换成 E24。

`POST /api/diagnose/manual` 可提交 `{"brand":"博世","error_code":"E:24"}`，错误码会归一化为 `E24`。目前只返回候选手册和转专业建议，`steps` 为空；未知品牌或错误码同样明确提示无引用。空白输入返回 422，数据库不可用返回 503。

### 图片 mock 与质量门

演示文件名：

- `router.jpg`：TP-Link 路由器
- `e24.jpg`：Bosch 洗碗机 E24
- `billy.jpg`：IKEA BILLY
- `microwave.jpg`：安全拒答
- `report.jpg`：报修场景

必须上传有效图片。过暗、模糊、分辨率不足、无法读取或超过大小限制会返回 422；质量判断依据图片内容，不是文件名。未知演示文件名同样返回 422，不编造诊断。文件名路由不是实际视觉识别。

### 反馈与报修

反馈仅接受 `done`、`not_useful`、`skipped`。报修请求支持：

```json
{"lang":"zh","photo_refs":["device-front.jpg"]}
```

```json
{"lang":"en","photo_refs":["device-front.jpg"]}
```

只收录 `done` 步骤，按 `idx` 排序。照片引用是文字，不会自动附加照片；发送时另附实际照片。中文不调用模型；英文可配置 Gemini 翻译，无 key 或失败时保留步骤编号并注明正文未翻译。两种情况下报告都保存到 `reports`。

需要在线翻译时，在 `server/.env` 配置：

```dotenv
GEMINI_API_KEY=替换为你自己的真实密钥
GEMINI_MODEL=gemini-2.5-flash
```

已有 `.env` 不要覆盖，修改配置后重启服务。key 不提交 Git，也不会启用真实图片诊断。

## 5. 测试与验收

```sh
python -X utf8 -m pytest tests -q
python experiments/run_acceptance.py
python experiments/run_server_checks.py
```

- pytest 覆盖语料、检索、加权、安全规则、图片质量、反馈、报修、重开数据库和级联删除。
- `run_acceptance.py` 重放 S1–S6 离线后端场景，可用 `--label` 和 `--output` 保存其他机器的结果。
- `run_server_checks.py` 使用真实 Uvicorn HTTP 和临时 SQLite，检查重启保留反馈/报告及删除级联。
- 这些检查不覆盖真实 Gemini 视觉、Windows 实机或手机预览/复制/分享。

数据和实验命令：

```sh
python corpus.py data/manifest.json data/chunks.json
python experiments/run_retrieval.py
python experiments/evaluate_scenarios.py
python experiments/evaluate_quality.py
python experiments/evaluate_safety.py --gate safety_gate.py --revision local --output experiments/safety-results.json
python experiments/evaluate_demo_alternatives.py
python experiments/package_demo_assets.py --output ../snapfix-demo-inputs.zip
```

换电脑演示和手机验收见[演示清单](../docs/demo-runbook.md)。来源、页码、排除页面和剩余事项见[数据交接说明](../docs/data-handoff.md)与[完成记录](../docs/review-audit.md)。

## 6. 联合开发边界

- BE-1 继续接入真实图片识别、生成和引用校验；不能让 key 的存在改变健康接口的虚假状态。
- BE-2 负责检索、存储和报修；安全规则统一使用 `safety_gate.py`，不另建分支副本。
- FE 对接反馈、报修和档案时，必须处理重拍、型号为空、安全拒答、未知错误码和无引用状态。
- 未确认完整型号时不假定手册适用；候选手册命中不等于真实故障已识别。
