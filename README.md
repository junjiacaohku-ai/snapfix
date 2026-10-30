# SnapFix 随手修

> 先搞懂，再决定。 / Snap it. Fix it. Or report it.

项目目标：拍照或手动输入设备故障信息，查询说明书并提供诊断、处理决策和报修支持。

HKU COMP7506A Group Project · Flutter + FastAPI · 演示 2026-11-19 · 截止交付 2026-11-30（组内目标 11-29）

## 当前版本

本 README 描述当前 BE-2 分支，macOS 和 Windows 均可配置后端。各队友尚未合并分支的功能不视为本分支已实现。

| 部分 | 当前状态 |
|---|---|
| FastAPI 后端 | 诊断仍为 mock；已接入 SQLite 档案、步骤反馈和报修草稿存储 |
| 说明书语料 | 已接收 16 份资料、2032 个切块，提供 JSON 导入脚本 |
| 检索与真实识别 | BM25 尚未接入诊断流程；真实 vision、完整安全门和引用校验待整合 |
| Flutter App | 本分支 `app/` 目前只有说明文档，尚未初始化 Flutter 工程 |
| 展示页 | `landing/index.html` 为静态项目展示页 |

运行说明与实际测试记录应区分：本文提供跨平台操作步骤，不代表已完成 macOS／Windows 双平台、手机或真实识别验收。完整后端说明见 [server/README.md](server/README.md)。

## 目录结构

```text
app/       Flutter App（本分支待初始化）
server/    FastAPI、SQLite 存储、语料 JSON 和导入程序
  data/    manuals.json、chunks.json，以及本机生成的数据库
  README.md
  main.py
  corpus_store.py
  session_store.py
docs/      项目计划、需求、调研与交付材料
landing/   静态项目展示页
```

## 环境要求

- 后端：Python **3.11 或以上**，使用 Python 自带 SQLite，无需安装数据库服务器。
- macOS：终端或 VS Code 内置 zsh/bash；Windows：PowerShell 或 cmd。
- 团队协作：Git。使用 VS Code 时可安装 Python 扩展。
- 前端开发另需 Flutter SDK 及目标平台工具；只做后端无需安装 Flutter、Xcode 或 Android Studio。

## 快速开始：后端

先在 VS Code 打开整个仓库。以下命令从**项目根目录**开始，逐行执行；已经位于 `server` 时跳过 `cd server`。

### macOS（zsh/bash）

先用 `python3 --version` 确认版本为 3.11 或以上。

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python corpus_store.py --database data/snapfix.db
python -m uvicorn main:app --reload
```

### Windows（PowerShell）

先用 `python --version` 确认版本为 3.11 或以上。

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python corpus_store.py --database data/snapfix.db
python -m uvicorn main:app --reload
```

cmd 的激活命令为 `.venv\Scripts\activate.bat`，其他后续 Python 命令相同。若 PowerShell 阻止激活，无需修改系统执行策略，可直接用 `.\.venv\Scripts\python.exe` 替代后续命令中的 `python`。Python Launcher、直接运行方式等详见 [后端安装说明](server/README.md#2-安装)。

`.venv` 只创建一次。以后在 `server` 中重新激活环境并启动即可；依赖或语料更新后再安装依赖或重新导入。当前交接版本的导入结果应为 16 份资料、2032 个切块。

### 打开接口页面

看到 `Application startup complete` 后打开 [Swagger UI](http://127.0.0.1:8000/docs)。这是 FastAPI 集成的后端接口调试界面，手机 App 界面由 Flutter 实现。

- 健康检查：[GET /api/health](http://127.0.0.1:8000/api/health)。
- `/` 首页未定义，访问根地址返回 404 时，请改为打开 `/docs`。
- 默认数据库：`server/data/snapfix.db`。自定义 `SNAPFIX_DB` 时，导入路径和服务路径必须一致。
- 停止服务：macOS 按 Control+C，Windows 按 Ctrl+C。终端需保持运行才能接收请求。
- 当前无需 API key；本分支尚未接入真实 Gemini 调用，健康接口的 provider 标记不能作为已调用模型的证据。

## 前端与展示页

Flutter 工程由前端负责人按 [app/README.md](app/README.md) 初始化。不要在尚未整合前端工程的本分支直接运行 `flutter run`。拿到已初始化的工程并配置 SDK 后，从项目根目录执行（两种系统相同）：

```sh
cd app
flutter pub get
flutter run
```

Android 模拟器在 macOS 和 Windows 上均可使用；iOS Simulator 仅在 macOS 配合 Xcode 使用。本机接口地址为 `http://127.0.0.1:8000`，Android Emulator 访问宿主机使用 `http://10.0.2.2:8000`。真实手机需另行配置可达的后端地址，不能用手机自身的 `127.0.0.1` 指代电脑。

展示页可直接用浏览器打开 [landing/index.html](landing/index.html)。

## 测试与验收

完整操作见 [后端测试说明](server/README.md#4-测试与验收)，macOS 和 Windows 使用同一套接口验收步骤：

1. 导入 JSON，检查说明书／切块数量、重复导入和外键关联。
2. 在 `/docs` 创建 mock 诊断，记录诊断 ID；提交步骤反馈，生成中英报修草稿。
3. 停止并重启服务，按原 ID 查询，确认诊断、步骤、反馈和草稿仍保留。
4. 删除专门创建的测试诊断，确认关联步骤、报修草稿一起删除，语料不受影响。

当前分支尚未加入自动化测试目录。真实识别、检索生成和手机全流程应另行验收；不要用 mock 或其他分支的测试结果代替。当前 E24 mock 仍有旧设备类别／引用示例，需与 BE-1、张帆的数据版本统一。

SQLite 存储模块、导入程序及 JSON 语料接收自张帆的数据分支，BE-2 完成后端存储接入。具体贡献以 Git、PR 和实际验收记录为准。

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
