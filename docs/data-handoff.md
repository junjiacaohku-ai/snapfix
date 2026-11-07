# 数据和接口说明

在 `server/` 安装依赖后运行：

```sh
python corpus.py data/manifest.json data/chunks.json
python corpus_store.py --database data/snapfix.db
python -m pytest tests -q
python experiments/run_acceptance.py
python experiments/run_server_checks.py
uvicorn main:app --reload
```

`manuals.json` 和 `chunks.json` 对应PRD的手册表和切块表，来源、页码等附加信息存在 `chunk_metadata`。重复导入会更新本批手册，保留其他手册。数据默认写入 `data/snapfix.db`，可用 `SNAPFIX_DB` 指定其他文件。诊断、反馈、报修草稿都保留在同一数据库，照片不保存。

检索可用 `Retriever(read_chunks(database)).search(...)`。支持类别、品牌别名、错误码和已核实的手册ID；E:24与E24等价，E240不同。章节名是规则识别的，原页码可回查；45个稀疏页、6个解码失败页记录在 `extraction-audit.json`，没有把这些页面当作完整可用文本。

接口约定：
- Bosch E24：洗碗机排水场景，型号未知时转专业处理；手动诊断会查询真实语料，目前不生成维修步骤。
- 高危描述：返回 `refused`，步骤为空。三条后端分支已在本地统一为一套 `check/SafetyVerdict` 规则和回归测试。
- 无效、过暗、模糊或过小的图片返回422；未知演示文件名也返回422。设备识别暂按文件名选场景。
- 未知品牌/错误码返回200，明确提示无可用引用且步骤为空，不回退成E24。反馈仅接受 `done/not_useful/skipped`，报修语言仅接受 `zh/en`。
- 报修草稿保存到数据库，照片引用只是文字，实际照片由发送者另附。

图片阈值是演示版启发式检查，不是已经完成手机端标定的识别模型。当前实测记录见 `experiments/acceptance-results.json`、`safety-results.json` 和 `server-check.json`。

## 下一阶段对接

后端、FE-1 和 FE-2 已在 `integration/w3-product` 集成。W2 基线已推送并开验收 PR #8；W3 分支继续完成真实管线、统一产品 UI、安全门和原图隐私整改，尚未合并到 `main`。

- **BE-2（史珺瑛）**：保留加权 `Retriever.search()`、SQLite 和双语报修集成，不再维护另一份安全门。Session 新增 `source_mode` 并有旧库自动迁移。
- **BE-1（曹峻嘉）**：真实管线代码已接入质量门、Gemini 视觉、检索、安全门、结构化生成和引用校验；替代 provider 测试通过，在线 key 验收仍需执行。
- **FE-1／FE-2（朱雨泰民、杨蕊嘉）**：产品 UI 在能力可用时统一调用 v1 图片/手动诊断并导入 UI 记录；无真实能力时明确显示未支持或提供显式预览，不静默伪造诊断。E24 未核实型号时不提供自行拆装步骤，原始照片只保留文件名引用。
- **张帆**：联调时按 `demo-runbook.md` 补当前版本的模拟器截图和实际耗时；补真实会议与贡献记录，更新报告。替代照片可以用于流程演示，不能当作真实故障识别准确率证据。
