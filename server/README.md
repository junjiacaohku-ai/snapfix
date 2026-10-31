# SnapFix Server · FastAPI 后端

本文说明当前 BE-2 分支的实际行为，提供 macOS 与 Windows 的安装、运行和验收步骤。后端使用 SQLite 保存数据；其他尚未合并分支的功能不视为已接入。

## 1. 环境要求

- Python **3.11 或以上**；已在本机 macOS、Python 3.14 环境验证，Windows 实机复测待完成。
- macOS 使用 zsh/bash；Windows 使用 PowerShell 或 cmd，均可使用 VS Code 终端。
- SQLite 使用 Python 标准库 `sqlite3`，无需安装数据库服务器。
- 首次安装依赖需要网络；安装完成后，检索、档案、图片 mock 和基础报修不需要 API key。
- 英文步骤正文在线翻译是可选功能，需要有效的 Gemini key 和网络；翻译不可用时仍生成基础英文报告。
- 只开发后端无需安装 Flutter、Android Studio 或 Xcode。

## 2. 安装

在 VS Code 打开项目根目录，即同时包含 `app`、`docs`、`landing`、`server` 的文件夹。以下命令从根目录执行；已在 `server` 时跳过 `cd server`。

### macOS（zsh/bash）

```bash
python3 --version
cd server
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Windows（PowerShell）

```powershell
python --version
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

确认版本不低于 3.11。如果 Windows 的 `python` 命令不可用，确认安装 Python 并启用 PATH；安装了 Python Launcher 时，可用 `py -3 --version` 检查，用 `py -3 -m venv .venv` 创建环境。

### Windows 的其他启动方式

cmd 激活命令：

```bat
.venv\Scripts\activate.bat
```

PowerShell 禁止执行激活脚本时，可以直接使用虚拟环境 Python，无需更改系统执行策略：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -X utf8 corpus_store.py --database data/snapfix.db
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

使用此方式时，后文所有 `python ...` 都替换成 `.\.venv\Scripts\python.exe ...`。

### 重新打开终端与依赖更新

`.venv` 只创建一次。以后进入 `server`，重新激活，再启动后端；依赖变更后重新执行安装命令。macOS 与 Windows 需要各自创建虚拟环境，不能直接复制 `.venv` 使用。

## 3. 运行与数据库

本节命令均在 `server` 目录、使用项目虚拟环境的 Python 执行。除单独标注外，两个系统命令相同。

### 3.1 导入现成语料

```sh
python -X utf8 corpus_store.py --database data/snapfix.db
```

读取 `data/manuals.json` 和 `data/chunks.json`，创建手册相关表并导入。当前数据预期输出：

```json
{"manuals": 16, "chunks": 2032}
```

使用张帆提供的现成 JSON，不必重新提取 PDF。重复导入更新本批说明书和切块，保留不属于本批的说明书。导入目前提供 Python 函数和命令行入口，没有 HTTP 语料上传端点。

当前代码读取 JSON 尚未显式指定 UTF-8；命令中的 `-X utf8` 用于避免不同系统默认编码导致失败。更新语料时先停止后端，导入后重新启动；当前索引按数据库路径缓存，不会自动发现数据库内容变化。

### 3.2 启动服务

```sh
python -m uvicorn main:app --reload
```

看到 `Application startup complete` 后打开：

- [Swagger UI 接口调试页面](http://127.0.0.1:8000/docs)
- [健康接口](http://127.0.0.1:8000/api/health)

保持终端运行，需要操作 Git 或查询数据库时另开终端。macOS 按 **Control+C** 停止，Windows 按 **Ctrl+C**；重新运行启动命令即重启。

`main:app` 指 `main.py` 中的 FastAPI 应用，`--reload` 在 Python 文件变更后重新加载。根地址 `/` 未定义，返回 404 时改为访问 `/docs`。

健康接口当前使用图片诊断的 mock 标记，返回 `mock: true`、`provider: "mock"`；即使英文报修实际调用 Gemini，这两个值也不会变。真实图片识别尚未接入，不能用健康标记判断报修翻译是否成功。

### 3.3 数据库与文件位置

默认数据库为 `server/data/snapfix.db`。语料导入与后端服务必须指向同一数据库。

| 表 | 用途 |
|---|---|
| `manuals` | 说明书名称、来源、设备类别等 |
| `manual_chunks` | 切块正文及所属说明书 |
| `chunk_metadata` | 辅助表：切块页码、品牌、来源等元数据 |
| `sessions` | 诊断记录、设备信息、决策和创建时间 |
| `steps` | 诊断步骤、引用和反馈 |
| `reports` | 报修语言、正文、时间及关联诊断 |

使用 SQLite 查看器打开数据库；普通文本编辑器提示二进制文件属于正常情况。数据变化后刷新查看器，或关闭标签页再打开。

### 3.4 可选：指定其他数据库

后端读取环境变量 `SNAPFIX_DB`，导入程序读取 `--database`。以下示例从 `server` 执行，保证二者路径一致。

macOS：

```bash
export SNAPFIX_DB="$PWD/data/dev.db"
python -X utf8 corpus_store.py --database "$SNAPFIX_DB"
python -m uvicorn main:app --reload
```

Windows PowerShell：

```powershell
$env:SNAPFIX_DB = Join-Path (Get-Location).Path "data/dev.db"
python -X utf8 corpus_store.py --database "$env:SNAPFIX_DB"
python -m uvicorn main:app --reload
```

停止服务后恢复默认：macOS 执行 `unset SNAPFIX_DB`；PowerShell 执行 `Remove-Item Env:SNAPFIX_DB -ErrorAction SilentlyContinue`。这些设置影响当前终端及其子进程。

### 3.5 报修和可选 Gemini 配置

没有 `.env` 或没有 key 时，后端仍可生成和保存报告：

| 情形 | 行为 |
|---|---|
| 中文 | 本地中文模板、已完成步骤原文，不调用 Gemini |
| 英文，存在已完成步骤且翻译成功 | 英文模板及翻译后的类别、步骤正文 |
| 英文，无 key／翻译失败 | 已完成步骤编号，如 `Step 1 (marked complete).`，并明确注明正文未翻译 |
| 英文，无已完成步骤 | 显示 `No completed steps recorded.`，不调用 Gemini |

仅收录 `feedback == "done"` 的步骤，按 `idx` 排序。品牌、型号、错误码和照片引用不送去翻译；原始步骤正文不会因翻译被覆盖。照片引用是文字，不会自动附加照片；发送时需要另附实际照片。翻译成功或降级生成的报告都会保存到 `reports`。

无密钥返回基础英文报告，不代表任意步骤正文都已经翻成英文。翻译服务不可用可能需要等待请求超时后才降级。

需要在线翻译时，在 `server` 创建 `.env`；已有文件直接编辑，不要覆盖。可从 `.env.example` 复制，并填写：

```dotenv
GEMINI_API_KEY=替换为你自己的真实密钥
GEMINI_MODEL=gemini-3.5-flash-lite
```

默认模型同样为 `gemini-3.5-flash-lite`。`OPENAI_API_KEY` 是预留字段，当前报修翻译未实现 OpenAI 备用调用。

`translation_service.py` 在导入时加载 `server/.env`；已有进程环境变量优先。修改配置后停止并重新启动服务，不要依赖 `.env` 自动热更新。配置 key 只启用可选翻译，不会启用真实图片诊断。

## 4. 测试与验收

### 自动化测试

在 `server` 安装开发依赖后运行；macOS 与 Windows 命令相同：

```sh
python -m pip install -r requirements-dev.txt
python -X utf8 -m pytest -q
```

测试覆盖语料导入、重开和重复导入、关联约束、真实语料 Top3、类别／错误码加权、错误码旁路、安全规则示例、报修字段、反馈筛选、翻译结果结构、无密钥和翻译失败降级、保存与级联删除。

`tests/conftest.py` 以及测试 fixture 使用临时数据库，不修改日常的 `data/snapfix.db`。翻译成功／失败使用替代函数；无密钥测试检查不创建 Gemini 客户端，因此自动测试不依赖真实 API key 或外网。

2026-10-31 本机 macOS、Python 3.14 的已记录结果：**29 passed, 1 warning**。警告为 Starlette 测试客户端的依赖弃用提示，不是测试失败；不要据此宣称 Windows、真实视觉或手机全流程已通过。

### 4.1 语料数量与关联关系

以下命令只读检查默认数据库：

```sh
python -c "import sqlite3; db = sqlite3.connect('file:data/snapfix.db?mode=ro', uri=True); print('manuals:', db.execute('SELECT COUNT(*) FROM manuals').fetchone()[0]); print('manual_chunks:', db.execute('SELECT COUNT(*) FROM manual_chunks').fetchone()[0]); print('foreign_key_check:', db.execute('PRAGMA foreign_key_check').fetchall()); db.close()"
```

预期为 `manuals: 16`、`manual_chunks: 2032`、`foreign_key_check: []`。数据版本或自定义路径变化时同步调整预期和命令。

### 4.2 分别验收检索、步骤反馈与报修

在 `/docs` 展开接口，点击 **Try it out**，填写参数后 **Execute**。

**A. 检索验收**

调用 `POST /api/manuals/search`：

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

预期 `200`、`matched: true`；Top3 中包含 `manual_id: "bosch-dishwasher-9001014024"`、PDF 第 35 页。`category` 是严格筛选，`category_hint` 是类别加权提示。结果包含来源和 `score_detail`。当前默认类别加分为 3、错误码贡献权重为 3，尚不代表已经完成多场景权重调优。

将错误码改为未知值 `E999`，查询正文也相应改为 `Bosch E999`，预期空 `matches`、`matched: false` 和明确的无引用提示。

调用 `POST /api/diagnose/manual`，提交 `{"brand":"Bosch","error_code":"E24"}`，会查询真实语料并保存诊断。目前只完成检索接入，不生成维修步骤，返回 `steps: []`；因此不要用这条记录验收步骤反馈。未知错误码同样不会自动换成 E24。

**B. 创建含步骤的演示诊断**

1. 调用 `POST /api/analyze/image`，字段 `file` 选择测试图片，文件名不要包含 `microwave`。
2. 当前实现按文件名选择场景，预期返回 Bosch 洗碗机 E24 演示记录，含一条记录型号／错误码并联系售后的步骤。型号未核实时为 `null`，引用明确标记未核验。
3. 记下最外层诊断 `id` 和 `steps` 内步骤 `id`。上传成功不代表真实识别或图片质量门已接入。
4. 先生成一次英文报告，确认尚未完成的步骤不会出现。
5. 调用反馈接口，提交 `{"feedback":"done"}`，确认返回记录中反馈为 `done`。
6. 分别提交以下报修请求：

```json
{"lang":"zh","photo_refs":["device-front.jpg"]}
```

```json
{"lang":"en","photo_refs":["device-front.jpg"]}
```

`device-front.jpg` 可换为实际上传文件名。预期均为 `200`，报告含设备字段、已完成步骤和照片引用；英文正文能否翻译取决于可选翻译是否可用，失败时检查编号及未翻译说明。

**C. 无密钥验收**

先停止服务，再临时以空 key 启动，不必删除 `.env` 中的真实配置。

macOS、Windows PowerShell 和 cmd 均可使用下面的启动命令：

```sh
python -c "import os, uvicorn; os.environ['GEMINI_API_KEY'] = ''; uvicorn.run('main:app', host='127.0.0.1', port=8000)"
```

它仅在这次 Python 进程中将 key 设为空，再启动服务；不会修改 `.env` 或终端配置。这次不启用 `--reload`，避免重载子进程影响空 key 的验收。

再次调用中文／英文报修接口，预期均返回 `200`，并新增已保存报告；英文已完成步骤以编号显示且正文注明未翻译。不要继续沿用旧版“无 key 应返回 503”的预期。

停止这次服务后，两个系统均使用正常命令恢复：

```sh
python -m uvicorn main:app --reload
```

### 4.3 重启保存与关联删除

1. 在数据库查看器记下本次诊断及中英文报告 ID。
2. 停止服务，以同一数据库重新启动。
3. `GET /api/sessions/{session_id}` 查询原 ID，确认步骤及 `done` 反馈仍在。
4. 查看 `reports` 表，确认重启前的相同报告 ID 和正文仍在；不要通过新生成报告代替检查旧报告。当前没有独立的报修草稿查询端点。
5. 对专门创建的测试诊断调用 `DELETE /api/sessions/{session_id}`，预期 `{"deleted":true}`。
6. 再查询应为 404；对应 `steps`、`reports` 均已删除，说明书及切块数量不变。

### 4.4 验收边界与后续工作

已记录的本机验收包含检索 Top3、中英文报告、无密钥报告及数据库保存；自动测试覆盖重开数据库与级联删除。Windows 实机复测、真实图片识别和手机预览／复制／分享仍需单独执行。

剩余联合工作：BE-1 将识别结果接入检索、生成和引用校验；FE 对接反馈、报修与档案。六场景检索评估及全组离线演示切换按四周冲刺计划继续推进。

## 5. 接口与实现范围

| 方法 | 路径 | 当前行为 |
|---|---|---|
| GET | `/api/health` | 当前图片诊断的 mock 状态 |
| POST | `/api/manuals/search` | BM25 候选片段、来源与分数；空召回明确返回 |
| POST | `/api/diagnose/manual` | 品牌／错误码归一化、安全检查、语料检索与诊断存储；目前不生成步骤 |
| POST | `/api/analyze/image` | 文件名包含 `microwave` 时返回拒答演示，其余返回 E24 演示 |
| GET | `/api/sessions` | 从 SQLite 读取诊断列表 |
| GET | `/api/sessions/{session_id}` | 从 SQLite 读取详情 |
| POST | `/api/sessions/{session_id}/steps/{step_id}/feedback` | 保存 `done`／`not_useful`／`skipped` 反馈 |
| POST | `/api/sessions/{session_id}/report` | 生成并保存中英报告；翻译不可用时英文降级 |
| DELETE | `/api/sessions/{session_id}` | 删除诊断，级联清除步骤和报告 |

实际请求结构以运行中的 `/docs` 为准。无效请求由校验返回 422，不存在的诊断／步骤返回 404；语料数据库读取失败可返回 503。翻译失败已在报修模板中降级，不再阻止基础报告生成。

## 6. 来源与数据约定

`data/manuals.json`、`data/chunks.json`、`corpus_store.py`、`session_store.py` 接收自张帆的数据分支。检索基于其参考实现扩展；本分支接入 SQLite、检索、加权、手动诊断和报修，安全接口与 BE-1 的 `check`／`SafetyVerdict` 保持兼容。具体贡献以提交、PR 和验收记录为准。

- `.venv`、数据库、`.env` 和 API key 不提交；换电脑后创建虚拟环境并从 JSON 导入。
- 未确认设备完整型号时不假定手册适用；候选手册命中不等于真实故障已识别。
- 当前上传的原始照片不会持久化；报告中的照片引用不等于附件。
- 手动检索、图片 mock、真实翻译、完整 RAG 管线和手机操作分别记录验收结果。
