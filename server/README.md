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
