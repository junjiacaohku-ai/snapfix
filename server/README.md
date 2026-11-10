# SnapFix Server · FastAPI 后端

本文描述后端与产品 UI 集成后的实际行为。真实图片管线已实现质量门、Gemini 视觉、BM25、安全门、结构化生成和引用校验；在线 Gemini 调用需有效 key 单独验收。手动错误码检索、SQLite、反馈和报修使用真实实现，mock 始终可用于离线演示。

Python、Flutter 的版本检查与按需安装、获取源码和打开完整 App，请先按 [根 README](../README.md) 操作，已有工具无需重复下载。本文件用于后端开发及 `/docs` 调试；仅启动下面的 Uvicorn 不会提供 Flutter 网页。

## 1. 环境要求

- Python 3.11 或以上；已在 macOS、Python 3.14 复测，Windows 实机复测待完成。
- SQLite 使用 Python 标准库，无需安装数据库服务器。
- 首次安装依赖需要网络；安装后，检索、档案、图片 mock 和基础报修不需要 key。
- v1 英文步骤正文在线翻译是可选增强；无 key 或翻译失败仍生成基础英文报告。App 的 `/api/fe2` 报修使用另一套模板，见第 4 节。

## 2. 安装与启动

从项目根目录进入 `server`（已经在其中时跳过 `cd server`）。以下两组只选自己的系统。完整网页预览与本节 API 服务二选一启动，不能同时占用 8000。

macOS：

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
python -X utf8 corpus_store.py --database data/snapfix.db
python -m uvicorn main:app --reload
```

Windows PowerShell：

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\python.exe -X utf8 corpus_store.py --database data/snapfix.db
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Windows 直接使用虚拟环境解释器，无需激活脚本；若系统仅有 `py` 命令，用 `py -m venv .venv` 创建环境。已经安装过依赖、导入过语料时无需每次重做，只需启动服务。语料导入预期输出：

```json
{"manuals": 16, "chunks": 2032}
```

启动后打开：

- [Swagger UI](http://127.0.0.1:8000/docs)
- [健康接口](http://127.0.0.1:8000/api/health)

`GET /api/health` 在无 key 或 `SNAPFIX_MOCK=1` 时返回 `mock: true`、`provider: "mock"`；配置有效 key 且未强制 mock 时返回 `provider: "gemini"`。该状态表示配置，不保证每次在线调用成功；每条 Session 的 `source_mode` 才区分实际结果为 mock、retrieval 或 gemini。

看到 `Uvicorn running ...` 且无后续启动错误才表示服务已启动。保持该终端运行；其他命令另开终端。按 `Ctrl + C` 停止服务。端口占用、根路径 404 等处理见 [根 README 的常见问题](../README.md#14-常见问题)。

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
| `fe2_sessions` | App 档案 JSON，包含修订、反馈、接收人草稿及维修状态 |

`corpus_store.py` 读取 `data/manuals.json` 和 `data/chunks.json`。重复导入会更新本批手册并保留其他手册。v1 删除 `sessions` 会级联删除相应 `steps` 和 `reports`。App 导入 v1 诊断后另存于 `fe2_sessions`；后续反馈不回写原记录，删除 App 档案也不删除 v1 原始诊断。不要把 App 删除操作等同于清除了全部相关表。

原始上传照片不持久化，只保存文件名引用；发送报修时需另附原图。测试使用临时数据库，不以日常档案作为可删除的测试数据。

## 4. API 行为

| 方法 | 路径 | 当前行为 |
|---|---|---|
| GET | `/api/health` | 图片诊断的 mock 状态 |
| POST | `/api/manuals/search` | BM25 候选片段、来源和加权分数 |
| POST | `/api/diagnose/manual` | 品牌/错误码归一化、安全检查、真实语料检索和存储；目前不生成维修步骤 |
| POST | `/api/analyze/image` | 先执行图片质量门；在线模式尝试 Gemini 管线，离线或在线失败时按约定文件名尝试 mock |
| GET | `/api/sessions` | 从 SQLite 读取诊断列表 |
| GET | `/api/sessions/{id}` | 从 SQLite 读取详情 |
| POST | `/api/sessions/{id}/steps/{step_id}/feedback` | 保存 `done`/`not_useful`/`skipped` |
| POST | `/api/sessions/{id}/report` | 生成并保存中英报告；英文翻译失败时降级 |
| DELETE | `/api/sessions/{id}` | 删除诊断并级联清除步骤和报告 |

上表为 v1 接口。完整字段见 [API 契约](../docs/api-contract.md)，当前实际注册的 v1 与 App 接口均可在运行中的 `/docs` 查看。

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

### 真实图片管线与 mock 降级

v1 先执行图片质量门，再尝试 Gemini 视觉提取、归一化、安全检查、BM25、结构化生成及引用 ID 校验。低置信度、空召回、型号为空或生成步骤未通过校验时不提供 DIY 步骤；高危结果直接拒答。引用 ID 来自召回结果不等于手册适用型号已核实，仍需核对设备与手册。在线调用失败可回退到标记为 `mock` 的演示，不应把它当成在线识别成功。

必须上传有效图片。过暗、模糊、分辨率不足、无法读取或超过大小限制会返回 422；质量判断依据图片内容，不是文件名。原始照片不写入 SQLite。

离线演示文件名：

- `router.jpg`：TP-Link 路由器
- `e24.jpg`：Bosch 洗碗机 E24
- `billy.jpg`：IKEA BILLY
- `microwave.jpg`：安全拒答
- `report.jpg`：报修场景

文件名路由只用于 mock，不是实际视觉识别。真实调用失败且文件名不匹配演示场景时返回 422，不编造诊断。

### 反馈与报修

反馈仅接受 `done`、`not_useful`、`skipped`。报修请求支持：

```json
{"lang":"zh","photo_refs":["device-front.jpg"]}
```

```json
{"lang":"en","photo_refs":["device-front.jpg"]}
```

只收录 `done` 步骤，按 `idx` 排序。照片引用是文字，不会自动附加照片；发送时另附实际照片。中文不调用模型；英文可配置 Gemini 翻译，无 key 或失败时保留步骤编号并注明正文未翻译。两种情况下报告都保存到 `reports`。

如需在线能力，在当前 `server` 目录仅首次复制 `.env.example` 为 `.env`：macOS 使用 `cp .env.example .env`，Windows PowerShell 使用 `Copy-Item .env.example .env`。已有文件直接编辑，不要覆盖。在 `.env` 配置：

```dotenv
GEMINI_API_KEY=替换为你自己的真实密钥
GEMINI_MODEL=gemini-2.5-flash
```

修改后重启服务。相同 key 也用于图片管线：未强制 `SNAPFIX_MOCK=1` 时会启用在线图片调用。`GEMINI_MODEL` 用于生成和翻译；视觉提取目前使用 `providers.py` 内的模型常量。终端环境变量优先于 `.env`，key 不提交 Git。

### App 产品接口 `/api/fe2`

Flutter 当前页面通过 `ui_api.py` 操作 `fe2_sessions`。它与上面的 v1 存储、报告接口不是同一条验收链路。

| 路径 | 用途及限制 |
|---|---|
| `GET /api/fe2/capabilities` | 报告在线能力配置，不验证一次实际模型调用能否成功 |
| `POST /api/fe2/demo` | 显式流程预览：`e24`、`router`、`billy`、`microwave` |
| `POST /api/fe2/diagnose` | 保存手动输入为待处理记录并检查安全；该接口本身不调用 BM25 |
| `POST /api/fe2/diagnose/photo` | 无在线能力时验证图片格式和大小、保存待处理记录，不执行 v1 亮度/清晰度诊断 |
| `POST /api/fe2/import/{legacy_id}` | 将 v1 记录导入为 App 副本；当前在线能力关闭时返回 409，mock 记录也禁止导入 |
| `GET/DELETE /api/fe2/sessions/{sid}` | 查看或删除 App 档案，删除不涉及 v1 原始诊断 |
| `POST /api/fe2/sessions/{sid}/steps/{step_id}/feedback` | 更新 App 档案中的步骤反馈 |
| `POST/PUT /api/fe2/sessions/{sid}/reports/{recipient}/{lang}` | 生成/保存接收人草稿；`recipient` 为 `landlord`、`technician`、`after_sales`，`lang` 为 `zh`、`en` |

App 模板列出 `done` 与 `not_useful` 并分别标注已执行/未改善，不收录 `skipped`。英文演示使用内置译文；其他中文可能原样保留并标记未翻译，不调用 `report_service.py` 的 Gemini 翻译。当前 App 模板只提醒附图，暂不列出已保存照片的文件名，英文模板也未完整包含设备类别。v1 报告的照片字段和翻译测试不能替代 App 报告验收。

生成端点首次生成后保留已有草稿，避免覆盖用户编辑；反馈变化后可通过 App 恢复模板，或调用报告路径后的 `/template` 获取新模板再保存。当前 App 的手动错误码调用还受在线能力开关控制，而 v1 检索本身无需 key。

## 5. 测试与验收

以下命令在 `server` 目录的新测试终端执行。确定性的六场景验收应使用未配置 Gemini key 的环境；`SNAPFIX_MOCK` 只强制图片演示，不关闭独立报告翻译。

macOS：

```bash
source .venv/bin/activate
python -X utf8 -m pytest tests -q
SNAPFIX_MOCK=1 python -X utf8 experiments/run_acceptance.py --label mac --output ../mac-acceptance.json
SNAPFIX_MOCK=1 python -X utf8 experiments/run_server_checks.py
```

Windows PowerShell：

```powershell
$env:SNAPFIX_MOCK = '1'
.\.venv\Scripts\python.exe -X utf8 -m pytest tests -q
.\.venv\Scripts\python.exe -X utf8 experiments/run_acceptance.py --label windows --output ..\windows-acceptance.json
.\.venv\Scripts\python.exe -X utf8 experiments/run_server_checks.py
```

- pytest 覆盖语料、检索、加权、安全规则、图片质量、反馈、报修、重开数据库和级联删除。
- `run_acceptance.py` 重放 S1–S6 离线后端场景，可用 `--label` 和 `--output` 保存其他机器的结果。
- `run_server_checks.py` 使用真实 Uvicorn HTTP 和临时 SQLite，检查重启保留反馈/报告及删除级联。
- 这些检查不覆盖真实 Gemini 视觉、Windows 实机或手机预览/复制/分享。

数据和实验命令：

以下均在 `server` 执行；macOS 已激活环境可用 `python`，Windows 将 `python` 换为 `.\.venv\Scripts\python.exe`。`corpus.py` 会重新生成切块文件，仅需要重做 ETL 时执行，正常运行直接导入现有 JSON 即可。

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

- BE-1 已实现真实图片识别、生成和引用校验；在线 key 调用与端到端耗时仍需实测，健康配置不能替代每条记录的 `source_mode`。
- BE-2 负责检索、存储和报修；安全规则统一使用 `safety_gate.py`，不另建分支副本。
- FE 对接反馈、报修和档案时，必须处理重拍、型号为空、安全拒答、未知错误码和无引用状态。
- 未确认完整型号时不假定手册适用；候选手册命中不等于真实故障已识别。
