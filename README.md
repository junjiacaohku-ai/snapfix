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

## 压缩时间线(原计划已落后,按 4 周冲刺重排)

| 周 | 目标 |
|---|---|
| W1(10/22–10/28) | 环境全通;mock 管线端到端;App 五屏骨架;语料开收(≥10 份手册) |
| W2(10/29–11/4) | 真实 vision 接入;RAG 检索调通;决策/报修功能完成 |
| W3(11/5–11/11) | 功能冻结;6 个验收场景全过;文档初稿;视频素材开录 |
| W4(11/12–11/19) | 修 bug + 排练(掐表两遍);**11/19 课堂演示** |
| 收尾(11/20–11/29) | 剪视频、补文档贡献节、readme 收尾;**11/29 提前交付** |

验收场景与演示剧本见 PRD 第 12 节与执行包第 5 节。
