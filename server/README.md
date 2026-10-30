# SnapFix Server

Python 3.11+。在本目录运行：

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python corpus_store.py --database data/snapfix.db
python -m pytest tests -q
uvicorn main:app --reload
```

接口文档：http://127.0.0.1:8000/docs

图片会经过实际质量检查和规则安全检查，设备识别暂用离线场景。演示文件名：`router.jpg`、`e24.jpg`、`billy.jpg`、`microwave.jpg`、`report.jpg`。必须上传有效图片，不能用空文件模拟。暗图和模糊图按图片内容判断，文件名不影响质量结果。

手动输入 `Bosch`/`博世` + `E24`/`E:24` 返回洗碗机场景。未知手册返回404，图片问题返回422。健康接口如实返回 `mock: true`，不调用模型服务。

默认数据库为 `data/snapfix.db`，可通过 `SNAPFIX_DB` 改路径。诊断、反馈和报修草稿会保存，删除诊断会一起删除相关步骤和草稿；照片不落盘，报修发送时另附。测试使用独立临时数据库。

数据与实验：

```sh
python corpus.py data/manifest.json data/chunks.json
python experiments/run_retrieval.py
python experiments/evaluate_scenarios.py
python experiments/evaluate_quality.py
python experiments/build_quality_variants.py
python experiments/evaluate_quality_variants.py
python experiments/evaluate_safety.py --gate safety_gate.py --revision local --output experiments/safety-results.json
python experiments/run_acceptance.py
# 备用机可指定名称和输出文件，避免覆盖已有记录
python experiments/run_acceptance.py --label demo-backup --output ../demo-backup.json
python experiments/run_server_checks.py
```

语料包括15份厂家说明书和1份安全资料；来源、页码和排除页面都有记录。格式与接口细节见 [交接说明](../docs/data-handoff.md)，本次结果见 [完成情况](../docs/review-audit.md)。

换电脑演示和手机验收步骤见[演示清单](../docs/demo-runbook.md)。

替代素材检查及给队友的图片包（含来源和许可）：

```sh
python experiments/evaluate_demo_alternatives.py
python experiments/package_demo_assets.py --output ../snapfix-demo-inputs.zip
```
