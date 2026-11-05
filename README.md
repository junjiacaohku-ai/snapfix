# SnapFix 随手修

> 先搞懂，再决定。 / Snap it. Fix it. Or report it.

HKU COMP7506A Group Project · Flutter + FastAPI · 演示 2026-11-19 · 截止交付 2026-11-30（组内目标 11-29）

项目目标：拍照或手动输入设备故障信息，查询说明书并提供诊断、处理决策和报修支持。

## 当前版本

本文描述当前 `feature/be2-storage-retrieval` 分支。其他队友尚未合并的功能不视为本分支已实现。最新分工和验收标准以 [四周冲刺计划](docs/2026-10-22%20SnapFix%20四周冲刺计划.md) 为准。

| 部分 | 当前状态 |
|---|---|
| SQLite | 诊断、步骤反馈、报修草稿持久化；删除诊断时级联删除步骤和草稿 |
| 说明书语料 | 16 份资料、2032 个切块，使用现成 JSON 导入 |
| BM25 | 已实现检索端点、类别提示加权、错误码加权，以及品牌别名和错误码归一化 |
| 手动错误码诊断 | 已调用真实语料检索；无召回明确提示无引用；目前不生成维修步骤 |
| 图片诊断 | 仍按文件名返回 E24／微波炉演示场景，尚未接入真实图片识别管线 |
| 报修 | 中文直接使用已完成步骤原文；英文可选 Gemini 翻译，无 key 或调用失败时仍可生成报告 |
| Flutter App | 本分支 `app/` 只有说明文档，前端工程待整合 |
| 展示页 | `landing/index.html` 为静态项目展示页 |

完整后端安装、接口和验收说明见 [server/README.md](server/README.md)。本文同时提供 macOS 和 Windows 命令；Windows 实机、手机流程及真实图片管线尚未完成联合验收。

## 目录结构

```text
app/                         Flutter 双端 App（FE-1 基础工程 + FE-2 产品交互）
docs/                        需求、分工、四周冲刺计划和调研
landing/                     静态展示页
server/
  main.py                    API 和请求校验
  corpus_store.py            JSON 语料导入
  session_store.py           SQLite 诊断、反馈和报告存储
  retrieval.py               BM25、归一化和加权排序
  retrieval_service.py       数据库读取与检索索引缓存
  diagnosis_service.py       手动错误码检索流程
  safety_gate.py             本分支使用的安全规则
  report_service.py          中英模板与翻译失败降级
  translation_service.py     可选 Gemini 翻译
  requirements.txt           运行依赖
  requirements-dev.txt       测试依赖
  tests/                     自动化测试
  data/                      manuals.json、chunks.json 和本机数据库
```

## 环境要求

- Python **3.11 或以上**；SQLite 使用 Python 标准库，无需另装数据库服务器。
- macOS 使用终端或 VS Code 内置 zsh/bash；Windows 使用 PowerShell 或 cmd。
- Git 用于协作；后端开发无需安装 Flutter、Xcode 或 Android Studio。
- 首次安装依赖需要网络。安装完成后，检索、档案、mock 诊断和基础报修无需 API key；英文步骤正文在线翻译需要有效 key 和网络。

## 快速开始：后端

从同时包含 `app`、`docs`、`landing`、`server` 的项目根目录执行。若已在 `server`，跳过 `cd server`；已有 `.venv` 时跳过创建，重新激活即可。

### macOS（zsh/bash）

```bash
python3 --version
cd server
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -X utf8 corpus_store.py --database data/snapfix.db
python -m uvicorn main:app --reload
```

### Windows（PowerShell）

```powershell
python --version
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -X utf8 corpus_store.py --database data/snapfix.db
python -m uvicorn main:app --reload
```

确认 Python 版本不低于 3.11。Windows 可用 `py -3` 创建环境；cmd 的激活命令为 `.venv\Scripts\activate.bat`。PowerShell 禁止激活脚本时，可直接用 `.\.venv\Scripts\python.exe` 替代后续命令中的 `python`，无需更改执行策略。

当前导入代码尚未明确指定文件编码，因此语料导入和测试命令使用 `-X utf8`，避免依赖电脑默认编码。语料导入预期输出为 `{"manuals": 16, "chunks": 2032}`。

看到 `Application startup complete` 后打开 [Swagger UI](http://127.0.0.1:8000/docs)。保持终端运行；停止服务按 Control+C（macOS）或 Ctrl+C（Windows）。根地址 `/` 未定义，返回 404 时请改为访问 `/docs`。

- 默认数据库：`server/data/snapfix.db`；自定义数据库必须让导入路径与服务路径一致。
- 更新语料时先停止服务，导入完成后重新启动，确保检索索引刷新。
- [健康接口](http://127.0.0.1:8000/api/health) 当前返回图片诊断的 mock 状态，不能用于判断报修翻译是否已调用 Gemini。

### 报修与可选密钥

没有 `.env` 或没有密钥也能启动并生成中英文报告：

| 报告情形 | 当前行为 |
|---|---|
| 中文 | 使用本地模板和已完成步骤原文，不调用 Gemini |
| 英文，翻译成功 | 使用英文模板及翻译后的已完成步骤正文 |
| 英文，无密钥／翻译失败 | 返回已完成步骤编号，并明确注明正文未翻译 |
| 没有已完成步骤 | 明确显示暂无已完成步骤，不编造操作 |

照片引用是文字，发送报修时需要另附实际照片。无密钥的英文降级报告不代表已完成任意步骤正文的英文翻译。

需要在线翻译时，在 `server/.env` 中配置，已有文件不要覆盖：

```dotenv
GEMINI_API_KEY=替换为你自己的真实密钥
GEMINI_MODEL=gemini-3.5-flash-lite
```

`translation_service.py` 会加载 `server/.env`，已有进程环境变量优先；修改后停止并重新启动服务。真实密钥不提交 Git，`OPENAI_API_KEY` 当前只是预留配置。配置密钥不会启用真实图片诊断。详细说明见 [后端文档](server/README.md#35-报修和可选-gemini-配置)。

## 测试与验收

在已激活环境的 `server` 目录执行，macOS 与 Windows 命令相同：

```sh
python -m pip install -r requirements-dev.txt
python -X utf8 -m pytest -q
```

2026-10-31 在本机 macOS、Python 3.14 环境记录的结果为 **29 passed, 1 warning**。警告为测试依赖弃用提示；这不是 Windows 或手机实测结果。测试使用临时数据库，翻译分支通过替代函数检查，不调用真实 Gemini。

人工验收见 [后端测试说明](server/README.md#4-测试与验收)：

1. 检索 `Bosch E24`，确认正确手册 PDF 第 35 页进入 Top3；未知错误码返回空召回。
2. 上传演示图片创建含步骤记录，提交 `done` 反馈，生成中英报告；无密钥时两种语言均应成功。
3. 停止并重启服务，查询原诊断，检查反馈和已有报告仍保留。
4. 删除测试诊断，确认关联步骤、报告一起删除，语料不受影响。

真实图片识别→检索→生成→引用校验仍需与 BE-1 联调；手机预览、复制和分享需与前端联调。Windows 实机复测、六场景检索评估及全组离线演示切换待后续完成。

## 前端与展示页

本分支包含 Flutter 工程，说明见 [app/README.md](app/README.md)。配置 SDK 后，从项目根目录执行：

```sh
cd app
flutter pub get
flutter run
```

Android Emulator 访问电脑后端使用 `http://10.0.2.2:8000`；真实手机需配置可达的后端地址。手机自己的 `127.0.0.1` 不指向电脑。iOS Simulator 仅在 macOS 配合 Xcode 使用。

展示页可直接打开 [landing/index.html](landing/index.html)。

## 分工(详见 docs/2026-09-17 SnapFix 执行包)

| 线 | 人 | 责任 |
|---|---|---|
| BE-1 管线编排 | 曹峻嘉(组长) | API 契约、管线编排、provider 适配、安全门、部署 |
| BE-2 检索与存储 | 史珺瑛 | 手册切块索引(BM25,张帆协助加权)、SQLite、报修端点;**readme 主笔** |
| FE-1 扫描与诊断 | 朱雨泰民 | 相机/相册、分析中过程页、诊断结果页;录屏素材 |
| FE-2 指导与档案 | 杨蕊嘉 | 分步指导交互、维修档案、报修助手页;**设计系统 + 视频剪辑** |
| D 数据与内容 | 张帆 | 语料 ETL、6 场景 mock 数据、调研对比表、验收清单执行 |

> FE 两人第一周先合出主题 + 共享组件库(杨蕊嘉主导视觉);互换预案:朱雨泰民 ↔ 杨蕊嘉。
> 若史珺瑛 Python 基础弱:SQLite 上移至 BE-1,史珺瑛转 D 线协助张帆,检索由曹峻嘉+张帆合做。

## Git 规则(一句话版)

- `main` 永远可跑可演示;**不直接 push main**,走 PR + 1 人 review,squash 合并
- 短分支 `feature/xxx`、`fix/xxx`,活不过 3 天;PR 小步(<300 行)
- 每天下班前 push;改 `pubspec.yaml` / 路由 / API 契约前群里喊
- commit 前缀:`feat:` / `fix:` / `docs:` / `chore:`

## 协作流程(每人每天的循环)

以下 Git 命令适用于 macOS 和 Windows，均在项目根目录执行。先用 `git status` 确认并妥善保存现有修改；下面是开始新任务的示例，不必为已有任务重复创建分支。

```sh
git switch main
git pull --ff-only origin main
git switch -c feature/archive-list
```

完成改动后，在 VS Code 源代码管理中检查并暂存本次相关文件，再提交和上传：

```sh
git diff --cached --stat
git commit -m "feat: connect archive list to sessions API"
git push -u origin feature/archive-list
```

分支名和提交说明按实际任务填写。首次关联远程分支后，后续提交可直接 `git push`。在 GitHub 页面创建 PR，选择 `base: main` 和自己的 `compare` 分支；不要求安装 GitHub CLI。队友尚未合并的分支不会随 `main` 自动进入本地，采用其文件时在 PR 中注明来源和依赖。

PR 发出后:

- **描述写两行**:做了什么 + 怎么验证(截图/录屏),review 的人 24h 内看
- **review 对子**:曹峻嘉 ↔ 史珺瑛(BE 互审)、朱雨泰民 ↔ 杨蕊嘉(FE 互审)、张帆的 PR 曹峻嘉审
- **review 只看三件事**:能跑吗?契约变了吗?有没有把 key/.env 提交进来?——4 周冲刺,不逐行抠风格
- 通过后在网页点 **Squash and merge**,删分支,本地切回 main 重新 ①

## 避坑清单(新人最容易踩的)

1. **误推 main 了**:群里说一声就行,**别 force push 掩盖**,别人可能已基于它开发
2. **冲突了别慌**:`git checkout main && git pull`,回自己分支 `git merge main`,逐个文件解冲突。分支活得越久冲突越多——所以分支活不过 3 天
3. **`.env` / API key 永远不提交**(已被 .gitignore 拦着;review 时再人工兜底一眼)
4. **改公共文件前群里喊**:`server/main.py` 的 API 结构、`app/pubspec.yaml`、路由表——别人正在依赖它们
5. **合并前本地跑通**:后端 `uvicorn main:app` 起得来,前端 `flutter run` 不崩——main 的"永远可演示"靠这最后一眼

## 压缩时间线(原计划已落后,按 4 周冲刺重排)

| 周 | 目标 |
|---|---|
| W1(10/22–10/28) | 环境全通;mock 管线端到端;App 五屏骨架;语料开收(≥10 份手册) |
| W2(10/29–11/4) | 真实 vision 接入;RAG 检索调通;决策/报修功能完成 |
| W3(11/5–11/11) | 功能冻结;6 个验收场景全过;文档初稿;视频素材开录 |
| W4(11/12–11/19) | 修 bug + 排练(掐表两遍);**11/19 课堂演示** |
| 收尾(11/20–11/29) | 剪视频、补文档贡献节、readme 收尾;**11/29 提前交付** |

验收场景与演示剧本见 PRD 第 12 节与执行包第 5 节。
