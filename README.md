# SnapFix 随手修

> 先搞懂，再决定。 / Snap it. Fix it. Or report it.

HKU COMP7506A Group Project · Flutter + FastAPI · 演示 2026-11-19 · 截止交付 2026-11-30（组内目标 11-29）

项目目标：拍照或手动输入设备故障信息，查询说明书并提供诊断、处理决策和报修支持。最新分工和验收标准以[四周冲刺计划](docs/2026-10-22%20SnapFix%20四周冲刺计划.md)为准。

## 当前集成基线

| 部分 | 当前状态 |
|---|---|
| SQLite | 保存诊断、步骤反馈和报修草稿；删除诊断时级联删除关联数据 |
| 说明书语料 | 16 份资料、2032 个切块，使用 JSON 导入 |
| BM25 检索 | 支持品牌别名、错误码归一化、严格类别筛选和类别提示加权 |
| 手动错误码诊断 | 查询真实语料；无召回时明确提示无引用，不编造维修步骤 |
| 图片诊断 | 已实现 Gemini 视觉 → BM25 → 安全门 → 生成 → 引用校验；无 key 时使用明确六场景 mock |
| 安全门 | 高危类别拒答，真实管线、FE-2 与离线演示共用同一套规则 |
| 报修 | 中文本地模板；英文可选 Gemini 翻译，无 key 或翻译失败仍可生成基础报告 |
| Flutter App | FE-1 基础工程与 FE-2 产品 UI 已整合；拍照和手动错误码在能力可用时统一走 v1 API |
| 展示页 | `landing/index.html` 为静态项目展示页 |

真实管线代码已实现并通过替代 provider 测试；在线 Gemini 调用仍需有效 key 单独验收。`source_mode` 区分 mock、retrieval 和 gemini，回退不会冒充真实识别。原始照片不写入 SQLite。详细边界见[后端文档](server/README.md)和[数据交接说明](docs/data-handoff.md)。

## 目录结构

```text
app/                         Flutter App（FE-1 基础工程 + FE-2 产品交互）
docs/                        需求、契约、分工、验收和演示素材
landing/                     静态展示页
server/
  main.py                    API 和请求校验
  providers.py               Gemini vision 适配层
  safety_gate.py             离线安全规则
  corpus_store.py            JSON 语料导入
  session_store.py           SQLite 诊断、反馈和报告存储
  retrieval.py               BM25、归一化和加权排序
  retrieval_service.py       数据库读取与索引缓存
  diagnosis_service.py       手动错误码检索流程
  image_quality.py           图片质量门
  report_service.py          中英模板与翻译失败降级
  translation_service.py     可选 Gemini 翻译
  tests/                     自动化测试
  data/                      manuals.json、chunks.json 和本机数据库
```

## 快速开始：后端

要求 Python 3.11 或以上。首次安装依赖需要网络；SQLite 使用 Python 标准库，无需安装数据库服务器。

### macOS（zsh/bash）

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
python -X utf8 corpus_store.py --database data/snapfix.db
python -m uvicorn main:app --reload
```

### Windows（PowerShell）

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
python -X utf8 corpus_store.py --database data/snapfix.db
python -m uvicorn main:app --reload
```

Windows 也可使用 `py -3` 创建环境；PowerShell 禁止激活脚本时，直接用 `.\.venv\Scripts\python.exe` 替代 `python`。

语料导入预期输出 `{"manuals": 16, "chunks": 2032}`。启动后访问 [Swagger UI](http://127.0.0.1:8000/docs) 和[健康接口](http://127.0.0.1:8000/api/health)。默认数据库为 `server/data/snapfix.db`，可通过 `SNAPFIX_DB` 改路径；导入和服务必须指向同一数据库。

## 测试与离线验收

在 `server` 目录执行：

```sh
python -X utf8 -m pytest tests -q
python experiments/run_acceptance.py
python experiments/run_server_checks.py
```

测试使用独立临时数据库，不修改日常记录，也不依赖真实 API key。六场景验收只覆盖离线后端，不等于真实视觉或手机全流程通过。张帆的数据交付、验证和剩余事项见[完成记录](docs/review-audit.md)。

## 报修与可选密钥

没有 `.env` 或 key 也能生成中英文报告。英文翻译成功时使用已完成步骤的译文；无 key 或翻译失败时保留步骤编号并明确注明正文未翻译。照片引用只是文字，发送报修时仍需另附实际照片。

需要在线翻译时，在 `server/.env` 配置，已有文件不要覆盖：

```dotenv
GEMINI_API_KEY=替换为你自己的真实密钥
GEMINI_MODEL=gemini-2.5-flash
```

`.env`、数据库、`.venv` 和 API key 不提交 Git。修改配置后重启服务。

## 前端与展示页

本分支包含 Flutter 工程，说明见 [app/README.md](app/README.md)。配置 SDK 后，从项目根目录执行：

```sh
cd app
flutter pub get
flutter analyze
flutter test
flutter run
```

W1 静态链路已在 iPhone 17 Pro / iOS 26.3 Simulator 通过集成测试；FE-2 产品 UI、档案、反馈和报修已整合，拍照与错误码在真实能力可用时统一调用 v1 API。Android Emulator 访问电脑后端使用 `http://10.0.2.2:8000`，iOS Simulator 默认使用 `http://127.0.0.1:8000`。真实手机需配置电脑的局域网地址，手机自己的 `127.0.0.1` 不指向电脑。展示页可直接打开 [landing/index.html](landing/index.html)。

## 分工

| 线 | 人 | 责任 |
|---|---|---|
| BE-1 管线编排 | 曹峻嘉（组长） | API 契约、管线编排、provider、安全门、部署 |
| BE-2 检索与存储 | 史珺瑛 | BM25、SQLite、报修端点、README |
| FE-1 扫描与诊断 | 朱雨泰民 | 相机/相册、分析中、诊断结果、录屏素材 |
| FE-2 指导与档案 | 杨蕊嘉 | 分步反馈、维修档案、报修助手、设计系统与视频 |
| D 数据与内容 | 张帆 | 语料 ETL、六场景、调研和验收清单 |

## Git 协作规则

- `main` 永远可跑可演示；不直推 `main`，走 feature 分支、PR 和 1 人 review，使用 squash 合并。
- 每天小步 push；改 `pubspec.yaml`、路由或 API 契约前先在群里同步。
- review 对子：曹峻嘉 ↔ 史珺瑛；朱雨泰民 ↔ 杨蕊嘉；张帆的 PR 由曹峻嘉审。
- 合并前本地跑通后端或前端，检查是否误提交 key、`.env` 或数据库。
- 误推 `main` 不要 force push 掩盖；冲突时把最新 `main` 合回自己的分支再解决。

常用流程：

```sh
git switch main
git pull --ff-only origin main
git switch -c feature/archive-list
# 完成修改并检查后
git add <相关文件>
git commit -m "feat: connect archive list to sessions API"
git push -u origin feature/archive-list
```
