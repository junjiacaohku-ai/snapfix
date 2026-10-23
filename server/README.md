# SnapFix Server(FastAPI)

## 运行

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

交互式接口文档:http://127.0.0.1:8000/docs

## 当前状态

- [x] PRD 第 10 节 v1 契约全部端点(mock 实现,内存存储);契约文档见 `docs/api-contract.md`
- [x] mock 场景:Bosch E24(可自修)/ 微波炉(安全门拒答)
- [x] 安全门分类器 v1(`safety_gate.py`,12 类高危类目,`python safety_gate.py` 可自检)— BE-1
- [x] provider 适配层 v1(`providers.py`,Gemini vision 提取,无 key 返回 None 由上层降级)— BE-1
- [ ] SQLite 持久化(PRD 第 9 节数据模型)— BE-2
- [ ] 手册语料切块 + BM25 检索 — BE-2 / D
- [ ] 管线编排器(质量门→vision→检索→安全门→生成→引用校验)— BE-1,W2
- [ ] 引用校验(步骤必须对应检索到的手册片段)— BE-1,W2

## 约定

- API key 只放 `.env`,任何代码、日志、commit 中不得出现 key
- mock 模式永远可用:`pytest` 与课堂演示不依赖网络与 key
- 照片处理后即删,不持久化原图(隐私红线,见 PRD 第 11 节)
