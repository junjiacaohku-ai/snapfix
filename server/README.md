# SnapFix Server(FastAPI)

## 运行

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

交互式接口文档:http://127.0.0.1:8000/docs

## 当前状态

- [x] PRD 第 10 节 v1 契约全部端点(mock 实现,内存存储)
- [x] mock 场景:Bosch E24(可自修)/ 微波炉(安全门拒答)
- [ ] SQLite 持久化(PRD 第 9 节数据模型)— BE-2
- [ ] 手册语料切块 + BM25 检索 — BE-2 / D
- [ ] 真实 vision(Gemini)+ provider 故障转移 — BE-1
- [ ] 规则安全门完整类目表(12 类)— BE-1
- [ ] 引用校验(步骤必须对应检索到的手册片段)— BE-1

## 约定

- API key 只放 `.env`,任何代码、日志、commit 中不得出现 key
- mock 模式永远可用:`pytest` 与课堂演示不依赖网络与 key
- 照片处理后即删,不持久化原图(隐私红线,见 PRD 第 11 节)

## D 线离线数据工具

安装 `pip install -r requirements.txt -r requirements-dev.txt`，在 server 目录执行
`python -m pytest tests -q`。PDF 提取运行 `python corpus.py manifest.json chunks.json`。
manifest 为对象数组，每项包含 `file`（相对 manifest 的 PDF 路径）、
`source_url`、`brand`、`device_category`、`title`。输出保留来源、页码和稳定块 ID；
每页切为最多 500 字的块。扫描件无文本时明确失败，需另行 OCR；CID乱码自动尝试PyMuPDF，仍不可读则失败；按编号或 Chapter 标题做启发式分节，未识别时标为 unclassified，须人工复核。
`weighted_matches` 提供类别 +3、品牌别名 +2、精确错误码 +5 的词法基线，供 BE-2 集成对比。

Mock 图片文件名路由：router、billy、microwave、dark/blur、report；其他文件名维持 E24。
质量门仅按文件名模拟，绝非真实图片检测。家具及路由器步骤为明确标记的合成内容，
不冒充官方手册；原 E24 示例引用也尚待真实手册核验。
第六场景通过 report 图片创建会话，再调用 feedback 与中英 report 端点完成。
未知品牌/错误码现返回 404，不再返回不相关的 Bosch 建议。
