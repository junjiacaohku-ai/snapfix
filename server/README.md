# SnapFix Server · FastAPI 后端

后端使用 FastAPI 提供诊断、维修档案、步骤反馈和中英报修草稿接口，使用 SQLite 保存数据。本文适用于 **macOS 和 Windows**，说明当前 BE-2 分支的实际行为；其他未合并分支的功能不视为已接入。

## 1. 环境要求

- Python **3.11 或以上**。
- macOS：使用系统终端或 VS Code 内置终端（zsh/bash）。
- Windows：使用 PowerShell 或 VS Code 内置 PowerShell；命令提示符（cmd）也可使用，激活方式见下文。
- SQLite 通过 Python 标准库 `sqlite3` 使用，无需安装 MySQL 或单独配置数据库服务器。
- 以下示例假设已获取包含 `session_store.py`、`corpus_store.py`、`data/manuals.json` 和 `data/chunks.json` 的代码版本。
- 当前后端开发不要求安装 Flutter、Android Studio 或 Xcode。

## 2. 安装

先在 VS Code 打开项目根目录，即同时包含 `app`、`docs`、`landing`、`server` 的文件夹。以下安装命令从项目根目录开始，逐行执行；若终端已经位于 `server`，跳过 `cd server`。

### macOS（zsh/bash）

先检查版本，确认输出为 Python 3.11 或以上：

```bash
python3 --version
```

首次配置：

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Windows（PowerShell）

先检查版本，确认输出为 Python 3.11 或以上：

```powershell
python --version
```

首次配置：

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

若 Windows 的 `python` 命令不可用，先确认安装了 Python 并启用了 PATH；已安装 Python Launcher 时，也可用 `py -3 --version` 检查版本，并用 `py -3 -m venv .venv` 创建环境。仍需确认所选版本不低于 3.11。

### Windows 激活的其他方式

在命令提示符（cmd）中，激活命令为：

```bat
.venv\Scripts\activate.bat
```

如果 PowerShell 提示禁止执行激活脚本，无需调整系统执行策略。可以不激活，直接使用虚拟环境的 Python：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe corpus_store.py --database data/snapfix.db
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

这种方式下，后文所有 `python ...` 命令都替换成 `.\.venv\Scripts\python.exe ...`。最后一条命令会持续运行服务，按 Ctrl+C 停止。

### 已有环境／重新打开终端

`.venv` 只需创建一次。之后进入 `server`，按自己的系统重新激活，再运行后端命令。依赖清单更新时，重新执行 `python -m pip install -r requirements.txt`。虚拟环境不能在 macOS 和 Windows 间复制使用，应在各自电脑上创建。

## 3. 运行与数据库

**本节所有命令均在 `server` 目录执行，且使用该项目虚拟环境的 Python。macOS 和 Windows 的后续 Python 命令相同。**

### 3.1 导入现成语料

```sh
python corpus_store.py --database data/snapfix.db
```

程序读取 `data/manuals.json` 和 `data/chunks.json`，创建手册相关表并导入数据。当前交接版本预期输出：

```json
{"manuals": 16, "chunks": 2032}
```

重复导入会更新本批说明书及其切块，保留不属于本批的说明书；不应导致数量翻倍。数据版本更新后，预期数量也应随之更新。

这一步使用张帆已经生成的 JSON，不需要重新执行 PDF 提取。`corpus_store.py` 提供内部导入函数和命令行入口，当前没有语料 HTTP 上传端点。

### 3.2 启动服务

```sh
python -m uvicorn main:app --reload
```

看到 `Application startup complete` 后，在浏览器打开：

- [Swagger UI 接口调试页面](http://127.0.0.1:8000/docs)
- [健康检查](http://127.0.0.1:8000/api/health)

保持该终端运行。需要同时使用 Git 或查询数据时，可以另开终端。停止服务：macOS 按 **Control+C**，Windows 按 **Ctrl+C**。再次运行启动命令即可重启。

`main:app` 指 `main.py` 中的 FastAPI 应用，`--reload` 表示保存代码后自动重新加载。当前没有定义网站首页，访问 `http://127.0.0.1:8000/` 返回 404 不代表服务启动失败，请访问 `/docs`。

### 3.3 数据库位置和表结构

默认文件为项目中的 `server/data/snapfix.db`。导入程序创建手册表，启动后端时 `SessionStore` 创建诊断相关表，二者使用同一个文件：

| 表 | 用途 |
|---|---|
| `manuals` | 说明书名称、来源、设备类别等 |
| `manual_chunks` | 说明书切块正文及所属说明书 |
| `sessions` | 诊断记录、设备信息、决策及创建时间 |
| `steps` | 诊断步骤、引用和用户反馈 |
| `reports` | 中英报修草稿及关联诊断 |
| `chunk_metadata` | 辅助表：保存切块页码、品牌、来源等元数据 |

通过数据库查看器打开 `.db` 文件；普通文本编辑器提示二进制文件属于正常情况。数据更新后，刷新查看器或关闭数据库标签页再打开。

### 3.4 可选：指定其他数据库

后端读取环境变量 `SNAPFIX_DB`，导入程序则读取 `--database` 参数。**自定义路径时，二者必须指向同一文件。**以下示例使用另一个开发数据库，仍从 `server` 执行。

macOS：

```bash
export SNAPFIX_DB="$PWD/data/dev.db"
python corpus_store.py --database "$SNAPFIX_DB"
python -m uvicorn main:app --reload
```

Windows PowerShell：

```powershell
$env:SNAPFIX_DB = Join-Path (Get-Location).Path "data/dev.db"
python corpus_store.py --database "$env:SNAPFIX_DB"
python -m uvicorn main:app --reload
```

停止服务后，恢复默认路径：macOS 执行 `unset SNAPFIX_DB`，PowerShell 执行 `Remove-Item Env:SNAPFIX_DB -ErrorAction SilentlyContinue`。环境变量设置仅对当前终端及其子进程生效。

## 4. 测试与验收

本分支提供以下人工验收方法；当前尚未加入自动化测试目录。不要直接使用其他分支的测试通过数量作为本分支的结果。执行后记录实际结果、测试日期和代码版本。

### 4.1 语料数量、重复导入和关联关系

重复运行导入命令，再用以下命令只读检查默认数据库（macOS、PowerShell、cmd 均可用）：

```sh
python -c "import sqlite3; db = sqlite3.connect('file:data/snapfix.db?mode=ro', uri=True); print('manuals:', db.execute('SELECT COUNT(*) FROM manuals').fetchone()[0]); print('manual_chunks:', db.execute('SELECT COUNT(*) FROM manual_chunks').fetchone()[0]); print('foreign_key_check:', db.execute('PRAGMA foreign_key_check').fetchall()); db.close()"
```

当前交接版本预期为 `manuals: 16`、`manual_chunks: 2032`、`foreign_key_check: []`。如使用自定义数据库，请同步修改检查命令中的文件路径。

### 4.2 创建诊断、反馈与中英报修

在 `/docs` 中展开接口，点击 **Try it out**，填写参数后点击 **Execute**。

1. 调用 `POST /api/diagnose/manual`：

   ```json
   {"brand": "Bosch", "error_code": "E24"}
   ```

2. 记录返回的诊断 `id`，以及 `steps` 中一个步骤的 `id`。
3. 调用 `GET /api/sessions` 和 `GET /api/sessions/{session_id}`，确认记录可查。
4. 调用 `POST /api/sessions/{session_id}/steps/{step_id}/feedback`，提交 `{"feedback":"done"}`。
5. 调用 `POST /api/sessions/{session_id}/report`，分别提交 `{"lang":"zh"}`、`{"lang":"en"}`。
6. 在数据库中确认诊断、步骤、反馈和两种语言的草稿已保存。`steps.session_id`、`reports.session_id` 应等于该诊断的 `sessions.id`，不是步骤自身的 `id`。

以上 E24 请求只用于验证当前 mock 的存储流程，不用于证明已经调用手册检索。

### 4.3 停止并重启后端

1. 停止 Uvicorn，然后使用同一数据库重新启动。
2. 重新打开 `/docs`，查询刚才记录的诊断 ID，不要通过创建新诊断代替查询旧记录。
3. 确认原诊断、步骤和 `done` 反馈仍在。
4. 在数据库中确认重启前的中英报修草稿仍在；当前没有单独的报修草稿查询端点。

### 4.4 删除关联数据

只使用专门创建的测试诊断：

1. 调用 `DELETE /api/sessions/{session_id}`，预期返回 `{"deleted":true}`。
2. 再查询该诊断，预期返回 404。
3. 确认属于该诊断的 `steps` 和 `reports` 记录一起删除。
4. 确认说明书及切块数量不受影响。

### 4.5 验收范围

语料数量和关联关系已有本机检查记录；重启、反馈、报修和删除是否通过，应以执行者的实际验收记录为准。本说明列出操作和预期，不代表所有步骤已在所有平台测试通过。尚未完成 macOS 与 Windows 双平台复测、真实识别或手机全流程验收。

## 5. 当前实现与待接入内容

- 已接入 SQLite 诊断、步骤反馈及报修草稿存储，档案列表和详情通过存储模块读取。
- 已接收现成 ETL 输出，提供手册和切块导入功能。
- 报修使用基础中英模板，照片由发送者另附。
- 诊断仍使用旧版 mock；未知品牌／错误码目前也可能返回 E24 兜底，不能视作真实诊断。
- 当前 mock 的 E24 设备类别和引用仍是旧示例；张帆数据分支已改用洗碗机场景，需与 BE-1 统一后再作检索演示。
- BM25 尚未接入本分支的诊断流程；真实 vision、完整安全门及引用校验待后续整合。
- 当前无需 API key；设置 `GEMINI_API_KEY` 仅会改变现有健康接口的模式标记，并不会使本分支自动接入 Gemini。健康标记不作为真实调用证据。

## 6. 来源与数据约定

`data/manuals.json`、`data/chunks.json`、`corpus_store.py`、`session_store.py` 接收自张帆的 `feature/zhangfan-data-delivery` 分支。BE-2 在此基础上接入诊断接口的 SQLite 存储；后续修改和验证通过 Git、PR 及验收记录说明。

- `.venv`、数据库、`.env` 和 API key 不提交到 Git；换电脑时重新创建环境并从 JSON 导入语料。
- 当前代码不会自动加载 `.env`，不要仅因创建该文件就认为环境变量已生效。
- 后端处理后不持久化上传的原始照片。
- mock 响应、后端存储测试、检索评估、真实识别和手机操作分别记录，不混作全流程通过。
