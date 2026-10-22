# SnapFix 随手修

> 先搞懂,再决定。 / Snap it. Fix it. Or report it.

拍一张照片,告诉你东西哪坏了、能不能自己修、怎么修、修不了怎么报修。
HKU COMP7506A Group Project · Flutter + FastAPI · 演示 2026-11-19 · 交付 2026-11-30

## 目录结构

```
/app      ← Flutter 双端 App(待 flutter create 初始化,见 app/README.md)
/server   ← FastAPI 后端(mock 管线已可跑,见 server/README.md)
/docs     ← 任务书、调研、PRD、执行包、会议纪要、最终交付文档
/landing  ← 项目展示页(静态 HTML,可直接开浏览器看)
```

## 快速开始

```bash
# 后端(Python 3.11+)
cd server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload   # → http://127.0.0.1:8000/docs 可调式全部接口

# 前端(需先装 Flutter SDK)
cd app && flutter run
```

无 API key 时后端自动走 **mock 确定性模式**,全流程可演示——这是课堂演示的兜底。

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

```bash
git checkout main && git pull          # ① 开工前:同步最新 main
git checkout -b feature/档案页列表      # ② 开短分支(自己的名字自己看得懂就行)
# …写代码…
git add -A && git commit -m "feat: 档案页列表接 /api/sessions"
git push -u origin feature/档案页列表   # ③ 下班前必 push,没做完也推(WIP 不丢人,丢代码才丢人)
gh pr create --fill                    # ④ 功能完成后发 PR(也可以在网页点 Compare & pull request)
```

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
