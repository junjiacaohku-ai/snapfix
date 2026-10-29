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
- Bosch E24：洗碗机排水场景，型号未知时转专业处理。
- 高危描述：返回 `refused`，步骤为空。安全规则保留BE-1的 `check/SafetyVerdict` 接口；合并BE-1分支时需保留本次新增规则和回归测试。
- 无效、过暗、模糊或过小的图片返回422；未知演示文件名也返回422。设备识别暂按文件名选场景。
- 未知品牌/错误码返回404。反馈仅接受 `done/not_useful/skipped`，报修语言仅接受 `zh/en`。
- 报修草稿保存到数据库，照片由发送者另附。

图片阈值是演示版启发式检查，不是已经完成手机端标定的识别模型。当前实测记录见 `experiments/acceptance-results.json`、`safety-results.json` 和 `server-check.json`。
